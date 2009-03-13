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
#
##################
#visroot='fxc-j0332-0.1s'
#imroot='j0332-0.1s'
#suffix='tst'
#halflist='aa ab'     # data split?  half = aa, ab, ac, ...
#phasebins=16
##################
visroot="$1"
imroot="$2"
suffix="$3"
halflist="$4"
phasebins="$5"

echo
echo '***Imaging phase bins***'
echo

#set -e -x  # for debugging
file='time-'${suffix}

for half in ${halflist}
  do

  for ((i=0; i<=${phasebins}-1; i++))
    do
    mpsmall=${imroot}'-xx-'${suffix}'-bin'${i}${half}.mp
    bmsmall=${imroot}'-xx-'${suffix}'-bin'${i}${half}.bm
    invert vis=${visroot}'-xx' map=$mpsmall beam=$bmsmall select='@'${file}'-bin'${i}${half} options=double,mfs sup=0 imsize=78,78
    mpsmall=${imroot}'-yy-'${suffix}'-bin'${i}${half}.mp
    bmsmall=${imroot}'-yy-'${suffix}'-bin'${i}${half}.bm
    invert vis=${visroot}'-yy' map=$mpsmall beam=$bmsmall select='@'${file}'-bin'${i}${half} options=double,mfs sup=0 imsize=78,78
  done

  echo
  echo '***Dirty image stats***'

  for ((i=0; i<=${phasebins}-1; i++))
    do
    echo 'Image '${i}':'
    imstat in=${imroot}'-xx-'${suffix}'-bin'${i}${half}.mp | tail -n 2
    imstat in=${imroot}'-yy-'${suffix}'-bin'${i}${half}.mp | tail -n 2
  done

done