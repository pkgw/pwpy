#!/usr/bin/env perl
use PDL;
use PDL::Transform::Cartography;
use PDL::NiceSlice;
use Astro::Coord;
use Astro::Time;
use Getopt::Long;


Getopt::Long::Configure ("bundling");
GetOptions('galactic|g' => \$galactic,
	   'help|h' => \$help,
	   'color|c=s' => \$color,
	   'rfile|r=s' => \$rfname,
	   'ofile|o=s' => \$ofname,
	   'map|m=s' => \$domap);

if ($help) {
	print "map.pl options:\n";
	print "  --galactic | -g\toutput in galactic coordinates\n";
	print "  --map | -m [fname]\t\tproduce map and write to nvss.fits\n";
	print "  --help | -h\t\tprint this help message\n";
	print "  --color | -c [color]\t\tspecify color for regions (default blue)\n";
	print "  --rfile | -r [fname]\t\tspecify input filename for regions (default pigss_ngalcap)\n";
	print "  --ofile | -o [fname]\t\tspecify output filename for regions (default ds9.reg)\n";
}

$color='blue' if (!defined $color);
$width=2000;
$PI = 3.141592653589793238462643383279502884197;

if ($domap ne '') {
	($phi,$rho,$flux)=rcols($domap);
	if ($galactic) {
		($fk4ra, $fk4dec) = fk5fk4(rad2turn($phi),rad2turn($rho));
		($l,$b)=fk4gal($fk4ra,$fk4dec);
		$phi=turn2rad($l);
		$rho=turn2rad($b);
	}
	$nelem=$rho->nelem;
	$map=zeroes($width,$width/2);
}


#
# Take PDLs of (RA,DEC) coordinates (in radians) and transform to pixel coordinates
# on the projected map
sub transform {
	my $phi=shift;	# RA
	my $rho=shift;	# DEC

	my $nelem=$rho->nelem;

	$phi *= 180.0/$PI;	# transform uses degrees
	$rho *= 180.0/$PI;

	my $proj = $phi->glue(1,$rho)->mv(1,0);	# Now $phi is first column, $rho is second column
	$proj -= 360*($proj>180);		# Transform uses different limits
	$proj->inplace->apply(t_aitoff);
	#$proj->inplace->apply(t_caree);

	return $proj;
}


# Transformed limits are -2sqrt(2)..2sqrt(2), -sqrt(2)..sqrt(2)
# Total width is sqrt(32), total height is sqrt(8)
sub pixel {
	my $xin=shift;
	my $yin=shift;
	my ($x,$y);

	$xin = ($xin+sqrt(8))/sqrt(32);	# Convert to range [0..1]
	$yin = ($yin+sqrt(2))/sqrt(8);

	$x = rint($xin * ($width-1));
	$y = rint($yin * ($width/2 -1));

	return($x,$y);
}

if ($domap ne '') {
	# This rotates by 180 degrees in RA; used to put PiGSS target points in the center of the image
	$phi += $PI;
	$mask = $phi > 2*$PI;
	$phi -= $mask*2*$PI;
	$proj=transform($phi,$rho);
	# Add fluxes to the appropriate map pixels, then write the map
	for ($i=0; $i<$nelem; $i++) {
		$j=$proj->at(0,$i);
		$k=$proj->at(1,$i);
		($x,$y)=pixel($j,$k);
		$map($x:$x,$y:$y)+=$flux->at($i);
	}
	wfits $map, 'nvss.fits';
}

if (!defined($rfname)) { $rfname='pigss_ngalcap'; }
if (!defined($ofname)) { $ofname='ds9.reg'; }
($ra,$dec)=rcols($rfname);
if ($galactic) {
	($fk4ra, $fk4dec) = fk5fk4(rad2turn($ra),rad2turn($dec));
	($l,$b)=fk4gal($fk4ra,$fk4dec);
	$ra=turn2rad($l);
	$dec=turn2rad($b);
}
$proj=transform($ra,$dec);
$nelem=$ra->nelem;
print "Appending regions to $ofname\n";
open FILE, ">>$ofname";
for ($i=0; $i<$nelem; $i++) {
	$x = ($proj->at(0,$i)+sqrt(8))/sqrt(32);	# Convert to range [0..1]
	$y = ($proj->at(1,$i)+sqrt(2))/sqrt(8);
	$x *= $width - 1;
	$y *= $width/2 - 1;
	print FILE "cross point $x $y # color=$color\n";
}
close FILE;
