#!/usr/bin/perl
use POSIX;
use Getopt::Long;

# obs@strato ~/dwhysong % ls `yesterdays_archdir`/pigss/mosfxa-pfhex-85-93-3040/visdata -l
# -rw-r--r-- 1 obs obs 678883428 Jul 27 13:49 /ataarchive/2010/07/27/pigss/mosfxa-pfhex-85-93-3040/visdata
# Estimated to be 5 scans with 496 baselines

$contact = 'dwhysong@astro.berkeley.edu';

sub gather_stats {
	my $dir=shift;
	my @targets = ("eliasn1-0001","eliasn1-0002","eliasn1-0003","eliasn1-0004","eliasn1-0005","eliasn1-0006","eliasn1-0007",
			"lockman-1","lockman-2","lockman-3","lockman-4","lockman-5","lockman-6","lockman-7","coma-0001","coma-0002",
			"coma-0003","coma-0004","coma-0005","coma-0006","coma-0007");

	# not used at the moment
	my @regions = ( 'eliasn1-0001 region="poly(536.85,667.98,491.04,561.94,551.32,491.66,648.97,605.10)"',
		'eliasn1-0002 region="poly(582.67,577.97,641.74,415.22,732.16,486.73,658.62,621.12)"',
		'eliasn1-0003 region="poly(534.44,587.83,529.62,449.74,656.21,446.04,648.97,564.41)"',
		'eliasn1-0004 region="poly(413.88,526.18,582.67,552.08,516.36,394.25,453.67,411.52)"',
		'eliasn1-0005 region="poly(436.79,628.52,548.91,532.35,510.33,404.12,415.09,566.87)"',
		'eliasn1-0006 region="poly(557.35,547.14,700.82,555.78,717.69,402.89,606.78,394.25)"',
		'eliasn1-0007 region="poly(370.48,603.86,516.36,602.63,515.15,457.14,377.72,434.94)"',
		'lockman-1 region="poly(518.77,547.14,659.83,549.61,661.03,442.34,526.00,432.48)"',
		'lockman-2 region="poly(546.50,494.13,395.80,483.03,407.86,386.86,576.64,411.52)"',
		'lockman-3 region="poly(500.69,611.26,507.92,508.92,438.00,483.03,381.33,576.74)"',
		'lockman-4 region="poly(440.41,521.25,498.28,523.72,583.87,446.04,429.56,420.15)"',
		'lockman-5 region="poly(459.70,511.39,617.63,512.62,552.53,383.16,423.53,385.62)"',
		'lockman-6 region="poly(506.72,531.12,640.54,576.74,693.58,447.27,551.32,434.94)"',
		'lockman-7 region="poly(381.33,585.37,540.47,602.63,551.32,450.97,418.71,431.24)"');


	chomp @targets;
	my $name;
	my $size;
	my @match;
	my $n;
	my $str='';

	opendir(DIR,$dir);
	my @files=grep(/^mosfx.*\d$/,readdir(DIR));
	closedir(DIR);

	if (scalar @files == 0) {
		return "No data files found in $dir!\n";
	}

	# Run 'listobs' on a file and count the number of baselines present
	my @listing=`listobs vis=$dir/$files[0]`;
	my $nbase = scalar grep(/^Bsln/,@listing);

	foreach $name (@targets) {
		@match = grep(/$name/,@files);
		$str = $str . "Warning: Only single correlator data found for $name\n" if (scalar @match == 1);
		$str = $str . "Warning: too many data files match $name\n" if (scalar @match > 2);
		$_=shift(@match);
	       	$size = -s "$_/visdata";
	       	$n = POSIX::ceil($size / ($nbase * 294912));	# 1024 chans x 4 pols x 18 integrations x 4 bytes
		foreach (@match) {
			my $size = -s "$dir/$_/visdata";
			my $n1 = POSIX::ceil($size / ($nbase * 294912));
			if ($n1 != $n) {
				$str = $str . "Warning: Number of scans differs between correlators for $name\n";
			}
		}
	}
	foreach $name (@targets) {
		@match = grep(/$name/,@files);
		foreach(@match) {
			@rgn = `grep $name /export/pigss-processing/regions | cut -f2 -d' '`;
			die "Error: found ",scalar(@rgn)," regions associated with $name. There should only be one." if (scalar @rgn != 1);
			$region = @rgn[0];
			chomp $region;
			if (! -d $_.".cm") {
				$str = $str . "Warning: $_.cm does not exist.\n";
				next;
			}
			$tmpstr = `imstat in=$_.cm $region | tail -n1`;
			@tmp = split /\s+/,$tmpstr;
			$rms = $tmp[3];
			if (length($rms) > 9) {
				$rms = substr($str,0,9);
			}
	       		$size = -s "$_/visdata";
	       		$n = POSIX::ceil($size / ($nbase * 294912));	# 1024 chans x 4 pols x 18 integrations x 4 bytes
			$str = $str . "$_.cm: $rms in $n scans\n" if ($rms > $fluxlimit);
		}
	}

	return $str;
}


sub use_date {
	my $date = shift;
	my ($dir, $targetdir);

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

	$dir="/export/pigss-processing/$d[0]-$d[1]-$d[2]/";

	if ( ! -e $dir ) {
#		print "No PiGSS data found in $dir\n";
		return(-1);
	}
	chdir($dir);
	return ($dir);
}




Getopt::Long::Configure ("bundling");
GetOptions('date|d=s' => \$date,
           'help|h' => \$help,
	   'limit|l=f' => \$fluxlimit);

if ($help) {
        print "PiGSS data quality tool for daily fields (eliasn1 and lockman)\n";
        print "Arguments:\n";
        print "\t--help\t\tshow this text.\n";
        print "\t--date [MM/DD/YY] or [MM/YY]\tprocess data from a specific date or month\n";
	print "\t--limit [#] print a message when the RMS is above [#] mJy\n";
        exit();
}

if (defined($fluxlimit)) {
	$fluxlimit *= 0.001;
}

if (defined($date)) {
	@d=split(/\//,$date);
	if (scalar(@d) == 3) {
		$dir = use_date($date);
		exit if ($dir==-1);
		print gather_stats($dir);
	}
	elsif (scalar(@d) == 2) {
		for ($i=1; $i<=31; $i++) {
			$date="$d[0]/$i/$d[1]";
			$dir = use_date($date);
			print "$date:\n";
			print (gather_stats($dir)) if ($dir!=-1);
		}
	}
	else { die "Unable to parse date string $date\n"; }
}

foreach(@ARGV) {
	$dir=$_;
	die "Error: cannot find $dir\n" if (! -d $dir);
	chdir($dir);
	$dir=`pwd`;
	chomp $dir;
	print gather_stats($dir);
}
