#!/usr/bin/env perl

use POSIX;
use Math::Trig;
use Astro::Coords;
use Getopt::Long;


$restart=0.5;
Getopt::Long::Configure ("bundling");
GetOptions('area|a=f' => \$area,
	   'help|h' => \$help,
	   'restart|r=f' => \$restart,
	   'glat|g=f' => \$minglat,
	   'boundary|b' => \$printboundaries,
           'format|f' => \$format);

if ($help) {
	print "pigss_fields.pl usage:\n";
	print "\t-a [area] effective beam width in arcmin\n";
	print "\t-f        format output for ATA catalog.list\n";
	print "\t-r [#]    re-start grid when cos(dec) falls by a factor of #\n";
	print "\t-g [dec]  minimum galactic latitude, in decimal degrees\n";
	print "\t-h        print this help message\n";
	exit;
}
$PI = 3.141592653589793238462643383279502884197;

if (!defined($minglat)) {
	$minglat = 30;
}

if (!defined($area)) {
	$interval = 3.5/sqrt(2.0)/3.14*$PI/180.0;;
}
else {
	$interval = $area/60.0*$PI/180.0;
}
	# If input is in square degrees, use this:
	#$A=@ARGV[0] * $PI * $PI / 129600; # input in sq. degrees
	#$radius = acos(1.0-$A/(2*$PI));
	#$interval = $radius * 2.0;
$ndec = 0;
$n=0;
$ngood=0;
$glat=$minglat+1;
$nrestart=-1;

# Hex spacing. Move sqrt(3)/2 * interval in DEC
$ddec = sqrt(3)/2*$interval;

#
#
# FIXME: retain hex pattern. Do this:
#
# Start at dec=0 with N0 = 2 pi / L points
#	Then, the next row has the same number of points N(i+1) = N(i)
#		UNTIL L(i) / L(0) < (1 - delta) for some delta
#	Then adjust N and fix the overlap, and start over.
#

sub calc_hemisphere {	
	while (abs($dec) < $PI/2.0) {
		$nrestart++;
		$cosdec0 = abs(cos($dec));
		$nrot = POSIX::ceil(2*$PI*abs(cos($dec))/$interval);	# number of cells around a circle of constant declination
		if ($nrot < 1) { $nrot = 1; }				# Always have at least one point (at the pole)
		$myinterval = 2*$PI / $nrot;				# slightly adjusted interval, to give the even spacing at this dec

		if ($printboundaries) {
			print STDERR "pfhex-$ndec\n";
		}
	
		while (abs(cos($dec))/$cosdec0 > $restart) {
			if ($ndec % 2 == 1) {
				$ra = $myinterval/2.0;				# In a hex pattern, offset every other row by half a spacing
			}
			else { $ra = 0.0; }

			if (!(($ndec > 0) and ($dec == 0))) { 			# Avoid duplication of the dec=0 row
				for ($nra=0; $nra<$nrot; $nra++) {
					$name="pfhex-$ndec-$nra";
					$c = new Astro::Coords(name=>$name, ra=>$ra, dec=>$dec, type=>'j2000', units=>'radians');
					$atara=(12.0/$PI)*$ra;
					$atadec=(180.0/$PI)*$dec;
					$glat = $c->glat( format => "s" );
					if ($glat>=$minglat) {
						if ($format) { printf "pigss2\tblank\t$name\t$atara\t$atadec\tdhw\n"; }
						else { printf "pfhex-$ndec-$nra\t$ra\t$dec\n"; }
						$ngood++;
					}
					$n++;
					$ra += $myinterval;
					if ($ra>=2*$PI) { $ra -= 2*$PI; }
				}
			}
			$dec += $ddec;
			$ndec++;
		}
	}
}

$dec = 0;
calc_hemisphere();
$dec = 0;
$ddec = - $ddec;
calc_hemisphere();

print STDERR "Restarted ",$nrestart," times.\n";
