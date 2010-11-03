#!/usr/bin/env perl

use Math::Trig qw(great_circle_distance pi);

$radius = 6.0 * 3.5/sqrt(2.0)/3.14*pi/180.0;
#print "Cutoff is $radius\n";

if (!defined($PIGSS_CATALOG)) {
	$PIGSS_CATALOG='/home/dwhysong/pigss/pfhex.fields';
} else {
	warn "Warning: using nonstandard catalog $PIGSS_CATALOG\n" if ($verbose);
}


open FILE, "< $PIGSS_CATALOG" or die "Error: $PIGSS_CATALOG $!\n";
foreach (<FILE>) {
	chomp;
	($name, $ra, $dec) = split;
	$dec = pi/2.0 - $dec;
	$poshash{$name}=("$ra $dec");
}
close FILE;

open FILE, "< .tmp/pfhex_fieldline" or die "Error: .tmp/pfhex_fieldline $!\n";
@fieldline=<FILE>;
close FILE;
chomp(@fieldline);

foreach $selected (keys(%poshash)) {
	($ra0, $dec0) = split(/\s+/,$poshash{$selected});
	@list=();
	%hash=();
	foreach $name (keys(%poshash)) {	     # Make a hash of distances to the selected field
		next if ($name eq $selected);
		($ra,$dec) = split(/\s+/,$poshash{$name});
		$dist=great_circle_distance($ra0, $dec0, $ra, $dec);
		push(@list, $name) if ($dist < $radius);
		$hash{$name}=1 if ($dist < $radius);
	}
	print "$selected: @list\n";
}
#	print "$selected has ",scalar(@list)," neighbors\n" if (scalar(@list) > 6);
#
#	if (scalar(@list) > 6) {
#		open REGFILE, "> .tmp/ds9.reg" or die "Error: .tmp/ds9.reg $!\n";
#		foreach(@fieldline) {				   # Put colors in the ds9 region file
#			$start=index($_,'pfhex');
#			$end=index($_,'}');
#			$name=substr($_,$start,$end-$start);
#			if ($hash{$name} == 1) {
#				print REGFILE $_," color=green\n";
#			}
#			else {
#				print REGFILE $_," color=blue\n";
#			}
#		}
#		close REGFILE;
#		print "Press return for graphical display (d for debug): "; $inp=<STDIN>;
#		system('ds9 -geometry 2000x1000 -cmap BB -log -fits nvss.fits -zoom 0.8 -regions load .tmp/ds9.reg -regions showtext no');
#	}
#}
