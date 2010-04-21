#!/bin/sh

for i in 0 2 4; do
	DATE=`date +%d/%m/%Y --date="$i days"`
	TIME=6:0:0
	./schedule.pl -g -n20000 -e 14 -t $DATE/$TIME | tee sim/possible."$i"
	head -n 28 sim/possible."$i" > sim/targets."$i"
	for x in `cat sim/targets."$i"` ;
		do ./schedule.pl -p "$x"=0
	done
done

i=5
DATE=`date +%d/%m/%Y --date="$i days"`
TIME=6:30:0
./schedule.pl -g -n20000 -e 14 -t $DATE/$TIME | tee sim/possible."$i"
head -n 28 sim/possible."$i" > sim/targets."$i"
for x in `cat sim/targets."$i"` ;
	do ./schedule.pl -p "$x"=0
done
