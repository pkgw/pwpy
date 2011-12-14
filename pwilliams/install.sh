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

if [ x"$1" = x-v ] ; then
    vee=v
    echo=echo
else
    vee=
    echo=:
fi

programs='
atastdflag
C
chbo
imrms
iquv
mirargmerge
pg2eps
polsplit
pwflag
pwimage2fits
pwimage2mir
sfind-to-lsm
sfind-to-olay
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
fancy/applytsys
fancy/atabpass
fancy/ataglue.py
fancy/atanudgetime
fancy/blink
fancy/box-fitpoint
fancy/box-overlay
fancy/box-region
fancy/box-topointmdl
fancy/byant
fancy/calctsys
fancy/calnoise
fancy/chanaver
fancy/checkshadow
fancy/cloplot
fancy/closanal
fancy/dualscal
fancy/fxcal.py
fancy/gpcat
fancy/gpmergepols
fancy/gptext
fancy/gpunity
fancy/mdl-makeimage
fancy/pwflux
fancy/pwmodel
fancy/pwshow
fancy/qimage
fancy/rtft
fancy/showgains
fancy/uvasimg
fancy/varcat
ms/mfsimager
ms/msclearimaging
ms/msconcat
ms/mshistory
ms/msimgadd
ms/msimgen
ms/msimsquash
ms/msimsub
ms/msmirhack
ms/mssetupimaging
ms/mssfextract
ms/mswpftsub
'

modules='
pyata/atactl.py
pyata/ataprobe.py
pyata/calibrators.py
pyata/fxlaunch.sh
pylib/ata2mir.py
pylib/atabpass.py
pylib/calctsys.py
pylib/calnoise.py
pylib/chanaver.py
pylib/closanal.py
pylib/dualscal.py
pylib/gpmergepols.py
pylib/gptext.py
pylib/hhaa.dat
pylib/numutils.py
pylib/pwflux.py
pylib/pwmodel.py
'

set -e
cp -p$vee $programs $pfx/bin
cp -p$vee $modules $pfx/lib/python/site-packages

if [ -f casapfx ] ; then
    $echo "Creating $pfx/bin/casa-python."
    casa=`cat casapfx`
    casa=`eval echo $casa`
    sed -e "s|%casa%|$casa|g" <ms/casa-python.in >$pfx/bin/casa-python
    chmod 755 $pfx/bin/casa-python
else
    cp -p$vee ms/casa-python.fail $pfx/bin/casa-python
fi
