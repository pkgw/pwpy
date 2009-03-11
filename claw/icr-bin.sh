#! /bin/bash
#
# Usage: micr.sh vis1
#
# Output files are
#
# *.mp Raw map
# *.bm Beam

vis="$1"
half='ab'

for ((i=0; i<=7; i++))
do
  mpsmall=${vis}-bin${i}${half}.mp
  bmsmall=${vis}-bin${i}${half}.bm
  invert vis=$vis map=$mpsmall beam=$bmsmall select='@time-bin'${i}${half} options=double,mfs sup=0 imsize=78,78
#  clean map=$mp beam=$bm out=$cl niters=3000
#  restor map=$mp beam=$bm model=$cl out=$rmsmall
#  rm -rf $mp $bm $cl
done