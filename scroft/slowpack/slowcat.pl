#!/usr/bin/perl
#
# ******************* SLOW ********************
# being the Source Locator and Outburst Watcher
# *********************************************
# Dedicated to Garrett Kent "Karto" Keating
# who made making maps manageable
# selfcal stupifyingly simple
# and RFI removal RAPIDer than ever before
#
# Runs sfind on a mosaic image, determines mosaic gains, discards sources
# from sfind.log in regions with gain lower than some cutoff
# Works with multiple epochs, preserving only sources that are within the 
# detection region in all epochs
#
# Steve "Quarto" Croft 7/11/08, 39000 feet over Kentucky
# Modified 7/15/08, feet firmly on the ground in Berkeley
# Modified 8/26/08 to also cull NVSS.txt (living it up at HCRO)
# Modified 6/16/09 to regrid gain images and make a single master gain image to speed things up
#
# Usage: slow.pl image1.cm image2.cm ... imagen.cm

# cutoff for the gain
$gaincut = 0.7;

# here are the sfind options
$sfopt = "xrms=5 rmsbox=100 options=auto,pbcorr,old";

$domakegain = 1; # make gain image
$dosfind = 1;  # run sfind
$docull = 1; # cull catalogs
$donvss = 1; # cull NVSS.txt too
#$domakegain = 0; # skip gain image
#$dosfind = 0; # skip sfind
#$docull = 0; # skip catalog culling
#$donvss = 0; # skip NVSS.txt culling

# command for MATHS (used to make master gain image)
# NB - it's possible this argument might get too long; this should 
# probably be reprogrammed to multiply these one at a time
$mathcmd = "maths exp='(";


# Make coverage maps and catalogs
$narg = @ARGV;
$argn = 0;
foreach $arg (@ARGV) {
    if ($arg =~ /(\w+).cm/) {
	$nloop = $argn+1;
	print "\n*** Beginning $arg (image $nloop of $narg) ***\n\n";
	$imroot[$argn] = $1;
	
	$inim[$argn] = "$imroot[$argn].cm";
	$gainim[$argn] = "$imroot[$argn].gain";
	$regridim[$argn] = "$imroot[$argn].regrid";
	$regridga[$argn] = "grg$argn";

# original output from sfind
	$sforig[$argn] = "sfind.$imroot[$argn].orig";
# final sfind catalog
	$sffin[$argn] = "sfind.$imroot[$argn].slow";
	
	if ($domakegain) {
# create gain image
	    system("rm -rf $gainim[$argn]");
	    print "Creating gain image $gainim[$argn]\n";
	    system("mossen in=$inim[$argn] gain=$gainim[$argn]");
# regrid image
	    print "Regridding image $inim[$argn]\n";
	    system("rm -rf $regridim[$argn]");
	    system("regrid in=$inim[$argn] tin=$inim[0] out=$regridim[$argn] axes=1,2");
# regrid gain image
	    print "Regridding gain image $gainim[$argn]\n";
	    system("rm -rf $regridga[$argn]");
	    system("regrid in=$gainim[$argn] tin=$gainim[0] out=$regridga[$argn] axes=1,2");
	}
	
	if ($dosfind) {
	    unlink($sforig[$argn]);
	    unlink($sffin[$argn]);
	    unlink("sfind.log");
	    print "Running sfind on $inim[$argn]\n";
	    system("sfind in=$inim[$argn] $sfopt");
	    rename("sfind.log","$sforig[$argn]");
	}
    }
    $mathcmd = "$mathcmd<$regridga[$argn]>";
    $argn++;
    if ($argn < $narg) { $mathcmd = "$mathcmd*" };
}


# make master gain image
$gainmos="allim.gain";
system("rm -rf $gainmos");
print "Making master gain image $gainmos\n";
$mathcmd = "$mathcmd)' out=$gainmos";
print "$mathcmd\n";
system($mathcmd);

if ($docull) {
# loop through catalogs one epoch at a time
    $ep = 0;
    while($ep < $argn) {
	$infile = $sforig[$ep];
	open(SF,$infile);
	@sf = <SF>;
	close(SF);
	
	$outfile = $sffin[$ep];
	open(SFO,">$outfile");
	
	print "Culling catalog $infile...";
	$fsize = `wc $infile | awk '{print \$1}'`;
	$snum = 0;
	
	foreach $sfi (@sf) {
	    $snum++;
#	printf ("\rCulling catalog %s... %d of %d",$infile,$snum,$fsize);
	    $pdone = 100.0 * $snum / $fsize;
	    printf ("\rCulling catalog %s... %6.3f percent done",$infile,$pdone);
# comments in input file get passed to output file
	    if ($sfi =~ "^#") {
		print SFO $sfi;
#	    print $sfi;
	    }
	    else {
		chomp($sfi);
		@sff = split(/\s+/, $sfi);
		$ra = $sff[0];
		$dec = $sff[1];
#	print "\n$ra $dec ";
		$ok = 1;
#		print "$gim:";
		$gain = `impos in=$gainmos coord=$ra,$dec type=hms,dms | grep GAIN | awk '{print \$7}'`;
		    chomp($gain);
#		print "$gain ";
		    if ($gain >= $gaincut) {
		    print SFO "$sfi\n";
		    }
	    }
	}
	close(SFO);
	print "\rDone. Output catalog is $outfile                    \n";
	$ep++;
    }
}

if ($donvss) {
# Now do NVSS
    $infile = "NVSS.txt";
    open(SF,$infile);
    @sf = <SF>;
    close(SF);
    
    $outfile = "NVSS.slow";
    open(SFO,">$outfile");
    
    print "Culling catalog $infile...";
    $fsize = `wc $infile | awk '{print \$1}'`;
    $snum = 0;
    
    foreach $sfi (@sf) {
	$snum++;
	$pdone = 100.0 * $snum / $fsize;
	printf ("\rCulling catalog %s... %6.3f percent done",$infile,$pdone);
# comments in input file get passed to output file
	if ($sfi =~ "^#") {
	    print SFO $sfi;
	}
	else {
	    chomp($sfi);
	    @sff = split(/\s+/, $sfi);
	    $ra = $sff[0];
	    $dec = $sff[1];
	    $ok = 1;
	    $epg = 0;
	    while($epg < $argn) {
		# check the gain at this positon at all epochs
		$gim = $gainim[$epg];
		$gain = `impos in=$gim coord=$ra,$dec type=absdeg,absdeg | grep GAIN | awk '{print \$7}'`;
		chomp($gain);
		if ($gain < $gaincut) {
# gain was below cutoff at this epoch
		    $ok = 0;
		}
		$epg++;
	    }
	    if ($ok) {
		print SFO "$sfi\n";
#		print "$sfi\n";
	    }
	}
    }
    close(SFO);
    print "\rDone. Output catalog is $outfile                    \n";
}

print "Completed\n";

