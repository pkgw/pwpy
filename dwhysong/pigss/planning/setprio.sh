#!/bin/bash

if [ -z $PIGSS_DATABASE ]; then
  PIGSS_DATABASE=/etc/observatory/pfhex
fi

if [ $# == 0 ];
  then echo "Usage: setprio.sh [filename] [priority]"
  echo "Example: setprio.sh pigss.targets 4"
  exit
fi
FIELDS=`cat $1 | grep pfhex`
STR='';
if [ $2 ];
  then PRIO=$2
else
  PRIO=3;
fi
for x in $FIELDS; do
    STR="-p $x=$PRIO $STR"
    echo Set priority $x = $PRIO
done
/home/dwhysong/pigss/schedule.pl -f $PIGSS_DATABASE $STR
