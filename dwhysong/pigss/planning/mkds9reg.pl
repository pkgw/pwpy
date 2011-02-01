#!/usr/bin/env perl

$pfile = shift @ARGV;

open FILE, "< .tmp/pfhex_fieldline" or die "Error: .tmp/pfhex_fieldline $!\n";
@fieldline=<FILE>;
close FILE;

open FILE, "< $pfile" or die "Error: $pfile $!\n";
@priolines=<FILE>;
close FILE;

chomp(@fieldline,@priolines);

foreach $line (@priolines) {			# Make a hash of colors from the schedule.pl output
	$line =~ /(pfhex-\d*-\d*) prio=(\d)/;	# $1 holds the name, $2 holds the priority

	if ($2 == 4) {
		$hash{$1} = 'magenta';
	}
	elsif ($2 == 3) {
		$hash{$1} = 'blue';
	}
	elsif ($2 == 2) {
		$hash{$1} = 'green';
	}
	else { die "Error: $1 has unhandled priority $2\n"; }
}


foreach(@fieldline) {				# Put colors in the ds9 region file
	$start=index($_,'pfhex');
	$end=index($_,'}');
	$name=substr($_,$start,$end-$start);
	print $_," color=",$hash{$name},"\n";
}
