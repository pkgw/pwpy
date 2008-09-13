#! /bin/bash
#
# Run self-calibrations on data files. Does both
# bandpass and mselfcal.

. common.sh

rm -f mf.list

for v in `./filter-list.py fx.list src=$cal "$@"` ; do
    freq=`cat $v/ws-freq`
    flux=`cat calfluxes.tab |grep "^$cal $freq" |cut -d' ' -f3`
    echo $v : flux $flux ...

    # Mfcal

    cmd smamfcal options=opoly polyfit=7 refant=3 line=chan,824,101 \
	vis=$v
    
    # UVcat to preserve gains
    mf="${v}.mf"
    rm -rf $mf
    shhcmd uvcat vis=$v out=$mf options=unflagged
    cp $v/ws-* $mf
    echo $mf >>mf.list

    # Self-cal

    cmd mselfcal options=amp,nosc flux=$flux vis=$mf

    # Puthd
    shhcmd puthd type=double value=0.5 in=$mf/interval
done
