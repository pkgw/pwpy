#! /bin/bash

if [ "$2" != xx -a "$2" != yy ] ; then
    echo "Usage: $0 vis polname" 1>&2
    exit 1
fi

uvcat vis="$1" out="$1".cp select="-auto,pol($2)"
selfcal vis="$1".cp options=noscale,amp flux=1.0 interval=30
uvplt device=1/xs axis=uu,am options=nobase vis="$1".cp
uvplt device=2/xs axis=vv,am options=nobase vis="$1".cp
rm -rf "$1".cp
