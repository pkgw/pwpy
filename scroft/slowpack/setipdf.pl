#!/usr/bin/perl

# assemble PDF file with transient lightcurves and postage stamps

$list1 = "setijid.txt";

# number of plots per page
$ppp = 9;

# if maxn = 1 then $ppp is considered a maximum number of plots, not an absolute number
# if so, objects will not break over a page
$maxn = 1;

$ouf = "twopp.tex";
$oudv = "twopp.dvi";
$oud = "twopp";
$oups = "twopp.ps";
$oupdf = "twopp.pdf";
$oupdff = "seticomb.pdf";
$ous = 'twopp.*';

unlink($oupdf);
unlink($ous);

open (ONE,$list1);
@one = <ONE>;
close(ONE);

open (OUF,">$ouf");

print OUF '\documentclass{article}'."\n".'\usepackage{graphicx}'."\n";
# Comment next line out if there are problems
print OUF '\usepackage{anysize}'."\n".'\marginsize{1.3in}{1.3in}{0.25in}{1in}'."\n";
print OUF '\begin{document}'."\n";
print OUF '\begin{figure}[p]'."\n".'\centering'."\n";

$n = 0;
$m = 1;

# this will be the number of lines of postage stamps per object
$nperim = 0;

foreach $line (@one) {
    @ins = split(/\s+/,$line);
    $im1 = $ins[0];
    if ($nperim == 0 && $maxn == 1) {
	$nperim = `ls -1 ps/$im1* | wc -l`;
        $nperim =~ s/\s+//g;
        $ppp = int($ppp / $nperim) * $nperim;
#        print "$nperim $ppp\n";
	}
    print "Incorporating $im1\n";
    print OUF '\includegraphics[trim= 3mm 10mm 138mm 146mm,clip=true,width=0.23\linewidth]{';
    $capt = $capti[$n];
    $n++;
    print OUF "seti/$im1.ps}%\n";
    $im2num = 1;
    $im2 = "ps/$im1"."_p$im2num.ps";
    while (-e $im2) { 
        print "Incorporating $im2\n";
	if ($im2num > 1) {
	    print OUF '\hspace*{0.23\linewidth}%'."\n";
	}
	print OUF '\includegraphics[width=0.77\linewidth]{'."$im2".'}'."\n";
        $im2num++;
        $im2 = "ps/$im1"."_p$im2num.ps";
	if ($m == $ppp) {
	    print OUF '\end{figure}\clearpage'."\n\n".'\begin{figure}[p]'."\n";
	    $m = 0;
	}
        $m++;
    }
}

print OUF '\end{figure}\end{document}'."\n";


close(OUF);

print "*** If the script breaks here, please edit setipdf.pl to put in the correct path to your LaTeX distribution ***\n";
# OS X doesn't have a proper LaTeX distro
if (-e "/usr/texbin/simpdftex") {
    system ("/usr/texbin/simpdftex latex --maxpfb $ouf");
    rename($oupdf,$oupdff);
}
# hope that latex, dvips, and ps2pdf are available and in the path
else {
    system ("latex $ouf");
    system ("dvips $oud");
    system ("ps2pdf $oups $oupdff");
}

unlink($oudv);
unlink ($ous);

print "Output file is $oupdff\n";


