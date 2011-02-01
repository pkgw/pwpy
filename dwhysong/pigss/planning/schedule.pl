#!/usr/bin/perl -w
# Schedule control: a non-interactive program to manage the target database.
#
# Schedule is a hash of hashes.
# Required fields:
# Name (str)
# Priority (int)
# ra (str)	J2000 only!
# dec (str)
#
# TODO:
#	Have autoreduce.pl generate a report that we parse
#	Add fields to database for epoch / RMS

$TZ = 'America/Los_Angeles';
$MINDELTA = 90 * 86400;	# 90 days in seconds

use DateTime;
use Getopt::Long;
use Astro::Telescope;
use Astro::SLA ();
use Astro::Coords;
use Astro::Time;
use DateTime::Format::Strptime;
use MLDBM::Sync;
use MLDBM qw(MLDBM::Sync::SDBM_File Storable);
use POSIX qw(floor);
use Fcntl qw(:DEFAULT :flock);
use ASTRO_UTIL;
use ATA;

#use strict;


# Constant parameters
$PI = 3.1415926535897932384626433832795028841971693993751;
$minmoondist = 10; # in degrees
$minmoondist /= 57.29577951; # convert to radians
$minsundist = 30; # in degrees
$minsundist  /= 57.29577951; # convert to radians


sub score {
	my %obj=@_;
	# Gymnastics with (6-$ha) are to handle circumpolar issues
	#my $ha=abs($obj{'ha'}+$obslen/2.0);	# hour angle at center of obs
	#my $sign = ($ha > 6) ? -1 : 1;		# negative if hour angle > 6 (for circumpolar targets at low el)
	#my $score = (($PI_2-$obj{'dec'}) * (12-$ha)) * $sign;				# both ha and dec
	#$score /= (12*$PI);								# normalize for both ha and dec
	my $ha=abs($obj{'ha'}+$obslen/2.0);						# hour angle at center of obs
	my $score = 6-POSIX::floor($ha);						# ha only
	$score /= 6;									# normalize for ha only

	# Score based on number of obesrved neighbors
	my $nlist = $obj{'extneighbors'};
	if ($nlist) {
		my $count = 0;
		foreach my $nname (split(/,/,$nlist)) {	# Loop over extneighbor list ($nname is the name of a neighbor)
			my $key = $index{$nname};
			my $ref = $tmp{$key};
			die "obj $obj{name} neighbor $nname ref $ref not defined\n" if (!defined %$ref);
			$count++ if ($ref->{prio} < $p);	# Increase score if a neighbor was observed
			if ($ref->{observable}==0) {		# Decrease score if we're at the edge of observable sky
				$count-=2;
			}
		}
		$count /= scalar(@_=split(/,/,$nlist));
		$score += $count;
	} else { die "no extneighbors list found\n"; }
	return($score);
}


sub calc_distances {
	my $coords=shift;
	my $date=shift;
	my $tel=shift;

	$coords->datetime($date);
	my $obj_ra = $coords->ra_app;
	my $obj_dec = $coords->dec_app;
	my $moon = new Astro::Coords(planet => 'moon');
	$moon->telescope($tel);
	$moon->datetime($date);
	my $m_ra = $moon->ra_app;
	my $m_dec = $moon->dec_app;
	my $sun = new Astro::Coords(planet => 'sun');
	$sun->telescope($tel);
	$sun->datetime($date);
	my $s_ra = $sun->ra_app(format=>'r');
	my $s_dec = $sun->dec_app(format=>'r');

	$mpa=$spa=0;	# Avoid warning
	($mdist, $mpa) = dist_pa($m_ra, $m_dec, $obj_ra, $obj_dec);
	($sdist, $spa) = dist_pa($s_ra, $s_dec, $obj_ra, $obj_dec);

	return($mdist,$sdist);
}


sub open_sched_rw {
	$db = tie %data, 'MLDBM::Sync', "$filename", O_CREAT|O_RDWR, 0640 or die $!;
	$db->Lock;
}


sub open_sched_ro {
	$db = tie %data, 'MLDBM::Sync', "$filename", O_CREAT|O_RDONLY, 0640 or die $!;
	$db->Lock;
}


sub close_sched {
	$db->UnLock;
}


sub parse_string_date {
	my $str=shift;
	my $TZ=shift;
	my $date;
	my $parser;
	my $format;
	my $nfields;
	@_ = split(/\//,$str);
	$nfields = scalar(@_);

	if ($nfields == 2) {
		$format='%m/%d/%Y';
		$parser = DateTime::Format::Strptime->new( pattern => $format, time_zone => $TZ, on_error => 'croak');
		my $tmpdate = DateTime->now(time_zone=>$TZ)->truncate(to=>'year');
		$date=$parser->parse_datetime($str."/".$tmpdate->year);
	}
	else {
		my @tmp=split(/\/|-/,$str);
		if (length($tmp[2])==4) { $format = '%m/%d/%Y'; }
		elsif (length($tmp[2])==2) { $format = '%m/%d/%y'; }
		else { die "Bad date string $str: year should have either 2 or 4 digits.\n"; }
		$parser = DateTime::Format::Strptime->new( pattern => $format, time_zone => $TZ, on_error => 'croak');
		$date=$parser->parse_datetime($str);
	}
	return $date;
}



sub parse_string_time {
	my $str = shift;
	my @tmp;
	my $date;

	@tmp = split(/:|\//,$str);
	if (scalar(@tmp)==3) {	# Time only
		$date = DateTime->now(time_zone=>'local');
		$date->set(hour=>$tmp[0]);
		$date->set(minute=>$tmp[1]);
		$date->set(second=>$tmp[2]);
		$date->set(nanosecond=>0);
	}
	elsif (scalar(@tmp)==6) {
		$date = DateTime->new(year=>$tmp[2],
				month=>$tmp[1],
				day=>$tmp[0],
				hour=>$tmp[3],
				minute=>$tmp[4],
				second=>$tmp[5],
				nanosecond=>0,
				time_zone=>'local');
	}
	else { die "Bad time string. Format is: dd/mm/yyyy/hh:mm:ss\n"; }
	$date->set_time_zone('UTC');
	
	return $date;
}

sub parse_decimal_time {
	my $t = shift;
	my $d = shift;
	my $tmp;

	if (!defined($d)) { $d = DateTime->now(time_zone=>'local'); }
	else { $d=$d->clone->set_time_zone('local'); }
	$d->set(hour=>int($t));
	$tmp = $t-int($t);
	$d->set(minute=>int(60*$tmp));
	$tmp *= 60;
	$tmp = $tmp-int($tmp);
	$d->set(second=>int(60*$tmp));
	$d->set(nanosecond=>0);
	$d->set_time_zone('UTC');

	return($d);
}

sub by_priority {
	my $x = $a{prio};
	my $y = $b{prio};
	return ($y <=> $x)
}


sub by_el {
	my $x = $a{'el'};
	my $y = $b{'el'};
	return ($y <=> $x)
}


sub by_heuristic { # $a and $b are passed by reference.
	my $i = ($b->{prio} <=> $a->{prio});
	if ($i) {
		return ($i);
	}
	return ($b->{'score'} <=> $a->{'score'});
}


sub by_dist {	# sort by distance to coordinates specified in global variables $cra, $cdec
	return ($a->{'dist'} <=> $b->{'dist'});
}


sub observable {
	my $hashref = shift;
	my $tel = shift;
	my $start = shift;
	my $end = shift;

	my %tmp = %$hashref;
	my @keys = keys %tmp;
	my $nelem = scalar @keys;
	my $nset=0;
	my $nclose=0;
	my $ndown=0;

	$p = 5 - $pass;

	foreach (@keys) {
		next if ($_ eq 'index' or $_ eq 'last');
		my $ref = $tmp{$_};

		my $coords = new Astro::Coords( 'name' => $ref->{'name'},
					'ra'   => $ref->{'ra'},
					'dec'  => $ref->{'dec'},
					'type' => 'J2000',
					'units'=> 'radians');
		$coords->telescope($tel);
		$coords->datetime($start);

		if ($ref->{prio} < $p) {
			$ref->{observable}=-1;		# Observed too many times
			next;
		}
		if ($ref->{prio} > $p) {
			$ref->{observable}=0;		# Hasn't been observed enough
			next;
		}

		# If pass>1, mark as unobservable if less than 3 months elapsed from the previous pass
		if ($pass > 1) {
			$key = "obsdate" . ($pass-1);	# key to the date of the previous observation
			if ($start < $ref->{$key}) {
				die "Error: $ref->{name} is marked as observed on $ref->{$key} which is after our observation starts ($start)";
			}
			$delta = $start->subtract_datetime_absolute($ref->{$key})->seconds;
			if ($delta < $MINDELTA) {
				$ref->{observable}=-1;
				next;
			}
		}

		# Short-circuit: discard anything below 20 degrees elevation
		if ($coords->el(format=>'d') < 20) {
			$ref->{observable}=0;
			$ndown++;
			next;
		}

		# Discard anything too close to the moon or sun.
		($mdist,$sdist) = calc_distances($coords,$start,$tel);
		if (($mdist < $minmoondist) or ($sdist < $minsundist)) {
			$ref->{observable}=0;
			$nclose++;
			next;
		}

		# Discard targets that do not remain above the el limit. Very expensive computation!
		my $tset=$coords->set_time(horizon=>$PI/9.0, event=>1);	# Majority of run time is spent here
		if (defined $tset) {
			if ($tset < $start) {
				print $ref->{name}." sets at $tset. Observation starts at $start and ends at $end\n";
				print "Coordinate object time is: ".$coords->{DateTime} . "\n";
				die "Error! set_time() returned a value that is before the beginning of the observation.\n";
			}
			if ($end > $tset) {				# Target sets during the observation
				$ref->{observable}=0;
				$nset++;
				next;
			}
		}
		$ref->{observable}=1;
	}
	if ($verbose) {							# Calculate and print the totals
		my ($ngood,$nbad,$ndone);				# I do this in a separate loop for efficiency
		$ngood = 0;
		$nbad = 0;
		$ndone = 0;
		foreach (@keys) {
			next if ($_ eq 'index' or $_ eq 'last');
			$ref = $tmp{$_};
			$ndone++ if ($ref->{observable}==-1);
			$ngood++ if ($ref->{observable}==1);
			$nbad++ if ($ref->{observable}==0);
		}
		print "Found $ngood observable fields, $nbad unobservable, and $ndone completed.\n";
		print "Of unobservables, $ndown are down, $nset will set, and $nclose are too close to the sun or moon.\n";
	}
	return $hashref;
}


# *****************************************************************************
# *************************** START OF MAIN PROGRAM ***************************
# *****************************************************************************

# TODO add options for:
#	sorting list (sort by ha (hour angle), ra, airmass, alt, priority, etc.
#	list all targets with a certain name
#	list all targets withing some radius of a specified RA/DEC


$filename = '/etc/observatory/pfhex';
$add = $mod = $query = $timestr = $list = $remove = $prio = $observe = $fixdate = '';
$get = $init = $usedist = $status = $verify = 0;
@prio = ();
@mod = ();
$pass = 1;
$nfields = 10000000;
$myprio = 4;
Getopt::Long::Configure ("bundling");
GetOptions     ('file|f=s' => \$filename,
		'add|a' => \$add,
		'help|h' => \$help,
		'remove|r=s' => \$remove,
		'list|l=s' => \$list,
		'get|g' => \$get,
		'dist|d' => \$usedist,
		'pass|x=i' => \$pass,
		'number|n=i' => \$nfields,
		'time|t=s' => \$timestr,
		'end|e=f' => \$end,
		'date=s' => \$fixdate,
		'modify|m=s' => \@mod,
		'observe|o=s' => \$observe,
		'priority|p=s' => \@prio,
		'initialize|i' => \$init,
		'verbose|v' => \$verbose,
		'verify' => \$verify,
		'status|s' => \$status,
		'query|q=s' => \$query);

if ($help) {
	print "Survey schedule manager\tCopyright (c) 2006-2009 David Whysong\n\n";
	print "Arguments:\n";
	print "\t--add|a\t\tadd targets to the database\n";
	print "\t--get|g\t\tuse heuristic to select a target\n";
	print "\t--status|s\tprint status information for plan.pl\n";
	print "\t  --dist|d\tuse Geoff's distance-based algorithm\n";
	print "\t  --number|n [#]\tnumber of fields to get\n";
	print "\t  --end|e [hh.]\tspecify end time (decimal hours, local TZ)\n";
	print "\t  --time|t [dd/mm/yyyy/hh:mm:ss]\tspecify start time (local TZ)\n";
	print "\t  --pass|x [#]\tselect fields for pass # (i.e. have been observed #-1 times)\n";
	print "\t--list [query]\tlist all targets\n";
	print "\t\t\t  where query is 'prio','date','obs', or 'all\n";
	print "\t--file\t\tselect database file\n";
	print "\t--remove [name]\tremove a target\n";
	print "\t--modify [name]\tmodify parameters for a target\n";
	print "\t--observe [date],[name]...\tmark target as observed on [date] (format mm/dd/yy or mm/dd)\n";
	print "\t--fixdate [date],[name]...\tchange observation dates (format mm/dd/yy or mm/dd)\n";
	print "\t--priority [name]=[#]\tset priority of a target to [#]\n";
	print "\t\t\tPriorities range from 0 to 10.\n";
	print "\t--query [name]\tprint current data for a target\n";
	print "\t--verify\tverify database integrity\n";
	print "\t--verbose\tprint extra information\n";
	print "\t--initialize\tcreate a new database, erasing all targets\n";
	print "\t--help\t\tshow this text.\n\n";
	exit();
}

die "Error: invalid value, pass < 1\n" if ($pass < 1);
if ($pass == 2) { $myprio = 3; } 
elsif ($pass > 2) { die("Error: invalid value, pass > 2 not supported\n"); }

if (($add ne '') + (scalar @prio > 0) + ($observe ne '') + ($fixdate ne '') + ($remove ne '') + ($list ne '') + $get + $status + $verify + (scalar @mod > 0) + $init + ($query ne '') > 1) {
	print "schedule.pl ",@ARGV;
	die ("Error: multiple operations specified. I'm confused! Giving up.\n");
}
if (($add eq '') + (scalar @prio) + ($observe ne '') + ($fixdate ne '') + ($remove eq '') + ($list eq '') + $get + $status + $verify + (scalar @mod > 0) + $init + ($query eq '')  == 0) {
	die "No operation specified.\n";
}

if ($timestr eq '') {
	$date = DateTime->now(time_zone=>'UTC');
}
else {
	$date = parse_string_time($timestr);
}

if ($get or $status) {
	die "End time not specified!\n" if (!defined $end);
	$end = parse_decimal_time($end,$date);
	if ($end < $date) {
		$end->add(days=>1);
	}
	die "Adjusted end time is still before start time.\n" if ($end < $date);
	$obslen = $end->subtract_datetime_absolute($date)->seconds;
	$obslen /= 3600.0;
	print "Observation length: $obslen hours\n" if ($verbose);
	print "Observation ends at: $end\n" if ($verbose);
	die "Invalid observation length\n" if ($obslen<0);
	#die "Number of targets not specified!\n" if (!defined $nfields); # unnecessary, now with default large value
	die "Must observe at least 1 field\n" if ($nfields<1);
}


# Database structure:
#
# %data is a hash which indexes each target in the list by target number.
# $data{last} is an integer corresponding to the last target in the list.
#
# Have to access data like this:
# $tmp = $mldb{key};			# retrieve value
# $tmp->{subkey}[3] = 'stuff';
# $mldb{key} = $tmp;			# store value
#
# see:
# http://htmlfixit.com/cgi-tutes/tutorial_Perl_Primer_014_Advanced_data_constructs_A_hash_of_hashes.php
# http://htmlfixit.com/cgi-tutes/tutorial_Perl_Primer_013_Advanced_data_constructs_An_array_of_hashes.php


# Print ATA status normally; extra information if $verbose
if ($list ne '') {
	sub quote { qq!"$_[0]"! }
	if ($list eq 'ata') {
		$printstr='pigss2 blank $$ref{name} $ra $dec dhw\n';
	}
	elsif ($list eq 'prio') {
		$printstr='$$ref{name} prio=$$ref{prio}\n';
	}
	elsif ($list eq 'obs') {
		$printstr='$$ref{name} prio=$$ref{prio} date=$$ref{date}\n';
	}
	elsif ($list ne 'all') {
		die "List option must be followed by type: --list ata, --list all, --list prio\n";
	}

	open_sched_ro();
	%tmp = %data;
	close_sched;
	delete $tmp{last};		# Don't show the non-target hash element
	delete $tmp{index};		# Don't show the index

	@keys = keys %tmp;
	$nelem = scalar @keys;
	if ($nelem == 0) {
		print "Schedule is empty.\n";
		exit();
	}
	print "Database has $nelem elements\n" if $verbose;

	@keys = sort {$a<=>$b} @keys;
	foreach (@keys) {
		$ref = $tmp{$_};
		if ($list eq 'all') {
			print "$_\t";
			while (($key,$value) = each %$ref) {
				next if ($key eq 'name');
				print "$key=$value  ";
			}
			print "\n";
		}
		elsif ($list eq 'obs') {
			$str = "$$ref{name} prio=$$ref{prio}";
			foreach $tmp (keys %$ref) {
				if ($tmp =~ /obsdate/) {
					if (!defined($$ref{$tmp})) {
						$str = $str . " $tmp=undef";
					}
					else {
						$str = $str . " $tmp=$$ref{$tmp}";
					}
				}
			}
			print "$str\n";
		}
		else {
			$ra = $$ref{'ra'} * 12.0/$PI;
			$dec = $$ref{'dec'} * 180.0/$PI;
			print eval quote($printstr);
		}
	}
	exit();
}


if ($add) {
	print "Input targets in ATA standard format, optinally appending the neighbor list:\n";
	print "\t\t\t\tHours!\t\tDegrees!\n";
	print "ata\tblank\t3c147-0001\t13.5612078\t27.2893508\tgcb [neighbor1 neigbor2 ...]\n";
	open_sched_rw();
	%index = $data{index};
	$num = $data{last};
	while (<>) {
		chomp;
		my ($proj,$name,$field,$ra,$dec,$obsrvr, @neighbors)=split(/\s+/);
		$num++;

		($field eq '') and die "Error: name must be specified.\n";
		$tmp{'name'} = $field;

		($ra eq '') and die "Error: right ascention must be specified.\n";
		$tmp{'ra'} = $ra*$PI/12.0;	# convert hours to radians
		
		($dec eq '') and die "Error: declination must be specified.\n";
		$tmp{'dec'} = $dec*$PI/180.0;	# convert degrees to radians

		$tmp{prio} = 4;

		if (scalar(@neighbors) > 0) {
			$nlist = join(",",@neighbors);
			$tmp{'neighbors'}=$nlist;
		}

		$data{$num} = \%tmp;
		$index{$field} = $num;
	}
	$data{last} = $num;
	$data{index} = \%index;

	close_sched();
	exit();
}

if ($remove) {
	open_sched_rw();
	$ref = $data{index};
	%index = %$ref;
	$num = $index{$remove};
	die "No such object found in database\n" if (!defined(%num));
	delete $data{$num};
	close_sched();
	exit();
}

if ($status) {
	open_sched_ro();
	%tmp = %data;
	close_sched();
	delete $tmp{last};
	delete $tmp{index};

	$tel = observatory_load;
	observable(\%tmp,$tel,$date,$end);

	foreach (keys(%tmp)) {
		$ref = $tmp{$_};
		%obj = %$ref;
		@str = ('not observable','observable','observed');
		print $ref->{name}." ".$str[$ref->{observable}]."\n";
	}
	exit();
}



if ($get) {								# Find targets to observe
	open_sched_ro();
	%tmp = %data;
	close_sched();
	my $ref = $data{index};
	%index = %$ref;
	delete $tmp{last};

	my $tel = observatory_load;

	if ($verbose) {							# Let's find and print the LST
		my $long = (defined $tel ? $tel->long : 0.0);
		$long == 0.0 and warn "Telescope longitude is zero; undefined telescope?\n";
		my $lst1 = 12/$PI*(Astro::SLA::ut2lst($date->year,$date->mon,$date->mday,$date->hour,$date->min,$date->sec,$long))[0];
		my $lst2 = 12/$PI*(Astro::SLA::ut2lst($end->year,$end->mon,$end->mday,$end->hour,$end->min,$end->sec,$long))[0];
		printf "LST ranges from %.1f to %.1f\n",$lst1,$lst2;
	}

	observable(\%tmp,$tel,$date,$end);

	my @keys = keys %tmp;
	my $nelem = scalar @keys;

	# Check to see if we're starting a new pass.
	# If so, we haven't observed anything yet, so
	# we have to skip the neighbor list check.
	$first = 1;
	foreach (@keys) {
		next if ($_ eq 'index');
		$ref = $tmp{$_};
		my %obj = %$ref;
		$first = 0 if ($obj{prio} == $p-1);
	}

	foreach (@keys) {
		next if ($_ eq 'index');
		$ref = $tmp{$_};
		my %obj = %$ref;
		next unless ($obj{observable} == 1);

		my $coords = new Astro::Coords( 'name' => $obj{'name'},
					'ra'   => $obj{'ra'},
					'dec'  => $obj{'dec'},
					'type' => 'J2000',
					'units'=> 'radians');
		$coords->telescope($tel);
		$coords->datetime($date);

		# Discard targets that don't have an observed neighbor
		my $nlist = $obj{'neighbors'};
		if ($nlist ne '' and not $first) {
			my $ok=0;
			foreach my $nname (split(/,/,$nlist)) {
				my $key = $index{$nname};
				$ref = $tmp{$key};
				%neighbor = %$ref;
				if ($neighbor{prio} < $p) {
					$ok++;
					last;
				}
			}
			next unless $ok;
		}

		# Store the parallactic angle
		#$obj{'parang'} = $coords->pa(format=>'r');

		# Store the hour angle
		$obj{'ha'} = $coords->ha(format=>'r')*12.0/$PI;

		# Store the elevation
		$obj{'el'} = $coords->el();

		# Score for heuristic sort
		$obj{'score'} = score(%obj);

		push @newlist, \%obj;
	}
	@newlist = sort by_heuristic @newlist;

	print scalar(@newlist)," targets available to observe.\n" if ($verbose);
	if ($nfields > scalar(@newlist)) { $nfields=scalar(@newlist); }

	if ($usedist) {
		# Resort, this is Geoff's distance-based algorithm
		$first=shift(@newlist);
		$cra = $first->{'ra'};
		$cdec = $first->{'dec'};
		foreach $ref (@newlist) {
			$ra = $ref->{'ra'};
			$dec = $ref->{'dec'};
			$pa=$ok=0;	# Avoid warning
			($dist,$pa,$ok) = dist_pa($ra,$dec,$cra,$cdec);
			$ref->{'dist'}=$dist;
		}
		@newlist = sort by_dist @newlist;
		unshift(@newlist,$first);
	}

	for ($i=0; $i<$nfields; $i++) {
		if (scalar @newlist == 0) { exit(); }
		$ref = $newlist[$i];
		%obj = %$ref;

		print $obj{'name'},"\n" if (! $verbose);

		if ($verbose) {
			my $coords = new Astro::Coords( name => $obj{'name'},
							ra   => $obj{'ra'},
							dec  => $obj{'dec'},
							type => 'J2000',
							units=> 'radians');
			$coords->telescope($tel);
			$coords->datetime($date);

			my $obj_ra = $coords->ra_app;
			my $obj_dec = $coords->dec_app;
			print $coords->status;

			print "Telescope position:\n";
			print "Longitude: ",$tel->long("d")," degrees\n";
			print "Latitude : ",$tel->lat("d")," degrees\n";
			$tset = $coords->set_time(horizon=>$PI/9.0, event=>1);
			if (defined $tset) { print "Sets at: $tset\n"; }
			else { print "Target is circumpolar\n"; }
			$ra=$coords->ra(format=>'r')*12.0/$PI;
			$dec=$coords->dec(format=>'d');
			print "Coordinates from ATA: $ra,$dec\n";

			($dist,$sdist)=calc_distances($coords,$date,$tel);
			printf "Angular separation from moon: %.1f degrees\n",$dist*57.29577951;
			printf "Angular separation from sun:  %.1f degrees\n",$sdist*57.29577951;
			print "Target priority: ",$obj{prio},"\n";
			print "Priority: ",$obj{prio},"\n";
			print "Score: ",$obj{'score'},"\n\n";
		}
	}
	exit();
}


if (scalar(@mod)) {
	open_sched_rw();
	print "Press return to leave a value unchanged. Enter 'undef' to un-define a value\n";
	print "RA and Dec are specified in radians!\n";
	%mydata = %data;
	$ref = $mydata{index};
	%index=%$ref;
	foreach $mod (@mod) {
		$num= $index{$mod};
		$ref = $mydata{$num};
		%obj = %$ref;
		print "$obj{name}:\n";
		die "No such object found in database\n" if (! %obj);
		foreach $key (keys(%obj)) {
			next if ($key eq 'name');
			print "  $key: [",$obj{$key},"]: ";
			$_=<>;
			chomp;
			if ($_ eq 'undef') {
				delete $obj{$key};
			}
			elsif ($_ ne '') {
				$obj{$key} = $_;
			}
		}
		$data{$num} = \%obj;
	}
	close_sched();
	exit();
}


if (scalar(@prio)) {
	open_sched_rw();
	$ref = $data{index};
	%index=%$ref;
	foreach (@prio) {
		($name, $pr)=split('=',$_);
		$num = $index{$name};
		if (!defined($num)) {
			$verbose and warn "$name not found in database.\n";
			next;
		}
		$ref = $data{$num};
		%obj = %$ref;
		die "Please specify priority.\n" if (!defined($pr));
		die "Priority must be from 0 to 10.\n" if (($pr>10) || ($pr<0));
		$verbose and print "Setting $name to priority $pr\n";
		if ($pr==4) {		# Marking as un-observed
			@keys = grep(/obsdate/,keys(%obj));
			foreach(@keys) { delete $obj{$_}; }
		}
		$obj{prio}=$pr;
		$data{$num} = \%obj;
	}
	close_sched();
	exit();
}


# FIXME
# Ideally, this would ask for which obsdate # to change
if ($fixdate) {
	@fixdate= split ',',$fixdate;
	open_sched_rw();
	$ref = $data{index};
	%index=%$ref;
	$date = shift @fixdate;
	$date = parse_string_date($date,$TZ);
	foreach $name (@fixdate) {
		$num = $index{$name};
		if (!defined($num)) {
			$verbose and warn "$name not found in database.\n";
			next;
		}
		$ref = $data{$num};
		%obj = %$ref;
		$i = 'obsdate' . (4 - $obj{prio});
		$verbose and print "$name has priority $obj{prio}. Setting date of observation $i to $date\n";
		$obj{$i} = $date;
		$data{$num} = \%obj;
	}
	close_sched();
	exit();
}



if ($observe) {
	@observe = split ',',$observe;
	open_sched_rw();
	$ref = $data{index};
	%index=%$ref;
	$date = shift @observe;
	$date = parse_string_date($date,$TZ);
	foreach $name (@observe) {
		$num = $index{$name};
		if (!defined($num)) {
			$verbose and warn "$name not found in database.\n";
			next;
		}
		$ref = $data{$num};
		%obj = %$ref;
		$pr = $obj{prio}-1;
		$key = 'obsdate' . (4 - $pr);

		# If less than $MINDELTA time has passed since the previous
		# observation, print a warning and update the PREVIOUS obsdate
		$prevkey = "obsdate" . (4-$obj{prio});	# key to the date of the previous observation

		if (defined($obj{$prevkey})) {
			if ($date < $obj{$prevkey}) {
				die "Error: $obj{name} is marked as observed on $obj{$prevkey} which is later than $date";
			}
			$delta = $date->subtract_datetime_absolute($obj{$prevkey})->seconds;
			if ($delta == 0) {
				warn "$name is already marked as observed on this date. Skipping...\n";
				next;
			}
			elsif ($delta < $MINDELTA) {
				warn "Warning: $obj{name}: minimum elapsed time has not passed. Updating timestamp but not marking as observed.\n";
				$obj{$prevkey} = $date;
				$data{$num} = \%obj;
				next;
			}
		}
		elsif ($obj{prio} < 4) {	# Prio is not 4, but we have no obsdate...
			die "Error: corrupt database: $obj{name} has priority $obj{prio} but $prevkey is not defined.\n";
		}

		if (defined($obj{$key})) {
			if ($obj{$key} == $date) {
				warn "Error: corrupt database: $name is not marked as observed but the observation date $key exists. Skipping...\n";
				next;
			}
			else {
				die "Error: corrupt database: $name is not maked as observed for this pass, but an observation date exists for this pass.\n";
			}
		}
		else {
			$verbose and print "Setting $name to priority $pr and observation date $key to $date\n";
			$obj{prio} = $pr;
			$obj{$key} = $date;
			$data{$num} = \%obj;
		}
	}
	close_sched();
	exit();
}



# Create an empty schedule database
if ($init) {
	open_sched_rw();
	%data = (last => 0);
	close_sched();
	exit();
}

if ($query) {
	$tel = observatory_load;
	open_sched_ro();
	%tmp = %data;
	$ref = $tmp{index};
	%index=%$ref;
	$key = $index{$query};
	$ref = $tmp{$key};
	%obj = %$ref;
	die "No such object found in database\n" if (! %obj);

	$coords = new Astro::Coords( name => $obj{'name'},
					ra   => $obj{'ra'},
					dec  => $obj{'dec'},
					type => 'J2000',
					units=> 'radians');
	$coords->telescope($tel);
	$coords->datetime($date);

	print $coords->status;
	print "Telescope position:\n";
	print "Longitude: ",$tel->long("d")," degrees\n";
	print "Latitude : ",$tel->lat("d")," degrees\n";
	$tset=$coords->set_time(horizon=>20*$PI/180.0, event=>1);
	if (defined $tset) { print "Sets at: $tset\n"; }
	else { print "Target is circumpolar\n"; }
	($dist,$sdist)=calc_distances($coords,$date,$tel);
	printf "Angular separation from moon: %.1f degrees\n",$dist*57.29577951;
	printf "Angular separation from sun:  %.1f degrees\n",$sdist*57.29577951;
	print "Target priority: ",$obj{prio},"\n";
	if (defined($obj{neighbors})) { print "Neighbor list: $obj{'neighbors'}\n"; }
	if (defined($obj{extneighbors})) { print "Extended neighbor list: $obj{'extneighbors'}\n"; }
	close_sched();
	exit();
}

if ($verify) {
	open_sched_ro();
	%tmp = %data;
	close_sched;
	delete $tmp{last};		# Don't show the non-target hash element
	delete $tmp{index};		# Don't show the index

	@keys = keys %tmp;
	$nelem = scalar @keys;
	if ($nelem == 0) {
		print "Database is empty.\n";
		exit();
	}

	$num=0;
	$err=0;
	@essential = ('name','ra','dec','prio','neighbors','extneighbors');
	foreach $key (@keys) {
		$num++;
		$ref = $tmp{$key};
		%obj = %$ref;
		foreach $str (@essential) {
			if (!defined($obj{$str})) {
				if ($str eq 'name') {
					warn "Warning: object found with no name.\n";
					$err=1;
				}
				else {
					warn "Warning: $obj{name} has no $str field.\n";
					$err=1;
				}
			}
		}
		if (defined($obj{prio})) {
			$nobs = 4 - $obj{prio};
			for ($i=1; $i<=$nobs; $i++) {
				$str = "obsdate" . $i;
				if (!defined($obj{$str})) {
					warn "Warning: $obj{name} has prio $obj{prio} but $str is not defined.\n";
					$err=1;
				}
			}
		}
	}
	if ($num != $nelem) {
		warn "Error: inspected $num elements, but there should be $nelem.\n";
		$err=1;
	}
	exit($err);
}
