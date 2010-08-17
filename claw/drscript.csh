#!/usr/bin/env tcsh

foreach n ( `gawk '{printf("%s\n",$1)}' times2` )
    set file = `ls -df day1-1430-hires/mosfxa-NVSS${n}-1430-100.icln day2-1430-hires/mosfxa-NVSS${n}-1430-100-flagged2.icln`
    if ( $file != '' ) then
	set ipeak = `imstat in=$file | tail -n 1 | gawk '{printf("%.3f\n",$4)}'`
	set isig = `imstat in=$file region='relpix,boxes(-400,-400,-100,-100)' | tail -n 1 | gawk '{printf("%.3f\n",$3)}'`
	set psig = `imstat in=$file:r.pcln region='relpix,boxes(-400,-400,-100,-100)' | tail -n 1 | gawk '{printf("%.3f\n",$3)}'`
	set theory = `grep $n times2 | gawk '{printf("%.3f\n",0.008/$2^0.5)}'`
	set dri = `echo $ipeak/$isig | bc`
	set drp = `echo $ipeak/$psig | bc`
	echo $n, $ipeak, $isig, $psig, $theory, $dri, $drp
    endif
end
