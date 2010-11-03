#!/usr/bin/env perl

use DateTime;
use DateTime::Format::Strptime;

$TZ='America/Los_Angeles';

sub read_sched {
	my $fname=shift;
	open INFILE, "<", "$fname";
	my @obs = <INFILE>;
	@obs = grep /PIGSS/, @obs;
	print "$fname: read " . scalar(@obs) . " PiGSS records\n" if $verbose;
	close INFILE;
	return @obs;
}


$filename = shift @ARGV;
die "Please specify a schedule file.\n" if (!defined($filename));
die "$filename not found." if not -f $filename;


@obs=read_sched($filename);


$prevobsend = DateTime->new(year=>1900, time_zone=>$TZ);       # Some time far in the past
foreach (@obs) {
	($startstr,$endstr)=split;
	$parser = DateTime::Format::Strptime->new(pattern => '%Y%b%d::%H:%M:%S', time_zone => $TZ, on_error => 'croak');
	$obsstart=$parser->parse_datetime($startstr);		# Start of observation
	$obsend=$parser->parse_datetime($endstr);		# End of observation

        warn "Observation at $startstr is longer than 24 hours." if ($obsend->subtract_datetime_absolute($obsstart)->seconds > 86400);
        warn "Observation at $startstr is shorter than 1 hour." if ($obsend->subtract_datetime_absolute($obsstart)->seconds < 3600);
	warn "Observation at $startstr ends before it starts." if ($obsstart > $obsend);
	warn "Observation at $startstr begins before the end of the previous observation." if ($obsstart < $prevobsend);

	$prevobsend = $obsend;
}
