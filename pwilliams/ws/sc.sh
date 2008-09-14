#! /bin/bash
#
# Run self-calibrations on data files. Does both
# bandpass and mselfcal.

. common.sh

rm -f sc.list

if [ ! -f calfluxes.tab ] ; then
    echo "Error: need table of cal fluxes called calfluxes.tab" 1>&2
    echo "See pw-make-cal-table if you have calmodels.py" 1>&2
    exit 1
fi

for v in `./filter-list.py ep.list src=$cal "$@"` ; do
    freq=`cat $v/ws-freq`
    flux=`cat calfluxes.tab |grep "^$cal $freq" |cut -d' ' -f3`
    echo $v : flux $flux ...

    # Mfcal

    cmd smamfcal options=opoly polyfit=7 refant=3 line=chan,824,101 \
	vis=$v
    
    # UVcat to preserve gains
    sc="${v}.sc"
    rm -rf $sc
    shhcmd uvcat vis=$v out=$sc options=unflagged
    cp $v/ws-* $sc
    echo $sc >>sc.list

    # Self-cal

    cmd mselfcal options=amp,nosc flux=$flux vis=$sc

    # Puthd
    shhcmd puthd type=double value=0.5 in=$sc/interval
done
