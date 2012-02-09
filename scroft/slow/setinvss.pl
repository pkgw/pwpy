#!/usr/bin/perl
#
# Takes output from SETI, grabs postage stamps from mosaic
# Queries NVSS (using Skyview) for matching postage stamps
# 
# User can then plot postage stamps using WIP script setinvss.wip
#
# S. Croft 2008/07/25
# Updated for SQL 2010 May

use DBI;

$dbfile = "slow.db";
$dbh = DBI->connect("dbi:SQLite:dbname=$dbfile") or die "Couldn't connect to database: " . DBI->errstr;

# Skyview Java file
$skyview = "java -jar /o/scroft/h/scripts/slow/skyview.jar";

# list of all sources
$mjids = $dbh->prepare("SELECT mjid,ra,decl FROM master WHERE mjid <> 'J'") or die "Couldn't prepare statement: " . $dbh->errstr;
$mjids->execute();

while (@fields = $mjids->fetchrow_array) {
    $mjid = $fields[0];
    $rap = $fields[1];
    $dep = $fields[2];
    $posi = sprintf("%.6f%+.6f",$rap,$dep);
    $outfile = "nvss/$mjid".".fits";
    if (!-e $outfile) {
	    print "Getting $outfile (RA = $rap Dec = $dep)\n";
	    system("$skyview survey='nvss' position='$posi' size=1.0 output=$outfile\n");
    }
}
