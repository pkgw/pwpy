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
#phasebins=16
##################
visroot="$1"
imroot="$2"
suffix="$3"
phasebins="$4"

echo
echo '***Imaging phase bins***'
echo

#set -e -x  # for debugging
file='time-'${suffix}


nsplit=`ls ${file}-bin0a? | wc | gawk '{printf "%d \n", $0}' | head -n 1`
if [ $nsplit -eq 1 ]
then
    splitlist='aa'
elif [ $nsplit -eq 2 ]
then
    splitlist='aa ab'
elif [ $nsplit -eq 3 ]
then
    splitlist='aa ab ac'
elif [ $nsplit -eq 4 ]
then
    splitlist='aa ab ac ad'
elif [ $nsplit -eq 5 ]
then
    splitlist='aa ab ac ad ae'
elif [ $nsplit -eq 6 ]
then
    splitlist='aa ab ac ad ae af'
elif [ $nsplit -eq 7 ]
then
    splitlist='aa ab ac ad ae af ag'
elif [ $nsplit -eq 8 ]
then
    splitlist='aa ab ac ad ae af ag ah'
elif [ $nsplit -eq 9 ]
then
    splitlist='aa ab ac ad ae af ag ah ai'
elif [ $nsplit -eq 10 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj'
elif [ $nsplit -eq 11 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak'
elif [ $nsplit -eq 12 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al'
elif [ $nsplit -eq 13 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am'
elif [ $nsplit -eq 14 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an'
elif [ $nsplit -eq 15 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao'
elif [ $nsplit -eq 16 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao ap'
elif [ $nsplit -eq 17 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao ap aq'
elif [ $nsplit -eq 18 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao ap aq ar'
elif [ $nsplit -eq 19 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao ap aq ar as'
elif [ $nsplit -eq 20 ]
then
    splitlist='aa ab ac ad ae af ah ai aj ak al am an ao ap aq ar as'
else
    echo 'Not getting split files higher than at!'
    splitlist='aa ab ac ad ae af ah ai aj ak al am an ao ap aq ar as at'
fi

for split in ${splitlist}
  do

  for ((i=0; i<=${phasebins}-1; i++))
    do
    mpsmall=${imroot}'-xx-'${suffix}'-bin'${i}${split}.mp
    bmsmall=${imroot}'-xx-'${suffix}'-bin'${i}${split}.bm
    invert vis=${visroot}'-xx' map=$mpsmall beam=$bmsmall select='@'${file}'-bin'${i}${split} options=double,mfs sup=0 imsize=50,50
    mpsmall=${imroot}'-yy-'${suffix}'-bin'${i}${split}.mp
    bmsmall=${imroot}'-yy-'${suffix}'-bin'${i}${split}.bm
    invert vis=${visroot}'-yy' map=$mpsmall beam=$bmsmall select='@'${file}'-bin'${i}${split} options=double,mfs sup=0 imsize=50,50
  done

  echo
  echo '***Dirty image stats***'

  for ((i=0; i<=${phasebins}-1; i++))
    do
    echo 'Image '${i}':'
    imstat in=${imroot}'-xx-'${suffix}'-bin'${i}${split}.mp | tail -n 2
    imstat in=${imroot}'-yy-'${suffix}'-bin'${i}${split}.mp | tail -n 2
  done

done