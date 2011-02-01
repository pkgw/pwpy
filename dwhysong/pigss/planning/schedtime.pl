#!/usr/bin/env perl

use DateTime;
use DateTime::Format::Strptime;

$TZ='America/Los_Angeles';

sub read_sched {
	my $fname=shift;
	open INFILE, "<", "$fname";
	my @obs = <INFILE>;
	close INFILE;
	return @obs;
}


$filename = shift @ARGV;
die "Please specify a schedule file.\n" if (!defined($filename));
die "$filename not found." if not -f $filename;


@obs=read_sched($filename);


$prevobsend = DateTime->new(year=>1900, time_zone=>$TZ);       # Some time far in the past

$str = $obs[-1];
($startstr,$endstr)=split(/\s+/,$str);
$parser = DateTime::Format::Strptime->new(pattern => '%Y%b%d::%H:%M:%S', time_zone => $TZ, on_error => 'croak');
$last=$parser->parse_datetime($endstr);
$last->truncate(to=>'day');

$str = $obs[0];
($startstr,$endstr)=split(/\s+/,$str);
$first=$parser->parse_datetime($startstr);
$first->truncate(to=>'day');


@obs = grep /PIGSS/, @obs;
$days = $last->subtract_datetime_absolute($first)->seconds / 86400.0;
$hours = 0;

foreach (@obs) {
	($startstr,$endstr)=split;
	$parser = DateTime::Format::Strptime->new(pattern => '%Y%b%d::%H:%M:%S', time_zone => $TZ, on_error => 'croak');
	$obsstart=$parser->parse_datetime($startstr);		# Start of observation
	$obsend=$parser->parse_datetime($endstr);		# End of observation

	$hours += $obsend->subtract_datetime_absolute($obsstart)->seconds / 3600.0;
}
print "PiGSS has $hours hours total.\n";
print "Schedule covers $days days.\n";

$tmp = $hours / ($days / 7);
print "PiGSS has $tmp hours per week.\n";

$tmp = $hours / ($days * 24);
print "PiGSS has $tmp of all telescope time.\n";
