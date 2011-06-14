#! /bin/bash
#
# Life is good when installation is so simple.

if [ ! -f instdest ] ; then
    echo "Create a file named 'instdest' specifying the install destination." >&2
    exit 1
fi

if [ x"$1" = x-v ] ; then
    vee=v
fi

dest=`cat instdest`
dest=`eval echo $dest`
set -e
cp -p$vee *.py $dest
