#!/usr/bin/perl

use MLDBM::Sync;
use MLDBM qw(MLDBM::Sync::SDBM_File Storable);
use Fcntl qw(:DEFAULT :flock);

sub open_sched_rw {
        $db = tie %data, 'MLDBM::Sync', "/etc/observatory/pfhex", O_CREAT|O_RDWR, 0640 or die $!;
        $db->Lock;
}

sub close_sched {
        $db->UnLock;
}


print "Enter input filename: ";
$infile=<>;
print "What key would you like to set? (e.g. neighbors extneighbors etc.): ";
$token=<>;
chomp($token);

open_sched_rw();
$ref = $data{index};
%index=%$ref;
open INFILE, "< $infile" or die "Can't open $infile: $!\n";
while (<INFILE>) {
	chomp;
	($name,@nlist) = split;

	$start=0;
	$end=index($_,':');
	$name=substr($name,$start,$end-$start);

	$keynum = $index{$name};
	$ref = $data{$keynum};
	%obj = %$ref;

	die "No such object found in database\n" if (!defined(%obj));

	$nlist = join ',',@nlist;
	#warn "$name has too many neighbors.\n" unless (scalar(@nlist) < 7);

	$obj{$token}=$nlist;

	#print "$name $token = $nlist\n";
	$data{$keynum} = \%obj;
}
close INFILE;
close_sched();
exit();
