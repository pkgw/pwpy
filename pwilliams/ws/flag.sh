#! /bin/bash
#
# Apply multiflag commands to all files

. common.sh

for v in `./filter-list.py fx.list "$@"` ; do
    src=`cat $v/ws-src`
    freq=`cat $v/ws-freq`
    pol=`cat $v/ws-pol`

    echo $v ...
    shhcmd multiflag2 spec='*.mf' pol=$pol freq=$freq vis=$v
done
