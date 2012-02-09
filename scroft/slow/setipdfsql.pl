#!/usr/bin/perl

# assemble PDF file with transient lightcurves and postage stamps

use DBI;

$dbfile = "slow.db";
$dbh = DBI->connect("dbi:SQLite:dbname=$dbfile") or die "Couldn't connect to database: " . DBI->errstr;

$thresh = 232;
$nosort = 0;
$sortav = 0;
$sortmax = 0;
$sortmaxata = 1;
$sortsum = 0;

foreach $arg (@ARGV) {
    if ($arg eq "nosort") {
        $nosort = 1;
    }
    if ($arg eq "sortav") {
        $sortav = 1;
    }
    if ($arg eq "sortmax") {
        $sortmax = 1;
    }
    if ($arg eq "sortmaxata") {
        $sortmaxata = 1;
    }
    if ($arg eq "sortsum") {
        $sortsum = 1;
    }
    if ($arg =~ /epochs=(\d+)/) {
	$nepo = $1;
	$epma = 1;
    }
    if ($arg =~ /thresh=(\S+)/) {
        $thresh = $1;
        $epma = 1;
    }
    if ($arg =~ /mjid=(\S+)/) {
	$mj = $1;
	$single = 1;
    }
    if ($arg eq "extreme") {
	$extreme = 1;
    }
}

$gd = "HAVING avg(good) == 1";

# list of all unique sources
if ($nosort) {
    $mjids = $dbh->prepare("SELECT DISTINCT mjid FROM master WHERE mjid <> 'J'") or die "Couldn't prepare statement: " . $dbh->errstr;
}
# list of all unique sources, ordered by mean flux over all epochs
if ($sortav) {
    $mjids = $dbh->prepare("SELECT mjid FROM master WHERE mjid <> 'J' GROUP BY mjid $gd ORDER BY AVG(fi)") or die "Couldn't prepare statement: " . $dbh->errstr;
}
# list of all unique sources, ordered by brightest flux at any epoch (including NVSS)
if ($sortmax) {
    $mjids = $dbh->prepare("SELECT mjid FROM master WHERE mjid <> 'J' GROUP BY mjid $gd ORDER BY MAX(fi)") or die "Couldn't prepare statement: " . $dbh->errstr;
}
# list of all unique sources, ordered by brightest flux at any ATA epoch
if ($sortmaxata) {
    $mjids = $dbh->prepare("SELECT mjid FROM master WHERE (mjid <> 'J' and epname LIKE 'ATA%') GROUP BY mjid $gd ORDER BY MAX(fi)") or die "Couldn't prepare statement: " . $dbh->errstr;
}
# list of all unique sources, ordered by total flux over all epochs
if ($sortsum) {
    $mjids = $dbh->prepare("SELECT mjid FROM master WHERE mjid <> 'J' GROUP BY mjid $gd ORDER BY SUM(fi)") or die "Couldn't prepare statement: " . $dbh->errstr;
}
# all transients with $nepo ATA epochs, peaking at > 232 mJy
if ($epma) {
    $mjids = $dbh->prepare("select distinct mjid from master where (mjid NOT IN (select distinct mjid from master where epname like 'NVSS%') AND mjid IN (select mjid from master group by mjid having avg(good) == 1)) group by mjid having (count (distinct epname) == $nepo and max(fi)>$thresh)") or die "Couldn't prepare statement: " . $dbh->errstr;
}
# sources with more than 50% variability
if ($extreme) {
#   ./extreme.csh 5
    $mjids = $dbh->prepare("select mjid from master where (extreme == 1 and epname like 'ATA%' and epname not like 'ATA_Coadd') group by mjid")  or die "Couldn't prepare statement: " . $dbh->errstr;
}

#$mjids = $dbh->prepare("SELECT mjid FROM master WHERE mjid <> 'J' GROUP BY mjid HAVING avg(good) == 1") or die "Couldn't prepare statement: " . $dbh->errstr;
#$mjids = $dbh->prepare("SELECT mjid FROM master WHERE mjid <> 'J' GROUP BY mjid") or die "Couldn't prepare statement: " . $dbh->errstr;
# for test                                                                     
if ($single) {
$mjids = $dbh->prepare("SELECT mjid FROM master WHERE mjid == '$mj' GROUP BY mjid") or die "Couldn't prepare statement: " . $dbh->errstr;
}



$mjids->execute();


#$list1 = "setijid.txt";

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

while (@ins = $mjids->fetchrow_array) {
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


