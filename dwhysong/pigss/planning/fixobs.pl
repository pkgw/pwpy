#!/usr/bin/perl -w

sub by_date {
	@tmp = split /-|\./,$a;
	$ma=$tmp[3];
	$da=$tmp[2];
	$ya=$tmp[4];

	@tmp = split /-|\./,$b;
	$mb=$tmp[3];
	$db=$tmp[2];
	$yb=$tmp[4];

	if ($ya <=> $yb) {
		return ($ya <=> $yb);
	}
	elsif ($ma <=> $mb) {
		return ($ma <=> $mb);
	}
	else {
		return ($da <=> $db);
	}
}



if (scalar(@ARGV) == 0) {
  print "Usage: fixobs.pl [filename] [...]";
  exit;
}

foreach $filename (@ARGV) {
	@fields = `grep pfhex $filename`;
	chomp @fields;
	print "Clearing fields: @fields\n";

	# Clear all obsdate fields and set priority to 4
	$priostr = join("=4 -p ",@fields);
	$priostr = "-p " . $priostr . "=4";
	system("schedule.pl $priostr");

	foreach $field (@fields) {
		@filelist = `grep -l ^$field done/pigss.targets*`;
		chomp @filelist;
		foreach(@filelist) {
			s/done\///;
		}
		@filelist = sort by_date @filelist;
		foreach(@filelist) {
			@tmp = split /-|\./,$_;
			$mm=$tmp[3];
			$dd=$tmp[2];
			$yy=$tmp[4];
			print("/home/dwhysong/pigss/schedule.pl -vo $mm\/$dd\/$yy,$field\n\n");
			system("/home/dwhysong/pigss/schedule.pl -vo $mm\/$dd\/$yy,$field");
		}
	}
}
