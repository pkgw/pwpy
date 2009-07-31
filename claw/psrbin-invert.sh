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
timebins="$4"
imsize="$5"

echo
echo '***Imaging time bins***'
echo

#set -e -x  # for debugging
file='time-'${suffix}

nsplit=`ls ${file}-on0a? | wc | gawk '{printf "%d \n", $0}' | head -n 1`
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

  for ((i=0; i<=${timebins}-1; i++))
    do
    mpsmall=${imroot}'-xx-'${suffix}'-on'${i}${split}.mp
    bmsmall=${imroot}'-xx-'${suffix}'-on'${i}${split}.bm
    invert vis=${visroot}'-xx' map=$mpsmall beam=$bmsmall select='@'${file}'-on'${i}${split} options=double,mfs sup=0 imsize=${imsize},${imsize}
    mpsmall=${imroot}'-yy-'${suffix}'-on'${i}${split}.mp
    bmsmall=${imroot}'-yy-'${suffix}'-on'${i}${split}.bm
    invert vis=${visroot}'-yy' map=$mpsmall beam=$bmsmall select='@'${file}'-on'${i}${split} options=double,mfs sup=0 imsize=${imsize},${imsize}
  done
done

for ((i=0; i<=${timebins}-1; i++))
  do
  mpsmall=${imroot}'-xx-'${suffix}'-avg'${i}.mp
  bmsmall=${imroot}'-xx-'${suffix}'-avg'${i}.bm
  invert vis=${visroot}'-xx' map=$mpsmall beam=$bmsmall select='@'${file}'-avg'${i} options=double,mfs sup=0 imsize=${imsize},${imsize}
  mpsmall=${imroot}'-yy-'${suffix}'-avg'${i}.mp
  bmsmall=${imroot}'-yy-'${suffix}'-avg'${i}.bm
  invert vis=${visroot}'-yy' map=$mpsmall beam=$bmsmall select='@'${file}'-avg'${i} options=double,mfs sup=0 imsize=${imsize},${imsize}
done