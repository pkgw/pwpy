#!/bin/bash

if [ $1 ];
  then CALLIST="`echo $1 | tr '|' ' '`"
else
  CALLIST="3C147 3C286 3C48"
fi

for CAL in $CALLIST; do
  RADEC=`radec.csh $CAL | tr -s ' ' | cut -f 4,5 -d ' '`
  ISUP=`sourceup.csh $RADEC 0.02`
  if [ $ISUP ];
    then echo $CAL
    exit
  fi
done
echo "none"
