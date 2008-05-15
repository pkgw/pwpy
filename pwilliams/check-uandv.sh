#! /bin/bash
#
# Plot amplitude as a function of U and V, to check how
# big a deal time-smearing is on the given dataset.
#
# Usage: check-uandv.sh [vis] [pol]
#
# where we select only the specified polarization.

v="$1"
shift
pol="$1"
shift

if [ "$pol" != xx -a "$pol" != yy ] ; then
    echo "Usage: $0 vis polname ..." 1>&2
    exit 1
fi

uvplt select="-auto,pol($pol)" device=1/xs axis=uu,am options=nobase vis=$v "$@"
uvplt select="-auto,pol($pol)" device=2/xs axis=vv,am options=nobase vis=$v "$@"
