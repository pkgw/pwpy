#!/usr/bin/perl
#
# Steve's Excellent Transient Identifier
# S. Croft 2008/02/13
#
# Usage seti.pl 
# Looks for sfind*.nvss in the current working directory
# 2008/05/14 - includes error bars
# 2008/05/14 - puts NVSS flux and error in columns 2 and 3; currently just using dummy value for error
# 2008/08/19 - using scalefac = 1
# 2008/10/1 - defaults to using peak flux
# 2009/2/13 - using circular match radius

# default columns for sfind (RA, Dec, pk-flux, err, flux, bmaj, bmin, PA, rms(bg), rms(fit))
$rac = 0;
$dec = 1;
$fpc = 4;
$fpec = 5;
$fic = 6;
$bmajc = 7;
$bminc = 8;
$pac = 9;
$rbc = 10;
$rfc = 11;
# additional columns for NVSS flux and error
$nfc = 15;
$nec = 99;

# match radius in arcsec
$matchrad = 600;

# use peak flux instead of integrated?
$usepk = 0;

foreach $arg (@ARGV) {
    if ($arg =~/mrad=(\S+)/) {
	$matchrad = $1;
    }
    if ($arg =~/usepk=y/) {
	$usepk = 1;
    }
}

print "Match radius is $matchrad\n";

# look for sfind logs
@infiles = `ls sfind.*.nvss`;

# output file (also prints to STDOUT)
open (OUF,">seti.txt");

$epoch = 1;

foreach $infile (@infiles)
{
    open(INF, "$infile");
    @inl = <INF>;
    close(INF);
    print "Read ".scalar(@inl)." lines from $infile\n";
    
    foreach $line (@inl)
    {
	if ($line =~ "^#") {
	}
	else {
# split into fields
	    @fields = split(/\s+/, $line);
	    $ra = $fields[$rac];
	    $de = $fields[$dec];
	    $fp = $fields[$fpc];
	    $fpe = $fields[$fpec];
	    $fi = $fields[$fic];
	    $bmaj = $fields[$bmajc];
	    $bmin = $fields[$bminc];
	    $pa = $fields[$pac];
	    $rb = $fields[$rbc];
	    $rf = $fields[$rfc];
	    $nf = $fields[$nfc];

	    $flux = $fi;

	    if ($usepk) {
		$flux = $fp;
	    }
	    
	    tora($ra); # convert RA to decimal degrees
	    todec($de); # convert dec to decimal degrees

	    $rade = sprintf("%10.6f%+10.6f %9.2f",$ra,$de,$nf);

	    if ($epoch == 1) {
# create hashes to hold the RAs and Decs
		$ras{$rade} = $ra;
		$decs{$rade} = $de;
# create an array of hashes to hold the flux measurements
		$fluxes[$epoch]{$rade} = sprintf("%9.2f",$flux);
		$fluxer[$epoch]{$rade} = sprintf("%7.2f",$rb);
	    }
	    else
# second or greater sfind.log, so compare to the original
	    {
		$critrad = $matchrad;
# ra and dec of the closest source in the original sfind.log to the current position
		$racl = 0;
		$decl = 0;
# check if this position is close to an existing position
# loop through the original hash keys and RAs from epoch 1
		while (($radeo, $rao) = each(%ras) ) {
		    if (defined $fluxes[$epoch]{$radeo}) {}
		    else {
# fill in dummy value at this epoch for sources that weren't detected for whatever reason
			$fluxes[$epoch]{$radeo} = sprintf("%9.2f",-99);	    
			$fluxer[$epoch]{$radeo} = sprintf("%7.2f",0);	    
		    }
		    $deo = $decs{$radeo};
#		    print "$radeo => $rao, $deo\n";
		    $diff = dist($ra,$de,$rao,$deo);			
#		    print "$frac\n";
		    if ($diff < $critrad) {
# this is the closest source to the new position thus far
			$critrad = $diff;
			$racl = $rao;
			$decl = $deo;
			$radecl = $radeo;
#			print "$radecl\n";
		    }
		}
		if ($racl > 0) {
# hash key of the closest source
#		    $radecl = sprintf("%10.6f%+10.6f",$racl,$decl);
		    $fluxes[$epoch]{$radecl} = sprintf("%9.2f",$flux);
		    $fluxer[$epoch]{$radecl} = sprintf("%7.2f",$rb);
#		    print "$radecl $epoch $flux !\n";
#		    print "$fluxes[$epoch]{$radecl}\n";
		}
		else {
# this source hasn't been seen before
		    $fluxes[$epoch]{$rade} = sprintf("%9.2f",$flux);
		    $fluxer[$epoch]{$rade} = sprintf("%7.2f",$rb);
		    $ras{$rade} = $ra;
		    $decs{$rade} = $de;
#		    print "$rade !\n";
# set its flux to dummy value at earlier epochs
		    for ($ep = 1; $ep < $epoch; $ep++) {
			$fluxes[$ep]{$rade} = sprintf("%9.2f",-99);
			$fluxer[$ep]{$rade} = sprintf("%7.2f",0);
		    }
		}
	    }
	}
    }
    $epoch++;
}

@rass = sort keys %ras;

#while (($rade, $ra) = each(%ras)) {

foreach $rade (@rass) {
    print "$rade ";
    print OUF "$rade ";
    for ($ep = 1; $ep < $epoch; $ep++) {
	print "$fluxes[$ep]{$rade} $fluxer[$ep]{$rade}";
	print OUF "$fluxes[$ep]{$rade} $fluxer[$ep]{$rade}";
	}
    print "\n";
    print OUF "\n";
}

close(OUF);


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
	$sign = -1;
    }
    else {
	$sign = 1;
    }
    if ($_[0] =~ /:/)
    {
        @des = split(/:/, $_[0]);
        $_[0] = $sign*((abs($des[0]))+($des[1]/60.0)+($des[2]/3600.0));
    }
    $_[0];
}

sub dist # calculate distance between two points
{
    $ra1 = @_[0];
    $dec1 = @_[1];
    $ra2 = @_[2];
    $dec2 = @_[3];
    
    # convert RA and Dec into decimals
    tora($ra1);
    todec($dec1);
    tora($ra2);
    todec($dec2);
# convert from degrees into arcsec
    $ra1a = $ra1 * 3600.0;
    $dec1a = $dec1 * 3600.0;
    $ra2a = $ra2 * 3600.0;
    $dec2a = $dec2 * 3600.0;
    
    $onerad = 57.2957795131;

# delta dec in arcsec
    $ddec = $dec2a - $dec1a;
    
# average dec
    $dav = ($dec2 + $dec1) / 2.0;
    
# delta RA in arcsec (RA increases towards negative x, but we want positive for angle)
    $drap = ($ra1a - $ra2a) * cos($dav/$onerad);
# here's the real RA diff
    $dra = -$drap;
    
# distance between 1 and 2
    $d = sqrt($ddec**2 + $dra**2);
    return $d;
}





