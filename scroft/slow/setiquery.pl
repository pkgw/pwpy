#!/usr/bin/perl
#

# e.g. to select sources with multiple matches in the same epoch (here ATA_Coadd)
# select mjid,fi,sum(fi) from master where (epname == "ATA_Coadd") group by mjid having sum(fi)>fi;

use DBI;

$dbfile = "slow.db";
$dbh = DBI->connect("dbi:SQLite:dbname=$dbfile") or die "Couldn't connect to database: " . DBI->errstr;

$nosort = 0;
$sortav = 0;
$sortmax = 0;
$sortmaxata = 1;
$sortsum = 0;
$printall = 0;
$thresh = 0;

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
    if ($arg =~ /minepochs=(\d+)/) {
        $nepo = $1;
        $epmin = 1;
    }
    if ($arg =~ /maxepochs=(\d+)/) {
        $nepo = $1;
        $epmax = 1;
    }
    if ($arg =~ /thresh=(\S+)/) {
        $thresh = $1;
    }
    if ($arg eq "radec") {
	$radec = 1;
    }
    if ($arg eq "printall") {
	$printall = 1;
    }
    if ($arg eq "newline") {
	$newline = 1;
    }
    if ($arg eq "dual") {
	$dual = 1;
    }
}

# list of all unique sources
if ($nosort) {
    $mjids = $dbh->prepare("SELECT DISTINCT mjid FROM master WHERE mjid <> 'J'") or die "Couldn't prepare statement: " . $dbh->errstr;
}
# list of all unique sources, ordered by mean flux over all epochs
if ($sortav) {
    $mjids = $dbh->prepare("SELECT mjid FROM master WHERE mjid <> 'J' GROUP BY mjid ORDER BY AVG(fi)") or die "Couldn't prepare statement: " . $dbh->errstr;
}
# list of all unique sources, ordered by brightest flux at any epoch (including NVSS)
if ($sortmax) {
    $mjids = $dbh->prepare("SELECT mjid FROM master WHERE mjid <> 'J' GROUP BY mjid ORDER BY MAX(fi)") or die "Couldn't prepare statement: " . $dbh->errstr;
}
# list of all unique sources, ordered by brightest flux at any ATA epoch
if ($sortmaxata) {
    $mjids = $dbh->prepare("SELECT mjid FROM master WHERE (mjid <> 'J' and epname LIKE 'ATA%') GROUP BY mjid HAVING max(fi) > $thresh ORDER BY MAX(fi)") or die "Couldn't prepare statement: " . $dbh->errstr;
}
# list of all unique sources, ordered by total flux over all epochs
if ($sortsum) {
    $mjids = $dbh->prepare("SELECT mjid FROM master WHERE mjid <> 'J' GROUP BY mjid ORDER BY SUM(fi)") or die "Couldn't prepare statement: " . $dbh->errstr;
}
# all transients with $nepo ATA epochs, peaking at > $thresh
if ($epma) {
    $mjids = $dbh->prepare("select distinct mjid from master where (mjid NOT IN (select distinct mjid from master where epname like 'NVSS%') AND mjid IN (select mjid from master group by mjid having avg(good) == 1)) group by mjid having (count (distinct epname) == $nepo and max(fi)>$thresh) ORDER BY MAX(fi)") or die "Couldn't prepare statement: " . $dbh->errstr;
}
# all transients with >= $nepo ATA epochs, peaking at > $thresh
if ($epmin) {
    $mjids = $dbh->prepare("select distinct mjid from master where (mjid NOT IN (select distinct mjid from master where epname like 'NVSS%') AND mjid IN (select mjid from master group by mjid having avg(good) == 1)) group by mjid having (count (distinct epname) >= $nepo and max(fi)>$thresh) ORDER BY MAX(fi)") or die "Couldn't prepare statement: " . $dbh->errstr;
}
# all transients with <= $nepo ATA epochs, peaking at > $thresh
if ($epmax) {
    $mjids = $dbh->prepare("select distinct mjid from master where (mjid NOT IN (select distinct mjid from master where epname like 'NVSS%') AND mjid IN (select mjid from master group by mjid having avg(good) == 1)) group by mjid having (count (distinct epname) <= $nepo and max(fi)>$thresh) ORDER BY MAX(fi)") or die "Couldn't prepare statement: " . $dbh->errstr;
}
# only sources appearing in both frequencies
# ******* NB - as written this will sum fluxes of matched sources at both frequencies - not what we want
# ******* should loop over frequencies instead, which means storing frequencies in DB always
if ($dual) {
    $mjids = $dbh->prepare("select m1.mjid,m1.ra,m1.decl,m1.epname,m1.freq,m2.epname,m2.mjid,m2.freq from master as m1, master as m2 where (m1.freq == '3040' and m2.freq == '3140' and m1.mjid == m2.mjid and m1.epname == m2.epname) group by m1.mjid") or die "Couldn't prepare statement: " . $dbh->errstr;
}


$mjids->execute();

# find number of epochs
$nep = $dbh->selectrow_array("SELECT COUNT (DISTINCT epname) FROM master") or die "Couldn't determine number of epochs: " . $dbh->errstr;
#print "$nep\n";

# this source at all epochs
$matchjid = $dbh->prepare("SELECT fi, rb FROM master WHERE (mjid == ? and epname == ?)") or die "Couldn't prepare statement: " . $dbh->errstr;

$rad = $dbh->prepare("SELECT ra, decl FROM master where (mjid == ?)") or die "Couldn't prepare statement: " . $dbh->errstr;
	
while (@data = $mjids->fetchrow_array) {
    $mjid = $data[0];
    print "$mjid ";
    if ($radec) {
		$rad->execute($mjid);
		@radecl = $rad->fetchrow_array;
		$ra = $radecl[0];
		$de = $radecl[1];
		print "$ra $de ";
    }
    for ($epoch = 0; $epoch < $nep; $epoch++) {
		$epname = "ATA$epoch";
		if ($epoch == 0) {
	    	$epname = "ATA_Coadd";
		}
		if ($epoch == $nep - 1) {
	    	$epname = "NVSS";
		}
    	$matchjid->execute($mjid,$epname);
		$nmatch = 0;
		$fit = 0;
		$rbst = 0;
		while (@data2 = $matchjid->fetchrow_array) {
	    	$fit += $data2[0];
	    	$rb = $data2[1];
# sum errors in quadrature
	    	$rbst += $rb**2;
#	    printf ("%10.3f %10.3f",$fi,$rb);
	    	$nmatch++;
		}	    
		$rbt = sqrt($rbst);
		if ($printall || $fit > 0) {
	    	printf (" %s %10.3f %10.3f %d",$epname,$fit,$rbt,$nmatch);
			if ($newline) {
				print"\n";
			}
		}
    }
    print "\n";

}
