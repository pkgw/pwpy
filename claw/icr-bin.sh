#! /bin/bash
#
# Usage: micr.sh vis1
#
# Output files are
#
# *.mp Raw map
# *.bm Beam
#
# Assumes data with no autos or cross-hand pol

#set -e -x  # for debugging

visroot='fxc-j0332-0.1s'
suffix='tst'
halflist='aa'     # data split?  half = aa, ab, ac, ...
file='time-'${suffix}

for half in ${halflist}
  do

  for ((i=0; i<=7; i++))
    do
    mpsmall=${visroot}'-xx-'${suffix}'-bin'${i}${half}.mp
    bmsmall=${visroot}'-xx-'${suffix}'-bin'${i}${half}.bm
    invert vis=${visroot}'-xx' map=$mpsmall beam=$bmsmall select='@'${file}'-bin'${i}${half} options=double,mfs sup=0 imsize=78,78
    mpsmall=${visroot}'-yy-'${suffix}'-bin'${i}${half}.mp
    bmsmall=${visroot}'-yy-'${suffix}'-bin'${i}${half}.bm
    invert vis=${visroot}'-yy' map=$mpsmall beam=$bmsmall select='@'${file}'-bin'${i}${half} options=double,mfs sup=0 imsize=78,78
  done

  echo '***Dirty image stats***'

  for ((i=0; i<=7; i++))
    do
    echo 'Image '${i}':'
    imstat in=${visroot}'-xx-'${suffix}'-bin'${i}${half}.mp | tail -n 2
    imstat in=${visroot}'-yy-'${suffix}'-bin'${i}${half}.mp | tail -n 2
  done

done