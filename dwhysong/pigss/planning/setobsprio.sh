#!/bin/bash

if [ -z $PIGSS_DATABASE ]; then
  PIGSS_DATABASE=/etc/observatory/schedule
else
  echo "Warning: using nonstandard database $PIGSS_DATABASE"
fi

if [ $# == 0 ];
  then echo "Usage: setobsprio.sh [filename] [priority]"
  echo "Example: setobsprio.sh pigss.targets 4"
  exit
fi
FIELDS=`cat $1`
if [ $2 ];
  then PRIO=$2
else
  PRIO=0;
fi
for x in $FIELDS;
  do if [ "lockman" != $x ]; then
    echo Set priority $x = $PRIO
    /home/dwhysong/pigss/schedule.pl -p "$x"="$PRIO" -f $PIGSS_DATABASE
  fi
done
