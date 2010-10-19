#! /bin/bash
#
# claw, 4aug09
# Script to find pulses by uv fitting for a point source in visibility data.
# Goal is to find significance of each fit relative to overall distribution

#timing
startt=`date +%s`

## User parameters ##
bgints=2  # size of background region to subtract mean emission
ints=10000   # number of integrations to use
skipint=0
binsize=1.0 # size of integration in seconds (why?)
interval=`echo 'scale=5; '${binsize}'*2/60' | bc`  # set this to assure at least two averaged bins in bg
visstep=56  # number of visibilities per integration.  sadly, needs to be hardwired...
bgsub=0   # do bgsub technique
# output properties:
#suffix='0.15'-${startt}
#visroot='fxmir-m82-0.15'
#outroot='m82-bgsub-'${suffix}
suffix='0.1-3'-${startt}
visroot='fxmir-m82-01-3'
outroot='m82-nosub-'${suffix}
cleanup=1

#set -x -e

if [ $cleanup -eq 1 ]
    then
    rm -f ${outroot}-*.txt
    rm -f /tmp/uvfitpulse-${suffix}.txt
    rm -rf ${visroot}'-'${suffix}-on
    rm -rf ${visroot}'-'${suffix}-off
    rm -rf ${visroot}'-'${suffix}-diff
    rm -rf ${outroot}-on
    rm -rf ${outroot}-off
    rm -rf ${outroot}-diff
    rm -rf ${visroot}'-'${suffix}-resid*
fi

touch ${outroot}-flux.txt
touch ${outroot}-x.txt
touch ${outroot}-y.txt

for ((i=${bgints}+${skipint};i<${ints}-${bgints}+${skipint};i++)); do
    echo 'Iteration:' $i
    # prep for new loop
    rm -rf ${visroot}'-'${suffix}-on
    rm -rf ${visroot}'-'${suffix}-off
    rm -rf ${visroot}'-'${suffix}-diff
    rm -rf ${outroot}-on
    rm -rf ${outroot}-off
    rm -rf ${outroot}-diff

    # define visibilities to use
    visbg0=`echo 'scale=0; '${visstep}'*('${i}'-'${bgints}')+1' | bc`     # get neighboring ints in background select
    visbg1=`echo 'scale=0; '${visstep}'*('${i}'+'${bgints}'+1)' | bc`     # get neighboring ints in background select
    vis0=`echo 'scale=0; '${visstep}'*'${i}'+1' | bc`     # get neighboring ints in background select
    vis1=`echo 'scale=0; '${visstep}'*('${i}'+1)' | bc`     # get neighboring ints in background select

    if [ $bgsub == 1 ]
	then
        # create uv data for mean visibility
	uvaver vis=${visroot} select='vis('${visbg0}','${visbg1}'),-vis('${vis0}','${vis1}')' line=chan,1,1,32 interval=${interval} out=${outroot}'-off'
	uvaver vis=${visroot} select='vis('${vis0}','${vis1}')' line=chan,1,1,32 interval=${interval} out=${outroot}'-on'

        # difference integration from mean emission
	~claw/code/mmm/claw/uvdiff vis=${outroot}'-on',${outroot}'-off' out=${outroot}'-diff'

       # uvfit
	uvfit vis=${outroot}'-diff' object=point fix=xy spar=11,0,0 >& /tmp/uvfitpulse-${suffix}.txt
    else
	uvfit vis=${visroot} select='vis('${vis0}','${vis1}')' object=point fix=xy spar=11,0,0 >& /tmp/uvfitpulse-${suffix}.txt
    fi

    # confirm that fit retuned good values
    if [ `grep 'Failed to determine covariance matrix' /tmp/uvfitpulse-${suffix}.txt | wc -l` != 0 ] || [ `grep 'Failed to converge' /tmp/uvfitpulse-${suffix}.txt | wc -l` != 0 ]
	then
	continue
    fi
    # if good, populate text files, else continue to next iter
    grep Flux /tmp/uvfitpulse-${suffix}.txt | awk '{printf("%s %s +/- %s\n",'"$i"',$2,$4)}' >> ${outroot}-flux.txt  # hack to get iter, flux, and error for every fit
#    grep Flux /tmp/uvfitpulse-${suffix}.txt | awk '{printf("%s +/- 1.00E-02",$0)}' | cut -c32-56 | awk '{printf("%s %s\n",'"$i"',$0)}' >> ${outroot}-flux.txt  # hack to get iter, flux, and error for every fit.  old method;  now skips bad iters.
    x=`grep Offset /tmp/uvfitpulse-${suffix}.txt | awk '{printf("%s\n",$4)}'`
    y=`grep Offset /tmp/uvfitpulse-${suffix}.txt | awk '{printf("%s\n",$5)}'`
# if xy fixed (hack)
    grep Offset /tmp/uvfitpulse-${suffix}.txt | awk '{printf("%s %s +/- %s\n",'"$i"','"$x"',$4)}' >> ${outroot}-x.txt
    grep Offset /tmp/uvfitpulse-${suffix}.txt | awk '{printf("%s %s +/- %s\n",'"$i"','"$y"',$5)}' >> ${outroot}-y.txt
# if xy free
#    grep Positional /tmp/uvfitpulse-${suffix}.txt | awk '{printf("%s %s +/- %s\n",'"$i"','"$x"',$4)}' >> ${outroot}-x.txt
#    grep Positional /tmp/uvfitpulse-${suffix}.txt | awk '{printf("%s %s +/- %s\n",'"$i"','"$y"',$5)}' >> ${outroot}-y.txt
done

stopt=`date +%s`
echo "Elapsed seconds:"
echo "scale=2; "${stopt}"-"${startt} | bc

