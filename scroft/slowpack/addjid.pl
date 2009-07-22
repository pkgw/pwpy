#!/usr/bin/perl
# changes malformed JIDs
# Usage: fixjid.pl infile racol decol outfile
# Columns start at 1

$infile = $ARGV[0];
$racol = $ARGV[1]-1;
$decol = $ARGV[2]-1;
$outfile = $ARGV[3];

open (INF, $infile);
@lines = <INF>;
close (INF);

open (OUT, ">$outfile");

foreach $item (@lines)
{
    chop($item);
# strip leading spaces
    $item =~ s/^\s+//;
#    print "$item\n";
    @fields = split(/\s+/, $item);
    $rap = $fields[$racol];
    $dep = $fields[$decol];
#    print "$rap $dep\n";
    tohms($rap);
    todms($dep);
    $njid = sprintf("J%02d%02d%02d%s%02u%02d%02d",$rahr,$ramn,$rasc,$sign,$dedg,$demn,$desc);
    print OUT "$njid $item\n";
}

close(OUT);

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
	$sign = "-";
    }
    else {
	$sign = "+";
    }
    $dedg = abs(int($dec));
    my $rem = abs($dec) - $dedg;
    $demn = int ($rem * 60.0);
    my $rem = $rem * 60.0 - $demn;
    $desc = $rem * 60.0;
    return 0;
}
