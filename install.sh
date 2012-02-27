#! /bin/bash

# Installation is configured with a shell script fragment called 'config.
# It should set these variables: prefix
# It may set: 
#  casaprefix - to install casa-python wrapper
#  mirpysrc - to install example programs from miriad-python

if [ ! -f config ] ; then
    echo >&2 "Create a file called 'config' with the install configuration."
    exit 1
fi

source ./config

if [ x"$prefix" = x ] ; then
    echo >&2 "error: no install prefix configured"
    exit 1
fi

if [ ! -d $prefix/lib/python/site-packages ] ; then
    echo >&2 "error: setup symlinks to create $prefix/lib/python/site-packages"
    exit 1
fi

if [ x"$1" = x-v ] ; then
    vee=v
    echo=echo
else
    vee=
    echo=:
fi

# Programs

for bindir in scibin intfbin ; do
    install -C$vee -m755 -t $prefix/bin $bindir/*[^~]
done

# Python modules

for libdir in pylib scilib intflib ; do
    install -C$vee -m644 -t $prefix/lib/python/site-packages $libdir/*.py
done

# Quickutils

mkdir -p$vee $prefix/share/quickutil
install -C$vee -m755 -t $prefix/bin quickutils/quembed

for util in quickutils/utils/*.py ; do
    d="$prefix/share/quickutil/$(basename $util)"

    if [ x$vee = xv ] ; then
	echo '(gen)' $util '->' "$d"
    fi

    echo '#- snippet:' $(basename $util) >"$d"
    echo '#- date:' $(date -r $util +'%Y %b %d') >>"$d"
    echo '#- SHA1:' $(sha1sum $util |cut -d' ' -f1) >>"$d"
    cat $util >>"$d"
    chmod 644 "$d"
done

# casa-python

if [ x"$casaprefix" = x ] ; then
    cp -p$vee intfmisc/casa-python.fail $prefix/bin/casa-python
else
    $echo "Creating $prefix/bin/casa-python."
    sed -e "s|%casa%|$casaprefix|g" <intfmisc/casa-python.in >$prefix/bin/casa-python
    chmod 755 $prefix/bin/casa-python
fi

# miriad-python examples

if [ x"$mirpysrc" != x ] ; then
    install -C$vee -m755 $mirpysrc/examples/gpcat $prefix/bin
    install -C$vee -m755 $mirpysrc/examples/rtft $prefix/bin
    install -C$vee -m755 $mirpysrc/examples/varcat $prefix/bin
    cat $mirpysrc/examples/chanaver.py intfmisc/chanaver-arf-support.py \
	>$prefix/lib/python/site-packages/chanaver.py
    chmod 644 $prefix/lib/python/site-packages/chanaver.py
fi

# Data file for ATA bandpass correction

install -C$vee -m644 intfmisc/hhaa.dat $prefix/lib/python/site-packages
