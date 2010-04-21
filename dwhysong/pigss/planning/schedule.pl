#!/usr/bin/perl
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
#	Switch input times from local to UT

use Getopt::Long;
use Astro::Telescope;
use Astro::Coords;
use Astro::Time;
use MLDBM::Sync;
use MLDBM qw(MLDBM::Sync::SDBM_File Storable);
use ASTRO_UTIL;
use Fcntl qw(:DEFAULT :flock);
use ATA;

#use strict;


# Constant parameters
$PI = 3.1415926535897932384626433832795028841971693993751;
$PI_2 = $PI/2.0;
$minmoondist = 10; # in degrees
$minmoondist /= 57.29577951; # convert to radians
$minsundist = 30; # in degrees
$minsundist  /= 57.29577951; # convert to radians
$maxairmass = 2;


sub score {
	my %obj=@_;

	my $ha=abs($obj{'ha'}+$obslen/2.0);	# hour angle at center of obs
	my $score = (($PI_2-$obj{'dec'}) * (12-$ha))**2 * (6.0-$ha) / abs(6.0-$ha);
	$score *= $obj{prio}/(12*$PI)**2;

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

	($mdist, $mpa) = dist_pa($m_ra, $m_dec, $obj_ra, $obj_dec);
	($sdist, $spa) = dist_pa($s_ra, $s_dec, $obj_ra, $obj_dec);

	return($mdist,$sdist);
}


sub open_sched_rw {
	$db = tie %data, 'MLDBM::Sync', "$filename", O_CREAT|O_RDWR, 0640 or die $!;
	$db->Lock;
}


sub open_sched_ro {
	$db = tie %data, 'MLDBM::Sync', "$filename", O_CREAT|O_RDWR, 0640 or die $!;
	$db->Lock;
}


sub close_sched {
	$db->UnLock;
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


sub by_alt {
	# Get the name. Use temporary variables because $a and $b are always
	# passed by reference.
	my $tmpa = $a;
	my $tmpb = $b;
	$tmpa =~ s/^(.+?),.*/$1/;
	$tmpb =~ s/^(.+?),.*/$1/;
	# Get rid of any whitespace around the name, but not *in* the name
	$tmpa =~ s/^\s*(.*?)\s*$/$1/;
	$tmpb =~ s/^\s*(.*?)\s*$/$1/;
	return ($alt{$tmpb} <=> $alt{$tmpa});
}


sub by_heuristic {
	# $a and $b are passed by reference.
	#my %ax = %$a;
	#my %bx = %$b;

	return ($b->{'score'} <=> $a->{'score'});
}


sub by_dist {	# sort by distance to coordinates specified in global variables $cra, $cdec
	return ($b->{'dist'} <=> $a->{'dist'});
}


# *****************************************************************************
# *************************** START OF MAIN PROGRAM ***************************
# *****************************************************************************

# TODO add options for:
#	sorting list (sort by ha (hour angle), ra, airmass, alt, priority, etc.
#	list all targets with a certain name
#	list all targets withing some radius of a specified RA/DEC


$filename = '/etc/observatory/schedule';
$add = $mod = $query = $timestr = '';
$list = $get = $init = $remove = $usedist = 0;
Getopt::Long::Configure ("bundling");
GetOptions     ('file|f=s' => \$filename,
		'add|a' => \$add,
		'help|h' => \$help,
		'remove|delete|r|d=s' => \$remove,
		'list|l' => \$list,
		'get|g' => \$get,
		'dist|d' => \$usedist,
		'number|n=i' => \$nfields,
		'time|t=s' => \$timestr,
		'end|e=f' => \$end,
		'modify|m=s' => \$mod,
		'priority|p=s' => \$prio,
		'initialize|i' => \$init,
		'verbose|v' => \$verbose,
		'query|q=s' => \$query);

if ($help) {
	print "Survey schedule manager\tCopyright (c) 2006-2009 David Whysong\n\n";
	print "Arguments:\n";
	print "\t--add\t\tadd a target to the database\n";
	print "\t--get [time]\tuse heuristic to select a target, to be observed for [time] hours\n";
	print "\t  --dist\t\t\tuse Geoff's distance-based algorithm\n";
	print "\t  --number [#]\t\t\tnumber of fields to get\n";
	print "\t  --end [dd/mm/yyyy/hh:mm:ss]\tspecify end time (local TZ)\n";
	print "\t  --time [dd/mm/yyyy/hh:mm:ss]\tspecify start time (local TZ)\n";
	print "\t--list\t\tlist all targets\n";
	print "\t--file\t\tselect database file\n";
	print "\t--remove [name]\tremove a target\n";
	print "\t--delete [name]\tremove a target\n";
	print "\t--modify [name]\tmodify parameters for a target\n";
	print "\t--priority [name]=[#]\tset priority of a target to [#]\n";
	print "\t\t\tPriorities range from 0 to 10.\n";
	print "\t--query [name]\tprint current data for a target\n";
	print "\t--verbose\tprint extra information\n";
	print "\t--initialize\tcreate a new database, erasing all targets\n";
	print "\t--help\t\tshow this text.\n\n";
	exit();
}

if (($add ne '') + ($remove > 0) + $list + $get + ($mod ne '') + $init + ($query ne '') > 1) {
	die ("Error: multiple operations specified. I'm confused! Giving up.\n");
}
if ($timestr eq '') {
	$date = DateTime->now(time_zone=>'UTC');
}
else {
	$date = parse_string_time($timestr);
}

if ($get) {
	die("End time not specified!\n") if (!defined $end);
	$end = parse_decimal_time($end,$date);
	if ($end < $date) {
		$end->add(days=>1);
	}
	die "Adjusted end time is still before start time.\n" if ($end < $date);
	$obslen = $end->subtract_datetime_absolute($date)->seconds;
	$obslen /= 3600.0;
	print "Observation length: $obslen hours\n" if ($verbose);
	die("Invalid observation length\n") if ($obslen<0);
	die("Number of targets not specified!\n") if (!defined $nfields);
	die "Must observe at least 1 field\n" if ($nfields<1);
}
if ($add + $remove + $list + $get + ($mod ne 0) + $init + $query == 0) {
	die ("No operation specified.\n");
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


if ($list) {
	open_sched_ro();
	%tmp = %data;
	delete $tmp{last};		# Don't show the non-target hash element
	delete $tmp{index};		# Don't show the index

	@keys = keys %tmp;
	$nelem = scalar @keys;
	if ($nelem == 0) {
		print "Schedule is empty.\n";
		exit();
	}

	@keys = sort {$a<=>$b} @keys;
	foreach (@keys) {
		$ref = $tmp{$_};
		print "$_\t";
		while (($key,$value) = each %$ref) {
			if ($key eq 'ra') {
				print "RA=",rad2str($value,'h',2),"   ";
			}
			elsif ($key eq 'dec') {
				print "DEC=",rad2str($value,'d',1),"   ";
			}
			else {
				print "$key=$value  ";
			}
		}
		print "\n";
	}
	close_sched;
	exit();
}


if ($add) {
	print "Input targets in ATA standard format:\n";
	print "\t\t\t\tHours!\t\tDegrees!\n";
	print "ata\tblank\t3c147-0001\t13.5612078\t27.2893508\tgcb\n";
	open_sched_rw();
	%index = $data{index};
	$num = $data{last};
	while (<>) {
		chomp;
		($proj,$name,$field,$ra,$dec,$obsrvr)=split(/\s+/);
		$num++;

		($field eq '') and die "Error: name must be specified.\n";
		$tmp{'name'} = $field;

		($ra eq '') and die "Error: right ascention must be specified.\n";
		$tmp{'ra'} = $ra*$PI/12.0;	# convert hours to radians
		
		($dec eq '') and die "Error: declination must be specified.\n";
		$tmp{'dec'} = $dec*$PI/180.0;	# convert degrees to radians

		$tmp{prio} = 4;

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

if ($get) {	# Find targets to observe
	open_sched_ro();
	%tmp = %data;
	delete $tmp{last};
	delete $tmp{index};
	close_sched();

	$tel = observatory_load;

	@keys = keys %tmp;
	$nelem = scalar @keys;

	foreach (@keys) {
		my $ref = $tmp{$_};
		my %obj = %$ref;

		my $coords = new Astro::Coords( 'name' => $obj{'name'},
					'ra'   => $obj{'ra'},
					'dec'  => $obj{'dec'},
					'type' => 'J2000',
					'units'=> 'radians');
		$coords->telescope($tel);
		$coords->datetime($date);

		next if ($obj{prio}==0);
		$el=$coords->el(format=>'d');
		next if ($el<20);

		# Discard targets that do not remain above the el limit
		$tset=$coords->set_time(horizon=>20*$PI/180.0, event=>1);
		if (defined $tset) {
			if ($end > $set) {
				$rise=$coords->rise_time(horizon=>20*$PI/180.0, event=>-1);
				next if ($rise < $date)	# Target is already up, and sets during the observation
			}
		}

		# Discard anything too close to the moon or sun.
		($mdist,$sdist) = calc_distances($coords,$date,$tel);
		next if ($mdist < $minmoondist);
		next if ($sdist < $minsundist);

		# Store the target ID number
		$obj{'id'} = $_;

		# Store the parallactic angle
		#$obj{'parang'} = $coords->pa(format=>'r');

		# Store the hour angle
		$obj{'ha'} = $coords->ha(format=>'r')*12.0/$PI;

		# May want to consider a heuristic that mixes priority with HA
		# / altitude... better to get a lower priority target at zenith
		# instead of a high priority target at airmass 5.

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
		foreach $obj (@newlist) {
			$ra = $obj->{'ra'};
			$dec = $obj->{'dec'};
			$obj{'dist'} = dist_pa($ra,$dec,$cra,$cdec);
		}
		@newlist = sort by_dist @newlist;
		unshift(@newlist,$first);
	}

	for ($i=0; $i<$nfields; $i++) {
		if (scalar @newlist == 0) { exit(); }
		$ref = $newlist[$i];
		%obj = %$ref;

		print $obj{'name'},"\n";

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
			my ($mdist, $mpa) = dist_pa($m_ra, $m_dec, $obj_ra, $obj_dec);
			my ($sdist, $spa) = dist_pa($s_ra, $s_dec, $obj_ra, $obj_dec);
			print $coords->status;
			$ra=$coords->ra(format=>'r')*12.0/$PI;
			$dec=$coords->dec(format=>'d');
			printf "ATA coordinates: $ra,$dec\n";
			printf "Angular separation from moon: %.1f degrees\n",$mdist*57.29577951;
			printf "Angular separation from sun:  %.1f degrees\n",$sdist*57.29577951;
			print "Priority: ",$obj{prio},"\n";
			print "Score: ",$obj{'score'},"\n\n";
		}
	}
	exit();
}


if ($mod) {
	open_sched_rw();
	%mydata = %data;
	$ref = $mydata{index};
	%index=%$ref;
	$num= $index{$mod};
	$ref = $mydata{$num};
	%obj = %$ref;
	die "No such object found in database\n" if (!defined(%obj));

	print "RA and Dec are specified in radians!\n";
	foreach $key (keys(%obj)) {
		next if ($key eq 'name');
		print "$key: [",$obj{$key},"]: ";
		$_=<>;
		chomp;
		if ($_ ne '') {
			$obj{$key} = $_;
		}
	}

	$data{$num} = \%obj;

	close_sched();
	exit();
}


if ($prio) {
	($name, $p)=split('=',$prio);
	die "Priority must be from 0 to 10.\n" if (($p>10) || ($p<0));
	die "Please specify priority.\n" if (!defined($p));
	open_sched_rw();
	$ref = $data{index};
	%index=%$ref;
	$num= $index{$name};
	$ref = $data{$num};
	%obj = %$ref;
	die "No such object found in database\n" if (!defined(%obj));
	$obj{prio}=$p;
	$data{$num} = \%obj;
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
	$tel = observatory_load ('/etc/observatory/location');
	open_sched_ro();
	%tmp = %data;
	$ref = $tmp{index};
	%index=%$ref;
	$key = $index{$query};
	$ref = $tmp{$key};
	%obj = %$ref;
	die "No such object found in database\n" if (!defined(%obj));

	my $coords = new Astro::Coords( name => $obj{'name'},
					ra   => $obj{'ra'},
					dec  => $obj{'dec'},
					type => 'J2000',
					units=> 'radians');
	$coords->telescope($tel);
	$coords->datetime($date);

	print $coords->status;

	($dist,$sdist)=calc_distances($coords,$date,$tel);
	printf "Angular separation from moon: %.1f degrees\n",$dist*57.29577951;
	printf "Angular separation from sun:  %.1f degrees\n",$sdist*57.29577951;
	print "Target priority: ",$obj{prio},"\n";
	print "Target score: ",score($obj),"\n";
	close_sched();
	exit;
}
