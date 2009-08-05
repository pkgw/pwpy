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
imagebin=3   # zero-based
phasebins=7
outphases=1 # not yet implemented
timebins=420   # how to split in time
interval=`echo 'scale=5; '${period}'/60/2' | bc`  # set this to half period to assure at least two averaged bins
suffix='tst'
visroot='fxc-j0332-0.1s'
#imroot='j0332-0.1s'
imsize=50
cleanup=2
# std naming convention
outn='time-'${suffix}

if [ ${cleanup} -ge 1 ]; then
    echo 'Cleaning up...'
    rm -rf ${visroot}'-time'*
    rm -rf ${visroot}'-on'*
    rm -rf ${visroot}'-avg'*
    rm -rf ${visroot}'-off'*
    rm -rf ${visroot}'-diff'*
    if [ ${cleanup} -ge 2 ]; then
	rm -f ${outn}'-time'*
	rm -f ${outn}'-on'*
	rm -f ${outn}'-avg'*
	rm -f ${outn}'-off'*
    fi
fi

## Run search ##
# create pulse bin
if [ ${cleanup} -ge 2 ]; then
    psrbin-timeselect.sh ${period} ${binsize} ${phasebins} ${outphases} ${ints} ${t0h} ${t0m} ${t0s} ${suffix} ${timebins} ${imagebin}

# need to lengthen number of ints in avg to avoid time overlaps  # may not be necessary after using off pulse subtraction
    for ((i=1;i<${timebins};i++)); do
	imm=`echo 'scale=0; '${i}'-1' | bc`
#	immmm=`echo 'scale=0; '${i}'-2' | bc`
#	cat ${outn}'-avg'${i} >> ${outn}'-avg'${imm}
	cat ${outn}'-off'${i} >> ${outn}'-off'${imm}
#	cat ${outn}'-off'${imm} >> ${outn}'-off'${immmm}
    done
    # hack for last one.  same as second to last...
    iult=`echo 'scale=0; '${timebins}'-1' | bc`
    ipenult=`echo 'scale=0; '${timebins}'-2' | bc`
#    ipenpenult=`echo 'scale=0; '${timebins}'-3' | bc`
#    cp ${outn}'-off'${ipenpenult} ${outn}'-off'${ipenult}
    cp ${outn}'-off'${ipenult} ${outn}'-off'${iult}
#    cp ${outn}'-avg'${ipenult} ${outn}'-avg'${iult}
fi

for ((i=0;i<${timebins};i++)); do
    # set file names
    filebin=${outn}'-on'${i}'aa' # select for bin.  assumes no splitting
#    fileavg=${outn}'-avg'${i} # select for average about bin
    fileoff=${outn}'-off'${i} # select for average about bin
	
    # need to average down.  interval must be big enough to avoid overlapping time stamps and small enough to have more than one integration per file
    uvaver vis=${visroot}'-xx' select='@'${filebin} line=chan,1,1,32 interval=${interval} out=${visroot}'-on'${i}
    uvaver vis=${visroot}'-xx' select='@'${fileoff} line=chan,1,1,32 interval=${interval} out=${visroot}'-off'${i}
#    uvaver vis=${visroot}'-xx' select='@'${fileavg} line=chan,1,1,32 interval=${interval} out=${visroot}'-avg'${i} # old method
#    ./uvdiff vis=${visroot}'-on'${i},${visroot}'-avg'${i} out=${visroot}'-diff'${i}  # old method
    ./uvdiff vis=${visroot}'-on'${i},${visroot}'-off'${i} out=${visroot}'-diff'${i}

    # do fit
    uvfit vis=${visroot}'-diff'${i} object=point
#    uvplt device=1/xs vis=${visroot}'-diff'${i} options=nobase,equal axis=re,im  # should be all real, with mean at best-fit flux density
done
