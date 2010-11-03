#!/usr/bin/env perl

use POSIX qw(floor);
use DateTime;
use DateTime::Format::Strptime;
use Getopt::Long;
use Math::Trig 'great_circle_distance';

$ENV{"PATH"}="/home/dwhysong/pigss:".$ENV{"PATH"};
$PI = 3.1415926535897932384626433832795028841971693993751;
$PI_2 = $PI/2.0;

# TODO:
#	- Increase speed of schedule.pl - most time is spent in Astro::Coords set_time method
#	- PGPLOT / PLPLOT display instead of DS9 where possible? (Need lots of work for point selection)

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


sub by_dist {   # sort by distance to coordinates specified in global variables $cra, $cdec
        return ($disthash{$a} <=> $disthash{$b});
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
print "Using: schedule.pl $SCHEDARGS -g\n";

chdir '/home/dwhysong/pigss/.tmp';

# Old color code:
# Yellow: already done (file: observed)
# Red: can be observed (file: possible)
# Blue: not observable (file: unobs) == all fields - possible - observed
# Green: selected for observation (file: targets)
#
# New color code:
# Red: not observable
# Yellow: can be observed
# Blue: already done
# Green: selected for observation (file: targets)

if ($restart) {
	unlink('targets');
	open(FILE,'status') || die "Unable to open status file\n";
	@fieldlist=<FILE>;
	close(FILE);
}
else {
	unlink('status','targets','ds9.reg');
	@fieldlist=`schedule.pl $SCHEDARGS -s | tee status`;
}

#@fieldline=`plotfields.pl $PLOTARGS -f pfhex_all`;	# 17 seconds; that's fast, apparently because pfhex_all is sorted
@fieldline=`cat pfhex_fieldline`;			# Even faster... save 17 seconds
chomp(@fieldline,@fieldlist);

foreach(@fieldlist) {					# Make a hash of colors from the schedule.pl output
	$len=index($_," ");
	$name=substr($_,0,$len);
	if (/not observable/) {
		$hash{$name}='red';
	}
	elsif (/observed/) {
		$hash{$name}='blue';
	}
	elsif (/observable/) {				# Would match "not observable" if we did this first
		$hash{$name}='yellow';
	}
	else { die "Unknown status for $name\n"; }
}

open FILE, ">ds9.reg";
foreach(@fieldline) {					# Put colors in the ds9 region file
	$start=index($_,'pfhex');
	$end=index($_,'}');
	$name=substr($_,$start,$end-$start);
	
	print FILE $_," color=",$hash{$name},"\n";
}
close FILE;

print "Press return for graphical display: ";
<STDIN>;
system('ds9 -geometry 2000x1000 -cmap BB -log -fits nvss.fits -zoom 0.8 -regions load ds9.reg -regions showtext no &');
print "Enter primary target field name: ";
$selected=<STDIN>;
chomp($selected);

system("grep -q $name $PIGSS_CATALOG") and die "$name not found in $PIGSS_CATALOG\n"; # Verify that $name appears in $PIGSS_CATALOG
if ($hash{$name} != 'yellow') { die "$name is not observable.\n"; }		# Verify that $name is observable



foreach(@fieldlist) {					# Make a list of observable fields
	$len=index($_,' ');
	$name=substr($_,0,$len);
	if (/observable/ and not /not/) {		# Careful, as "not observable" would match /observable/
		push @possible, $name;
	}
}

@catalog=`cat $PIGSS_CATALOG`;				# Make a hash of "RA DEC" strings
chomp(@catalog);
foreach (@catalog) {
	($name, $ra, $dec) = split;
	$dec = $PI_2 - $dec;
	$poshash{$name}=("$ra $dec");
}

($ra0, $dec0) = split(/\s+/,$poshash{$selected});
foreach $name (@possible) {				# Make a hash of distances to the selected field
	($ra,$dec) = split(/\s+/,$poshash{$name});
	$disthash{$name}=great_circle_distance($ra0, $dec0, $ra, $dec);
}

undef @possible;					# Erase @possible
foreach $key (sort by_dist (keys(%disthash))) {
	unshift @possible, $key;			# @possible is a list sorted by distance
}

for ($i=0; $i<$NFIELDS; $i++) {				# Move the targets to a new list
	$_=pop(@possible);
	push @targets, $_;
}

open FILE, ">targets";
foreach $name (@targets) {				# Set the target fields to be green in the color hash
	$hash{$name}='green';
	print FILE $name,"\n";				# Write the targets file
}
print("Adding EliasN1 fields.\n") if ($verbose);
for ($i=1; $i<=7; $i++) {
	print FILE "eliasn1-000$i\n";
}
close FILE;

open FILE, ">ds9.reg";					# Write a new region file
foreach(@fieldline) {
	$start=index($_,'pfhex');
	$end=index($_,'}');
	$name=substr($_,$start,$end-$start);
	
	print FILE $_," color=",$hash{$name},"\n";
}
close FILE;

chdir '/home/dwhysong/pigss';
print "Press return for graphical display: ";
<STDIN>;
system("ds9 -geometry 2000x1000 -cmap BB -log -fits nvss.fits -zoom 0.8 -regions load .tmp/ds9.reg -regions showtext no &");
link ".tmp/targets", "pigss.targets" || warn "Cannot link .tmp/targets to pigss.targets\n";
$i=0;
do {
	$name="pigss.targets-$DATE.$i";
	$regname="/home/dwhysong/pigss/status/pigss-$DATE-$i.reg";
	$i++;
} until (! -e $name);
link "pigss.targets", $name || warn "Cannot link pigss.targets to $name\n";
system("cp .tmp/ds9.reg $regname");
system("bzip2 -9 $regname");
print "Writing: $name\n";
