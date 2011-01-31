#!/usr/bin/env perl

use Carp;
use Getopt::Long;
use POSIX;
use File::Temp;
$ENV{"PATH"}="/export/pigss-processing/bin:/hcro/miriad/build/bin:/home/obs/mmm/karto/RAPIDBeta:/home/obs/mmm/karto/cals:".$ENV{"PATH"};
$ENV{"LD_LIBRARY_PATH"}="/hcro/miriad/build/lib";


sub Fork {
    my($pid);
    FORK: {
	if (defined($pid = fork)) {
	    return $pid;
	} elsif ($! =~ /No more process/) {
	    sleep 5;
	    redo FORK;
	} else {
	    croak "Can't fork: $!";
	}
    }
}


##	OpenMax(): Return the maximum number of possible file descriptors.
##	If sysconf() does not give us value, we punt with our own value.
sub OpenMax {
	my $openmax = POSIX::sysconf( &POSIX::_SC_OPEN_MAX );
	(!defined($openmax) || $openmax < 0) ? 64 : $openmax;
}


sub use_date {
	my $date = shift;
	my ($datadir, $targetdir);

	chomp($date);
	my @d=split(/\//,$date);
	if (scalar(@d) > 3 or scalar(@d) < 2) {
		die "Date string $date not understood. Use format: mm/dd/yy\n";
	};
	foreach (@d) {
		if (length($_) != 2) {
			if (length($_) == 1) {
				$_='0'.$_;
			}
			elsif (length($_) == 4) {
				$_=substr($_,2,2);
			}
			else { die "Date string $date not understood. Use format: mm/dd/yy\n"; }
		}
	}

  	$datadir="/ataarchive/20$d[2]/$d[0]/$d[1]/pigss";
	$targetdir="/export/pigss-processing/$d[0]-$d[1]-$d[2]";

	if ( ! -e $datadir ) {
		print "No PiGSS data found in $datadir\n";
		return(-1);
	}
	return ($datadir, $targetdir);
}


sub process_data {
	my $datadir=shift;
	my $targetdir=shift;
	my @FILES;
	my $name;
	my $tmpdir;
	my $tmpfile;

	if ($datadir == -1) { return; }

	print "Data: $datadir\tTarget: $targetdir\n" if($verbose);
	system ("mkdir $targetdir")  && die "cannot create $targetdir ($!)";
	chdir $targetdir;
	open STDOUT, '>', "autoreduce.log" or die "Can't redirect STDOUT: $!";
	open STDERR, ">&STDOUT"     or die "Can't dup STDOUT: $!";
	select STDERR; $| = 1;      # make unbuffered
	select STDOUT; $| = 1;      # make unbuffered

	@FILES=`ls -d $datadir/mosfx?-*`;
	chomp(@FILES);
	$tmpdir = File::Temp->newdir(TEMPLATE=>'PiGSS_XX',DIR=>'/dev/shm');
	foreach (@FILES) {
		$name = (split /\//, $_)[-1];
		$tmpfile = "$tmpdir/$name";
		system("cp -af $_ $tmpfile");
		system("uvsort vis=$tmpfile out=$name");
		system("rm -rf $tmpfile");
	}
	undef $tmpdir;
	system("cp $datadir/pigss.targets $targetdir");
	system("/export/pigss-processing/bin/reduce.pl -cf");
}


$daemon=0;
Getopt::Long::Configure ("bundling");
GetOptions('date|d=s' => \$date,
	   'auto|a' => \$daemon,
	   'verbose|v' => \$verbose,
	   'help|h' => \$help);

if ($help) {
	print "PiGSS data reduction script\n";
	print "Arguments:\n";
	print "\t--help\t\tshow this text.\n";
	print "\t--date [MM/DD/YY] or [MM/YY]\tprocess data from a specific date or month\n";
	print "\t--auto\t\trun in automatic daemon mode\n";
	print "\t--verbose\tprint extra diagnostics\n";
	exit();
}

if ($daemon) {				# Daemonize, so we don't hold up the observing script
	my($pid, $sess_id, $i);

	## Fork and exit parent
	my $pid = Fork;
	exit 0 if $pid;
	exit 1 if not defined $pid;

	## Detach ourselves from the terminal
	croak "Cannot detach from controlling terminal" unless $sess_id = POSIX::setsid();

	## Prevent possibility of acquiring a controling terminal
	$SIG{'HUP'} = 'IGNORE';
	$pid = Fork;
	exit 0 if $pid;
	exit 1 if not defined $pid;

	## Change working directory
	chdir "/export/pigss-processing/";

	## Clear file creation mask
	#umask 0;

	## Close open file descriptors
	foreach $i (0 .. OpenMax) { POSIX::close($i); }

	## Reopen stderr, stdout, stdin to /dev/null
	open(STDIN,  "+>/dev/null");
	open(STDOUT, "+>&STDIN");
	open(STDERR, "+>&STDIN");
}


if (defined($date)) {
	@d=split(/\//,$date);
	if (scalar(@d) == 3) {
		($datadir,$targetdir) = use_date($date);
		process_data($datadir,$targetdir);
	}
	elsif (scalar(@d) == 2) {
		for ($i=1; $i<=31; $i++) {
			$date="$d[0]/$i/$d[1]";
			($datadir,$targetdir) = use_date($date);
			process_data($datadir,$targetdir);
		}
	}
	else { die "Unable to parse date string $date\n"; }
}
else {
	$datestr=`date +%m/%d/%y`;
	($datadir,$targetdir) = use_date($datestr);
	if ($datadir == -1) {
  		$datestr=`date -d yesterday +%m/%d/%y`;
		($datadir,$targetdir) = use_date($datestr);
	}
	die "Can't find any data to process.\n" if ($datadir == -1);
	process_data($datadir,$targetdir);
}
