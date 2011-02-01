#!/usr/bin/perl -w

if (scalar(@ARGV) == 0) {
  print "Usage: setobs.pl [filename] [...]";
  exit;
}

foreach $filename (@ARGV) {
	@fields = `grep ^pfhex $filename`;
	chomp @fields;
	$fields = join ',', @fields;
	@tmp = split /-|\./,$filename;
	$mm=$tmp[3];
	$dd=$tmp[2];
	$yy=$tmp[4];

	print("/home/dwhysong/pigss/schedule.pl -f /etc/observatory/pfhex -vo $mm\/$dd\/$yy,$fields\n\n");
	system("/home/dwhysong/pigss/schedule.pl -f /etc/observatory/pfhex -vo $mm\/$dd\/$yy,$fields");
	print("mv -i $filename done/\n");
	system("mv -i $filename done/");
}
