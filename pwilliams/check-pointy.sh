#! /bin/bash
#
# Check how much uncalibrated data looks like a point source.
# We make a temporary copy of the dataset, selfcal it to 
# a point source with flux=1, and then plot amplitudes and
# phases as a function of uvdistance.
#
# Usage: check-pointy.sh [vis] [pol]
#
# where we select only the specified polarization.

if [ "$2" != xx -a "$2" != yy ] ; then
    echo "Usage: $0 vis polname" 1>&2
    exit 1
fi

uvcat vis="$1" out="$1".cp select="-auto,pol($2)"
selfcal vis="$1".cp options=noscale,amp flux=1.0 interval=30
uvplt device=1/xs axis=uvdist,am options=nobase vis="$1".cp yrange=0,2
uvplt device=2/xs axis=uvdist,ph options=nobase vis="$1".cp
rm -rf "$1".cp
