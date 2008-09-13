#! /bin/sh

first=true

for i in "$@" ; do
    $first || read foo
    first=false
    echo $i
    cgdisp device=1/xs options=wedge in=$i >/dev/null
done
