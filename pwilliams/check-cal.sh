#! /bin/bash
#
# Check the calibration applied to a dataset, by plotting
# amplitude and phase versus UV distance to see if they look
# nice and flat.
#
# Usage: check-cal.sh [visname] [pol]
#
# where we select only the specified polarization.

if [ "$2" != xx -a "$2" != yy ] ; then
    echo "Usage: $0 vis polname" 1>&2
    exit 1
fi

uvplt select="-auto,pol($2)" device=1/xs axis=uvdist,am options=nobase vis="$1"
uvplt select="-auto,pol($2)" device=2/xs axis=uvdist,ph options=nobase vis="$1"

