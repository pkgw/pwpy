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
#period=0.71452    # period from literature
period=0.7136692   # period that fixes phase shift?
bin=0.1
phasebins=16
outphases=1  # not yet implemented
ints=1500
t0h=02
t0m=05
t0s=02.4
suffix='tst'
visroot='fxc-j0332-0.1s'
imroot='j0332-0.1s'
suffix='tst'
halflist='aa'     # data split?  half = aa, ab, ac, ...
######################

set -e -x

#clean up
rm -rf ${imroot}-*-${suffix}-*.bm ${imroot}-*-${suffix}-*.* ${imroot}-icube-${suffix}.* time-${suffix}-bin*

timelist.sh ${period} ${bin} ${phasebins} ${outphases} ${ints} ${t0h} ${t0m} ${t0s} ${suffix}

icr-bin.sh ${visroot} ${imroot} ${suffix} ${halflist} ${phasebins}

avgim.sh ${imroot} ${suffix} ${halflist} ${phasebins}
