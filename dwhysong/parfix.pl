#!/usr/bin/perl -w

use Time::HiRes qw(usleep);


# /proc/loadavg contains:
#0.92 2.09 1.06 1/326 20455
#1min 5min 10m  ^ This is the # of running processes
sub getload {
	my $nsamples=shift;
	my $usec=shift;
	my $weight=shift;
	my ($i,$str,$nprocs,$load1m, $load5m, $load);
	$usec=20 unless defined($usec);
	$usec *= 1000;
	$weight=0.9 unless defined($weight);
	$nprocs=0;
	for ($i=0; $i<$nsamples; $i++) {
		$str = `cat /proc/loadavg`;
		$str =~ m/\s(\S+)\//;
		$nprocs+=$1;
		if ($nsamples>1) { usleep($usec); }
	}
	($load1m, $load5m)=split(/\s/,$str);
	$nprocs /= $nsamples;
	$load = $weight*$nprocs+(1.0-$weight)*$load1m;
	#print("Load is: $nprocs $load1m $load5m: $load\n");
	return $load;
}



@list = `find . -name mosfx*0`;
sub launch {
	$file = shift(@list);
	chomp($file);
	print ("Launching: fixdata $file 2>&1 > /dev/null &\n");
	system("fixdata $file 2>&1 > /dev/null &");
}


@procs=grep(/processor/,`cat /proc/cpuinfo`);
$nprocs=scalar(@procs);
print "Detected $nprocs processors.\n";

for ($i=0; $i<$nprocs/2; $i++) {
	launch;
}

do {
	$load=getload(2);	# Simple, fast check
	if ($load < $nprocs-2) {
		sleep(1);
		$load = getload(10,200,0.2);	# Double check, and make sure!
		print "System load: $load\n";
		if ($load < $nprocs) {
			launch;
			sleep(15);
			print("Continuing.\n");
		}
	}
} until (scalar(@list)==0);
