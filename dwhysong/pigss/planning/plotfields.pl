#!/usr/bin/env perl
use PDL;
use PDL::Transform::Cartography;
use PDL::NiceSlice;
use Astro::Coord;
use Astro::Time;
use Getopt::Long;


Getopt::Long::Configure ("bundling");
GetOptions('galactic|g' => \$galactic,
	   'ata|a' => \$ataformat,
	   'master|m=s' => \$masterfile,
	   'help|h' => \$help,
	   'color|c=s' => \$color,
	   'file|f=s' => \$fname,
	   'ofile|o=s' => \$ofname);

if ($help) {
	print "map.pl options:\n";
	print "  --ata | -a\tinput coordinates in ATA catalog.list format\n";
	print "  --galactic | -g\toutput in galactic coordinates\n";
	print "  --help  | -h\t\tprint this help message\n";
	print "  --color | -c [color]\tspecify color for regions (default blue)\n";
	print "  --file  | -f [fname]\tspecify input file containing fields (default pigss2.done)\n";
	print "  --master| -m [fname]\tspecify master catalog file (default pigss2.fields)\n";
	print "  --ofile | -o [fname]\tspecify output filename for regions (default ds9.reg)\n";
	exit;
}

defined($masterfile) or $masterfile='pigss2.fields';
$color='blue' if (!defined $color);
$width=2000;
$PI = 3.141592653589793238462643383279502884197;

# Take PDLs of (RA,DEC) coordinates (in radians) and transform to pixel coordinates
# on the projected map
sub transform {
	my $phi=shift;	# RA
	my $rho=shift;	# DEC

	my $nelem=$rho->nelem;

	$phi *= 180.0/$PI;	# transform uses degrees
	$rho *= 180.0/$PI;

	my $proj = $phi->glue(1,$rho)->mv(1,0);	# Now $phi is first column, $rho is second column
	$proj -= 360*($proj>180);		# Transform uses limits of [-180,180] in both coordinates
	$proj->inplace->apply(t_aitoff);
	#$proj->inplace->apply(t_mercator);
	#$proj->inplace->apply(t_caree);

	return $proj;
}


if (!defined($fname)) { $fname='pigss2.done'; }
open(FILE, "< $fname") || die("Can't open $fname: $!\n");
@targets=<FILE>;
close FILE;
chomp @targets;
exit if (scalar(@targets)<1);
$filter='/'.join("|",@targets).'/';
$filter =~ s/\+/\\\+/g;		# escape the + in the field names

if ($ataformat) {
	($ra,$dec,$name)=rcols($masterfile, 3,4, { PERLCOLS => [2], KEEP=>$filter });
	$ra *= $PI/12.0;	# Convert from hours/degrees to radians
	$dec *= $PI/180.0;
}
else {
	($ra,$dec,$name)=rcols($masterfile, 1,2, { PERLCOLS => [0], KEEP=>$filter });
}

# This rotates by 180 degrees in RA; used to put PiGSS target points in the center of the image
$ra += $PI;
$mask = $ra > 2*$PI;
$ra -= $mask*2*$PI;

if ($galactic) {
	print "plotfields.pl: converting to galactic coordinates\n";
	($fk4ra, $fk4dec) = fk5fk4(rad2turn($ra),rad2turn($dec));
	($l,$b)=fk4gal($fk4ra,$fk4dec);
	$ra=turn2rad($l);
	$dec=turn2rad($b);
}
$proj=transform($ra,$dec);
$nelem=$ra->nelem;
if (defined($ofname)) {
	print "plotfields.pl: appending $nelem regions to $ofname\n";
	open FILE, ">>$ofname";
}
for ($i=0; $i<$nelem; $i++) {
	$x = ($proj->at(0,$i)+sqrt(8))/sqrt(32);	# Convert to range [0..1]
	$y = ($proj->at(1,$i)+sqrt(2))/sqrt(8);
	$x *= $width - 1;
	$y *= $width/2 - 1;
	print FILE "cross point $x $y # color=$color text={$$name[$i]}\n" if defined $ofname;
	print "cross point $x $y # color=$color text={$$name[$i]}\n" if (!defined $ofname);
}
close FILE if defined $ofname;
