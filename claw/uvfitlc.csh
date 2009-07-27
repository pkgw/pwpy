#! /bin/bash
#
# claw, 27jul09
# Script to do uv fitting for a point source in visibility data.
# Goal is to test fast imaging concepts on pulsar data.



## User parameters ##
#pulsar properties
period=0.7137   # period that makes b0329 pulse more constant with time
binsize=0.1
ints=3000
# time for j0332-0.1s:
t0h=02
t0m=05
t0s=02.4
# output properties:
imagebin=4   # zero-based
phasebins=8
outphases=0 # not yet implemented
timebins=1   # how to split in time
suffix='tst'
visroot='fxc-j0332-0.1s'
imroot='j0332-0.1s'
imsize=50
cleanup=1
# std naming convention
outn='time-'${suffix}
file=${outn}'-time'${imgbin} # select for bin
fileavg=${outn}'-avg'${imgbin} # select for average about bin


# create pulse bin
#psrbin-timeselect.sh ${period} ${binsize} ${phasebins} ${outphases} ${ints} ${t0h} ${t0m} ${t0s} ${suffix} ${timebins} ${imagebin}

# split ${file}-time${i}  # create individual bins from list of bins, then
# for loop?

#uvfit vis=${visroot}'-xx' select='@'${fileavg}0 object=gaussian  # fit average source
uvfit vis=${visroot}'-xx' select='@'${file}0aa object=gaussian,point spar=-5.455E-3,-355.83,491.95,1656.9791,18.646,90.0 fix=fxyab # fit additional source
