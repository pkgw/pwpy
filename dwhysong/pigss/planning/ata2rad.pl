#!/usr/bin/env perl

use Astro::Time;

$PI = 3.141592653589793238462643383279502884197;

while (<>) {
	chomp;
	@field=split(/\s+/);

	$field[3]*=$PI/12.0;
	$ra=$field[3];
	$dec=$field[4]*$PI/180.0;
	print "$ra\t$dec\n";
}
