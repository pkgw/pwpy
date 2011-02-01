#!/usr/bin/env perl
use PDL;
use PDL::Graphics::PGPLOT::Window;
use PDL::Graphics::LUT;
use PDL::Transform::Cartography;
use PDL::NiceSlice;
use Astro::Coord;
use Astro::Time;
use Getopt::Long;

$dev='/xs';

# FIXME: the color (grayscale, actually) display only works if you also display a map.
# Otherwise everything is the same color.

# Take PDLs of (RA,DEC) coordinates (in radians) and transform to pixel coordinates
# on the projected map
sub transform {
	my $phi=shift;  # RA
	my $rho=shift;  # DEC

	$phi *= 180.0/$PI;      # transform uses degrees
	$rho *= 180.0/$PI;

	my $proj = $phi->glue(1,$rho)->mv(1,0); # Now $phi is first column, $rho is second column
	$proj -= 360*($proj>180);	       # Transform uses different limits
	$proj->inplace->apply(t_aitoff);
	#$proj->inplace->apply(t_caree);

	return $proj;
}


# Given an RA/DEC coordinate, return pixel coordinates for the map image.
# Transformed limits are -2sqrt(2)..2sqrt(2), -sqrt(2)..sqrt(2)
# Total width is sqrt(32), total height is sqrt(8)
sub pixel {
	my $xin=shift;
	my $yin=shift;
	my ($x,$y);

	$xin = ($xin+sqrt(8))/sqrt(32); # Convert to range [0..1]
	$yin = ($yin+sqrt(2))/sqrt(8);

	$x = rint($xin * ($width-1));
	$y = rint($yin * ($width/2 -1));

	return($x,$y);
}


# Rotate RA coordinate (in radians)
sub dorotate {
	my $rot = shift;	# scalar value in degrees
	my $coords = shift;     # a PDL

	$coords += $rotate;
	my $mask = $coords > 2*$PI;
	$coords-= $mask*2*$PI;

	return $coords;
}

$database='/etc/observatory/pfhex';
$rotate = 180.0; # This default is useful for PiGSS-2. Convert to radians later.
Getopt::Long::Configure ("bundling");
GetOptions('galactic|g' => \$galactic,
	   'help|h' => \$help,
	   'database|b=s' => \$database,
	   'infile|i=s' => \$infile,
	   'device|d=s' => \$dev,
	   'file|f=s' => \$priofile,
	   'rotate|r=f' => \$rotate,
	   'map|m=s' => \$domap);

if ($help) {
	print "map.pl options:\n";
	print "  --galactic | -g\t\toutput in galactic coordinates\n";
	print "  --map      | -m [fname]\tload map image (default nvss.fits)\n";
	print "  --help     | -h\t\tprint this help message\n";
	print "  --database | -b\t\tspecify database for schedule.pl\n";
	print "  --device   | -d [dev]\t\tspecify PGPLOT device\n";
	print "  --file     | -f [fname]\tspecify input priority file (output of 'schedule.pl -l prio')\n";
	print "  --infile   | -i [fname]\tspecify input filename for regions (default pfhex.fields)\n";
	print "  --rotate   | -r [degrees]\trotate RA coordinates\n";
	exit();
}

$rotate *= $PI/180.0;   # Convert to radians.
$color='blue' if (!defined $color);
$width=2000;
$PI = 3.141592653589793238462643383279502884197;
@colors=(1,2,3,4,5);

$map = rfits($domap) if ($domap ne '');

if (!defined($infile)) { $infile='pfhex.fields'; }

($name,$ra,$dec)=rcols($infile,{ PERLCOLS => [0] });	# $name is an array ref

# Let's get status information to assign colors
$color = zeroes($ra->nelem);
if (defined $priofile) {
	die "Error: $priofile not found.\n" if (not -f $priofile);
	open INFILE, "<", "$priofile";
	@lines= <INFILE>;
	close INFILE;
}
else {
	@lines = `./schedule.pl -f $database -l prio`;
}
if (scalar @lines != $ra->nelem) {
	die "Error: $infile has ",$ra->nelem," elements but schedule.pl returned ",scalar(@lines),"\n";
}
foreach $line (@lines) {
	$line =~ /(pfhex-\d*-\d*) prio=(\d)/;		# $1 holds the name, $2 holds the priority
	$priohash{$1} = $2;
}
for ($i=0; $i<$ra->nelem; $i++) {
	$color->slice("$i") .= $colors[5-$priohash{$$name[$i]} ];
}


$ra = dorotate($rotate,$ra);
if ($galactic) {
	($fk4ra, $fk4dec) = fk5fk4(rad2turn($ra),rad2turn($dec));
	($l,$b)=fk4gal($fk4ra,$fk4dec);
	$ra=turn2rad($l);
	$dec=turn2rad($b);
}
$proj=transform($ra,$dec);


$win = pgwin($dev, {Aspect => 1, WindowWidth => 12});
#$win = pgwin($dev, {Aspect => 0.5, WindowWidth => 18});
#ctab(lut_data("ramp"));
$win->ctab(lut_data("heat"));
#$win->ctab(lut_data('rainbow'));
if ($domap) {
	my ($mean, $rms, $median, $min, $max) = stats($map);
	my ($mean,$prms,$median,$min,$max,$adev,$rms) = stats($map);
	my $min = 0;
	my $max = $mean + $rms;
	imag ($map, $min, $max, {PIX=>1,ALIGN=>'CC'});
	hold;
}
$x = $proj->slice("0,:") + sqrt(8);
$x /= sqrt(32);
$x *= $width-1;
$y = $proj->slice("1,:") + sqrt(2);
$y /= sqrt(8);
$y *= $width/2-1;
$win->env(min($x),max($x),min($y),max($y));
$x = $x->flat->append(pdl([-999,-999]));
$y = $y->flat->append(pdl([-999,-999]));
$color = $color->append(pdl[$colors[0],$colors[-1]]);
#$win->points($x,$y,{SYMBOL=>DOT,SYMBOLSIZE=>1,XRange=>[0,$width],YRange=>[0,$width/2],ColorValues=>$color});
$win->points($x,$y,{ColorValues=>$color,SYMBOLSIZE=>0.5});

print "elem: " . $x->nelem . " " . $y->nelem . " " . $color->nelem . "\n";
print "Unique color values: " . $color->uniq . "\n";
