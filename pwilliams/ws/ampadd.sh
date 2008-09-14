#! /bin/bash
#
# Generate ampadd output files for all of our data.

. common.sh

freqs=`./index-list.py fx.list freq "$@"`

for freq in $freqs ; do
    vises=$(./comma.py $(./filter-list.py fx.list freq=$freq))
    shhcmd ampadd.py vis=$vises log=rfi-$freq.txt
done
