#!/usr/bin/env perl

# FIXME
#	Handle situation where I'm scheduling an observation that has already begun (e.g. use DateTime->now + 20 min instead of start time)
#

use POSIX qw(floor);
use DateTime;
use DateTime::Format::Strptime;
use Getopt::Long;
use Math::Trig 'great_circle_distance';
use Astro::Telescope;
use Astro::Time;
use Astro::SLA ();
use ATA;

$daily='coma';

BEGIN {
	$pass = 2;
	$ENV{"PATH"}="/home/dwhysong/pigss:/home/dwhysong/bin:/bin:/usr/bin";
	$PI = 3.1415926535897932384626433832795028841971693993751;
	$PI_2 = $PI/2.0;
	$TZ='America/Los_Angeles';

	Getopt::Long::Configure ("bundling");
	GetOptions     ('file|f=s' => \$filename,
                	'help|h' => \$help,
                	'number|n=f' => \$selectnfields,
                	'date|d=s' => \$selectdate,
			'interactive|i' => \$interactive,
			'block|b:f' => \$minblock,
			'test|t' => \$test,
			'pass|p=i' => \$pass,
			'unsafe|u' => \$unsafe,
                	'verbose|v' => \$verbose);

	if ($help) {
        	print "Survey schedule planner\tCopyright (c) 2010 David Whysong\n\n";
        	print "Arguments:\n";
        	print "\t--help\t\tshow this text.\n";
        	print "\t--file [name]\tread schedule from file [name]\n";
        	print "\t--interactive\tselect targets manually from ds9 plot\n";
        	print "\t--number [#]\tnumber of fields to observe per hour\n";
        	print "\t--date [mm/dd/yyyy]\tschedule only a particular date\n";
		print "\t--block [#]\tbreak up observations into blocks of at least # hours\n";
		print "\t--pass [#]\tobserve pass [#]\n";
		print "\t--test\ttest mode; do not generate schedules\n";
		print "\t--unsafe\tdo not perform (slow) consistency check\n";
        	print "\t--verbose\tprint extra information\n";
        	exit();
	}

	print "Finding targets for pass #$pass\n\n";

	if (!defined($PIGSS_DATABASE)) {
		$PIGSS_DATABASE='/etc/observatory/pfhex';
	} else {
		warn "Warning: using nonstandard database $PIGSS_DATABASE\n" if ($verbose);
	}

	# Make a copy of the database, and operate on that
	print "Copying database.\n";
	@dbfileext = ('.dir','.lock','.pag');
	unlink glob ".tmp/tmpdb*";
	foreach $ext (@dbfileext) {
		$file = $PIGSS_DATABASE . $ext;
		system("cp $file .tmp/tmpdb$ext");
	}
	$PIGSS_DATABASE='/home/dwhysong/pigss/.tmp/tmpdb';

#	sub fix_database {
#		$prio = 5 - $pass;
#		print "Resetting database priorities:\n";
#		foreach $file (@filelist) {
#			print "$file ";
#			@targets=`grep pfhex $file`;
#			chomp @targets;
#			$priostr = join("=$prio -p ",@targets);
#			$priostr = "-p " . $priostr . "=$prio";
#			system("schedule.pl -f $PIGSS_DATABASE $priostr");
#		}
#	}
#
	sub interrupt_handler {
#  		print "Interrupt! I will attempt to fix the database, but this is not perfect. Consider running fixobs.pl.\n";
		die "User abort\n";
	}
	$SIG{'INT'} = 'interrupt_handler';
}


sub command_line {
	my $str;
	my $done = 0;
	my @words = ("\n","exit\n","bye\n","c\n","cont\n","continue\n","done\n","quit\n","logout\n");

	do {
		print "mksched: ";
		$str = <STDIN>;
		foreach (@words) { if ($str eq $_) { $done++; } }
		if ($done == 0) {
			eval "$str";
			if (defined $@) { print $@,"\n"; }
		}
	} while ($done == 0);
}


sub mysystem {
	$str = shift;
	print "system($str)\n" if $verbose;
	system($str);
	if ($? == -1) {
		die "failed to execute: $!\n";
	}
	elsif ($? & 127) {
		printf "child died with signal %d, %s coredump\n", ($? & 127), ($? & 128) ? 'with' : 'without';
		die;
	}
	elsif ($? >> 8) {
		printf "child exited with value %d\n", $? >> 8;
		die;
	}
}

sub mark_observed {
	my $date = shift;
	my @targets = @_;
	chomp @targets;
	print "Marking targets as observed.\n" if $verbose;
	my $fields = join(",",@targets);
	my $datestr=$date->strftime("%m/%d/%Y");
        mysystem("schedule.pl -f $PIGSS_DATABASE -o $datestr,$fields");
}


sub read_sched {
	my $fname=shift;
	open INFILE, "<", "$fname";
	my @obs = <INFILE>;
	@obs = grep /PIGSS/, @obs;
	print "$fname: read " . scalar(@obs) . " PiGSS records\n" if $verbose;
	close INFILE;
	return @obs;
}


sub parse_string_date {
	my $str=shift;
	my $TZ=shift;
	my $date;
	my $parser;
	my $format;
	my $nfields = split(/\//,$str);

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


sub parse_decimal_time {
	my $t = shift;
	my $d = shift;
	my $tmp;

	if (!defined($d)) { $d = DateTime->now(time_zone=>$TZ); }
	else { $d=$d->clone->set_time_zone($TZ); }
	$d->set(hour=>int($t));
	$tmp = $t-int($t);
	$d->set(minute=>int(60*$tmp));
	$tmp *= 60;
	$tmp = $tmp-int($tmp);
	$d->set(second=>int(60*$tmp));
	$d->set(nanosecond=>0);

	return($d);
}


sub make_decimal_hours {
	my $t = shift;	# DateTime object
	my $h;

	$h=$t->hour+$t->minute/60.0+$t->second/3600.0;
	return $h;
}


sub by_dist {   # sort by distance to coordinates specified in global variables $cra, $cdec
        return ($disthash{$a} <=> $disthash{$b});
}

chdir '/home/dwhysong/pigss';
if (not $unsafe) {
	print "Performing consistency check on database.\n";
	die "\nfailed: $!\n" if system("schedule.pl -f $PIGSS_DATABASE --verify");
}

if ($minblock<0) { die "Blocking time must be positive\n"; }
if ($minblock==0) {		# --block but argument not specified
	$minblock = 3.3;	# Pick something reasonable
}

if (!defined($PIGSS_CATALOG)) {
	$PIGSS_CATALOG='/home/dwhysong/pigss/pfhex.fields';
} else {
	warn "Warning: using nonstandard catalog $PIGSS_CATALOG\n" if ($verbose);
}

die "Please specify a schedule file.\n" if (!defined($filename));
@obs=read_sched($filename);
if (!defined($selectnfields)) {
	$selectnfields=5.0;
}

$tel=observatory_load();
$long = (defined $tel ? $tel->long : 0.0);
$long == 0.0 and warn "Telescope longitude is zero; undefined telescope?\n";

# Find the median RA for the daily files
$dailyfile=$daily.'.cat';
open FILE, "< $dailyfile" or die "Error: $dailyfile $!\n";
foreach (<FILE>) {
	chomp;
	(undef, undef, undef, $ra) = split;
	push @list, $ra;
}
@tmp = sort {$a<=>$b} @list;
$daily_ra = $tmp[($#tmp/2)];
close FILE;
undef @tmp;
undef @list;


open FILE, "< $PIGSS_CATALOG" or die "Error: $PIGSS_CATALOG $!\n";
foreach (<FILE>) {
	chomp;
	($name, $ra, $dec) = split;
	$dec = $PI_2 - $dec;
	$poshash{$name}=("$ra $dec");
}
close FILE;

if ($selectdate ne '') {
	$mydate = parse_string_date($selectdate,$TZ);		# Specific date to schedule
	print "Searching for PiGSS observations on $mydate\n";
}
$now = DateTime->now(time_zone=>$TZ);
$obsnum = 0;
$prevobsdate = DateTime->new(year=>1900, time_zone=>$TZ);       # Some time far in the past
foreach (@obs) {
	($startstr,$endstr)=split;
	$parser = DateTime::Format::Strptime->new(pattern => '%Y%b%d::%H:%M:%S', time_zone => $TZ, on_error => 'croak');
	$obsstart=$parser->parse_datetime($startstr);		# Start of observation
	$date=$obsstart->clone()->truncate(to=>'day');		# Day of the observation's start
	$obsend=$parser->parse_datetime($endstr);		# End of observation

	print "string: $_ obsstart: $obsstart  obsend: $obsend\n" if ($obsend->subtract_datetime_absolute($obsstart)->seconds > 86400);
        die "Observation at $startstr is longer than 24 hours." if ($obsend->subtract_datetime_absolute($obsstart)->seconds > 86400);
	$obsend->subtract(DateTime::Duration->new(minutes=>9));	# Subtract 9 minutes so we don't run over
	die "Adjusted end time is still before start time.\n" if ($obsend < $obsstart);

	# Check to see if we've moved to a new day; if so, observe daily fields
	if ($prevobsdate == $date) {
		$obsnum++;
	}
	else {
		$obsnum = 0;			# New day
		$prevobsdate = $date;
	}

	if ($obsend < $now) {
		print "Observation at $startstr has already ended; skipping.\n" if $verbose;
		next;
	}
	if ($obsstart < $now) {
		print "Observation at $startstr has already started; press 'y' to skip:";
		$_=<STDIN>;
		chomp;
		if (lc($_) eq 'y') {
			print "Skipping $startstr\n";
			next;
		}
	}

	$DATE=$date->strftime("%d-%m-%Y");			# Use this for writing files
	$fname="pigss.targets-$DATE.$obsnum";			# Output target file name
	$regname="status/ds9reg-$DATE-$obsnum";			# Output ds9 region file name
	if (defined($selectdate)) {				# If specified, we only process the selected date
		if ($mydate > $date) {
			if ( -f $fname ) {
				@targets = `grep ^pfhex $fname`;
				mark_observed($date,@targets);
			}
			next;
		}
		elsif ($mydate < $date) {
			next;
		}
	}
	elsif (-e "pigss.targets-$DATE.$obsnum") {		# In batch mode, skip this observation if the target file exists
		print "pigss.targets-$DATE.$obsnum already exists; skipping this observation\n";

		# Mark these targets as observed on the corresponding date
		@fields = `grep ^pfhex pigss.targets-$DATE.$obsnum`;
		chomp @fields;
		$fields = join ',', @fields;
		$datestr = $date->strftime("%m/%d/%Y");

		#print("/home/dwhysong/pigss/schedule.pl -f $PIGSS_DATABASE -vo $datestr,$fields\n\n");
		system("/home/dwhysong/pigss/schedule.pl -f $PIGSS_DATABASE -vo $datestr,$fields");

		next;
	}
	print "Scheduling for: $obsstart $obsend\n" if ($verbose or $interactive);
	$obslen = $obsend->subtract_datetime_absolute($obsstart)->seconds;
	$obslen /= 3600.0;
	die "Invalid observation length\n" if ($obslen<0);
	print "  Observation length: $obslen hours\n" if ($verbose);

	unlink glob ".tmp/ds9reg*";
	unlink '.tmp/targets';
	open TARGETFILE, "> .tmp/targets" or die "Error: .tmp/targets $!\n" unless $test;

	$nblocks = POSIX::floor($obslen / $minblock);		# Break the observation up into shorter blocks if necessary
	$nblocks = 1 if ($nblocks < 1);
	$blkint = $obslen / $nblocks;
	$blkminutes = POSIX::floor(60*$blkint);
	$blkend = $obsstart;
	print "  Breaking the observation into $nblocks blocks of $blkint hours.\n" if $verbose and $nblocks > 1;

	for ($blk=0; $blk < $nblocks; $blk++) {
		$tmpregname=".tmp/ds9reg-$DATE-$blk";			# Temporary ds9 region file name
		foreach (@targets) {
			$targethash{$_}=1;				# A hash of targets selected in previous iterations
		}
		@targets=();						# Don't keep previous iteration's targets!
		$blkstart = $blkend;
		$blkmid = $blkstart->clone;
		$blkmid->add(DateTime::Duration->new(seconds=>$blkminutes * 30));
		$blkend = $blkstart->clone;
		$blkend->add(DateTime::Duration->new(minutes=>$blkminutes));
		die "Block $blk ran over the end of the observation\n" if ($blkend > $obsend);

		# need to convert to UTC for ut2lst. We'll switch back to local time immediately afterward.
		$blkmid->set_time_zone('UTC');
		$lst = 12/$PI*(Astro::SLA::ut2lst($blkmid->year,$blkmid->mon,$blkmid->mday,$blkmid->hour,$blkmid->min,$blkmid->sec,$long))[0];
		$blkmid->set_time_zone($TZ);
		$nfields=POSIX::floor($blkint * $selectnfields);	# Number of fields to observe.
		print "  block $blk centered at $blkmid and LST $lst: selecting $nfields targets.\n" if $verbose;
		next if $test;
		$STARTTIME=$blkstart->strftime("%d/%m/%Y/%H:%M:%S");
		$ENDTIME=make_decimal_hours($blkend);
		$SCHEDARGS="-f$PIGSS_DATABASE -t$STARTTIME -e$ENDTIME";
		if ($pass > 1) { $SCHEDARGS = $SCHEDARGS . " -x $pass"; }

		print "Running: schedule.pl $SCHEDARGS -s\n" if $verbose;
		@fieldlist=`schedule.pl $SCHEDARGS -s | tee .tmp/status`;

		#@fieldline=`plotfields.pl $PLOTARGS -f pfhex_all`;	# 17 seconds; that's fast, apparently because pfhex_all is sorted
		open FILE, "< .tmp/pfhex_fieldline" or die "Error: .tmp/pfhex_fieldline $!\n";	# Even faster... save 17 seconds
		@fieldline=<FILE>;
		close FILE;

		chomp(@fieldline,@fieldlist);

		foreach(@fieldlist) {					# Make a hash of colors from the schedule.pl output
			$len=index($_," ");
			$name=substr($_,0,$len);
			if ($targethash{$name} == 1) {			# We've already planned to observe this one!
				$hash{$name}='magenta';
			}
			elsif (/not observable/) {
				$hash{$name}='red';
			}
			elsif (/observed/) {
				$hash{$name}='blue';
			}
			elsif (/observable/) {				# Would match "not observable" if we did this first
				$hash{$name}='yellow';
			}
			else { die "Unknown status for $name\n"; }
		}


		if ($interactive) {
			open REGFILE, "> $tmpregname" or die "Error opening $tmpregname: $!\n";
			foreach(@fieldline) {					# Put colors in the ds9 region file
				$start=index($_,'pfhex');
				$end=index($_,'}');
				$name=substr($_,$start,$end-$start);
				print REGFILE $_," color=",$hash{$name},"\n";
			}
			close REGFILE;
			print "Press return for graphical display (d for debug): "; $inp=<STDIN>;
			system("ds9 -geometry 2000x1000 -cmap BB -log -fits nvss.fits -zoom 0.8 -regions load $tmpregname -regions showtext no &");
			if (lc($inp) eq 'd') {
				command_line();
			}
			print "Enter primary target field name: ";
			$selected=<STDIN>;
			chomp($selected);
		}
		else {
			print "Running: schedule.pl $SCHEDARGS -g\n" if $verbose;
			@selectlist=`schedule.pl $SCHEDARGS -g | tee .tmp/schedget`;
			chomp(@selectlist);
			undef($selected);
			if (scalar(@selectlist)==0) {
				die "Couldn't get a target for block $blk.\n";
				next;						# skip to next block; invalidated by the die above, which used to be warn
			}
			while ($targethash{$selectlist[0]}==1) {
				die "ERROR: ",$selectlist[0]," is marked for observation, but is being returned by schedule.pl -g\n";
				shift(@selectlist);				# Discard fields that are already scheduled
			}
			$selected=shift(@selectlist);
		}

		print "    Searching for $nfields targets near: $selected\n" if $verbose;
		die "$selected not found in $PIGSS_CATALOG\n" if $poshash{$selected}=='';	# Verify that it exists
		if ($hash{$selected} != 'yellow') { die "$selected is not observable.\n"; }	# Verify that it is observable

		foreach(@fieldlist) {					# Make a list of observable fields
			$len=index($_,' ');
			$name=substr($_,0,$len);
			next if ($targethash{$name} == 1);		# Already planned to observe this one, skip
			next if (/not observable/);			# /observable/ would accept "not observable"
			if (/observable/) {
				push @possible, $name;
			}
		}

		%disthash=();						# Must initialize, as the values depend on $selected
		($ra0, $dec0) = split(/\s+/,$poshash{$selected});
		foreach $name (@possible) {				# Make a hash of distances to the selected field
			($ra,$dec) = split(/\s+/,$poshash{$name});
			$disthash{$name}=great_circle_distance($ra0, $dec0, $ra, $dec);
		}

		undef @possible;					# Replace unsorted @possible with sorted values from hash
		foreach $key (sort by_dist (keys(%disthash))) {
			unshift @possible, $key;			# @possible is now sorted by distance to $selected
		}

		if ($obsnum == 0 and abs($lst - $daily_ra) < $blkint/2.0) {	# Observe daily fields
			print("    Including daily ($daily) fields.\n") if $verbose;
			for ($i=1; $i<=7; $i++) {
				push @targets, "$daily-000$i";
				$nfields--;
			}
			if ($nfields < 1) {
				warn "Not enough time to observe daily fields; continuing anyway.\n";
				$nfields = 0;
			}
		}
		if ($nfields > scalar(@possible)) {
			$nfields = scalar(@possible);
			warn "Only $nfields fields are available.\n";
		}
		for ($i=0; $i<$nfields; $i++) {				# Select nearest fields and move them to @targets
			$_=pop(@possible);
			unshift @targets, $_;
		}

		print TARGETFILE "BEGIN\n";
		foreach $name (@targets) {				# Set the target fields to be green in the color hash
			$hash{$name}='green';
			print TARGETFILE $name,"\n";			# Write to the targets file
		}
		print TARGETFILE "END ",make_decimal_hours($blkend),"\n";

		# Modify target priority in the database, so we don't select the same targest over and over again
		# Note, we don't set the date field, as that is a destructive operation so it shouldn't be done until
		# the observation has been completed.
		mark_observed($date,@targets);
		#print "Modifying target priority.\n";
		#$prio = 4 - $pass;
		#$priostr = join("=$prio -p ",@targets);
		#$priostr = "-p " . $priostr . "=$prio";
		#system("schedule.pl $SCHEDARGS $priostr");

		open REGFILE, "> $tmpregname" or die "Error: $tmpregname : $!\n";	# Write a new region file
		foreach(@fieldline) {
			$start=index($_,'pfhex');
			$end=index($_,'}');
			$name=substr($_,$start,$end-$start);
			print REGFILE $_," color=",$hash{$name},"\n";
		}
		close REGFILE;
		if ($interactive) {
			print "Enter y for a graphical display (d for debug): ";
			$inp=<STDIN>;
			if (lc($inp) eq 'y') {
				system("ds9 -geometry 2000x1000 -cmap BB -log -fits nvss.fits -zoom 0.8 -regions load $tmpregname -regions showtext no &");
				print "Press return to continue: "; <STDIN>;
			}
			elsif (lc($inp) eq 'd') {
				command_line();
			}
		}
	}
	close TARGETFILE unless $test;

	if (!$test) {
		push @filelist, $fname;
		warn "Warning: $fname exists and is being overwritten!" if (-e $fname);
		system("cp .tmp/targets $fname");
		if ($? == -1) {
			print "failed to execute: $!\n";
		}
		elsif ($? & 127) {
			printf "child died with signal %d, %s coredump\n", ($? & 127), ($? & 128) ? 'with' : 'without';
		}
		elsif ($? >> 8) {
			printf "child exited with value %d\n", $? >> 8;
		}
		print "Saved: $fname and " if $verbose;
		(scalar(glob "$regname*")==0) or warn "Error: $regname exists!";
		for ($blk=0; $blk<$nblocks; $blk++) {
			system("cp .tmp/ds9reg-$DATE-$blk $regname-$blk");
			print "$regname-$blk\n" if $verbose;
		}
	}
}

#fix_database;

