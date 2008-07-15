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

vis="$1"
shift

if echo $vis |egrep '(xx|yy)' >/dev/null ; then
    autosel="-auto"
else
    pol="$1"
    shift

    if [ "$pol" != xx -a "$pol" != yy ] ; then
	echo "Usage: $0 vis polname" 1>&2
	exit 1
    fi

    autosel="-auto,pol($pol)"
fi

uvcat vis="$vis" out="$vis".cp select="$autosel"
selfcal vis="$vis".cp options=noscale,amp flux=1.0 interval=30
uvplt device=1/xs axis=uvdist,am options=nobase vis="$vis".cp "$@"
uvplt device=2/xs axis=uvdist,ph options=nobase vis="$vis".cp "$@"
rm -rf "$vis".cp
