#!/usr/bin/perl
#
# Takes output from SETI, grabs postage stamps from mosaic
# Queries NVSS (using Skyview) for matching postage stamps
# 
# User can then plot postage stamps using WIP script setinvss.wip
#
# S. Croft 2008/07/25
#
# Skyview Java file
$skyview = "java -jar INSTALLDIR/skyview.jar";


# Usage setinvss.pl catalog.txt

$catalog = $ARGV[0];
#$mosaic = $ARGV[1];

open(CAT,$catalog);
@cat = <CAT>;
close(CAT);

foreach $line (@cat) {
            @fields = split(/\s+/, $line);
# positions look like 216.053004+42.236194
	    $posi = $fields[0];
	    @pos = split(/\+/,$posi);
	    $rap = $pos[0];
	    $dep = $pos[1];
	    tohms($rap);
	    todms($dep);
	    $jid = sprintf("J%02d%02d%02d%s%02u%02d%02d",$rahr,$ramn,$rasc,$sign,$dedg,$demn,$desc);
	    $outfile = "nvss/$jid"."_NVSS.fits";
	    unlink($outfile);
	    print "Getting $outfile (RA = $rap Dec = $dep\n";
#	    print "skyview $ra $dec\n";
#	    print "skyview survey='nvss' position='$posi' size=1.0 output=$outfile\n";
	    system("$skyview survey='nvss' position='$posi' size=1.0 output=$outfile\n");
}

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
    
sub todms # converts decimal to dec ($dedg, $demn, $desc)
{
    my $dec = $_[0];
    if ($dec < 0) {
        $sign = "m";
    }
    else {
        $sign = "p";
    }
    $dedg = abs(int($dec));
    my $rem = abs($dec) - $dedg;
    $demn = int ($rem * 60.0);
    my $rem = $rem * 60.0 - $demn;
    $desc = $rem * 60.0;
    return 0;
}

