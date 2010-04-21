#!/bin/bash
if [ $1 ];
  then DIR=$1
  cd $DIR
  echo "Looking in \"$DIR\"..."
else
  if [ -d `archdir`/pigss ] ;
    then DIR=`archdir`/pigss
  elif [ -d `./yesterdays_archdir`/pigss ] ; then
    DIR=`./yesterdays_archdir`/pigss
  else
    echo "Can't find PiGSS data directory. Giving up."
    exit
  fi
    cd $DIR
fi

if [ $2 ];
  then TIME=`date -u +%H:%M`
  DATE=`date -u +%y%b%d`
  SELECTX="-auto,pol(xx),time($DATE:$2,$DATE:$TIME)"
  SELECTY="-auto,pol(yy),time($DATE:$2,$DATE:$TIME)"
else
  SELECTX="-auto,pol(xx)"
  SELECTY="-auto,pol(yy)"
fi

FILES=`ls -d mosfx?-3[cC]*`

for i in $FILES ; do
  echo uvspec interval=10 device=/xs select="$SELECTX" nxy=8,8 axis=cha,pha vis="$i"
  uvspec interval=10 device=/xs select="$SELECTX" nxy=8,8 axis=cha,pha vis="$i"
  echo uvspec interval=10 device=/xs select="$SELECTY" nxy=8,8 axis=cha,pha vis="$i"
  uvspec interval=10 device=/xs select="$SELECTY" nxy=8,8 axis=cha,pha vis="$i"
done
