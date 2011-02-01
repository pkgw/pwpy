#!/usr/bin/env perl

use DateTime;
use DateTime::Format::Strptime;
use Astro::Telescope;
use Astro::Time;
use Astro::SLA ();
use ATA;

$TZ='America/Los_Angeles';

sub parse_string_time {
        my $str = shift;
        my @tmp;
        my $date;

        @tmp = split(/:|\//,$str);
        if (scalar(@tmp)==3) {  # Time only
                $date = DateTime->now(time_zone=>'local');
                $date->set(hour=>$tmp[0]);
                $date->set(minute=>$tmp[1]);
                $date->set(second=>$tmp[2]);
                $date->set(nanosecond=>0);
        }
        elsif (scalar(@tmp)==6) {
                $date = DateTime->new(year=>$tmp[2],
                                month=>$tmp[1],
                                day=>$tmp[0],
                                hour=>$tmp[3],
                                minute=>$tmp[4],
                                second=>$tmp[5],
                                nanosecond=>0,
                                time_zone=>'local');
        }
        else { die "Bad time string. Format is: dd/mm/yyyy/hh:mm:ss\n"; }
        $date->set_time_zone('UTC');

        return $date;
}


$str = $ARGV[0];
$tel=observatory_load();
$long = (defined $tel ? $tel->long : 0.0);
$long == 0.0 and warn "Telescope longitude is zero; undefined telescope?\n";

print "LST at $str is: ";
$time = parse_string_time($str);

# need to convert to UTC for ut2lst. We'll switch back to local time immediately afterward.
$time->set_time_zone('UTC');
$lst = 12/$PI*(Astro::SLA::ut2lst($time->year,$time->mon,$time->mday,$time->hour,$time->min,$time->sec,$long))[0];
$time->set_time_zone($TZ);
print "$lst\n";
