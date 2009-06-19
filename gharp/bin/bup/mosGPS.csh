#!/bin/tcsh -f
# script to observe a list of sources & calibrator in fx64 mode - jrf 29mar08
# modified to add multiple sources -- 17aug07 --- gcb
# updated for genobs 02sep07 - jrf
# Added sending of blog post to log.hcro.org - cgk 21jan08
# Added parameter for log book identification purposes - cgk 25jan08
# updated to fx64 - jrf 29mar08
# updated to fringe rotation - jrf 12apr08
# simplified code - added frot.csh, multiple cals & durations - jrf 18apr08
# modified to accept instrument:group for corr a,b,c,d - jrf & DavidM 20nov08
# changed generic name to include corr (eg: mosfxa)

onintr fail

set dump64 = 5       # 5 sec fx correlator integration time

# get required inputs (sou & cal times in seconds; stop time in local hrs)

if ($#argv < 10) then
  echo "Enter Freq LO SourceList Soutime Cal Caltime Stoptime name Inst:grp bw (eg: 1430 b m31-1,m31-2,m31-3 1200 3c48 60 8.8 m31 fx64a:fxa 104)"
  set flt      = ($<)
  set freq     = $flt[1]
  set lo       = $flt[2]
  set soulist  = $flt[3]
  set dursou   = $flt[4]
  set callist  = $flt[5]
  set durcal   = $flt[6]
  set stop     = $flt[7]
  set logident = $flt[8]
  set inst     = $flt[9]
  set bw       = $flt[10]
else
  set freq     = $1
  set lo       = $2
  set soulist  = $3
  set dursou   = $4
  set callist  = $5
  set durcal   = $6
  set stop     = $7
  set logident = $8
  set inst     = $9
  set bw       = $10
endif

if ($bw != "") then
    bw.csh $inst $bw
endif
 
set caldump=`echo $durcal $dump64 | awk '{printf "%3.0f",$1/$2}'`   # dumps for fxmir
set soudump=`echo $dursou $dump64 | awk '{printf "%3.0f",$1/$2}'`   # dumps for fxmir

# get required files (copies hookup again every scan below)

cp ~/bin/genswitch .

set ic=`echo $inst | cut -d: -f1 | gawk -F '' '{print ($NF)}'` # corr name
set vis=mosfx{$ic}               # generic name for mapping run
set switch="`cat genswitch`"     # standard atafx switches
set pswitch                      # for planets (use -ephem switch)
set elmin=18                     # elevation limit 
set alist=`slist.csh $inst`      # list of antennas in group
set pwd = `pwd`                  # current working directory for fxmir
spolist.csh $inst                # make list of antpols for atafx
set antpols = `cat antpols`      # antpols list for atafx
set compasscheck = 1
set begin=`date +%T | tr ':' ' ' | awk '{print $1+($2/60)-0.1}'`
set hours=`echo $stop $begin | awk '{if ($1>$2) print $1-$2; else print $1-$2+24}'`
set hrs = `echo $hours | awk '{print $1+2}'`
echo -----------------------------------------------------------
echo  Cals=$callist - Sources=$soulist 
echo Freq=$freq  LO=$lo Switch=$switch Stop=$stop
echo  Instrument:group = $inst
echo " ----------------------------------------------------------"

if (`echo $inst | grep ':'` == '') then
  echo "Must include instrument and group separated by a colon.  Exiting!"
  exit 1
endif

# make ephemeris once for each source and cal over the full obs period
# --------------------------------------------------------------------
# calibrator ephemeris (no solar system objects)
foreach cal (`echo $callist | tr ',' ' '`)
  radec.csh $cal
  set racal = `awk '{print $4}' radec`
  set deccal = `awk '{print $5}' radec`
  ataradecephem $racal $deccal `date -u +%Y-%m-%dT%H:%M:00.000Z` +{$hrs}hours --utcms --interval 10 >! check
  set el1 = `head -1 check | awk '{printf "%3.0f", $3}'`
  set el2 = `tail -1 check | awk '{printf "%3.0f", $3}'`
  echo "cal $cal El range for observations is $el1 to $el2"
  mv check $cal.ephem
  atawrapephem $cal.ephem
end

foreach sou (`echo $soulist | tr ',' ' '`)
    ataephem $sou --utcms --interval 10
  # source (solar system or deep space objects ok)
#  set planet = (`atalistsolarsys -l | grep -i $sou`)
#  if (`echo $planet` != '') then
#    set pswitch = '-ephem'
#    set rasou = $planet[2]
 #   set decsou = $planet[3]
#    atasolarsysephem $planet[1] `date -u +%Y-%m-%dT%H:%M:00.000Z` +{$hrs}hours --utcms --interval 10  >! check
 # else
#    radec.csh $sou
#    set rasou = `awk '{print $4}' radec`
#    set decsou = `awk '{print $5}' radec`
#    ataradecephem $rasou $decsou `date -u +%Y-%m-%dT%H:%M:00.000Z` +{$hrs}hours --utcms --interval 10 >! check
#    rm radec
#  endif
# set el1 = `head -1 check | awk '{printf "%3.0f", $3}'`
# set el2 = `tail -1 check | awk '{printf "%3.0f", $3}'`
# echo "sou $sou El range observations is $el1 to $el2"
# mv check $sou.ephem
 atawrapephem $sou.ephem
end

echo " "
echo " >>>>>>>>>>>>>>> Observe time is $hours hours <<<<<<<<<<<<<"
echo " "

# Make a note to log.hcro.org
/hcro/ata/scripts/notify-obs-blog.csh $logident "Freq: $freq" "LO: $lo" "Antennas: $alist" "Switch: $switch" "PSwitch: $pswitch" "Begin: $begin" "Hours: $hours" "Stop: $stop" "SOUList: $soulist" "Callist: $callist" "Dir: $pwd"

fxlaunch $inst                     # restart FXServer & fx2nets on fx64a
atasetskyfreq $lo $freq            # set LO frequency
atalockserver lo$lo $vis           # lock the LO against accidental changes
atasetpams $alist; atalnaon $alist # set pams to default settings; turn on lnas

#goto skip # >>>> unhash this line to skip important but time-consuming setups

# set intime, frequency, focus, lnas and pams
echo " "
echo "setting focus, itime, attemplifiers" 
echo " "
atasetfocus $alist $freq           # set focus
setintfx.csh $dump64 $inst         # set correlator integration time
autoattenall.csh $inst             # set attemplifiers for rms = 13
waitfocus $alist $freq             # wait for focus to reach $freq
atagetfocus $alist > focus         # get the current focus settings & errors
skip:

# begin infinite loop - exit by finish or fail
begin:
  date | & tee -ia $vis.log
  if (`stopnow.csh $begin $stop` == 'stop') goto finish
  echo "----------------------------------------------------" | & tee -ia $vis.log
  echo sourcelist is $soulist, callist is $callist | & tee -ia $vis.log
  echo "----------------------------------------------------" | & tee -ia $vis.log
 
# observe any cals that are currently up
cal:
foreach cal (`echo $callist | tr ',' ' '`)
  radec.csh $cal
  set racal = `awk '{print $4}' radec`
  set deccal = `awk '{print $5}' radec`
  set durhr=`echo $durcal | awk '{print ($1/3600)+.1}'`
 if(`sourceup.csh $racal $deccal $durhr|grep ok` != "ok") then
   echo "------------------------------------------------"
   echo "$cal is NOT up - skipping it and moving on"
   echo "------------------------------------------------"
 else  
   echo "------------------------------------------------"
   date | & tee -ia $vis.log
   echo " moving to $cal - observe for $durcal sec"  | tee -ia $vis.log
   echo "------------------------------------------------"

# ------------------ Calibrator observing block ----------------------
# start fringe rotation for current scan; wait 10sec for ephem to load
# begin tracking ephemeris
# start fxmir & atafx; put fxmir in background and launch atafx
# wait for above processes to complete before continuing

   set alist=`slist.csh $inst`            # update list of antennas
   spolist.csh $inst               # update list of antpols for atafx
   frot.csh $inst $cal.ephem $freq `pwd` start
   sleep 10 &
   atatrackephem $alist $cal.ephem -w | & tee -ia track.log
   wait
   set caltimes = `date -u +%y%h%d:%H:%M:%S`
#   frfx64.csh $pwd $freq $cal $racal,$deccal $caldump $inst &
   atafx $vis-$cal-$freq $antpols $inst $cal.ephem -duration $durcal $switch
#   wait
   set caltimes = ($caltimes `date -u +%y%h%d:%H:%M:%S` 0 0)
   if ($compasscheck) echo "compass $pwd/$vis-$cal-$freq $caltimes[1] $caltimes[2] $inst" > ~/karto/compass.log
   set compasscheck = 0
 frot.csh $inst $sou.ephem $freq `pwd` kill
 endif
end                 # end loop over all cals in list

# observe any sources that are currently up
sou:
foreach sou (`echo $soulist | tr ',' ' '`)
  if (`stopnow.csh $begin $stop` == 'stop') goto finish
  set durhr=`echo $dursou | awk '{print ($1/3600)+.1}'`
  set planet = (`atalistsolarsys -l | grep -i $sou`)
  if (`atacheck $sou | grep "Az, El" | awk '{if ($5*1 > 16.5 && $5*1 < 85) print 0; else print 1}'`) then
    echo "$sou not up... skipping."
#  if (`echo $planet` != '') then
#    set rasou = $planet[2]
#    set decsou = $planet[3]
#  else
#     radec.csh $sou
#     set rasou = `awk '{print $4}' radec`
#     set decsou = `awk '{print $5}' radec`
#  endif
#  if(`sourceup.csh $rasou $decsou $durhr|grep ok` != "ok") then
#    echo "------------------------------------------------"
#    echo "$sou is NOT up - skipping it and moving on" 
#    echo "------------------------------------------------"
  else
    echo "------------------------------------------------"
    date | & tee -ia $vis.log
    echo " moving to $sou - observe for $dursou sec"  | tee -ia $vis.log
    echo "------------------------------------------------"

# ------------------ Source observing block ----------------------
# kill frot.rb if running and start fringe rotation for current scan
   set alist=`slist.csh $inst`            # update list of antennas
   spolist.csh $inst               # update list of antpols for atafx
   frot.csh $inst $sou.ephem $freq `pwd` start
   sleep 10 &
   atatrackephem $alist $sou.ephem -w | & tee -ia track.log
   wait
#   frfx64.csh $pwd $freq $sou $rasou,$decsou $soudump $inst &
   atafx $vis-$sou-$freq $antpols $inst $sou.ephem -duration $dursou $switch
   frot.csh $inst $sou.ephem $freq `pwd` kill
   set compasscheck = 1
  endif
end             # end loop over list of sources

goto begin	# infinite loop; terminate script by finish or fail

finish:
frot.csh $inst $sou.ephem $freq `pwd` kill
ataunlockserver lo$lo $vis
 rm -f radec check
 echo "-----------------------------------------------------" | tee -ia $vis.log
 echo "Finished -  the time is `date`, the stop time is $stop" | tee -ia $vis.log
exit 0

fail:
# kill frot.rb if running and turn fringe rotation off
  frot.csh $inst $sou.ephem $freq `pwd` kill
  ataunlockserver lo$lo $vis
  rm -f radec check
  echo "-----------------------------------------------------" | tee -ia $vis.log
  echo "$00 failed for some reason.  stopping observation" | tee -ia $vis.log
exit 1
