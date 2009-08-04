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
period=0.7137   # period that makes b0329 pulse more constant with time
#period=0.358738    # period for b1933
#period=0.25310    # period that works for b0950
binsize=0.1
ints=3000

# time for j0332-0.1s:
t0h=02
t0m=05
t0s=02.4

# time for b1933-0.1s:
#t0h=19
#t0m=37
#t0s=25.3

# time for b0950-0.1s-6000
#t0h=01
#t0m=32
#t0s=35.7

# output properties:
imagebin=1   # zero-based
phasebins=6
outphases=1  # not yet implemented
timebins=42   # how to split in time
suffix='tst'
visroot='fxc-j0332-0.1s'
imroot='j0332-0.1s'
imsize=50
cleanup=1
######################

set -e -x

# loop to do trial periods
#for ((i=1; i<=25; i++))
#  do
#  period=`echo 0.3593-0.00003*${i} | bc`
#  suffix=p${i}
  
#clean up
  rm -rf ${imroot}-xx-${suffix}-*.* ${imroot}-yy-${suffix}-*.* # remove xx, yy ims for time and avg
  rm -rf ${imroot}-i-${suffix}-*.* ${imroot}-i??-${suffix}-*.*  # i, ixx, iyy
  rm -rf ${imroot}-ion*-${suffix}.* ${imroot}-ion*-${suffix}-sub.* ${imroot}-iavg*-${suffix}*.*   # remove old image cubes
  rm -f time-${suffix}-on* time-${suffix}-avg*    # remove time filter files

  psrbin-timeselect.sh ${period} ${binsize} ${phasebins} ${outphases} ${ints} ${t0h} ${t0m} ${t0s} ${suffix} ${timebins} ${imagebin}

  psrbin-invert.sh ${visroot} ${imroot} ${suffix} ${timebins} ${imsize}

  psrbin-avsubcl.sh ${imroot} ${suffix} ${timebins} ${imsize}

  if [ $cleanup -eq 1 ]
      then
      rm -rf ${imroot}-?-${suffix}-*.* 
      rm -rf ${imroot}-??-${suffix}-on*.* 
      rm -rf ${imroot}-??-${suffix}-avg*.* 
      rm -rf ${imroot}-ion?-${suffix}.* ${imroot}-iavg?-${suffix}.*
      rm -f time-${suffix}-on* time-${suffix}-avg* time-${suffix}-off*
  fi
#done