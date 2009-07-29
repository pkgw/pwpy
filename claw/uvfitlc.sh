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
timebins=10   # how to split in time
suffix='tst'
visroot='fxc-j0332-0.1s'
#imroot='j0332-0.1s'
imsize=50
cleanup=1
# std naming convention
outn='time-'${suffix}

if [ ${cleanup} -eq 1 ]; then
    rm -rf ${visroot}'-pulse'*
    rm -rf ${visroot}'-avg'*
    rm -rf ${visroot}'-diff'*
    rm -f ${outn}'-time'*
    rm -f ${outn}'-avg'*
fi

## Run search ##
# create pulse bin
psrbin-timeselect.sh ${period} ${binsize} ${phasebins} ${outphases} ${ints} ${t0h} ${t0m} ${t0s} ${suffix} ${timebins} ${imagebin}

for ((i=0;i<${timebins};i++)); do
    # set file names
    filebin=${outn}'-time'${i}'aa' # select for bin
    fileavg=${outn}'-avg'${i} # select for average about bin
	
    # need to average down.  interval must be big enough to avoid overlapping time stamps and small enough to have more than one integration per file
    uvaver vis=${visroot}'-xx' select='@'${filebin} line=chan,1,1,32 interval=0.1 out=${visroot}'-pulse'${i}
    uvaver vis=${visroot}'-xx' select='@'${fileavg} line=chan,1,1,32 interval=0.1 out=${visroot}'-avg'${i}
    uvdiff vis=${visroot}'-pulse'${i},${visroot}'-avg'${i} out=${visroot}'-diff'${i}

    # do fit
    uvfit vis=${visroot}'-diff'${i} object=point
    uvplt device=1/xs vis=${visroot}'-diff'${i} options=nobase axis=re,im  # should be all real, with mean at best-fit flux density
done