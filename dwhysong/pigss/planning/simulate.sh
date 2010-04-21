#!/bin/bash
./schedule.pl -i
./schedule.pl -a < pigss_ngalcap.catalog.list

for i in `seq 1 4 40`; do
	DATE=`date +%d/%m/%Y --date="$i days"`
	TIME=6:0:0
	echo $DATE
	./schedule.pl -g -n20000 -e 14 -t $DATE/$TIME | tee sim/possible."$i"
	head -n 28 sim/possible."$i" > sim/targets."$i"
	for x in `cat sim/targets."$i"` ;
		do ./schedule.pl -p "$x"=0
	done

	j=$i
	let j++
	DATE=`date +%d/%m/%Y --date="$j days"`
	TIME=6:0:0
	echo $DATE
	./schedule.pl -g -n20000 -e 14 -t $DATE/$TIME | tee sim/possible."$j"
	head -n 28 sim/possible."$j" > sim/targets."$j"
	for x in `cat sim/targets."$j"` ;
		do ./schedule.pl -p "$x"=0
	done
done
