#!/usr/bin/env perl

use POSIX qw(floor);
#use PDL;
use DateTime;
use DateTime::Format::Strptime;
use Getopt::Long;

$ENV{"PATH"}="/home/dwhysong/pigss:".$ENV{"PATH"};

# TODO:
#	- reduce number of calls to schedule.pl by using a simple way to find nearest fields
#	- PGPLOT / PLPLOT display instead of DS9 where possible? (Need lots of work for point selection)
#	- use a single monolithic file of pre-computed points instead of running plotfields

sub parse_string_time {
	my $str = shift;
	my @tmp;
	my $date;

	@tmp = split(/:|\//,$str);
	if (scalar(@tmp)==3) {  # Time only
		$date = DateTime->now(time_zone=>'America/Los_Angeles');
		$date->set(hour=>$tmp[0]);
		$date->set(minute=>$tmp[1]);
		$date->set(second=>$tmp[2]);
		$date->set(nanosecond=>0);
	}
	elsif (scalar(@tmp)==6) {  # Date and time
		$date = DateTime->new(year=>$tmp[2],
				month=>$tmp[1],
				day=>$tmp[0],
				hour=>$tmp[3],
				minute=>$tmp[4],
				second=>$tmp[5],
				nanosecond=>0,
				time_zone=>'America/Los_Angeles');
	}
	else { die "Bad time string $str. Format is: dd/mm/yyyy/hh:mm:ss\n"; }
	
	return $date;
}

sub parse_decimal_time {
	my $t = shift;
	my $d = shift;
	my $tmp;

	if (!defined($d)) { $d = DateTime->now(time_zone=>'America/Los_Angeles'); }
	else { $d=$d->clone->set_time_zone('America/Los_Angeles'); }
	$d->set(hour=>int($t));
	$tmp = $t-int($t);
	$d->set(minute=>int(60*$tmp));
	$tmp *= 60;
	$tmp = $tmp-int($tmp);
	$d->set(second=>int(60*$tmp));
	$d->set(nanosecond=>0);

	return($d);
}



Getopt::Long::Configure ("bundling");
GetOptions     ('file|f=s' => \$filename,
		'restart|r' => \$restart,
                'help|h' => \$help,
                'number|n=i' => \$nfields,
                'start|s=s' => \$STARTTIME,
		'date|d=s' => \$DATE,
                'end|e=f' => \$ENDTIME,
                'verbose|v' => \$verbose);

if ($help) {
        print "Survey schedule planner\tCopyright (c) 2010 David Whysong\n\n";
        print "Arguments:\n";
        print "\t--help\t\tshow this text.\n\n";
        print "\t--file\t\tselect database file\n";
	print "\t--restart\tdo not run first pass (assume files in .tmp are good)\n";
        print "\t--number [#]\tnumber of fields to observe per hour\n";
	print "\t--date [mm/dd/yyyy]\tspecify date of observation\n";
        print "\t--start [#]\tspecify start time in ATA decimal format (America/Los_Angeles TZ)\n";
        print "\t--end [#]\tspecify end time in ATA decimal format (America/Los_Angeles TZ)\n";
        print "\t--verbose\tprint extra information\n";
        exit();
}



if (-f '/home/dwhysong/pigss/pigss.targets') {
	print "Before runing this script, be sure that observed fields have zero priority in the database.\n";
	die "Fatal error: pigss.targets exists.\n";
}

if (!defined($DATE)) {
	$date=DateTime->now(time_zone=>'America/Los_Angeles')->truncate(to=>'day');
	$DATE=$date->strftime("%d-%m-%Y");
}
else {
	my $parser = DateTime::Format::Strptime->new( pattern => '%m/%d/%Y', time_zone => 'America/Los_Angeles', on_error => 'croak');
	$date=$parser->parse_datetime($DATE);
	$DATE=$date->strftime("%d-%m-%Y");
}

if (!defined($STARTTIME)) {
	print "Enter decimal start time: ";
	$STARTTIME=<STDIN>;
	chomp($STARTTIME);
}
$start = parse_decimal_time($STARTTIME,$date);
$STARTTIME=$start->strftime("%d/%m/%Y/%H:%M:%S");

if (!defined($ENDTIME)) {
	print "Enter decimal end time: ";
	$ENDTIME=<STDIN>;
	chomp($ENDTIME);
}
$end = parse_decimal_time($ENDTIME);
if ($end < $start) {
	$end->add(days=>1);
}
die "Adjusted end time is still before start time.\n" if ($end < $start);
$obslen = $end->subtract_datetime_absolute($start)->seconds;
$obslen /= 3600.0;
print "Observation length: $obslen hours\n" if ($verbose);
print "Observation ends at: $end\n" if ($verbose);
die "Invalid observation length\n" if ($obslen<0);

$NFIELDS=POSIX::floor($obslen * 5.2) - 7;	##### Subject to change, of course
print "Will select $NFIELDS targets.\n";

if (!defined($PIGSS_DATABASE)) {
	$PIGSS_DATABASE='/etc/observatory/pfhex';
} else {
	warn "Warning: using nonstandard database $PIGSS_DATABASE\n";
}
if (!defined($PIGSS_CATALOG)) {
	$PIGSS_CATALOG='/home/dwhysong/pigss/pfhex.fields';
} else {
	warn "Warning: using nonstandard catalog $PIGSS_CATALOG\n";
}

$PLOTARGS="-m $PIGSS_CATALOG";
$SCHEDARGS="-d -f$PIGSS_DATABASE -t$STARTTIME -e$ENDTIME";
print "Using: schedule.pl $SCHEDARGS -g -n50000\n";

chdir '/home/dwhysong/pigss/.tmp';

if (! $restart) {
	unlink('unobs','unobs2','obs','new','pos','ds9.reg','possible','observed','targets');
	system("schedule.pl $SCHEDARGS -g -n50000 > possible");
	system("schedule.pl $SCHEDARGS -l | grep prio=0 | cut -f3 -d= | cut -f1 -d' ' > observed");
	system("plotfields.pl $PLOTARGS -c red -f possible -o ds9.reg > /dev/null");
	system("plotfields.pl $PLOTARGS -c yellow -f observed -o ds9.reg > /dev/null");

	# Make list of unobserved fields (blue);
	system("cat possible observed > all");
	system("cat $PIGSS_CATALOG | cut -f1 > unobs2");
	system("cat all unobs2 | sort | uniq -u > unobs");
	system("plotfields.pl $PLOTARGS -c blue -f unobs -o ds9.reg > /dev/null");
}

print "Press return for graphical display: ";
<STDIN>;

system('ds9 -geometry 2000x1000 -cmap BB -log -fits nvss.fits -zoom 0.8 -regions load ds9.reg -regions showtext no &');
print "Enter primary target field name: ";
$NAME=<STDIN>;
chomp($NAME);
# Verify that $NAME appears in $PIGSS_CATALOG
system("grep -q $NAME $PIGSS_CATALOG") and die "$NAME not found in $PIGSS_CATALOG\n";
# Load data, selecting only those in "possible" list
#@POS=`grep -f possible $PIGSS_CATALOG`;	# Make into hash, using name as a key?
# Sort by distance from selected target
# Select first $NFIELDS from list
system("schedule.pl $SCHEDARGS -p $NAME=5");
system("schedule.pl $SCHEDARGS -g -n$NFIELDS | sort -n > targets");
system("schedule.pl $SCHEDARGS -p $NAME=4");
system("cat ds9.reg | fgrep -vf targets > tmp");
system("mv tmp ds9.reg");
system("plotfields.pl $PLOTARGS -c green -f targets -o ds9.reg > /dev/null");
chdir '/home/dwhysong/pigss';
print "Press return for graphical display: ";
<STDIN>;
system("cp .tmp/ds9.reg status/pigss-$DATE.reg");
system("ds9 -geometry 2000x1000 -cmap BB -log -fits nvss.fits -zoom 0.8 -regions load .tmp/ds9.reg -regions showtext no &");
print("Adding EliasN1 fields.\n");
#system("echo lockman >> .tmp/targets");
system("echo eliasn1 >> .tmp/targets");
link ".tmp/targets", "pigss.targets" || warn "Cannot link .tmp/targets to pigss.targets\n";
$i=0;
do {
	$NAME="pigss.targets-$DATE.$i";
	$i++;
} until (! -e $NAME);
link "pigss.targets", $NAME || warn "Cannot link pigss.targets to $NAME\n";
print "Writing: $NAME\n";
