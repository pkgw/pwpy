#! /bin/bash
#
# Check the calibration applied to a dataset, by plotting
# amplitude and phase versus UV distance to see if they look
# nice and flat.
#
# Usage: check-cal.sh [visname] [pol]
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

uvplt select="$autosel" device=1/xs axis=uvdist,am options=nobase vis="$vis" "$@"
uvplt select="$autosel" device=2/xs axis=uvdist,ph options=nobase vis="$vis" "$@"

