#!/usr/bin/env perl

#
# mapgrid.pl
#
# This program approximates a sensitivity map over a limited strip of DEC for the pfhex grid.
#
# It is not perfect...
#


use PDL;
use PDL::ImageND;
use POSIX;
use Getopt::Long;
use ASTRO_UTIL;

$PI = 3.141592653589793238462643383279502884197;
$sample=6;
$ofname='strip';
Getopt::Long::Configure ("bundling");
GetOptions('area|a=f' => \$area,
           'help|h' => \$help,
	   'format|f' => \$ataformat,
           'infile|i=s' => \$ifname,
           'outfile|o=s' => \$ofname,
	   'sample|s=f' => \$sample);

if ($help) {
        print "mapgrid.pl usage:\n";
        print "\t-a [area] effective beam width in arcmin\n";
        print "\t-h        print this help message\n";
	print "\t-f        load inputs in ATA catalog.list format.\n";
        print "\t-i        input filename\n";
        print "\t-o        output file prefix\n";
        print "\t-s        sampling (pixels per beam)\n";
        exit;
}

if (!defined($area)) {
        $interval = 3.5/sqrt(2.0)/3.14*$PI/180.0;;
}
else {
        $interval = $area/60.0*$PI/180.0;
}

# Read catalog. This should be just a couple rows across a dec boundary.
if ($ataformat) {
        ($ra,$dec,$name)=rcols($ifname, 3,4, { PERLCOLS => [2] });
        $ra *= $PI/12.0;        # Convert from hours/degrees to radians
        $dec *= $PI/180.0;
}
else {
        ($ra,$dec,$name)=rcols($ifname, 1,2, { PERLCOLS => [0] });
}

# Map it.

sub gauss_inten {
	my $r = shift;
	my $c = $interval / sqrt(8*log(2));
	$int = exp(-$r*$r/(2*$c*$c));
	return($int);
}

sub euclidsq { sumover(pow($_[0],2)); }

sub gausskern {
        my $fwhm = shift;
	$fwhm /= (8*log(2))**0.25;
        my $width = shift;
        if (($width % 2) == 0) { $width++; }
        my $k = zeroes (double, $width, $width);
        $k = ($k->allaxisvals - scalar floor($width/2)) / $fwhm;
        $k = euclidsq($k);
        $k = exp(- $k);
        return ($k);
}

$width = POSIX::ceil(2*$sample);
print "Kernel width: $width\n";
$dec0 = $dec->min;
$map = zeroes(POSIX::ceil(2*$PI*$sample/$interval),$width+POSIX::ceil(($dec->max - $dec0)*$sample/$interval));
print "Map is: ",$map->dim(0)," x ",$map->dim(1),"\n";
$mask = gausskern($sample, $width);
$mask *= ($mask > 0.1);
wfits $mask, "mask.fits";

#for ($i=0; $i<$map->dim(0); $i++) {
#	for ($j=0; $j<$map->dim(1); $j++) {
#		for ($k=0; $k<$ra->nelem; $k++) {
#			$myra = $i * 2*$PI/$map->dim(0);
#			$mydec = $j * (sqrt(3)*$interval+$dec->max) / $map->dim(1);
#			($r,$pa,$er) = dist_pa($myra, $mydec, $ra->at($k), $dec->at($k));
#			if ($r < 2*$interval) {
#				$map->slice("$i,$j") += gauss_inten($r);
#			}
#		}
#	}
#}

open FILE, ">$ofname.reg";
for ($k=0; $k<$ra->nelem;$k++) {
	$i=floor($ra->at($k)*$map->dim(0)/(2*$PI));
	$j=floor(($dec->at($k)-$dec0)*$sample/$interval+$width/2);
	print "$$name[$k] $i, $j\n";
	$a=$i-$width/2;
	$b=$i+$width/2;
	$c=$j-$width/2;
	$d=$j+$width/2;
	$map->slice("$a:$b,$c:$d") += $mask;
	print FILE "cross point $i $j # color=green text={$$name[$k]}\n";

}
close FILE;
wfits $map, $ofname.".fits";
system("ds9 -geometry 2000x1000 -cmap BB -log -fits $ofname.fits -zoom 0.8 -regions load $ofname.reg -regions showtext no");
