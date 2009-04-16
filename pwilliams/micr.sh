#! /bin/bash
#
# Multi-file Invert, Clean, Restore.
#
# Generate an image from several vis files. Unlike icr.sh,
# no polarization filtering is performed.
#
# Usage: micr.sh [vis1] [vis2] [vis3] ....
#
# Output files are
#
# [vis1].mp - Raw map
# [vis1].bm - Beam
# [vis1].cl - Cleaned map
# [vis1].rm - Restored map

vis="$1"
mp="$1".mp
bm="$1".bm
cl="$1".cl
rm="$1".rm
shift

while [ $# -gt 0 ] ; do
    vis="$vis,$1"
    shift
done

set -e -x

rm -rf $mp $bm $cl $rm
invert vis=$vis map=$mp beam=$bm select=-auto options=double,mfs,systemp sup=0
clean map=$mp beam=$bm out=$cl niters=5000
restor map=$mp beam=$bm model=$cl out=$rm
