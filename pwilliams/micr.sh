#! /bin/bash

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
invert vis=$vis map=$mp beam=$bm select=-auto options=double,mfs sup=0
clean map=$mp beam=$bm out=$cl niters=5000
restor map=$mp beam=$bm model=$cl out=$rm
