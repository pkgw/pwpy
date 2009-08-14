#! /bin/bash
#
# claw, 4aug09
# Script to find pulses by uv fitting for a point source in visibility data.
# Goal is to find significance of each fit relative to overall distribution

#timing
startt=`date +%s`

## User parameters ##
bgints=2  # size of background region to subtract mean emission
ints=4000   # number of integrations to use
skipint=0
binsize=0.1 # size of integration in seconds
interval=`echo 'scale=5; '${binsize}'*2/60' | bc`  # set this to assure at least two averaged bins
visstep=10  # number of visibilities per integration.  sadly, needs to be hardwired...
# output properties:
suffix='fixxy-short'
visroot='fxc-b0950-0.15s-4000'
outroot='b0950-'${suffix}
cleanup=1

set -x -e

if [ $cleanup -eq 1 ]
    then
    rm -f ${outroot}-*.txt
    rm -f /tmp/uvfitpulse-${suffix}.txt
    rm -rf ${visroot}'-'${suffix}-on
    rm -rf ${visroot}'-'${suffix}-off
    rm -rf ${visroot}'-'${suffix}-diff
    rm -rf ${visroot}'-'${suffix}-resid*
fi

touch ${outroot}-flux.txt
touch ${outroot}-x.txt
touch ${outroot}-y.txt

for ((i=${bgints}+${skipint};i<${ints}-${bgints}+${skipint};i++)); do
    # prep for new loop
    rm -rf ${visroot}'-'${suffix}-on
    rm -rf ${visroot}'-'${suffix}-off
    rm -rf ${visroot}'-'${suffix}-diff

    # define visibilities to use
    visbg0=`echo 'scale=0; '${visstep}'*('${i}'-'${bgints}')+1' | bc`     # get neighboring ints in background select
    visbg1=`echo 'scale=0; '${visstep}'*('${i}'+'${bgints}'+1)' | bc`     # get neighboring ints in background select
    vis0=`echo 'scale=0; '${visstep}'*'${i}'+1' | bc`     # get neighboring ints in background select
    vis1=`echo 'scale=0; '${visstep}'*('${i}'+1)' | bc`     # get neighboring ints in background select

    # create uv data for mean visibility
    uvaver vis=${visroot}'-xx' select='vis('${visbg0}','${visbg1}'),-vis('${vis0}','${vis1}')' line=chan,1,1,32 interval=${interval} out=${visroot}'-'${suffix}'-off'
    uvaver vis=${visroot}'-xx' select='vis('${vis0}','${vis1}')' line=chan,1,1,32 interval=${interval} out=${visroot}'-'${suffix}'-on'

    # difference integration from mean emission
    ./uvdiff vis=${visroot}'-'${suffix}'-on',${visroot}'-'${suffix}'-off' out=${visroot}'-'${suffix}'-diff'

    # uvfit
    uvfit vis=${visroot}'-'${suffix}'-diff' object=point fix=xy >& /tmp/uvfitpulse-${suffix}.txt
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

