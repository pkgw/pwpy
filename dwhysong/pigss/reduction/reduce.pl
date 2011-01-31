#!/usr/bin/env perl
BEGIN { $^W = 1; }

use Getopt::Long;
$ENV{"PATH"}="/export/pigss-processing/bin:/hcro/miriad/build/bin:/home/obs/mmm/karto/RAPIDBeta:/home/obs/mmm/karto/cals:".$ENV{"PATH"};

# FIXME: error
# ### Warning [gpcopy]:  Merging bandpasses is not implemented


$plim="0.0001,80";
$dograph='';
Getopt::Long::Configure ("bundling");
GetOptions('cal|c' => \$docal,
           'graphic|g' => \$dograph,
	   'help|h' => \$help,
	   'manual|m=s' => \$frqs,
	   'prefix|p=s' => \$prfx,
	   'test|t' => \$test,
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
	print "\t-t\ttest mode\n";
	exit;
}


sub banner {
        print "\n" . "*" x 80 . "\n";
}


sub printheader {
        my $str=shift;
        print "\n" . "*" x 80 . "\n\t$str\n" . "*" x 80 . "\n";
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
	@pfxs=('pf','pfhex','lockman','eliasn1','coma');
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


sub unique {
	my @array=@_;

        my %found;
        @found{@array}=();
        return keys %found;
}


@cals=getcals;
for ($i=0; $i<(scalar(@corrs)); $i++) {
#	%hash=();
	$corr=$corrs[$i];
	$freq=$freqs[$i];
	if ($doflag) {
		printheader("Flagging correlator $corr");
		@tmp=();
		foreach $cal (@cals) {
			$fname="mosfx$corr-$cal-$freq";
			push @tmp, $fname;
		}
		$calline = join ',',@tmp;

		$tmp=();
		foreach $pfx (@pfxs) {
			@tmp = `ls -d mosfx$corr-$pfx*-$freq 2> /dev/null`;
			chomp @tmp;
			@files = (@files,@tmp);
		}

		if (not $test) {
			open OUTFILE, ">", "autoflag-$corr-tmp.txt";
			foreach(@files) {
				print OUTFILE "$_\n";
			}
			close OUTFILE;

			foreach $file (@files) {
				`uvflag vis=$file flagval=u`;
			}
		}
		print("Running: autoflag cal=$calline vis=\@autoflag-$corr-tmp.txt options=ata,nonoise\n");
		$test or `autoflag cal=$calline vis=\@autoflag-$corr-tmp.txt options=ata,nonoise 2>&1 | tee autoflag-$corr.log`;
	}
	foreach $cal (@cals) {
		$flux=getflux($cal,$freq);
		$fname="mosfx$corr-$cal-$freq";
		printheader("Processing calibrator: $fname");
		if ($doflag and not $test) {
			system("flag.sh $fname 2>&1");
#			@badbase = `neweprms.csh vis=$fname plim=$plim`;
#			@{$hash{"$cal-$corr"}} = @badbase;
#			chomp @badbase;
#			foreach $badbl (@badbase) {
#				system("uvflag vis=$fname select=\"$badbl\" flagval=f options=none > /dev/null");
#			}
			banner;
		}
		if ($docal and not $test) {
			system("newcalcal.csh vis=$fname flux=$flux 2>&1");
		}
		# Now sort out the calibrator dependence in %hash
#		if ($doflag) {
#			@badbase=();
#			foreach $cal (@cals) {
#				push @badbase,@{$hash{"$cal-$corr"}};
#				delete $hash{"$cal-$corr"};
#			}
#			@badbase = unique(@badbase);
#			@{$hash{$corr}} = @badbase;
#		}
	}

	foreach $pfx (@pfxs) {
		@files=`ls -d mosfx$corr-$pfx*-$freq 2> /dev/null`;
		chomp @files;
		print "Found these files to process:\n";
		foreach $file (@files) { print "\t$file\n"; }

		foreach $file (@files) {
			printheader "Processing: $file";
			if ($doflag and not $test) {
				system("flag.sh $file 2>&1");
				banner;
#				foreach $badbl (@{$hash{$corr}}) {
#					print "Flagging $badbl\n";
#					print("uvflag vis=$file select=\"$badbl\" flagval=f options=none");
#					system("uvflag vis=$file select=\"$badbl\" flagval=f options=none");
#				}
#				banner;
			}
			foreach $cal (@cals) {
				$calfname="mosfx$corr-$cal-$freq";
				$test or system("gpcopy vis=$calfname out=$file mode=merge 2>&1");
			}
			$test or system("image.csh $file $file $dograph 2>&1");
		}
	}
}

foreach $pfx (@pfxs) {
	$test or system("linmos.sh $pfx 2>&1");
	$test or system("avg12.csh $pfx 2>&1");
}
