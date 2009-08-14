#!/usr/bin/perl
# Source Locator and Outburst Watcher
# Produces a PDF with postage stamps of ATA sources from multiple epochs which match NVSS sources
#
# Steve Croft 2008/08/19
# Rewritten in Perl 2009/07/06
#
# Requires Supermongo, WIP, MIRIAD, LaTeX, Perl, Java (must be installed by user and in path)
# You can test that these are installed as follows:
# sm -h
# wip -h
# miriad -h
# latex -v
# perl -v
# java -version
#
# Also requires Skyview Java script (installed locally by INSTALL script)
# plus cfitsio, NVSSlist and NVSS catalog (installed locally by INSTALL script)
# plus a whole slew of Perl scripts (supplied as part of install):
# nvsscal.pl
# slowcat.pl
# matchcolnl.pl
# setierrcirc.pl
# setisortmax.pl
# setinvss.pl
# addjid.pl
# atanvssseticm.pl
# setipdf.pl
# 
#
# NB - SLOW may delete files in the working directory; create a new directory and copy the input maps there before running
# NB - the presence of additional sfind files, mosaics, etc. in the working directory may cause SLOW not to run as expected
#      although generally a restart from a previous run of SLOW is possible (but may not produce the expected results).
#      The default switches should allow SLOW to run in a directory containing nothing butwine  input ATA mosaics.
#
# TO DO - option to reject sources that are less than n sigma from sfind catalogs - configurable sfind options?
# TO DO - run sfind on coadd and report fluxes in postage stamps

$nvsscat = 1; # Get NVSS catalog?
$gcat = 1; # Generate sfind culled catalogs?
$matchrad = 600; # Default match radius
$negmatch = 0; # 1 = Keep only NVSS non-matches; 0 = Keep only NVSS matches
$allmatch = 0; # Ignore negmatch and keep all matches?
$fmin = 15; # NVSS minimum flux
# *** for testing purposes, can set fmin to be high, either here or on command line, so that NVSS catalog
# *** is smaller and script runs more quickly
#$fmin = 200;
$nrad = 35; # NVSS search radius (degrees) - make this bigger than the input image; *** TO DO - fix this to make it correspond to input image size
$nvssmatch = 0; # NOT IMPLEMENTED 
$mkfits = 1; # Make 2D FITS images of input files?
$mkcats = 1; # Match catalogs to NVSS?
$usepk = 0; # Use peak flux from sfind rather than integrated?
$seti = 1; # Run Steve's Excellent Transient Identifier
$atasort = 1; # 0 = sort on NVSS max flux; 1 = sort on ATA max flux
$coadd = 1; # Make coadd image?
$swarp = 0; # Use SWARP to make coadd?
$nvsspost = 1; # Get NVSS postage stamps?
$nvssmir = 1; # Generate MIRIAD versions of NVSS postage stamps
$eppost = 1; # Generate FITS postage stamps from input files?
$rejbl = 1; # Reject sources where more than 200 pixels are blanked? CURRENTLY NOT IMPLEMENTED
$fluxgr = 1; # Generate flux graphs?
$postps = 1; # Generate postscript postage stamps?
$comball = 1; # Combine graphs and postage stamps into a single PDF?


$imn = 0;

foreach $arg (@ARGV) {
#    print "*** $arg ***\n";
    if ($arg eq "nvsscat") {
	$nvsscat = 1;
    }
    elsif ($arg eq "nonvss" || $arg eq "nonvsscat") {
	$nvsscat = 0;
    }
    elsif ($arg =~ /matchrad=(\d+\.?\d*)/) {
	$matchrad = $1;
    }
    elsif ($arg eq "negmatch") {
	$negmatch = 1;
    }
    elsif ($arg eq "nvssmatch") {
	$negmatch = 0;
    }
    elsif ($arg eq "allmatch") {
	$allmatch = 1;
    }
    elsif ($arg =~ /fmin=(\d+\.?\d*)/) {
	$fmin = $1;
    }
    elsif ($arg eq "mkfits") {
	$mkfits = 1;
    }
    elsif ($arg eq "nofits" || $arg eq "nomkfits") {
	$mkfits = 0;
    }
    elsif ($arg eq "gcats") {
	$gcat = 1;
    }
    elsif ($arg eq "nogcats") {
	$gcat = 0;
    }
    elsif ($arg eq "mkcats") {
	$mkcats = 1;
    }
    elsif ($arg eq "nocats" || $arg eq "nomkcats") {
	$mkcats = 0;
    }
    elsif ($arg eq "seti") {
	$seti = 1;
    }
    elsif ($arg eq "noseti") {
	$seti = 0;
    }
    elsif ($arg eq "atasort") {
	$atasort = 1;
    }
    elsif ($arg eq "nvsssort") {
	$atasort = 0;
    }
    elsif ($arg eq "coadd") {
	$coadd = 1;
    }
    elsif ($arg eq "nocoadd") {
	$coadd = 0;
    }
    elsif ($arg eq "swarp") {
	$swarp = 1;
    }
    elsif ($arg eq "linmos") {
	$swarp = 0;
    }
    elsif ($arg eq "nvsspost") {
	$nvsspost = 1;
    }
    elsif ($arg eq "nonvsspost") {
	$nvsspost = 0;
    }
    elsif ($arg eq "nvssmir") {
	$nvssmir = 1;
    }
    elsif ($arg eq "nonvssmir") {
	$nvssmir = 0;
    }
    elsif ($arg eq "eppost") {
	$eppost = 1;
    }
    elsif ($arg eq "noeppost") {
	$eppost = 0;
    }
    elsif ($arg eq "rejbl") {
	$rejbl = 1;
    }
    elsif ($arg eq "norejbl") {
	$rejbl = 0;
    }
    elsif ($arg eq "fluxgr") {
	$fluxgr = 1;
    }
    elsif ($arg eq "nofluxgr") {
	$fluxgr = 0;
    }
    elsif ($arg eq "postps") {
	$postps = 1;
    }
    elsif ($arg eq "nopostps") {
	$postps = 0;
    }
    elsif ($arg eq "comball") {
	$comball = 1;
    }
    elsif ($arg eq "nocomball") {
	$comball = 0;
    }
    elsif ($arg =~ /(\w+).cm/) {
	$imroot = $1;
	$inim = "$imroot.cm";
	$inimreg = "$imroot.regrid";
#	$im2d = "$imroot_2d.fits";
	push(@allim,$inim);
	push(@allimreg,$inimreg);
	push(@allroot,$imroot);
#	push(@im2ds,$im2d);
	$imn++;
    }
}

$allims = join(" ",@allim);
$allimc = join(",",@allim);
$allimregs = join(",",@allimreg);

print "Input images are $allims\n";

if ($nvsscat) { 
    print "\n*** Getting NVSS catalog ***\n\n";
#   # get NVSS catalog
#
## *** NB - search radius currently defaults to 35 degrees
# search radius in arcsec:
    $nrada = $nrad*3600;
# *** NB - defaulting to integrated fluxes (deconvolved values) for NVSS ***
# *** NB - minimum NVSS flux defaults to 15; note that at 25 we were detecting some sources in ATA
# (particularly multi-component sources) at this level
#
    system("INSTALLDIR/nvsscal.pl $allim[0] fmin=$fmin rad=$nrada usepk=0");
    unlink("NVSS.txt");
    rename("$allim[0].nvss.txt","NVSS.txt");
    die "NVSS catalog creation failed" if (-z "NVSS.txt");
}

if ($gcat) {
    print "\n*** Generating catalogs from ATA data ***\n\n";
#   # run Source Locator and Outburst Watcher perl script (runs sfind, determines mosaic gains, preserves sources in good regions of the image)
    system("INSTALLDIR/slowcat.pl $allims");
}

if ($mkfits) {
    foreach $imroot (@allroot) {
      system ("fits in=$imroot.cm out=$imroot.fits op=xyout");
      unlink("$imroot_2d.fits");
# *** NEED A WAY TO MAKE 2D FITS FILES - REGRID WOULD WORK WITH AXES OPTIONS
      system("cp $imroot.fits $imroot_2d.fits");
    }
}

if ($mkcats) {
    system("rm -rf sfind.*.nvss");
    print "\n*** Matching catalogs to NVSS ***\n\n";
    foreach $imroot (@allroot) {
	print "Matching catalog for $imroot\n";
      if ($nvssmatch) {
#	# instead of looking for NVSS matches to ATA sources, look for ATA matches to NVSS sources
#        # We should treat NVSS as just another epoch
# *** CURRENTLY NOT IMPLEMENTED
       } else {
	   system("INSTALLDIR/matchcolnl.pl sfind.$imroot.slow 1 2 NVSS.slow 1 2 $matchrad");
	   rename("match.cat","sfind.$imroot.matn");
	 if ($allmatch) {
	     system("cat sfind.$imroot.matn | grep -v '\\\*' > sfind.$imroot.nvss");              
         } else {
          if ($negmatch) {
	      system("awk '{if (\$15 == 0) print}' sfind.$imroot.matn | grep -v '\\\*' > sfind.$imroot.nvss");              
	   } else {
	       system("awk '{if (\$15 > 0) print}' sfind.$imroot.matn | grep -v '\\\*' > sfind.$imroot.nvss");
	   }
         }
       }
    }
}

if ($seti) {
    print "\n*** Matching catalogs across epochs ***\n\n";
#   # call Steve's Excellent Transient Identifier (matches sfind catalogs) - now using a circular match
    system("INSTALLDIR/setierrcirc.pl mrad=$matchrad usepk=$usepk");
    rename("seti.txt","setialln.txt");
    system("sort -k2 -nr setialln.txt > seti.txt");

   # uncomment the following line to throw out things which are absent at some epoch; this is optional
#   system("cat setialln.txt | sort -k2 -nr | grep -v '\-99' > seti.txt");
}

if ($atasort) {
    print "\n*** Sorting catalogs based on maximum ATA flux in any epoch ***\n\n";
## sort on max ATA flux in any epoch
    rename("seti.txt","setiuns.txt");
    system("INSTALLDIR/setisortmax.pl");
    rename("setisort.txt","seti.txt");
}

if ($coadd) {
    print "\n*** Creating the coadd image ***\n\n";
    unlink("coadd.fits");
    system("rm -rf coadd.cm");
    system("rm -rf coadd_tmp????.fits");
if ($swarp) {
## SWARP method
#   # copy the SWarp config file
    system("cp INSTALLDIR/default.swarp .");
    system("swarp $allims");
    system("fits in=coadd.fits out=coadd.cm op=xyin");
} else {
    system("linmos in=$allimregs out=coadd.cm options=taper");
}
}

$cwd = `pwd`;
chomp($cwd);
$dir = "$cwd/nvss";

if ($nvsspost) {
    print "\n*** Downloading NVSS postage stamp images ***\n\n";
#   # this is where we'll put the NVSS postage stamps
    system("rm -rf nvss");
    mkdir nvss, 0744;
   # generate the NVSS postage stamps
    system("INSTALLDIR/setinvss.pl seti.txt");
}

#   # here's the list of NVSS postage stamps
@nvsscutf = <$dir/J*.fits>;

if ($nvssmir) {
    print "\n*** Making MIRIAD versions of NVSS postage stamp images ***\n\n";
    foreach $nvss (@nvsscutf) {
	print "$nvss\n";
	($nvsscm = $nvss) =~ s/.fits/.cm/;
	system("rm -rf $nvsscm");
	system("fits in=$nvss out=$nvsscm op=xyin");
    }    
}

@nvsscut = <$dir/J*.cm>;

if ($eppost) {
    print "\n*** Making postage stamps for each epoch and for coadd image ***\n\n";
    system("rm -rf coadd");
    print "Creating postage stamps\n";
    mkdir coadd, 0744;
    $n = 1;
    # create epoch directories
    foreach $imroot (@allroot) {
	$epn = "ATA$n";
	system("rm -rf $epn");
	mkdir $epn, 0744;
	$n+=1;
    }

    # loop through all NVSS postage stamps
    foreach $nvssc (@nvsscut) {
	# define output filenames for other postage stamps
	print "\nMaking scaled coadd, NVSS, and ATA postage stamps using $nvssc\n";
	$nvsscs = $nvssc;
	$coaddc = $nvssc;
	$nvsscs =~ s+nvss/J+nvss/scl_J+;
	$coaddc =~ s+nvss/J+coadd/J+;
	$coaddc =~ s+_NVSS+_coadd+;
	$coaddcs = $coaddc;
	$coaddcs =~ s+/coadd/+/coadd/scl_+;

	# create a postage stamp from the coadd
	print "Creating coadd postage stamp $coaddc\n";
# need to create a soft link here because otherwise MIRIAD might choke on long filenames
	system("rm -f coaddpostslow");
	system("rm -f nvsspostslow");
	system("rm -f mathinslow");
	system("ln -s $nvssc nvsspostslow");
        system("regrid in=coadd.cm tin=nvsspostslow out=coaddpostslow axes=1,2");
	rename("coaddpostslow","$coaddc");
	system("ln -s $coaddc mathinslow");

# scale coadd image - could use histo here but stats will suffice for images with median ~ 0
	print "Creating scaled coadd image $coaddcs\n";
	system("rm -rf $coaddcs");
# need to iterate the statistics with sigma clipping here - too dominated by sources right now
	$statout = `imstat in=$coaddc | tail -1`;
	@stats = split(/\s+/,$statout);
#	$mean = $stats[2];
	$rms = $stats[3];
	    if ($rms > 0) {
		$loin = $rms;
		$hiin = 8.0 * $rms;
		$scl = 1000.0/($hiin + $loin);

		system("maths exp=\"(<mathinslow>+$loin)*$scl\" out=mathoutslow");
		system("mv mathoutslow $coaddcs; rm -f mathinslow");
	    }
	    else {
		system("cp -r $coaddc $coaddcs");
	    }

# scale NVSS image
	print "Creating scaled NVSS image $nvsscs\n";
	system("rm -rf $nvsscs");
	$statout = `imstat in=$nvssc | tail -1`;
	@stats = split(/\s+/,$statout);
#	$mean = $stats[2];
	$rms = $stats[3];
	    if ($rms > 0) {
		$loin = $rms;
		$hiin = 8.0 * $rms;
		$scl = 1000.0/($hiin + $loin);
#		system("maths exp=\"(<$nvssc>+$loin)*$scl\" out=$nvsscs");
		system("rm -f mathinslow");
		system("ln -s $nvssc mathinslow");
		system("maths exp=\"(<mathinslow>+$loin)*$scl\" out=mathoutslow");
		system("mv mathoutslow $nvsscs; rm -f mathinslow");
	    }
	    else {
		system("cp -r $nvssc $nvsscs");
	    }

# *** NOW MAKE FITS FILE?
	
	$n=1;
	# loop through each epoch
	foreach $imroot (@allroot) {
	    $epn = "ATA$n";
	    print "$epn\n";
	    $atac = $nvssc;
	    $atac =~ s+nvss/J+$epn/J+;
	    $atac =~ s+_NVSS+_$n+;
	    $atacs = $atac;
	    $atacs =~ s+$epn/J+$epn/scl_J+;
	    # create the postage stamp
	    print "Creating $epn postage stamp $atac\n";
	    system("rm -rf imrootcmslow");
	    system("ln -s $imroot.cm imrootcmslow");
	    system("regrid in=imrootcmslow tin=nvsspostslow out=epochpostslow axes=1,2");
	    rename("epochpostslow","$atac");
# scale the image
	    print "Creating scaled $epn image $atacs\n";
	    system("rm -rf $atacs");
	    $statout = `imstat in=$atac | tail -1`;
	    @stats = split(/\s+/,$statout);
#	$mean = $stats[2];
	    $rms = $stats[3];
	    if ($rms > 0) {
		$loin = $rms;
		$hiin = 8.0 * $rms;
		$scl = 1000.0/($hiin + $loin);
#		system("maths exp=\"(<$atac>+$loin)*$scl\" out=$atacs");
		system("ln -s $atac mathinslow");
		system("maths exp=\"(<mathinslow>+$loin)*$scl\" out=mathoutslow");
		system("mv mathoutslow $atacs; rm -f mathinslow");
	    }
	    else {
		system("cp -r $atac $atacs");
	    }
# *** NOW MAKE FITS FILE?
	    $n+=1;
	}
    }
}

## create the output J2000 IDs
    system("cat seti.txt | sed s/+/' '/g > tmp.txt ; INSTALLDIR/addjid.pl tmp.txt 1 2 tmp2.txt ; cat tmp2.txt | sed s/+/p/g > setijid.txt");

if($rejbl) {
# only keep sources with a fraction $goodcut or more of good pixels in every epoch  
    $goodcut = 0.9;
    unlink("setijidi.txt");
    if (!-e "setijid.orig") {
	system("cp setijid.txt setijid.orig");
    }
    rename("setijid.txt","setijidi.txt");
    
    open(SETIJ,"setijidi.txt");
    @setij = <SETIJ>;
    close(SETIJ);
    
    open(SETIO,">setijid.txt");
    
    foreach $seti (@setij) {
# loop through sources
# assume this epoch is good unless we discover otherwise
	$blgood = 1;
	$n = 1;
	foreach $imroot (@allroot) {
# loop through epochs
	    $epn = "ATA$n";
	    @setis = split(/\s+/,$seti);
	    $imname = $setis[0];
	    print ("immask in=$epn/scl_${imname}_$n.cm\n");
	    $imm = `immask in=$epn/scl_${imname}_$n.cm | tail -1`;
	    @ims = split(/\s+/,$imm);
	    $good = $ims[1];
	    $total = $ims[4];
	    $goodper = $good / $total;
#	    print "$good $total $goodper";
	    if ($goodper < $goodcut) {
		$blgood = 0;
	    }
	    $n+=1;
	}
        if ($blgood) {
	    print SETIO "$seti";
	}
    }
    close(SETIO);   
}

if ($fluxgr) {
    print "\n*** Making graphs of flux vs. epoch ***\n\n";
    system("rm -rf seti");
    mkdir seti, 0744;
   # create the panels with the graphs of flux vs. epoch
   # now works for arbitrary number of epochs
    system("sm < INSTALLDIR/setimulterindim.sm");
}

if ($postps) {
    print "\n*** Assembling postage stamp images into postscript files ***\n\n";
    system("rm -rf ps");
    mkdir ps, 0744;
    unlink("atanvssall.wip");
   # create the WIP master script
    system("INSTALLDIR/atanvssseticm.pl");

#   # run the WIP master script (using the NULL device as default)
    system("wip -d /NULL atanvssall.wip");
}

if ($comball) {
    print "\n*** Assembling postage stamps and flux graphs into PDF file ***\n\n";
#    system("INSTALLDIR/setipdf.pl; open seticomb.pdf");
    system("INSTALLDIR/setipdf.pl");
}
