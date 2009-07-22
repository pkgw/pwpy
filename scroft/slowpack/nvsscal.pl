#!/usr/bin/perl
#
# Generates MIRIAD image using NVSSlist
# Usage: nvsscal.pl image
#
# S. Croft March 2008
# 
# NB use .cm image as input (has beam information)
# options fmin=xxx minimum flux
#         rad=xxx default search diameter
#
# 3/24/08 - fixed bright source problem (sources > 10Jy handled correctly)
# 3/26/08 - fixed conversion from integrated flux to Jy / pixel
# 5/12/08 - outputs NVSS file in plain text too
#
# TO DO - create output scripts that run DEMOS and SELFCAL
#
# *** Make sure MIRIAD is set up before running - this script calls MIRIAD commands ***

use Math::Trig;

$rad = 36000; # default search diameter
$fmin = 50; # default minimum flux of 50 mJy
$fwhm = 300; # default Gaussian FWHM (pixels)
$fscfac = 1.0; # divide NVSS flux by this to get radius of circles in overlay file

# use peak flux instead of int?
$usepeak = 0;

# *************************************************************************** # 
$nvssdir = "INSTALLDIR/NVSS/"; # path to NVSSlist directory
# see ftp://nvss.cv.nrao.edu/pub/nvss/CATALOG/README                          #
# *************************************************************************** #

foreach $arg (@ARGV) {
    if ($arg =~ /fmin=(\d+\.?\d*)/) {
	$fmin = $1;
    }
    if ($arg =~ /rad=(\d+\.?\d*)/) {
	$rad = $1;
    }
    if ($arg =~ /fwhm=(\d+\.?\d*)/) {
	$fwhm = $1;
    }
    if ($arg =~ /usepk=1/ || $arg =~ /usepk=y/ || $arg =~ /usepk\+/) {
	$usepeak=1;
        print "Using peak (fitted) values rather than integrated (deconvolved)\n";
    }
}

if (!$usepeak) {
    print "Using integrated (deconvolved) values\n";
}

print "Using minimum flux $fmin mJy\n";
print "Using search radius $rad arcmin\n";
        
$nvssex = "$nvssdir"."NVSSlist";
$nvsscfg = "$nvssdir"."NVSSlist.cfg";

system("cp $nvsscfg .");

$tfile = "/tmp/nvssin.tmp"; # inputs for NVSSlist
$nfile = "/tmp/nvssout.tmp"; # outputs from NVSSlist
$gfile = "imgen.nvss.gauss"; # MIRIAD imgen script for Gaussian image
$cfile = "imgen.nvss.cl"; # MIRIAD imgen script for "clean component" image

$inim = $ARGV[0];
$blim = "$inim.blank";
$ouim = "$inim.nvss.gauss"; # Gaussian image
$cim = "$inim.nvss.cl"; # "clean component" image
$toim = "$inim.nvss.gtmp"; # temporary Gaussian image
$tcim = "$inim.nvss.ctmp"; # temporary clean image

$olay = "$inim.olay"; # MIRIAD overlay file
$ptxt = "$inim.nvss.txt"; # plain text output

# Hopefully this script works for negative decs smaller than 1 degree (haven't checked)
$sign="+";

# conversion factors from Jy/beam to Jy/pixel
# in square arcseconds (ellipse area = 1/2 * bmaj * 1/2 * bmin * pi) * (3600 * 180 / pi)**2
#$beamsqar = `gethd in=$inim/bmaj` * `gethd in=$inim/bmin` * 0.785398;
$beamsqar = `gethd in=$inim/bmaj` * `gethd in=$inim/bmin` * 3.3415E10;
$pixsize = `gethd in=$inim/cdelt2` * 206265;
$beampix = $beamsqar / ($pixsize * $pixsize);

#scale factor from NVSS integrated flux in mJy to ATA Jy/pix
#$jyp = 1 / ($beampix * 1000.0);
$jyp = 1 / 1000.0;

#print "Beam is $beamsqar sq. arcsec. = $beampix pixels\n";
print "Correction factor from mJy/beam to Jy/pix is $jyp\n";

# get RA and DEC of image center from headers
$ra = 57.2957795 * `gethd in=$inim/crval1`;
$de = 57.2957795 * `gethd in=$inim/crval2`;

print "Image center is $ra $de\n";

# clean up from the last run
system("rm -r $blim >& /dev/null");
system("rm -r $ouim >& /dev/null");
system("rm -r $cim >& /dev/null");
system("rm -r $toim >& /dev/null");
system("rm -r $tcim >& /dev/null");

print "Creating blank image $blim\n";

system ("maths exp=\"($inim-$inim)\" out=$blim");

# maximum flux for NVSSlist
$fmax = 1.0E10;

# NVSSlist needs sexagesimal format
tohms($ra);
todms($de);

printf ("Searching within %f arcsec of ",$rad);
printf ("%02d %02d %05.2f ",$rahr,$ramn,$rasc);
printf ("%s%02d %02d %05.2f\n",$sign,$dedg,$demn,$desc);

# create the input file for NVSSlist
unlink($tfile);
open(SC,">$tfile");

# Comments are NVSSlist prompts
# Enter any output file name [terminal] {CR}
print SC "$nfile\n";
# Enter any input field list file name [ask] {CR}
print SC "\n";
# Enter equinox code 1=B1900 2=B1950 3=J2000 [3] {3}
print SC "3\n";
# Enter 0=Deconvolved 1=Fitted 2=Raw values [0] {0}
print SC "$usepeak\n";
# Enter minimum, maximum flux density (mJy) [0,1.0E10] {$fmin,$fmax}
print SC "$fmin,$fmax\n";
# Enter minimum percent pol. flux density [0] {0}
print SC "0\n";
# Enter object name [none} {CR}
print SC "\n";
# Enter central RA (hh mm ss.ss) {$rahr $ramn $rasc}
printf SC ("%02d %02d %05.2f\n",$rahr,$ramn,$rasc);
# Enter central Dec (sdd mm ss.s) {$dedg $demn $desc}
printf SC ("%s%02d %02d %05.2f\n",$sign,$dedg,$demn,$desc);
# Search radius, verification radius in arcsec [15,0] {$rad,0}
print SC "$rad,0\n";
# Search box halfwidth in hr,deg [12,180]
print SC "\n";
# Max, min abs gal latitude in deg [0,90]
print SC "\n";

close(SC);

unlink($nfile);

# run NVSSlist on this input script
system("$nvssex < $tfile >& /dev/null");
#system("$nvssex < $tfile");

unlink($tfile);

open(NF,"$nfile");
my @nf = <NF>;
close(NF);

#unlink($nfile);
unlink($gfile);
unlink($olay);
unlink($ptxt);

# create the MIRIAD script that calls imgen to generate the Gaussian image
# We're currently using arbitrary FWHM for the Gaussians
# need to run this if we want to actually generate the image
open(GF,">$gfile");

# create the MIRIAD script that calls imgen to generate the clean image
# need to run this if we want to actually generate the image
open(CF,">$cfile");

# create the MIRIAD overlay file
open(OF,">$olay");

# create the plain text output
open(PT,">$ptxt");

# we'll be calling imgen several times to avoid arguments that are too long
$imgenst = "imgen in=$blim out=$ouim object=";
$imgenstc = "imgen in=$blim out=$cim object=";

# these variables contain multiple imgen calls
$imgensta = "";
$imgenstca = "";

# these variables contain the object characteristics (spar) for imgen
$sparst = "spar=";
$sparstc = "spar=";

# imgen will fail if the argument gets too long, so we have to split it up into
# several runs of imgen - defaulting to 20 components per run
$comperun = 20;
# first component for this run
$comp = 1;

foreach $inl (@nf)
{
#    print $inl;
    chop($inl);
    # strip leading spaces
    $inl =~ s/^\s+//;
    # look for lines that contain NVSS positions and fluxes
    if ($inl =~ /^(\d+)\s+(\d+)\s+(\d+\.\d\d)\s+([+-])(\d+)\s+(\d+)\s+(\d+\.\d)......\s*(\d+\.\d)/) {
	$rah = $1;
	$ram = $2;
	$ras = $3;
	$raa = sprintf("%02d:%02d:%05.2f",$rah,$ram,$ras);
	$rafp = tora($raa);
	$sign = $4;
	$ded = $5;
	$dem = $6;
	$des = $7;
	$dea = sprintf("%s%02d:%02d:%05.2f",$sign,$ded,$dem,$des);
	$defp = todec($dea);
	$flux = $8;

# how far is this position from the field center?
	@off = distoff($ra,$de,$raa,$dea);
	$rao = $off[0];
	$deo = $off[1];
#        printf ("%02d %02d %05.2f ",$rah,$ram,$ras);
#	printf ("%s%02d %02d %05.2f ",$sign,$ded,$dem,$des);
# generate a Gaussian at that position
	$sparst = sprintf ("%s,%.1f,",$sparst,$flux);
	$sparst = sprintf ("%s%d,%d,%d,%d,5",$sparst,$rao,$deo,$fwhm,$fwhm);
	$imgenst = "$imgenst,gaussian";

# generate a point (pseudo clean component) at that position
# scale the flux from mJy to Jy / pixel
	$fluxjyp = $flux * $jyp;
	$sparstc = sprintf ("%s,%.5f,",$sparstc,$fluxjyp);
	$sparstc = sprintf ("%s%d,%d",$sparstc,$rao,$deo);
	$imgenstc = "$imgenstc,point";
# this goes into the overlay file too
	$fluxsc = $flux / $fscfac; # scale the circles a bit
	printf OF ("ocircle hms dms nvss no %2d %2d %5.2f %2d %2d %5.2f %7d 0 0\n",$rah,$ram,$ras,$ded,$dem,$des,$fluxsc);
	printf PT ("%9.5f %9.5f %9.1f\n",$rafp,$defp,$flux);
# done with this component
	$comp++;
	if ($comp > $comperun) {  # start a new imgen call to avoid long args
	    $comp = 1;
	    $imgenst = "$imgenst $sparst\n";
# get rid of the extraneous last equals sign
	    $imgenst =~ s/=,/=/g;
	    
	    $imgenstc = "$imgenstc $sparstc\n";
# get rid of the extraneous last equals sign
	    $imgenstc =~ s/=,/=/g;
	    $imgensta = "$imgensta$imgenst";
	    $imgenstca = "$imgenstca$imgenstc";
# Between each call to imgen, move the files to a temporary file.
# We'll add the next set of components to this temp file to
# create the output map
	    $imgenst = "rm -rf $toim; mv $ouim $toim\nimgen in=$toim out=$ouim object=";
	    $imgenstc = "rm -rf $tcim; mv $cim $tcim\nimgen in=$tcim out=$cim object=";
# reset the imgen parameters for the next batch	    
	    $sparst = "spar=";
	    $sparstc = "spar=";
	}
    }
}

# add the remaining components (last batch)
if ($comp > 1) {	
    $imgenst = "$imgenst $sparst\n";
    $imgenst =~ s/=,/=/g;
    
    $imgenstc = "$imgenstc $sparstc\n";
    $imgenstc =~ s/=,/=/g;
    $imgensta = "$imgensta$imgenst";
    $imgenstca = "$imgenstca$imgenstc";
    $imgenst = "rm -rf $toim; mv $ouim $toim\nimgen in=$toim out=$ouim object=";
    $imgenstc = "rm -rf $tcim; mv $cim $tcim\nimgen in=$tcim out=$cim object=";
    
    $sparst = "spar=";
    $sparstc = "spar=";
}
    

print GF "$imgensta"."rm -rf $toim\n";
#print GF "cgdisp in=$ouim device=/xs olay=$olay\n";
print GF "cgdisp in=$ouim device=/xs\n";

print CF "$imgenstca"."rm -rf $tcim\n";
# change units to Jy/pix in header
print CF "puthd in=$cim/bunit value=JY/PIXEL\n";
#print GF "cgdisp in=$ouim device=/xs olay=$olay\n";
#print CF "cgdisp in=$ouim device=/xs\n";

close(GF);
close(OF);
close(PT);
close(CF);

# make the scripts executable
system("chmod +x $gfile");
system("chmod +x $cfile");

print "Generated output MIRIAD script $gfile\n";
print "Generated output MIRIAD script $cfile\n";
print "Generated MIRIAD overlay file $olay\n";
print "Generated NVSS text file $ptxt\n";

sub tohms # converts decimal to RA ($rahr, $ramn, $rasc)
{
    my $ra = $_[0];
    $rahr = int ($ra/15.0);
    my $rem = $ra / 15.0 - $rahr;
    $ramn = int(60 * $rem);
    my $rem = $rem * 60.0 - $ramn;
    $rasc = $rem * 60.0;
    return 0;
}
    
sub todms # converts decimal to dec ($sign$dedg, $demn, $desc)
{
    my $dec = $_[0];
    if ($dec < 0) {
	$sign = "-";
	$dec = -1 * $dec;
    }
    else {
	$sign = "+";
    }
    $dedg = int ($dec);
    my $rem = $dec - $dedg;
    $demn = int ($rem * 60.0);
    my $rem = $rem * 60.0 - $demn;
    $desc = $rem * 60.0;
    return 0;
}

sub distoff # calculates distance between two positions
{
    $ra1 = @_[0];
    $de1 = @_[1];
    $ra2 = @_[2];
    $de2 = @_[3];
    
    $rad1 = tora($ra1); # convert to decimal
    $ded1 = todec($de1); # as above
    $rad2 = tora($ra2); # convert to decimal
    $ded2 = todec($de2); # as above
    
    $radi = $rad2 - $rad1;
    $dedi = $ded2 - $ded1;
    $desav = ($ded1 + $ded2)/2.0;

# in arcseconds
    $dedas = 3600.0 * $dedi;
    $radas = 3600.0 * (($radi)*cos($ded1/57.29578));
    @offs = ($radas,$dedas);
    return @offs;
}
    
sub tora   # converts RA xx:xx:xx.xx to decimal or leaves as decimal
{ 
    if ($_[0] =~ /:/)
    {
        @ras = split(/:/, $_[0]);
        $_[0] = (($ras[0]*15.0)+($ras[1]/4.0)+($ras[2]/240.0));
    }
    $_[0];
}


sub todec   # converts DEC xx:xx:xx.xx to decimal or leaves as decimal
{
    if ($_[0] =~ /-/) {
        $sgn = -1;
    }
    else {
        $sgn = 1;
    }
    if ($_[0] =~ /:/)
    {
        @des = split(/:/, $_[0]);
        $_[0] = $sgn*((abs($des[0]))+($des[1]/60.0)+($des[2]/3600.0));
    }
    $_[0];
}
