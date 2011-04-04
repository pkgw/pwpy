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
iquv
mirargmerge
pg2eps
polsplit
pwflag
show
sortinplace
tiam
tiph
ucvc
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
fancy/applytsys
fancy/atabpass
fancy/ataglue.py
fancy/atanudgetime
fancy/box-fitpoint
fancy/box-overlay
fancy/box-region
fancy/byant
fancy/calctsys
fancy/chanaver
fancy/closanal
fancy/dualscal
fancy/fxcal.py
fancy/gpcat
fancy/gpmergepols
fancy/gpunity
fancy/multiflag2
fancy/pwflux
fancy/pwmodel
fancy/qimage
fancy/uvasimg
fancy/varcat
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
pylib/chanaver.py
pylib/closanal.py
pylib/dualscal.py
pylib/gpmergepols.py
pylib/hhaa.dat
pylib/multiflag.py
pylib/multiflag2.py
pylib/numutils.py
pylib/pwflux.py
pylib/pwmodel.py
'

set -e
cp -vp $programs $pfx/bin
cp -vp $modules $pfx/lib/python/site-packages
