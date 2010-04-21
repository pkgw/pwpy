#!/bin/bash

if [ -f pigss.targets ] ;
then
  echo "Warning: pigss.targets exists."
  echo "Before runing this script, be sure that observed fields have zero priority in the database."
  exit
fi

if [ $# == 1 ];
  then DATE=$1
else
  DATE=`date +%d/%m/%Y`
fi
DATE2=`echo $DATE | tr '/' '-'`

echo -n "Enter start time (default 23:0:0): "
read STARTTIME
echo -n "Enter end time (default 7): "
read ENDTIME
echo -n "Enter number of fields (default 50): "
read NFIELDS

if [ -z $NFIELDS ] ;
  then NFIELDS=50
fi

if [ -z $STARTTIME ] ;
  then STARTTIME="23:0:0"
fi

if [ -z $ENDTIME ] ;
  then ENDTIME=7
fi

if [ -z $PIGSS_DATABASE ]; then
  PIGSS_DATABASE=/etc/observatory/schedule
else
  echo "Warning: using nonstandard database $PIGSS_DATABASE"
fi
if [ -z $PIGSS_CATALOG ]; then
  PIGSS_CATALOG=/home/dwhysong/pigss/.tmp/pigss2.fields
else
  echo "Warning: using nonstandard catalog $PIGSS_CATALOG"
fi
PLOTARGS="-m $PIGSS_CATALOG"
SCHEDARGS="-d -f$PIGSS_DATABASE -t$DATE/$STARTTIME -e$ENDTIME"
echo Using: schedule.pl $SCHEDARGS -g -n50000
PIGSS=/home/dwhysong/pigss
PATH=`pwd`:$PATH
if [ ! -d .tmp ] ; then mkdir .tmp ; fi
pushd .tmp
rm -f unobs unobs2 obs new pos ds9.reg possible observed targets
schedule.pl $SCHEDARGS -g -n50000 > possible
schedule.pl $SCHEDARGS -l | grep prio=0 | cut -f3 -d= | cut -f1 -d' ' > observed
plotfields.pl $PLOTARGS -c red -f possible -o ds9.reg > /dev/null
plotfields.pl $PLOTARGS -c yellow -f observed -o ds9.reg > /dev/null

# Make list of unobserved fields (blue)
cat possible observed > all
cat $PIGSS_CATALOG | cut -f1 > unobs2
cat all unobs2 | sort | uniq -u > unobs
plotfields.pl $PLOTARGS -c blue -f unobs -o ds9.reg > /dev/null

/sbin/getkey -m "Press a key for graphical display: "
echo
ds9 -geometry 2000x1000 -cmap BB -log -fits nvss.fits -zoom 0.8 -regions load ds9.reg -regions showtext no &
echo -n "Enter primary target field name: "
read NAME
schedule.pl $SCHEDARGS -p "$NAME"=5
schedule.pl $SCHEDARGS -g -n"$NFIELDS" | sort -n > targets
schedule.pl $SCHEDARGS -p "$NAME"=4
cat ds9.reg | fgrep -vf targets > tmp
mv tmp ds9.reg
plotfields.pl $PLOTARGS -c green -f targets -o ds9.reg > /dev/null
popd
/sbin/getkey -m "Press a key for graphical display: "
echo
cp .tmp/ds9.reg status/pigss-$DATE2.reg
ds9 -geometry 2000x1000 -cmap BB -log -fits nvss.fits -zoom 0.8 -regions load .tmp/ds9.reg -regions showtext no
ln .tmp/targets pigss.targets
ln pigss.targets pigss.targets-$DATE2
echo "Writing: pigss.targets-$DATE2"
