#!/usr/bin/env perl

use Astro::Time;

while (<>) {
	chomp;
	@field=split(/\s+/);

	$ra=rad2str($field[0],'H',2);
	$dec=rad2str($field[1],'D',1);
	print "$ra\t$dec\n";
}
