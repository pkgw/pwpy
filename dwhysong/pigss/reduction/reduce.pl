#!/usr/bin/env perl

use Getopt::Long;

$infile='/home/obs/dwhysong/.reduce';

Getopt::Long::Configure ("bundling");
GetOptions('cal|c' => \$docal,
           'graphic|g' => \$dograph,
	   'help|h' => \$help,
	   'manual|m=s' => \$frqs,
	   'prefix|p=s' => \$prfx,
           'flag|f' => \$doflag);

if ($help) {
        print "reduce.pl: PiGSS data reduction script\n\tDavid Whysong\n\n";
        print "Usage:\n\n";
	print "\t-c\tprocess calibrator files\n";
	print "\t-h\tprint this help message\n";
	print "\t-f\tflag data\n";
	print "\t-p [name]\tdata file prefix\n";
	print "\t-g\tdisplay graphical plots\n";
	print "\t-m [freq]\tmanually enter frequency setup\n";
	exit;
}

@callist=('3C147','3c147','3C286','3c286','3C48','3c48');
#@fluxes=(11.663,9.638,8.232);
@corrs=('a','c');
if (defined($frqs)) {
	@freqs=split /,|\s/, $frqs;
	print "Frequencies: @freqs\n";
}
else {
	@freqs=('3040','3140');
}
if (defined($prfx)) {
	@pfxs=split /,|\s/, $prfx;
	print "File prefixes: @pfxs\n";
}
else {
	@pfxs=('pf','pfhex','lockman');
}

sub getcals {
	my @list;
	my $test;
	foreach $test (@callist) {
		if (`ls -d mosfx*$test* 2>/dev/null`) {
			push @list, $test;
		}
	}
	return @list;
}


sub getflux {
	my $cal=shift;
	my $freq=shift;
	my $flux;
	my @data;

	$freq /= 1000;
	@data=`/home/obs/mmm/karto/cals/calinfo target=$cal freq=$freq`;
	@data=grep /Estimated/, @data;
	@data=split(' ',$data[0]);
	$flux=$data[2];
	print "$cal: using estimated flux $flux at $freq GHz\n";
	return $flux;
}


for ($i=0; $i<(scalar(@corrs)); $i++) {
	@cals=getcals;
	$corr=$corrs[$i];
	$freq=@freqs[$i];
	$master=$cals[0];
	$masterfile="mosfx$corr-$master-$freq";
	if ($docal) {
		foreach $cal (@cals) {
			$flux=getflux($cal,$freq);
			$fname="mosfx$corr-$cal-$freq";
			system("flag.sh $fname 2>&1");
			system("newrfisweep.csh vis=$fname 2>&1");
			system("newcalcal.csh vis=$fname flux=$flux 2>&1");
		}
	}

	foreach $pfx (@pfxs) {
		@files=`ls -d mosfx$corr-$pfx*-$freq 2> /dev/null`;
		print "ls -d mosfx$corr-$pfx*-$freq 2> /dev/null\n";
		print `ls -d mosfx$corr-$pfx*-$freq 2> /dev/null\n`;
		chomp @files;
		print "Found these files to process:\n";
		foreach $file (@files) { print "\t$file\n"; }

		foreach $file (@files) {
			if ($doflag) {
				system("flag.sh $file 2>&1");
				system("newrfisweep.csh scans=999 subint=999 options=rescan,noseedcorr vis=$file 2>&1");
			}
			foreach $cal (@cals) {
				$calfname="mosfx$corr-$cal-$freq";
				system("gpcopy vis=$calfname out=$file mode=merge 2>&1");
			}
			system("image.csh $file $file $dograph 2>&1");
		}
	}
}

foreach $pfx (@pfxs) {
	system("linmos.sh $pfx 2>&1");
	system("avg12.csh $pfx 2>&1");
}
