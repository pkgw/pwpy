#!/bin/bash -l

export PATH=/home/obs/pigss2/bin:/home/obs/mmm/karto/RAPIDBeta:/home/obs/mmm/karto/cals:$PATH

cd /export/data1/dwhysong

SOURCEDIR=`archdir`/pigss
YY=`date +%y`
MM=`date +%m`
DD=`date +%d`
if [ ! -e $SOURCEDIR ] ;
  then SOURCEDIR=`yesterdays_archdir`/pigss
  YY=`date -d yesterday +%y`
  MM=`date -d yesterday +%m`
  DD=`date -d yesterday +%d`
fi

TARGETDIR="/export/data1/dwhysong/"$DD$MM$YY

mkdir $TARGETDIR
cd $TARGETDIR
ls -d $SOURCEDIR/mosfx?-* | sed 's/^/cp -rf /' | sed 's/$/ . /' > uvshadow.csh
source uvshadow.csh 2>&1 > autoreduce.log 
cp $SOURCEDIR/pigss.targets $TARGETDIR
reduce.pl -cf 2>&1 >> autoreduce.log
