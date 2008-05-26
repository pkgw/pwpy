#! /bin/sh -e

src="$1"
freq="$2"
radec="$3"
ndumps="$4"
outbase="$5"

dir=`pwd`

ssh -x x2.fxa \
 "cd '$dir' && fxmir.rb -s '$src' -f $freq -r '$radec' fx64a '${outbase}_1' $ndumps" &
ssh -x x1.fxa \
 "cd '$dir' && fxmir.rb -s '$src' -f $freq -r '$radec' fx64a '${outbase}_2' $ndumps"
wait
exit 0
