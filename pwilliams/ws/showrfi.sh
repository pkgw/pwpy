#! /bin/sh

if [ ! -f "$1" ] ; then
    echo "Usage: $0 [rfi-NNNN.txt]" 1>&2
    exit 1
fi

echo "plot '$1' using 1:3 with lines" |gnuplot -persist -

