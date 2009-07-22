#!/usr/bin/perl
#
# Check for correspondence of radio / optical positions
# S. Croft 29/10/01
#
# Usage matchcolnl.pl filea cola1 cola2 fileb colb1 colb2 cutoff 
# NB The first column is column 1
# Keeps just the nearest match
# Outputs whole_line_a whole_line_b offset
# Outputs all filea whether matched or not
#

@ar = @ARGV;
$radf = $ar[0];
$cola1 = $ar[1] - 1;
$cola2 = $ar[2] - 1;
$optf = $ar[3];
$colb1 = $ar[4] - 1;
$colb2 = $ar[5] - 1;
$arcs = $ar[6];

open(RAD, "$radf");
@radl = <RAD>;
close(RAD);
print "Read $radf\n";

open(OPT, "$optf");
@optl = <OPT>;
close(OPT);
print "Read $optf\n";

# counters
$n = 0;
$m = 0;
$p = 0;

# cutoff = 10 arcsec
#$arcs = 10.0;
$diffcut = ($arcs / 3600.0)**2.0;

foreach $radpos (@radl)
{
    if ($radpos =~ "^#") {
    } else {
    chop ($radpos);
    push(@rposl, $radpos);
    push(@oposo, "NID");
    
# strip leading spaces
    $radpos =~ s/^\s+//;
# split into fields
    @rads = split(/\s+/, $radpos);
    
    $rraf = $rads[$cola1];
    $rdef = $rads[$cola2];
    
    $rra = tora($rraf); # convert to decimal
    $rde = todec($rdef); # as above

# now store the positions in arrays
    push(@rrias, $rra);
    push(@rdecs, $rde);
    push(@rmatc, "99999.99");
    
# this array stores the number of matches
    push(@requ, "0");
   }
}

foreach $optpos (@optl)
{
    if ($optpos =~ "^#") {
    } else {
    chop ($optpos);
    push(@oposl, $optpos);
# strip leading spaces
    $optpos =~ s/^\s+//;
# split into fields
    @opts = split(/\s+/, $optpos);
    
    $oraf = $opts[$colb1];
    $odef = $opts[$colb2];
    
    $ora = tora($oraf); # convert to decimal
    $ode = todec($odef); # as above
    
# now store the positions in arrays
    push(@orias, $ora);
    push(@odecs, $ode);

# this array stores the fields which are equivalent
    push(@oequ, "0");
}
}

$m = 0;

open(MATCH,">match.cat");

# now check for matches
foreach $item (@requ)
{
    $p = 0;
    $diffcrit = $diffcut;
    foreach $comp (@oequ)
    {

# compute the square of the difference in degrees between the two positions
# to be tested; $diffcut is the square of the cutoff value for which we
# consider that we have matched fields

	$rad = $rrias[$m] - $orias[$p];
	$ded = $rdecs[$m] - $odecs[$p];
	$desav = ($rdecs[$m] + $odecs[$p])/2.0;

	$diffsq = ((($rad)*cos($desav/57.29578))**2.0 + ($ded)**2.0);

# the two positions fall within the cutoff value
# if they satisfy the following condition
	if ($diffsq < $diffcrit)
	{
	    $diffcrit = $diffsq;
	    $diffa = 3600.0*sqrt($diffsq);
	    $rmatc[$m] = sprintf("%5.2f",$diffa);
	    $oposo[$m] = $oposl[$p];
#	    print "$rrias[$m] $rdecs[$m] $orias[$p] $odecs[$p] $diffa\n";
#	    print MATCH "$rrias[$m] $rdecs[$m] $orias[$p] $odecs[$p] $diffa\n";
#	    $requ[$m] +=1;
	}
	$p++;
    }
# If there's no match, the "closest" match is meaningless
# so let's sub all the numbers with zeroes here
    if ($rmatc[$m] > 99999) {
	$oposo[$m] = $oposl[1];
	$oposo[$m] =~ s/\d/0/g;
    }
      $m++;
}

$q = 0;

foreach $item (@requ)
{
    print "$rposl[$q] $oposo[$q] $rmatc[$q]\n";
    print MATCH "$rposl[$q] $oposo[$q] $rmatc[$q]\n";
    $q++;
}

close(MATCH);

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







