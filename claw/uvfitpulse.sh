#! /bin/bash
#
# claw, 4aug09
# Script to find pulses by uv fitting for a point source in visibility data.
# Goal is to find significance of each fit relative to overall distribution

## User parameters ##
bgints=3  # size of background region to subtract mean emission
ints=3000   # number of integrations to use
binsize=0.1 # size of integration in seconds
interval=`echo 'scale=5; '${binsize}'*2/60' | bc`  # set this to assure at least two averaged bins
visstep=10  # number of visibilities per integration.  sadly, needs to be hardwired...
# output properties:
suffix='tst'
visroot='fxc-j0332-0.1s'
outfile='j0332-0.1s-'${suffix}'.txt'
cleanup=1

#set -x -e

if [ $cleanup -eq 1 ]
    then
    rm -f ${outfile}
    rm -rf ${visroot}'-'${suffix}-on
    rm -rf ${visroot}'-'${suffix}-off
    rm -rf ${visroot}'-'${suffix}-diff
fi

touch ${outfile}

for ((i=${bgints};i<${ints};i++)); do
    # define visibilities to use
    visbg0=`echo 'scale=0; '${visstep}'*('${i}'-'${bgints}')+1' | bc`     # get neighboring ints in background select
    visbg1=`echo 'scale=0; '${visstep}'*('${i}'+'${bgints}'+1)' | bc`     # get neighboring ints in background select
    vis0=`echo 'scale=0; '${visstep}'*'${i}'+1' | bc`     # get neighboring ints in background select
    vis1=`echo 'scale=0; '${visstep}'*('${i}'+1)' | bc`     # get neighboring ints in background select

    # create uv data for mean visibility
    uvaver vis=${visroot}'-xx' select='vis('${visbg0}','${visbg1}'),-vis('${vis0}','${vis1}')' line=chan,1,1,32 interval=${interval} out=${visroot}'-'${suffix}'-off'
    uvaver vis=${visroot}'-xx' select='vis('${vis0}','${vis1}')' line=chan,1,1,32 interval=${interval} out=${visroot}'-'${suffix}'-on'

    # difference integration from mean emission
    ./uvdiff vis=${visroot}'-'${suffix}'-on',${visroot}'-'${suffix}'-off' out=${visroot}'-'${suffix}'-diff' #select='vis('${vis0}','${vis1}')'

    # uvfit
    uvfit vis=${visroot}'-'${suffix}'-diff' object=point | grep Flux | awk '{printf("%s +/- 1.00E-02",$0)}' | cut -c32-56 | awk '{printf("int%s %s\n",'"$i"',$0)}' >> ${outfile}  # hack to get iter, flux, and error for every fit

    rm -rf ${visroot}'-'${suffix}-on
    rm -rf ${visroot}'-'${suffix}-off
    rm -rf ${visroot}'-'${suffix}-diff
done
