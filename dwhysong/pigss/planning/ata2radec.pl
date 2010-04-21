#!/usr/bin/env perl

use Astro::Time;

$PI = 3.141592653589793238462643383279502884197;

while (<>) {
	chomp;
	@field=split(/\s+/);

	$field[3]*=$PI/12.0;
	$ra=rad2str($field[3],'H',2);
	$dec=deg2str($field[4],'D',1);
	print "$ra\t$dec\n";
}
