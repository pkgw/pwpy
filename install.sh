#! /bin/bash

if [ ! -f instdest ] ; then
    echo "Create a file named 'instdest' specifying the install destination." >&2
    exit 1
fi

dest=`cat instdest`
dest=`eval echo $dest`
set -e
cp -vp *.py *.glade $dest
