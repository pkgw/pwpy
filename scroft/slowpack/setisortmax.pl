#!/usr/bin/perl
#
# Sort setialln.txt (see slow.cl) in descending order of brightest ATA
# detection
#
# S. Croft 2008/11/25
#

open(SETI,"setiuns.txt");
@setii=<SETI>;
close(SETI);

# output script
$outf = "setisort.txt";
open(OUT,">$outf");

foreach $seti (@setii) {
#    chomp($seti);
    @ins = split(/\s+/,$seti);
    
    $ra = ($ins[0] * 240.0);
    $dec = ($ins[1] * 3600.0);
    
# number of epochs
    $nep = (@ins - 2) / 2;
    
# maximum flux at this epoch
    $maxf = 0;
    
    for ($ep = 1; $ep <= $nep; $ep++) {
	$col = 2*($ep);
	$flux = $ins[$col];
	if ($flux > $maxf) {
	    $maxf = $flux;
	}
    }
    $setihash{$maxf} = $seti;
}

# sort the hash in descending order of max flux
foreach $hashkey (sort {$b<=>$a} keys %setihash) {
#    print "$hashkey --- ";
    print OUT "$setihash{$hashkey}";
}

print "Output file is $outf\n";
close(OUT);
