#! /bin/bash
#
# Divide the FX-caled and flagged data files into
# separate epochs.

. common.sh

rm -f ep.list

if [ ! -f epochbdys.tab ] ; then
    echo "No epochbdys.tab -- assuming all one epoch."

    for v in `./filter-list.py fx.list "$@"` ; do
	echo $v ...

	d=$v-noep
	rm -rf $d
	shhcmd uvcat options=unflagged vis=$v out=$d
	cp $v/ws* $d
	echo noep >$d/ws-epoch
	echo $d >>ep.list
    done
else
    for v in `./filter-list.py fx.list "$@"` ; do
	echo $v ...

	curep=1
	tmin='60JAN01:0:0:0'

	for bdtime in `cat epochbdys.tab` ; do
	    d=$v-$curep
	    rm -rf $d
	    shhcmd uvcat options=unflagged vis=$v out=$d \
		select="time($tmin,$bdtime)"
	    cp $v/ws* $d
	    echo $curep >$d/ws-epoch
	    echo $d >>ep.list

	    curep=`expr $curep + 1`
	    tmin="$bdtime"
	done

	tmax=`date -u +'%y%b%d:%H:%M:%S'`
	d=$v-$curep
	rm -rf $d
	shhcmd uvcat options=unflagged vis=$v out=$d \
	    select="time($tmin,$tmax)"
	cp $v/ws* $d
	echo $curep >$d/ws-epoch
	echo $d >>ep.list
    done
fi
