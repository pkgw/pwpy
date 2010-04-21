#!/usr/bin/env perl

use Astro::Time;

$PI = 3.141592653589793238462643383279502884197;

print "Enter positions in format: HH:MM:SS [-]DD:MM:SS\n";

while (<>) {
	chomp;
	@field=split(/\s+/);

	$ra=str2rad($field[0],'H');
	$ra*=12.0/$PI;
	$dec=str2deg($field[1],'D');
	print "$ra\t$dec\n";
}
