#! /bin/bash
#
# "Check SelfCal'ed U and V". Make a temporary copy of the data
# set, selfcal it, and plot amplitude versus U and V. A quick
# way to see how bad the time-smearing is affecting a given 
# dataset.
#
# Usage: check-scuv.sh [vis] [pol]
#
# where we select only the specified polarization.

if [ "$2" != xx -a "$2" != yy ] ; then
    echo "Usage: $0 vis polname" 1>&2
    exit 1
fi

uvcat vis="$1" out="$1".cp select="-auto,pol($2)"
selfcal vis="$1".cp options=noscale,amp flux=1.0 interval=30
uvplt device=1/xs axis=uu,am options=nobase vis="$1".cp
uvplt device=2/xs axis=vv,am options=nobase vis="$1".cp
rm -rf "$1".cp
