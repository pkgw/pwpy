#!/usr/bin/perl
#
# Steve's Excellent Transient Identifier
# S. Croft 2010/05/11
#
# Usage seti.pl 
# Looks for sfind*.slow in the current working directory

use DBI;
use Math::Trig qw(great_circle_distance pi);

$onerad = 180.0/pi;
$n = 90.0/$onerad;

$dbfile = "slow.db";
$dbh = DBI->connect("dbi:SQLite:dbname=$dbfile") or die "Couldn't connect to database: " . DBI->errstr;

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
$matchrad = 75.0;

foreach $arg (@ARGV) {
    if ($arg =~/mrad=(\S+)/) {
	$matchrad = $1;
    }
    elsif ($arg =~ /(\S+).cm/) {
        $imroot = $1;
#        $inim = "$imroot.cm";
#        $inslow = "sfind.$imroot.slow";
	push(@imroots,$imroot);
#	push(@inims,$inim);
#        push(@infiles,$inslow);
    }

}

$srad = $matchrad / 3600.0;
print "Match radius is $matchrad\n";

# look for sfind logs
#@infiles = `ls sfind.*.nvss`;
#@infiles = `ls sfind.coadd.slow sfind.mos*.slow`;
@infiles2 = `ls NVSS.slow`;

# output file (also prints to STDOUT)
#open (OUF,">seti.txt");

$epoch = 0;

# create the catalog
$dbh->do( "CREATE TABLE master (id, mjid, jid, epname, ra float, decl float, fp float, fpe float, fi float, bmaj float, bmin float, pa float, rb float, rf float, nf float, epjd float, good int, freq int, finm )" ) or die "Couldn't create table: " . $dbh->errstr;
# add a source to the catalog
$addsrc = $dbh->prepare( "INSERT INTO master VALUES ( ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,? )" ) or die "Couldn't prepare statement: " . $dbh->errstr;
# set the master JID if it's not already set
$updsrc = $dbh->prepare( "UPDATE master SET mjid=? WHERE (mjid=='J' and id==?)" ) or die "Couldn't prepare statement: " . $dbh->errstr;

$id = 1;

#print "Reading ATA catalogs into database ...";

# Read in files and populate the SQLite3 database
foreach $inroot (@imroots)
{
    chomp($inroot);
    $infile = "sfind.$inroot.slow";
    $inim = "$inroot.cm";
    $epjd = `gethd in=$inim/obstime`;
    $freq = `gethd in=$inim/restfreq`;
    chomp($epjd);
	chomp($freq);
	$freq *= 1000;
    $epname = "ATA$epoch";
    if ($epoch == 0) {
	$epname = "ATA_Coadd";
    }
    open(INF, "$infile");
    @inl = <INF>;
    close(INF);
    print "Read ".scalar(@inl)." lines from $infile\nPopulating database ...\n";
    
# go through SFIND file line by line, and enter the details into the database
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
	    	    
	    @ras = split(/:/, $ra);
	    @des = split(/:/, $de);
	    $rahr = $ras[0];
	    $ramn = $ras[1];
	    $rasc = $ras[2];
	    $dedg = $des[0];
	    $demn = $des[1];
	    $desc = $des[2];
	    tora($ra); # convert RA to decimal degrees
	    todec($de); # convert dec to decimal degrees
	    
#	    $rade = sprintf("%10.6f%+10.6f %9.2f",$ra,$de,$nf);
	    
	    $jid = sprintf( "J%02d%02d%02dp%02d%02d%02d",$rahr,$ramn,$rasc,$dedg,$demn,$desc);
	    if ($fp > 0 && $fi > 0) {
		$addsrc->execute($id, "J", $jid, $epname, $ra, $de, $fp, $fpe, $fi, $bmaj, $bmin, $pa, $rb, $rf, $nf, $epjd, 1, $freq, $inim );
	    }
	    $id++;
	}
    }
    print "Done\n";
    $epoch++;
} 

$rac = 0;
$dec = 1;
$fic = 2;
$rbc = 3;

# now do NVSS (loop isn't really necessary here)
foreach $infile (@infiles2)
{
    chomp($infile);
    $epname = "NVSS";
    open(INF, "$infile");
    @inl = <INF>;
    close(INF);
    print "Read ".scalar(@inl)." lines from $infile\nPopulating database ...\n";
    
# go through SFIND file line by line, and enter the details into the database
    foreach $line (@inl)
    {
	if ($line =~ "^#") {
	}
	else {
# split into fields
	    @fields = split(/\s+/, $line);
	    $ra = $fields[$rac];
	    $de = $fields[$dec];
	    $fi = $fields[$fic];
	    $rb = $fields[$rbc];
#	    $rahx = $ra;
#	    $dehx = $de;
	    
#	    $rahr = $ras[0];
#	    $ramn = $ras[1];
#	    $rasc = $ras[2];
#	    $dedg = $des[0];
#	    $demn = $des[1];
#	    $desc = $des[2];
	    
	    $rade = sprintf("%10.6f%+10.6f",$ra,$de);
	    $jid = $rade;
#	    $jid = sprintf( "J%02d%02d%02dp%02d%02d%02d",$rahr,$ramn,$rasc,$dedg,$demn,$desc);
	    $addsrc->execute($id, "J", $jid, $epname, $ra, $de, "0", "0", $fi, "0", "0", "0", $rb, "0", "0", 0, 1, 1430, "NVSS");
	    $id++;
	}
    }
    $epoch++;
} 

print "Done\n";

$nep = $epoch;

# We're going to loop through every single source at each epoch and put it into the master table

print "Preparing database queries ...\n";

#$dbh->do( "CREATE TABLE master (jid, epname, ra float, decl float, fp float, fpe float, fi float, bmaj float, bmin float, pa float, rb float, rf float, nf float)" ) or die "Couldn't create table: " . $dbh->errstr;

# list of all the sources with "ATA*" as the epoch name
$retnext = $dbh->prepare("SELECT ra, decl, epname, jid, id FROM master WHERE (epname LIKE 'ATA%')") or die "Couldn't prepare statement: " . $dbh->errstr;
# list of all sources (not just ATA) within some search box
$retrad = $dbh->prepare("SELECT ra, decl, epname, id FROM master WHERE (ra > ? and ra < ? and decl > ? and decl < ?)") or die "Couldn't prepare statement: " . $dbh->errstr;


#for ($epoch = 0; $epoch < $nep; $epoch++) {
#    $epname = "ATA$epoch";
#    if ($epoch == 0) {
#	$epname = "ATA_Coadd";
#    }
#    print "$epname\n";

$retnext->execute() or die $dbh->errstr;

$nid = $dbh->selectrow_array("SELECT COUNT (DISTINCT id) FROM master WHERE (epname LIKE 'ATA%')") or die "Couldn't prepare statement: " . $dbh->errstr;

print "Done\n";

# go through the whole master catalog line by line
while (@data = $retnext->fetchrow_array) {
    $ra1 = $data[0];
    $de1 = $data[1];
    $epname1 = $data[2];
    $mjid = $data[3];
    $id1 = $data[4];
    $pdone = 100.0 * $id1 / $nid;
    printf ("\rMatching ... %6.3f percent done",$pdone);
#    print "$id1\n";
    $cfac = cos($de1/$onerad);
    
# first select all close-by sources from the master catalog (in some box a couple of times bigger than the match radius, just to be on the safe side)
# could make this box smaller to speed things up a bit
    $ral = $ra1 - 2*$srad/$cfac;
    $rah = $ra1 + 2*$srad/$cfac;
    $del = $de1 - 2*$srad;
    $deh = $de1 + 2*$srad;
    if ($deh > 90) {
	# easiest just to unconstrain the limits to avoid the wraparound situation, even though this takes a little longer
	$del = -90;
	$deh = 90;
    }
    if ($del < -90) {
	$del = -90;
	$deh = 90;
    }
    if ($rah > 360) {
	$ral = 0;
	$rah = 360;
    }
    if ($ral < 0) {
	$ral = 0;
	$rah = 360;
    }
    
# extract all close by sources from the master catalog
    $retrad->execute($ral,$rah,$del,$deh) or die $dbh->errstr;
    while (@data = $retrad->fetchrow_array) {
#		print $data[0] . ", " . $data[1] . "\n";
	$ra2 = $data[0];
	$de2 = $data[1];
	$epname2 = $data[2];
	$id2 = $data[3];
	$aa = $ra2/$onerad;
	$ab = $ra1/$onerad;
	$da = $de1/$onerad;
	$db = $de2/$onerad;
	
	$diffr = great_circle_distance($aa-$n,$n-$da,$ab-$n,$n-$db);
	$diffd = $onerad * $diffr;
# is the source actually within the search radius?
	if ($diffd <= $srad) {
#	    print "MATCH: ";
#	    print "$ra1 $de1 $epname1 $ra2 $de2 $epname2 $diffd\n";
	    $updsrc->execute($mjid,$id2);
	}
    }
}
print "\n";

# Catalog creation can be done using setiquery.pl
# list of all sources
#$mjids = $dbh->prepare("SELECT DISTINCT mjid FROM master") or die "Couldn't prepare statement: " . $dbh->errstr;
#$mjids->execute();

# this source at all epochs
#$matchjid = $dbh->prepare("SELECT fi, rb FROM master WHERE (mjid = ? and epname = ?)") or die "Couldn't prepare statement: " . $dbh->errstr;

#while (@data = $mjids->fetchrow_array) {
#    $mjid = $data[0];
#    for ($epoch = 0; $epoch < $nep; $epoch++) {
#	$epname = "ATA$epoch";
#	if ($epoch == 0) {
#	    $epname = "ATA_Coadd";
#	}
#    print "$epname ";
#    $matchjid->execute($mjid,$epname);
#	if (@data2 = $matchjid->fetchrow_array) {
#	    $fi = $data2[0];
#	    $rb = $data2[1];
#	    print "$fi $rb";
#	} else {
#	    print "0 0";
#	}
#	print "\n";
#    }
#}

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






