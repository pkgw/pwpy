#! /bin/bash
#
# Install the scripts and Python modules in MMM/pwilliams into other directories;
# this helps reduce the proliferation of $PYTHONPATH entries, at the expense of
# having to remember to reinstall.

if [ ! -f instpfx ] ; then
    echo "Create a file called 'instpfx' with the install prefix." >&2
    exit 1
fi

pfx=`cat instpfx`
pfx=`eval echo $pfx`

programs='
atastdflag
C
chbo
icr.sh
micr.sh
mirargmerge
pg2eps
polsplit
pwflag
show
sortinplace
tiph
uvdam
uvdph
uvlock
uvlwcp
uvlwrevert
uvrevert
walsh_adc_conflict.sh
walsh-flags.py
fancy/ampadd.py
fancy/amprfi
fancy/atabpass
fancy/ataglue.py
fancy/byant
fancy/calctsys
fancy/closanal
fancy/fxcal.py
fancy/gpcat
fancy/gpunity
fancy/multiflag2
fancy/qimage
fancy/uvasimg
fancy/varcat.py
'

modules='
pyata/atactl.py
pyata/ataprobe.py
pyata/calibrators.py
pyata/fxlaunch.sh
pyata/rfi.py
pylib/amprfi.py
pylib/ata2mir.py
pylib/atabpass.py
pylib/blflag.py
pylib/blmapper.glade
pylib/calctsys.py
pylib/closanal.py
pylib/hhaa.dat
pylib/multiflag.py
pylib/multiflag2.py
'

set -e
cp -vp $programs $pfx/bin
cp -vp $modules $pfx/lib/python/site-packages
