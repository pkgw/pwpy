#!/usr/bin/perl -w
use ATA;
use Getopt::Long;
use POSIX;
use Fcntl qw(:flock SEEK_END);

# TODO:
#	Possibly support case where $targets and $bad are both set

sub read_fields {
	my $fname = shift;
	my @fields;
	my $targetstring;
	open(FILE, "< $fname") || die("Can't open $fname: $!\n");
	@fields = <FILE>;
	chomp(@fields);
	$targetstring = join('|',@fields);
	close FILE;
	return $targetstring;
}

$catalog='/home/obs/dwhysong/pfhex.cat';
sub verify_fields {
	my @fields=@_;
	my @tmp;
	my $test;
	print "Verifying targets... ";
	foreach $test (@fields) {
		@tmp=`grep $test $catalog`;
		if (scalar(@tmp) == 0) {
			print("Error: $test is not found in catalog $catalog!\n");
			exit(1);
		}
	}
	print "done.\n";
}


sub get_prevdir {
	my ($d1,$d2,$d3);
	$d1 = `date +%Y -d yesterday`;
	chomp($d1);
	$d2 = `date +%m -d yesterday`;
	chomp($d2);
	$d3 = `date +%d -d yesterday`;
	chomp($d3);
	return "/ataarchive/".$d1."/".$d2."/".$d3."/pigss";
}


sub mywarn {
	my $str=shift;
	print "\n***********************************************************************\n";
	print "\tWarning: $str\n";
	print "***********************************************************************\n\n";
}


$donefile="/home/obs/dwhysong/pigss2.done";
$targetfilename="/home/obs/dwhysong/pigss.targets";
$lockfile="/home/obs/dwhysong/.pigss_run";


# Parse command line
$end=-1;
$test=0;
$bad=0;
$restart=0;
Getopt::Long::Configure ("bundling");
GetOptions('end|e=f' => \$end,
	   'restart|r' => \$restart,
	   'cal|c=s' => \$calibrator,
	   'dir|d=s' => \$topdir,
	   'test|t' => \$test,
	   'nfields|n=i' => \$nfields,
	   'field|f=s' => \$targets,
	   'bad|b' => \$bad);

# Lock file to prevent multiple instances
open($fh, ">>", $lockfile) or die "Cannot open $lockfile - $!\n";
flock($fh, LOCK_EX|LOCK_NB) or die "Cannot lock $lockfile - $!. Another pigss2.pl process is likely running.\n";

if ($restart + $bad + defined($nfields) + defined($targets) > 1) {
	die("I'm confused. Please specify only one of --restart, --bad, --nfields, and --field.\n");
}

if ($end<0) {
	print("PiGSS survey script\n\tDavid Whysong\n\n");
	print("Usage:\n\tpigss2.pl [--end|e] <end> [--field|f] <field string or filename> [--nfields|n] <#> [--restart|r] [--bad|b] [--test|t]\n\n");
	die("End time not specified.\n");
}
$end-=0.15;
if ($end<0) { $end+=24; }
($end>24) && die("Error: Invalid end time.\n");

@tm=localtime();
$now = $tm[2]+$tm[1]/60.;
$hms = $tm[2].$tm[1].$tm[0];
if ($now > $end) { $now -= 24 };
$duration=$end-$now;
print "Ending 9 minutes early; duration is $duration\n";

if (!defined $topdir) {
	$topdir=`archdir`;
}
chomp($topdir);
$dir=$topdir."/pigss";
$mytargetfile=$dir."/pigss.targets";

# Target field selection
if (!defined($targets)) {
	### Restart on same day
	if (-d $dir) { # directory already exists
		mywarn "Directory exists - attempting to restart."; if (-f $mytargetfile && -r $mytargetfile && -s $mytargetfile) {
	        	open(FILE, "< $mytargetfile") || die("Can\'t open $mytargetfile: $!\n");
	        	while (<FILE>) { $targets=$_; }		# $targets will be the LAST entry (line in the file)
			chomp($targets);
	        	close FILE;
			$restart=1;
		}
		else {
			mywarn("Unable to resume from previous target list. Charging ahead anyway...");
		}
		chdir($topdir);
		if ($bad) {
			print("--bad option set. Using a new data directory.\n");
			$rename = "pigss.".$hms;
			($test > 0) || system("mv pigss $rename") && die "cannot rename existing directory ($!)";
		}
	}
	elsif (($duration < $end && $end < 12) || $restart) {
		### Restart in the morning; check previous day's directory
		$prevdir=get_prevdir;
		mywarn "Attempting to restart $prevdir";
		$prevtargetfile=$prevdir."/pigss.targets";
		if (-f $prevtargetfile && -r $prevtargetfile && -s $prevtargetfile) {
	        	open(FILE, "< $prevtargetfile") || die("Can\'t open $prevtargetfile: $!\n");
	        	while(<FILE>) { $targets=$_; }		# $targets will be the LAST entry (line in the file)
			chomp($targets);
	        	close FILE;
		}
		else {
			mywarn("Unable to resume from previous target list. Charging ahead anyway...");
			if (!$bad) {
				mywarn(" *** This will not resume in the previous data directory! ***");
			}
		}
	}

	if (defined($targets)) {
		print("Resuming previous targets.\n");
	}
	else {
		# The user let pigss2.pl select new target fields. For now, we'll try to read from a file.
		$targets=$targetfilename;
		if (! -f $targets) {
			print "Please specify some targets.\n";
			exit(1);
		}
	}
}
# Get new targets. The $targets variable is either a filename or a target list

# Handle the case where it is a filename
if (-f $targets) {
	$targetfilename=$targets;
	print("Reading target list from $targetfilename\n");
	$targets=read_fields($targetfilename);
	$date=`date +%d-%m-%Y`;
	chomp($date);
	system("cp $targetfilename observed/pigss2-$date") if ($test==0);
}
#if (!$restart) {
#	print("Adding Lockman hole fields.\n");
#	$targets = "lockman" . "|" . $targets;
#}

if (!defined($nfields)) {
	$nfields=floor($duration * 4.7);	# Specific for PiGSS
}
if ($nfields <= 0) {
	$nfields=0;
}

@targets=split(/\|/,$targets);
$nobs=scalar(@targets)+6;
if ($nfields < $nobs) {
	mywarn("excessive number of target fields ($nobs, max $nfields)!");
}

verify_fields(@targets);
print "Target field(s) will be: $targets\n";

if (!defined $calibrator) {
	$calibrator='3C286|3C147|3C48';
}
print "Calibrator(s) will be: $calibrator\n";

if ($test) {
	die "Test mode selected -- aborting before run.\n";
}
else {
	# Create data directory
	system("mkdir -p $dir") && die "cannot create $dir ($!)";
	if (defined($prevdir)) { $dir = $prevdir; }
	print "Data directory will be: $dir\n";
	chdir($dir) || die "cannot cd to $dir ($!)";
	
	# Write current target list to a file in the data directory
	open(FILE, ">> $mytargetfile") || die("Can\'t open $mytargetfile: $!\n");
	print FILE $targets,"\n";
	close(FILE);

	# Mark these fields as observed, by setting priority to zero
	#foreach (@targets) {
	#	system("$schedule -p $_=0");
	#}

	# Unlock LOs and set the correlator bandwidths again, since this tends to get messed up
	system("unlocklo a");
	system("unlocklo b");
	system("bw.csh fx64a:fxa 100");
	system("bw.csh fx64c:fxa 100");
	# Execute the observation
	system("fxconf.rb satake fxa `slist.csh none`");
	print ("Executing: mosfx_pigss_prime.csh 3040 3140 \"$targets\" \"$calibrator\" $end pigss2");
	system("mosfx_pigss_prime.csh 3040 3140 \"$targets\" \"$calibrator\" $end pigss2");
	system("fxconf.rb satake none `slist.csh fxa`");
	system("park.csh `slist.csh none`");

	# Copy scan list to aster
	# or do this: cat timelog | grep pfhex | cut -f 5 -d ' '
	system("scp -n pfhex-scans.log dwhysong\@aster:pigss/");

	# Log the completed fields
	open(FILE, ">> $donefile") || die("Can\'t open $donefile: $!\n");
	print FILE $dir,"\t",$targets,"\n";
	close(FILE);

	# Initiate data reduction
	#system("ssh -f obs\@pulsar-2 pigss2/autoreduce.sh");
	flock($fh, LOCK_UN) or die "Cannot unlock $fh - $!\n";
	close($fh);
	print ("pigss2.pl exits: ",`date`);
	exit(0);
}
