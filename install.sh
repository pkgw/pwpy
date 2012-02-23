#! /bin/bash
#
# Life is good when installation is so simple.

if [ ! -f instdest ] ; then
    echo >&2 "error: create a file named 'instdest' specifying the install destination."
    exit 1
fi

if [ x"$1" = x-v ] ; then
    vee=v
fi

dest=`cat instdest`
dest=`eval echo $dest`
set -e

mkdir -p$vee $dest/bin $dest/share/quickutil
cp -p$vee quembed $dest/bin

for util in utils/*.py ; do
    d="$dest/share/quickutil/$(basename $util)"

    if [ x$vee = xv ] ; then
	echo '(gen)' $util '->' "$d"
    fi

    echo '#- snippet:' $(basename $util) >"$d"
    echo '#- date:' $(date -r $util +'%Y %b %d') >>"$d"
    echo '#- SHA1:' $(sha1sum $util |cut -d' ' -f1) >>"$d"
    cat $util >>"$d"
done
