#! /bin/bash
#
# Master script to create phased images of pulsar
# claw, 13mar09
#
# Usage: psr-img.sh
#
# Output files:
# - text files with time filters for each phase bin (possibly more than one to avoid 256 line limit of miriad)
# - beam and map images for each phase bin and pol (and possibly to avoid 256 line limit of miriad)
# - beam and map image cubes
# - mean-subtracted, clean and restored image cubes

######################
# customize here

# observation properties:
#period=0.7136692   # period that fixes b0329 phase shift
#period=0.358738    # period for b1933
period=0.398478    # trial period for b1933
bin=0.1
ints=12000

# time for j0332-0.1s:
#t0h=02
#t0m=05
#t0s=02.4

# time for b1933-0.1s:
t0h=19
t0m=37
t0s=25.3

# output properties:
phasebins=4
outphases=1  # not yet implemented
suffix='tst'
visroot='fxc-b1933-0.1s-12000-shad'
imroot='b1933-0.1s'
frac='all'   # 'all', '1/3', '2/3', '2/2', etc.
cleanup=0
######################

set -e -x

#clean up
rm -rf ${imroot}-?-${suffix}-*.* ${imroot}-??-${suffix}-bin*.* ${imroot}-???-${suffix}-bin*.* ${imroot}-icube-${suffix}*.* time-${suffix}-bin*

psr-timeselect.sh ${period} ${bin} ${phasebins} ${outphases} ${ints} ${t0h} ${t0m} ${t0s} ${suffix} ${frac}

psr-invert.sh ${visroot} ${imroot} ${suffix} ${phasebins}

psr-avsubcl.sh ${imroot} ${suffix} ${phasebins}

if [ $cleanup -eq 1 ]
    then
    rm -rf ${imroot}-?-${suffix}-*.* ${imroot}-??-${suffix}-bin*.* time-${suffix}-bin*
fi