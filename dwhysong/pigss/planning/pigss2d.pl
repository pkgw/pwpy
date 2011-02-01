#!/usr/bin/env perl
BEGIN { $^W = 1; }

use ATA;
use Getopt::Long;
use DateTime;
use DateTime::Format::Strptime;
use POSIX;
use Fcntl qw(:flock SEEK_END);

# TODO:
#	Choose the nearest available calibrator (or best for pol?), rather than the first from an arbitrary list
#	email->SMS : 5059182055@txt.att.net
#	Convert mosfx scripts to perl
#	Use new obs library stuff, or at least communicate with it
#
# FIXME: duplicate stdout/stderr to log file
#	 use taint mode?

@maillist = ('dwhysong@gmail.com','sblair@seti.org','karto@hcro.org','5059182055@txt.att.net');
$contact = 'dwhysong@astro.berkeley.edu';
$hostname=`hostname`;
chomp $hostname;
$catalog='/home/obs/dwhysong/pfhex.cat' if ($hostname eq 'strato');
$catalog='/home/dwhysong/pigss/pfhex.cat' if ($hostname eq 'aster.berkeley.edu');
$donefile="/home/obs/dwhysong/pigss2.done";
$lockfile="/home/obs/dwhysong/.pigss_run";
$TZ='America/Los_Angeles';
$mydir = `pwd`;
chomp $mydir;

$troubletime = DateTime->new(year=>1900, time_zone=>$TZ);	# Some time far in the past

# Signal handler: ctrl-c should land us in debug mode.

sub interrupt_handler {
	print "Interrupt!\n";
	$waiting=0;
	command_line();
}
$SIG{'INT'} = 'interrupt_handler';


sub mywarn {
	my $str=shift;
	print "\n***********************************************************************\n";
	print "\tWarning: $str\n";
	print "***********************************************************************\n\n";
}


sub mysystem {
	$str=shift;
	my $retval=0;
	if ($test) {
		print "test: $str\n";
	} else {
		print "$str\n";
		$retval = system $str;
		trouble("Failed with return value $retval: $!\n",$str) if $retval;
	}
	return $retval;
}

sub debug {
	my $str;
	my $done = 0;
	my @words = ("\n","exit\n","bye\n","c\n","cont\n","continue\n","done\n","quit\n","logout\n");

	do {
		print "pigss2d debug: ";
		$str = <STDIN>;
		foreach (@words) { if ($str eq $_) { $done++; } }
		if ($done == 0) {
			eval $str;
			warn "$@\n" if $@;
		}
	} until $done;
}


sub command_line {
	my $command = shift;
	my $str;
	my @words = ("continue","debug","abort");
	@words = (@words,"retry") if $command;
	my $done = 0;
	mywarn "Observing is interrupted!" if $observing;
	print "Failed at: $command\n" if $command;
	print "Dropping to command line.\n";
	do {
		print "  @words\n";
		print "pigss2d: ";
		$str = <STDIN>;
		chomp($str);
		if ($str eq 'continue') {
			$done++;
		}
		elsif ($str eq 'debug') {
			$done++;
			debug();
		}
		elsif ($str eq 'retry' and $command) {
			print "eval: $command\n";
			eval $command;
			warn "$@\n" if $@;
		}
		elsif ($str eq 'abort') {			# Kill any child processess
			if ($observing) {
				print "Releasing antennas to 'none' group. They will NOT be parked.\n";
				mysystem("fxconf.rb satake none `slist.csh fxa`");
			}
			$pgroup = getpgrp(0);
			kill -15 => $pgroup;
		}
		else {
			print "Command not understood\n";
		}
	} until $done;
}


sub send_mail {
	my ($to, $from, $subject, $message) = @_;
	my $sendmail = "/usr/sbin/sendmail";
	$test and open(MAIL,">&STDOUT");
	$test or open(MAIL, "|$sendmail -oi -t");
	print MAIL "From: $from\n";
	print MAIL "To: $to\n";
	print MAIL "Subject: $subject\n\n";
	print MAIL "$message\n";
	close(MAIL);
}


sub trouble {
	my $message = shift;
	my $command = shift;
	# use global variable $troubletime to avoid rapid-fire messaging
	mywarn $message;
	my $currenttime=DateTime->now(time_zone=>$TZ);
	if ($currenttime->subtract_datetime_absolute($troubletime)->seconds > 30) {;
		$troubletime = $currenttime;
		foreach (@maillist) {
			send_mail($_,'obs@strato.hcro.org',$message,"Hope you're checking email");
		}
	}
	else { warn "Not sending email/SMS, last error was < 5 minutes ago\n"; }
	command_line($command);
}


sub parse_decimal_time {
	my $t = shift;
	my $d = shift;		# This allows one to specify the day/month/year
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


sub read_sched {
	my $fname=shift;
	open INFILE, "<", "$fname";
	my @obs = <INFILE>;
	@obs = grep /PIGSS/, @obs;
	print "Read " . scalar(@obs) . " PiGSS records from $fname\n" if $verbose;
	close INFILE;
	chomp @obs;
	return @obs;
}


sub wait_until {
	my $t = shift;
	my $sec=0;

	my $now = DateTime->now(time_zone=>$TZ);
	while (1) {
		last if ($now > $t);
		print "Waiting until $t\n" if $verbose;
		return(-1) if $test;
		my $dur = $t->subtract_datetime_absolute($now);
		$sec = 1 + $dur->in_units('seconds');
		$waiting=1;
		sleep($sec);
		$now = DateTime->now(time_zone=>$TZ);
		trouble "Did not wait long enough!" if ($now < $t and $waiting);
	}
	return($sec);
}


sub read_fields {
	my $fname = shift;
	my $skip = shift;
	my $end=-1;
	my $endtime;
	my @fields;
	my $targetstring;
	my $blknum = 0;
	my $i;

	print "Reading targets from $fname\n" if $verbose;
	my $time = DateTime->now(time_zone=>$TZ);			# Current time
	$_=open(FILE, "< $fname");
	if ($_==0) {	# open failed
		trouble("Unable to open target file $fname",'$_=open(FILE, "< $fname");');
	}
	while ($skip) {
		$_ = <FILE>;
		if (/END/) {
			$blknum++;
			$skip--;
		}
		return ("",-1) if (eof FILE);
	}
	do {
		do {
			$_=<FILE>;
			return ("",-1) if (!defined $_);	# End of file reached
			if (/BEGIN/) {
				$end = -1;
			}
			elsif (/END/) {
				@_ = split;
				$end = $_[1];
				$endtime = parse_decimal_time($end,$obsstart);
				$endtime->add(days => 1) if ($endtime < $obsstart);	# past midnight
			}
			else {
				push @fields, $_ unless !defined $_;
			}
		} until ($end != -1);
		if ($time > $endtime) {
			mywarn "Skipping block $blknum because time $time > endtime $endtime";
			@fields=();
			$blknum++;
		}
	} while ($time > $endtime);
	close FILE;
	chomp(@fields);
	$targetstring = join('|',@fields);
	return ($targetstring,$end,$blknum);
}


sub verify_fields {
	my @fields = @_;
	print "Verifying targets... " if $verbose;

	open CATFILE, "<", "$catalog";
	while (<CATFILE>) {
		my @tmp = split;
		push @cat, $tmp[2];	# Third element is the field name
	}
	close CATFILE;
	chomp @cat;
	my $cat = join(' ', @cat) . ' ';

	# $cat is a space-separated list of targets. Include the trailing space in the search to get
	# an exact match, i.e. we don't match pfhex-123-4 to pfhex-123-45
	foreach (@fields) {
									# Index is faster than perl grep
		trouble "Error: $_ is not found in catalog $catalog!" if index($cat,"$_ ")==-1;
	}
#	Unix grep is MUCH faster for some reason. The trailing tab forces an exact match.
#	foreach $test (@fields) {
#		@tmp=`grep '$test	' $catalog`;
#		trouble "Error: $test is not found in catalog $catalog!\n" if (scalar(@tmp) == 0);
#	}
	print "done.\n" if $verbose;
}



sub do_obs {
	my $targets=shift;
	my $end=shift;
	my $dir=shift;

	$mytargetfile=$dir."/pigss.targets";

	die("Error: Invalid end time.\n") unless ($end < 24 and $end >= 0);

	@tm=localtime();
	$now = $tm[2]+$tm[1]/60.;
	if ($now > $end) { $now -= 24 };
	$duration=$end-$now;
	print "Duration is $duration hours.\n" unless $test;

	@targets=split(/,|\|/,$targets);
	verify_fields(@targets);
	
	if (! $test) {
		# Write full target list to a file in the data directory
		open(FILE, ">> $mytargetfile") || die("Can\'t open $mytargetfile: $!\n");
		print FILE $targets,"\n";
		close(FILE);
	
		print ("Executing: mosfx_pigss_obs.csh 3040 3140 \"$targets\" \"$calibrator\" $end");
		mysystem("mosfx_pigss_obs.csh 3040 3140 \"$targets\" \"$calibrator\" $end");
	}
}



# Get information on the data we have collected. Return a string to put in the
# email at the observation's end.
sub gather_stats {
        my @targets = `cat $targetfile | grep -v BEGIN | grep -v END`;
        chomp @targets;
        my %hist=();
	my $n;
        my $str='';
	my @nontargets;
	my @list;

        opendir(DIR,$dir);
        my @files=grep(/mosfx.*\d/,readdir(DIR));
        closedir(DIR);

        if (scalar @files == 0) {
                return "No data found!\n\nThis is an automated message. Contact $contact with any questions.\n\n";
        }

        # Run 'listobs' on a file and count the number of baselines present
        my @listing=`listobs vis=$dir/$files[0]`;
        my $nbase = scalar grep(/^Bsln/,@listing);

        foreach my $name (@targets) {
                my @match = grep(/$name/,@files);
                $str = $str . "Warning: No data found for $name\n" if (scalar @match == 0);
                $str = $str . "Warning: Only single correlator data found for $name\n" if (scalar @match == 1);
                $str = $str . "Warning: too many data files match $name\n" if (scalar @match > 2);
		$hist{0}++ if (scalar @match == 0);
		$_=shift(@match);
               	my $size = -s "$dir/$_/visdata";
               	$n = POSIX::ceil($size / ($nbase * 294912));	# 1024 chans x 4 pols x 18 integrations x 4 bytes
               	$str = $str . "$name : Estimate $n scans\n";
               	$hist{$n}++;
		foreach (@match) {
                	my $size = -s "$dir/$_/visdata";
                	my $n1 = POSIX::ceil($size / ($nbase * 294912));
			if ($n1 != $n) {
                		$str = $str . "Warning: Number of scans differs between correlators for $name\n";
			}
		}
        }
	# Find files that don't match the target list, and print a warning
	my %seen=();
	foreach (@files) {
		push @list, (/mosfx.-(.*)-\d+/i);
	}
	@seen{@targets} = ();
	foreach $name (@list) {
		push(@nontargets,$name) unless exists $seen{$name};
		$seen{$name} = 1;	# Prevent duplicates in @nontargets
	}
	$str = $str . "Data also exist for: @nontargets which are not in the target list\n" if @nontargets;

        my $hstr = "\nHistogram of scan counts:\n\n";
        foreach (sort keys %hist) {
                $hstr = $hstr . "$_: " . "*" x $hist{$_} . "\n";
        }
	$str = $hstr . "\n\n" . $str;			# Put the histogram on top
        $str = $str . "\n\nThis is an automated message. Contact $contact with any questions.\n\n";
        return $str;
}



###########################################
# Start of main progam
###########################################
#
# We aren't observing yet
$observing=0;
# Parse command line
$test=0;
$bad=0;
$schedfile='ata-schedule';
Getopt::Long::Configure ("bundling");
GetOptions('help|h' => \$help,
	   'cal|c=s' => \$calibrator,
	   'test|t' => \$test,
	   'file|f=s' => \$schedfile,
	   'verbose|v' => \$verbose,
	   'bad|b' => \$bad);

if ($hostname ne 'strato') {
	mywarn "Not running on strato; test mode enabled.\n\t\t    You will not be observing.";
	$test = 1;
}
else {
	# Lock file to prevent multiple instances
	open($fh, ">>", $lockfile) or die "Cannot open $lockfile - $!\n";
	flock($fh, LOCK_EX|LOCK_NB) or die "Cannot lock $lockfile - $!. Another pigss2.pl process is likely running.\n";
}

if ($help) {
	print("PiGSS survey manager\n\tDavid Whysong\n\n");
	print("Usage:\n");
	print "\t-h\t\tdisplay help\n";
	print "\t-f\t\tname of schedule file\n";
	print "\t-t\t\ttest mode, do not execute telescope commands\n";
	print "\t-c [cals]\tcomma-separated list of calibrators\n";
	print "\t-b\t\tbad data; discard data for observation currently in progress\n";
	print "\t-v\t\tprint verbose diagnostics\n\n";
	exit;
}

@obslist = read_sched($schedfile);

$obsnum = 0;
$prevobsdate = DateTime->new(year=>1900, time_zone=>$TZ);	# Some time far in the past
foreach $obs (@obslist) {
	($startstr,$endstr)=split(/\s+/,$obs);
	$parser = DateTime::Format::Strptime->new(pattern => '%Y%b%d::%H:%M:%S', time_zone => $TZ, on_error => 'croak');
	$obsstart=$parser->parse_datetime($startstr);		# Start of observation
	$obsend=$parser->parse_datetime($endstr);		# End of observation
	$time = DateTime->now(time_zone=>$TZ);			# Current time

	# Check to see if we've moved to a new day; keep track of how many observations in the day
	# $obsdate is the date of the previous observation in @obslist
	if ($prevobsdate == $obsstart->clone()->truncate(to=>'day')) {
		$obsnum++;
	}
	else {
		$obsnum = 0;						# New day...
		$prevobsdate=$obsstart->clone()->truncate(to=>'day');
	}

	# Bounds checking, i.e. make sure there's enough time for things
	next if ($time > $obsend);			# Skip over past observations

	die "Error: observation at $obsstart is longer than 24 hours." if ($obsend->subtract_datetime_absolute($obsstart)->seconds > 86400);
	if ($obsend->subtract_datetime_absolute($obsstart)->seconds < 3600) {
		mywarn "Observation at $obsstart is less than 1 hour long. Skipping...";
		next;
	}
	if ($obsend->subtract_datetime_absolute($time)->seconds < 1200) {
		mywarn "Less than 20 minutes remaining in current observation. That's too short. Skipping...";
		next;
	}
	if ($time > $obsstart) {
		print "We appear to be in the middle of an observation that started at $obsstart\n" if $verbose;
	}
	else {
		print "Will wait for the next observation at $obsstart\n" if $verbose;
	}


	$datestr=$obsstart->strftime("%d-%m-%Y");		# Use this for writing files
	$targetfile = $mydir . "/pigss.targets-$datestr.$obsnum";
	$dir="/ataarchive/" . $obsstart->strftime("%Y/%m/%d") . "/pigss/";

	# Wait until ~20 minutes before start time to generate ephemerides
	$ephemtime = $obsstart->clone()->subtract(minutes => 20);
	wait_until($ephemtime) || mywarn "We're late generating the ephemerides.";

	# Make data directory
	if (! -d $dir) {
		mysystem("mkdir -p $dir") && trouble "cannot create $dir $!";
	}
	print "Data directory will be: $dir\n";
	chdir($dir) || trouble("cannot cd to $dir ($!)","chdir($dir)") unless $test;

	if (!defined $calibrator) {
		$calibrator='3C286,3C147,3C48';
	}
	print "Calibrators will be selected from: $calibrator\n";

	# Generate ephemerides
	@ephemlist = `cat $targetfile | grep -v BEGIN | grep -v END`;
	(scalar(@ephemlist)>5) || trouble("Target list from $targetfile is too short.");
	foreach $sou (@ephemlist) {
		chomp $sou;
		if (-f $sou.".ephem") {
			print "Ephemeris for $sou exists; skipping\n" if $verbose;
			next;
		}
		mysystem("ataephem $sou --utcms --interval 10 --catalog $catalog --starttime `date -u +%Y-%m-%dT%H:%M:00Z` --nocull");
		mysystem("atawrapephem $sou.ephem");
	}
	@ephemlist = split(/,|\|/,$calibrator);
	foreach $cal (@ephemlist) {
		chomp $cal;
		if (-f $cal.".ephem") {
			print "Ephemeris for $cal exists; skipping\n" if $verbose;
			next;
		}
		mysystem("ataephem $cal --utcms --interval 10 --starttime `date -u +%Y-%m-%dT%H:%M:00Z` --nocull");
		mysystem("atawrapephem $cal.ephem");
	}

	($obsstart > $time) and wait_until($obsstart);

	# Execute the observation
	if (! $test) {
		$antlist = `slist.csh none`;
		@_=split(/,/,$antlist);
		if (scalar @_ < 20) {
			mywarn "Less than 20 antennas in the none group!";
			trouble("Trouble starting PiGSS: not enough antennas in group none");
		}
	}
	$observing=1;	# We're taking control of the telescope now
	send_mail('atauser@seti.org','obs@strato.hcro.org','PiGSS is taking the array',"This is an automatic message. Contact $contact with any questions.");
	mysystem("fxconf.rb satake fxa `slist.csh none`");
	mysystem("mosfx_pigss_init.csh 3040 3140 \"none\" \"$calibrator\"");

	$blk=0;
	while (1) {
		# Read targets and end time for this block
		($targets,$end,$blk) = read_fields($targetfile, $blk);
		last if ($targets eq '');
		# verify that $end is not later than $obsend
		$blkend = parse_decimal_time($end,$obsstart);
		if ($blkend > $obsend) {
			trouble "Block end time $blkend is later than observation end time $obsend!";
		}
		if ($verbose) {
			print "Block $blk targets:\n";
			$i=0;
			foreach (split(/,|\|/,$targets)) {
				print "  $_";
				$i++;
				if ($i % 5 == 0) { print "\n"; }
			}
			if ($i % 5 != 0) { print "\n"; }
		}

		# Execute the observation
		do_obs($targets,$end,$dir);
		$blk++;
	}

	mysystem("park.csh `slist.csh fxa`");
	mysystem("fxconf.rb satake none `slist.csh fxa`");
	$observing=0;	# We're done observing
	
	if (! $test) {
		# Copy scan list to aster
		# or do this: cat timelog | grep pfhex | cut -f 5 -d ' '
	        $date=`date +%d-%m-%Y`;
		mysystem("scp pfhex-scans.log dwhysong\@aster:pigss/scanlogs/scans-$date");
	
		# Log the completed fields
		open(FILE, ">> $donefile") || die("Can\'t open $donefile: $!\n");
		print FILE $dir,"\t",$targets,"\n";
		close(FILE);
	}

	chdir($mydir) || trouble("cannot cd to $mydir ($!)","chdir($mydir)") unless $test;
	print "Observation complete at ",`date`;
	send_mail('atauser@seti.org','obs@strato.hcro.org','PiGSS is finished with the array',gather_stats);
	rename($targetfile,"observed/pigss.targets-$datestr.$obsnum") || mywarn "Unable to move target file: $!" unless $test;
	# Initiate data reduction. This is non-blocking as autoreduce.pl daemonizes.
	mysystem("ssh obs\@pulsar-1 /export/pigss-processing/autoreduce.pl -a");
}
if ($hostname eq 'strato') {
	flock($fh, LOCK_UN) or die "Cannot unlock $fh - $!\n";
	close($fh);
}
print ("pigss2d.pl exits: ",`date`);
