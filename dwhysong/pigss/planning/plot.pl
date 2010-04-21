#!/usr/bin/env perl

use lib '/usr/lib64/perl5/site_perl/5.8.8/x86_64-linux-thread-multi/PDL/Graphics';
use PDL;
use ASTRONOMY;


$fname=$ARGV[1];
$fname2=$ARGV[2];
print $fname;

($x,$y} = rcols($fname);

$win=PDL::Graphics::PGPLOT::Window->new(Device=>"sim/$fname2/jpg", Aspect=>0.5, WindowWidth=>12);
$im=imload("nvss.fits");
disp_image($im,$win,1);
points($x,$y,{Colour=>Red, symbol => plus};
