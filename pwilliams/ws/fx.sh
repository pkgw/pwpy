#! /bin/bash
#
# FX calibrate raw data into pol-separated files.

. common.sh

rm -f fx.list

for raw in $raw/$rawglob ; do
    b=`basename $raw`
    src=`echo $b |cut -d- -f$srcitem`
    freq=`echo $b |cut -d- -f$freqitem`

    for pol in xx yy ; do
	sfp=$src-$freq-$pol

	echo $sfp
	
	rm -rf $sfp $sfp.tmp
	shhcmd fxcal.py vis=$raw select="pol($pol)" out=$sfp.tmp
	shhcmd uvcat select=-auto vis=$sfp.tmp out=$sfp

	echo $sfp >>fx.list
	echo $src >$sfp/ws-src
	echo $freq >$sfp/ws-freq
	echo $pol >$sfp/ws-pol

	rm -rf $sfp.tmp
    done
done

exit 0
