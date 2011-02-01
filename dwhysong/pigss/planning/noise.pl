#!/usr/bin/perl

use PDL;
use PHOT;
#use PDL::Graphics::PGPLOT;
#use PDL::Graphics::PGPLOT::Window;


print "# name\t\t\tsigma\n";
foreach $infile (@ARGV) {
	$im =  rfits($infile);

	$nbins = $im->nelem / 1000;
	if ($nbins < 30) {
		print "$infile is too small to fit.\n";
		next;
	}

        $mean = $im->davg;
        # This isn't an RMS so as to avoid being dominated by the high points
        $skydev = abs($im - $mean)->dsum / $im->flat->ngoodover;

        # Now throw out pixels that are off by more than 6 * $skydev
        $im = $im->setbadif(abs($im - $mean) > 6.0 * $skydev);

        # Recalculate the mean and "deviation"...
        $mean = $im->davg;
        $skydev = abs($im - $mean)->dsum / $im->flat->ngoodover;

        # Now make a histogram of the sky values
        if ($im->type == float || $im->type == double) {
                $hstep = 3.0 * $skydev / $nbins;
                $hmin = $mean - $hstep * $nbins/2;
                $hmax = $mean + $hstep * $nbins/2;
        }
        else {
                $hstep = rint(3.0 * $skydev / $nbins) + 1;
                $hmin = rint(($mean - $hstep * $nbins/2) / $hstep) * $hstep;
                $hmax = $hmin + $nbins * $hstep;

        }
        # Make the histogram. Out-of-range values must be flagged as bad.
        $im = $im->setbadif($im > $hmax);
        $im = $im->setbadif($im < $hmin);
        ($xvals, $hist) = hist ($im, $hmin, $hmax, $hstep);

        # Abort if more than half the values are in one bin (i.e. distribution is very wrong)
	if ($hist->maximum > $hist->dsum / 2.0) {
        	warn "$infile: pixel brightness distribution seems wrong.";
		next;
	}

        # Fit the histogram to a skewed Gaussian and return the fit
        ($skycnt, $sigma, $skyerr, $yfit) = skew_gauss_fit($xvals, $hist, $nbins);
        ($sigma < 0) and die "Sky fit failed.\n";

	#$win = dev '/xs';
	#bin($xvals,$hist);
	#hold;
	#bin($xvals,$yfit,{COLOUR=>RED});

	$skyerr = sclr $skyerr;
        print "$infile\t\t$sigma\n";
}
