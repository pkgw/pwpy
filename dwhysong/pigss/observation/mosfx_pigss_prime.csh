#!/bin/tcsh -f
# script to observe a list of sources & calibrator in fx16 mode 	jrf - 18jan08
# modified to add multiple sources -- 17aug07 --- gcb
# updated for genobs 02sep07 - jrf
# Added sending of blog post to log.hcro.org - colby 21jan08
# Modified to observe sources until specified interval elapses, then intersperse calibrator - sdc 25jan08
# Source list is search string in catalog.list -- gcb 31jan08
# Copied colby's logident commands from mos16.csh --- gcb 31jan08
# Copied this script from mos16_sdc.csh -- colby 05feb08
# updated to fx64 - jrf 29mar08
# removed obsolete recoveroffnom & added ephem file to atafx - jrf 31oct08
# updated script to accept instrument:group names - jrf 22nov08
# added correlator numonic to dataset names; fixed calls to atafx - jrf 09jan09
# added an extra frot kill - sdc 24mar09
# Modified to accept a list of calibrators - dhw 18nov09
# Modified to pre-generate ephemerides and use atawrapephem - dhw 30nov09
set lo1 = b
set lo2 = a
set inst1 = 'fx64a:fxa'
set inst2 = 'fx64c:fxa'
set subarray = "fxa"
set ucat = /home/obs/dwhysong/pfhex.cat
echo "MOSFX Prime Set to Start!"
onintr fail

if ($#argv < 6) then
  echo "Enter Freq1, Freq2, Source List Match, Cal, Stoptime and Logident (eg: 1420 1430 atat 3c48 8.8 atats)"

  set flt = ($<)
  set freq1 = $flt[1]
  set freq2 = $flt[2]
  set soucmd = "egrep $flt[3]  $ucat"
  set soulist  = `$soucmd | awk '{print $3}'`
  set callist  = $flt[4]
  set stop = $flt[5]
  set logident = $flt[6]
else
  set freq1 = $1
  set freq2 = $2
  set soucmd = "egrep $3  $ucat"
  set soulist  = `$soucmd | awk '{print $3}'`
  set callist  = $4
  set stop = $5
  set logident = $6
endif

echo $soulist

# get required files (copies hookup again every scan below)
cp ~/bin/genswitch .
cp ~/bin/hookup8x1.dat .

set ic1=`echo $inst1 | cut -d: -f1 | gawk -F '' '{print ($NF)}'`   # corr name
set ic2=`echo $inst2 | cut -d: -f1 | gawk -F '' '{print ($NF)}'`   # corr name
set inttime=10      # 10 sec integration time
set switch="`cat genswitch`"     # standard atafx8x1 switches
set elmin=18            # elevation limit 
set durcal=60           # 1 min cal observation
set dursou=180           # 2 min source
set vis1=mosfx{$ic1}      # generic name for mapping run (with corr numonic)
set vis2=mosfx{$ic2}      # generic name for mapping run (with corr numonic)
set calint = 3000       # 50 min between calibrators
spolist.csh $inst1       # make list of antpols in file 'antpols'
set alist = `slist.csh $inst1`
set antpols = `cat antpols`
set pwd = `pwd`

set inst1bw = 104.8576
set inst2bw = 104.8576
# Get the EXACT bandwitdh setting for each correlator
set inst1bw = `ebw.csh $inst1bw | awk '{print $9}'`
set inst2bw = `ebw.csh $inst2bw | awk '{print $9}'`

set finalscan=0     # this is 1 for final observation of calibrator

echo -----------------------------------------------------------
echo  Cal=$callist - Sources=$soulist
echo Freq1=$freq1 LO1=$lo1  Freq2=$freq2 LO2=$lo2 Switch=$switch Stop=$stop
echo  Instrument:group1 = $inst1       group2 = $inst2
echo " ----------------------------------------------------------"

set begin = `date +%T | tr ':' ' ' | awk '{print $1+($2/60)-0.1}'`
set hours = `echo $stop $begin | awk '{if ($1>$2) print $1-$2; else print $1-$2+24}'`
# time last calibrator was observed (start with dummy value)
set lastcal = -99

echo " "
echo " Make ephemeris for each field and calibrator"
echo " "
foreach cal (`echo $callist | tr ',' ' ' | tr '|' ' '`)
  echo Making ephemeris for $cal
  ataephem $cal --utcms --interval 10 --starttime `date -u +%Y-%m-%dT%H:%M:00Z`
  atawrapephem $cal.ephem
end

if ("$soulist" != 'none') then
 foreach sou (`echo $soulist | tr ',' ' ' | tr '|' ' '`)
  if ( ! -r $sou.ephem ) then
    ataephem $sou --utcms --interval 10 --catalog $ucat --starttime `date -u +%Y-%m-%dT%H:%M:00Z`
    atawrapephem $sou.ephem
  endif
 end
else
 echo "No ephemerides needed for source list = $soulist"
endif

echo " "
echo " >>>>>>>>>>>>>>> Observe time is $hours hours <<<<<<<<<<<<<"
echo " "

# Make a note to log.hcro.org
/hcro/ata/scripts/notify-obs-blog.csh $logident "Freq: $freq1" "LO: $lo1" "Antennas: $alist" "Switch: $switch" "Begin: $begin" "Hours: $hours" "Stop: $stop" "SOUList: $soulist" "Cal: $callist" "Dir: $PWD"

# kill frot.rb if it is running
frotkiller.csh >> frot.kill

# set frequency, lnas and pams, focus, attemplifiers, itime, fxlaunch
atalnaon $alist; atasetpams $alist; atasetfocus $alist $freq1 & # Setup antennas
atasetskyfreq $lo1 $freq1 | & tee -ia mosfx.log
atasetskyfreq $lo2 $freq2 | & tee -ia mosfx.log
setintfx.csh $inttime $inst1; fxlaunch $inst1 ; if !(-e autoattenall.$inst1) attenauto.csh $inst1 & # Get correlator set up
setintfx.csh $inttime $inst2; fxlaunch $inst2 ; if !(-e autoattenall.$inst2) attenauto.csh $inst2 & # Get correlator set up

atalockserver lo$lo1 $vis1
atalockserver lo$lo2 $vis2
wait

if (-e autoattenall.log) mv autoattenall.log autoattenall.$inst1
if (-e autoattenall.log) mv autoattenall.log autoattenall.$inst2
waitfocus $alist $freq1; atagetfocus $alist > focus & # wait for focus to reach freq and get value


begin:          # begin infinite loop

  echo "----------------------------------------------------" | & tee -ia mosfx.log
  echo Starting from beginning of sourcelist $soulist, with cal $callist | & tee -ia mosfx.log
  echo "----------------------------------------------------" | & tee -ia mosfx.log

foreach sou (`echo $soulist | tr ',' ' '`)
    set alist = `slist.csh $inst1`
    date | & tee -ia mosfx.log
    if (`stopnow.csh $begin $stop` == 'stop') set finalscan=1
 
    set durhr=`echo $durcal | awk '{print ($1/3600)+.1}'`
    # current time
    set ctime = `date +%s`
    # set docal = 1 if it's time to observe the calibrator
    set docal = `echo $ctime $lastcal $calint | awk '{if ($1 - $2 >= $3) print 1 ; else print 0}'`

    docal:
    if ($docal || $finalscan ) then
	echo -n "Getting a calibrator from $callist... "
	set cal = `/home/obs/dwhysong/getcal.sh $callist`
	echo $cal
	# calibrator ephemeris (no solar system objects)
	radec.csh $cal
	set racal = `awk '{print $4}' radec`
	set deccal = `awk '{print $5}' radec`
	if(`sourceup.csh $racal $deccal $durhr|grep ok` != "ok") then
	    echo "------------------------------------------------"
	    echo "$cal is NOT up - skipping to $sou"
	    echo "------------------------------------------------"
	else  
	    cp ~/bin/hookup8x1.dat .
	    echo "------------------------------------------------"
	    date | & tee -ia mosfx.log
	    echo " moving to cal $cal - observe for $durcal sec"  | tee -ia mosfx.log
	    echo "------------------------------------------------"
	    echo `date +%s`": Starting obs on $cal" >> timelog
	    atatrackephem $alist $cal.ephem -w | & tee -ia track.log ; echo `date +%s`": Antennas on source" >> timelog &
	    frotkiller.csh >> frot.kill; echo `date +%s`": FROT Killed" >> timelog
	    frotnear.csh $inst1 $cal.ephem $freq1 `pwd` start; echo `date +%s`": FROT for $inst1 good" >> timelog &
	    frotnear.csh $inst2 $cal.ephem $freq2 `pwd` start; echo `date +%s`": FROT for $inst2 good" >> timelog &
	    wait
# make a note of when we observed the calibrator
	    set lastcal = `date +%s`
	    set caltimes = `date -u +%y%h%d:%H:%M:%S`

# New code added for speed boost
##################################
	    set timestamp = `date +%s`
	    echo `date +%s`": Catchers start" >> timelog
	    atafx_launch atafx.$inst1.$timestamp $vis1-$cal-$freq1 $antpols $inst1 $cal.ephem -duration $durcal -bw $inst1bw $switch
	    atafx_launch atafx.$inst2.$timestamp $vis2-$cal-$freq2 $antpols $inst2 $cal.ephem -duration $durcal -bw $inst2bw $switch
	    
	    sleep `echo $inttime | awk '{print ($1*3.5)+8}'`
	    set starttime1 = (`grep 'Getting Dump 0' atafx.$inst1.$timestamp | awk '{print $1,$2}'`)
	    set starttime2 = (`grep 'Getting Dump 0' atafx.$inst2.$timestamp | awk '{print $1,$2}'`)
	    if ($#starttime1 == 2) then
		set starttime1 = (`date -d "$starttime1" +%s`)
	    else
		set starttime1 = 0
	    endif
		
	    if ($#starttime2 == 2) then
		set starttime2 = (`date -d "$starttime2" +%s`)
	    else
		set starttime2 = 0
	    endif
	    set currenttime = `date +%s`
	    sleep `echo $currenttime $starttime1 $starttime2 $durcal $inttime | awk '{if (($2 == 0 && $3 == 0) || ($2+$4 < $1+(2*$5) && $3+$4 < $1+(2*$5))) {print 0; next}; if ($2 > $3) {print $2+$4-$1-(2*$5); next}; if ($2 <= $3) {print $3+$4-$1-(2*$5); next}}'`
	    echo `date +%s`": Data in the pipe, moving targets..." >> timelog
	    sleep 30; set caltimes = ($caltimes `date -u +%y%h%d:%H:%M:%S` 0 0); echo "compass $pwd/$vis1-$cal-$freq1 $caltimes[1] $caltimes[2] $inst1" > ~/karto/compass.fx64$ic1; echo "compass $pwd/$vis2-$cal-$freq2 $caltimes[1] $caltimes[2] $inst2" > ~/karto/compass.fx64$ic2 &
####################################
#   if ($status) goto fail

	endif
    endif

## if this is the final calibrator, end 
    if ( $finalscan ) goto finish

    sou:

    if (`stopnow.csh $begin $stop` == 'stop') set finalscan=1
    if ( $finalscan ) goto docal
    set durhr=`echo $dursou | awk '{print ($1/3600)+.1}'` 
    /home/obs/dwhysong/radec.csh $sou $ucat

    set rasou = `awk '{print $4}' radec`
    set decsou = `awk '{print $5}' radec`
    
    if(`sourceup.csh $rasou $decsou $durhr|grep ok` != "ok") then
	echo "------------------------------------------------"
	echo "$sou is NOT up - skipping" 
	echo "------------------------------------------------"
    else
	echo "------------------------------------------------"
	date | & tee -ia mosfx.log
	echo " moving to $sou - observe for $dursou sec"  | tee -ia mosfx.log
	echo "------------------------------------------------"
	echo `date +%s`": Starting obs on $sou" >> timelog
	atatrackephem $alist -w $sou.ephem | & tee -ia track.log ; echo `date +%s`": Antennas on source" >> timelog&
	frotkiller.csh >> frot.kill; echo `date +%s`": FROT Killed" >> timelog
	frotnear.csh $inst1 $sou.ephem $freq1 `pwd` start; echo `date +%s`": FROT for $inst1 good" >> timelog &
	frotnear.csh $inst2 $sou.ephem $freq2 `pwd` start; echo `date +%s`": FROT for $inst2 good" >> timelog &
	wait

	set timestamp = `date +%s`
	echo `date +%s`": Catchers start" >> timelog
	atafx_launch atafx.$inst1.$timestamp $vis1-$sou-$freq1 $antpols $inst1 $sou.ephem -duration $dursou -bw $inst1bw $switch
	atafx_launch atafx.$inst2.$timestamp $vis2-$sou-$freq2 $antpols $inst2 $sou.ephem -duration $dursou -bw $inst2bw $switch

	sleep `echo $inttime | awk '{print ($1*3.5)+8}'`
	    set starttime1 = (`grep 'Getting Dump 0' atafx.$inst1.$timestamp | awk '{print $1,$2}'`)
	    set starttime2 = (`grep 'Getting Dump 0' atafx.$inst2.$timestamp | awk '{print $1,$2}'`)
	if ($#starttime1 == 2) then
	    set starttime1 = (`date -d "$starttime1" +%s`)
	else
	    set starttime1 = 0
	endif
	
	if ($#starttime2 == 2) then
	    set starttime2 = (`date -d "$starttime2" +%s`)
	else
	    set starttime2 = 0
	endif
	set currenttime = `date +%s`
	
	sleep `echo $currenttime $starttime1 $starttime2 $dursou $inttime | awk '{if (($2 == 0 && $3 == 0) || ($2+$4 < $1+(2*$5) && $3+$4 < $1+(2*$5))) {print 0; next}; if ($2 > $3) {print $2+$4-$1-(2*$5); next}; if ($2 <= $3) {print $3+$4-$1-(2*$5); next}}'`
	echo `date +%s`": Data in the pipe, moving targets..." >> timelog
    endif
end             # end loop over mosaic list of sources

goto begin	# end of infinite loop - start at beginning of mosaic list again; must terminate script by finish or fail

finish:
frotnear.csh $inst1 dummy.ephem $freq1 $pwd kill
frotnear.csh $inst2 dummy.ephem $freq2 $pwd kill
ataunlockserver lo$lo1 $vis1
ataunlockserver lo$lo2 $vis2
 rm -f radec check
 echo "-----------------------------------------------------" | tee -ia mosfx.log
 echo "Finished -  the time is `date`, the stop time is $stop" | tee -ia mosfx.log
exit 0

fail:
  ataunlockserver lo$lo1 $vis1
  ataunlockserver lo$lo2 $vis2
  frotnear.csh $inst1 dummy.ephem $freq1 `pwd` kill
  frotnear.csh $inst2 dummy.ephem $freq2 `pwd` kill
  rm -f radec check
  echo "-----------------------------------------------------" | tee -ia mosfx.log
  echo "$00 failed for some reason.  stopping observation" | tee -ia mosfx.log
exit 1
