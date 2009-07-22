#!/usr/bin/perl
#
# Generates WIP script to plot up ATA / NVSS postage stamps
#
# S. Croft 2008/08/26
#
# See also atanvss.pl
# Usage: atanvss.pl 

open(SETIJID,"setijid.txt");
@setijid=<SETIJID>;
close(SETIJID);

# output script
$outf = "atanvssall.wip";
open(OUT,">$outf");
print OUT "macro INSTALLDIR/doheadseti.wip\n";

foreach $seti (@setijid) {
    @ins = split(/\s+/,$seti);
    
    $imroot = $ins[0];
    $ra = ($ins[1] * 240.0);
    $dec = ($ins[2] * 3600.0);
        
# number of epochs
    $nep = (@ins - 4) / 2;
    
# also do coadd and NVSS
    $nim = $nep + 2;

# start on the first block of postage stamps
    $psblock = 1;
    
# number of postage stamps per block
    $num_per_block = 6; 
    
# current postage stamp number
    $psnum = 1;
    
    $line2 = "expand 0.5\nticksize 60 0 600 0\nviewport 0.3 0.9 0.3 0.9\n";
    $line1 = "device \"ps/$imroot"."_p$psblock.ps\"/vcps\n";
    
    print OUT $line1;
    print OUT $line2;

    for ($imn = 1; $imn <= $nim; $imn++) {
	$argn = 2 + (($imn - 1) * 2);
	$pfx = "ATA$imn";
	$sfx = "_$imn.cm";
        $tits = $pfx;
	$flux = $ins[$argn+2];
 # box color
	$bcol = 1;
    	if ($imn == $nim - 1) {
	    $pfx = "coadd";
	    $sfx = "_coadd.cm";
	    $tits = "ATA Coadd";
	    $flux = "";
	    $bcol = 4;
	}
	if ($imn == $nim) {
	    $pfx = "nvss";
	    $sfx = "_NVSS.cm";
	    $tits = "NVSS";
	    $flux = $ins[3];
	    $bcol = 2;
	}
	$imname = "$pfx/scl_$imroot$sfx";
	print "$imname $psblock:$psnum\n";
	print OUT "image $imname\npanel -$num_per_block 1 $psnum\nwinadj 0 nx 0 ny\nheader rd\ndoheader\npalette 0\nhalftone 0 1000\n";
	if ($psnum == 1) {
	    print OUT "color $bcol\nbox bcnsthz bcnstvdyz\ncolor 1\nxlabel Right Ascension (J2000)\nmtext L 6.0 0.5 0.5 Declination (J2000)\n";
#	    print OUT "box bcnsthz bcnstvdyz\nxlabel Right Ascension (J2000)\nmtext L 6.0 0.5 0.5 Declination (J2000)\n";
	}
	else {
	    print OUT "color $bcol\nbox bcnsthzf bcstvdyz\ncolor 1\n";
#	    print OUT "box bcnsthzf bcstvdyz\n";
	}
	print OUT "mtext T 1.0 0.0 0.0 $tits f = $flux\n";
	if ($imn == 1) {
#	    print OUT "mtext T 2.3 1.0 1.0 $imroot\n";
	    print OUT "mtext T 2.3 0.0 0.0 $imroot\n";
	}
	print OUT "symbol 27\ndot $ra $dec\n";
	$psnum++;
	if ($psnum > $num_per_block && $imn < $nim) { 
	    $psnum = 1;
	    $psblock++;
	    
	    print OUT "itf 0\ndevice /null\n";
	    $line1 = "device \"ps/$imroot"."_p$psblock.ps\"/vcps\n";
	    print OUT $line1;
	    print OUT $line2;
	}
    }
    if ($psnum <= $num_per_block) {
	# draw a box in the background color to force the output postscript to be as wide as it would be if there were $num_per_block panels in this file
	print OUT "panel -$num_per_block 1 $num_per_block\nwinadj 0 nx 0 ny\ncolor 0\nbox bc c\ncolor 1\n";
    }
    print OUT "itf 0\ndevice /null\n";
}
print OUT "exit\n";
close(OUT);
