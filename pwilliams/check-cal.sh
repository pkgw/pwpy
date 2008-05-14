#! /bin/bash

if [ "$2" != xx -a "$2" != yy ] ; then
    echo "Usage: $0 vis polname" 1>&2
    exit 1
fi

uvplt select="-auto,pol($2)" device=1/xs axis=uvdist,am options=nobase vis="$1"
uvplt select="-auto,pol($2)" device=2/xs axis=uvdist,ph options=nobase vis="$1"

