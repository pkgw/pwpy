#!/usr/bin/env perl
# syntax: multiflag.pl filename
# E.g. to apply flags to all mosfxc-* in cwd:
# multiflag.pl mosfxc-* | csh
#
# SDC 2009/04/08
# Modified to flag groups of antennas
# DHW 2009/04/08
# Modified to execute uvflag

# file containing bad antenna numbers, one per line
$badf="/home/dwhysong/bin/badants";

open(BADF,$badf);
@badants=<BADF>;
close(BADF);

# need to break down flagging commands into less than ~50 characters
# so MIRIAD doesn't choke on too long a line
$antfbatch = 0;
$antflags[$antfbatch] = "\"ant(";
foreach $badant (@badants) {
    chomp ($badant);
    $antflags[$antfbatch] = "$antflags[$antfbatch]$badant,";
    if (length($antflags[$antfbatch]) > 50) {
	# this flagging command is getting too big, so start a new one
	chop($antflags[$antfbatch]);
	$antflags[$antfbatch]="$antflags[$antfbatch])\"";
	$antfbatch+=1;
	$antflags[$antfbatch] = "\"ant(";
    }
}

# close off the last flagging command
chop($antflags[$antfbatch]);
$antflags[$antfbatch]="$antflags[$antfbatch])\"";

if ($antflags[$antfbatch] eq "\"ant)\"") {
    # last flagging command had nothing in it
    delete($antflags[$antfbatch]);
}
    
# loop through files from the command line
foreach $file (@ARGV) {
    # loop through each flagging command
    foreach $flagcom (@antflags) {
	# output flagging commands
	print("executing: uvflag vis=$file flagval=f select=$flagcom\n");
	system("uvflag vis=$file flagval=f select=$flagcom\n");
    }
}
