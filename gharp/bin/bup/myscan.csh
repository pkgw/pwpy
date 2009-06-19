#!/bin/tcsh -f
# adapted from Rick's "scan.csh"
# allows you to input the ephemeris and antpollist from command line

alias MATH 'set \!:1 = `echo "\!:3-$" | bc -l`'

onintr fail
set dump64 = `getint64.csh`       # fx correlator integration time (sec)
set group=fx64c:fxa               # hardwired group name 
set stop = 0

if ($#argv < 4) then
  echo "Enter Freq, LO, Cal.ephem, antpol_list and duration (seconds) (eg: 1628 b 3c48.ephem antpols 60)"
  set flt = ($<)
  set freq = $flt[1]
  set lo   = $flt[2]
  set ephem  = $flt[3]
  set aplist = $flt[4]
  set durcal  = $flt[5]
else
  set freq = $1
  set lo   = $2
  set ephem  = $3
  set aplist = $4
  set durcal  = $5
endif

# get required files
cp ~/bin/genswitch .

set switch="`cat genswitch`"     # standard atafx switches
set pswitch              # for planets
set elmin=18             # elevation limit 
set vis=scan             # generic name for scans
set alist = `slist.csh`  # list of ants in fxa
set antpols = `cat $aplist`
set pwd = `pwd`
set dump=`echo $durcal $dump64 | awk '{printf "%3.0f",$1/$2}'`
MATH focusfreq = ($freq * 1.25)

set begin = `date +%T | tr ':' ' ' | awk '{print $1+($2/60)-0.1}'`
set hours = `echo $stop $begin | awk '{if ($1>$2) print $1-$2; else print $1-$2+24}'`

echo -----------------------------------------------------------
echo Freq=$freq  LO=$lo  Cal=$ephem Switch=$switch
echo " "

  set el1 = `head -1 $ephem | awk '{printf "%3.0f", $3}'`
  set el2 = `tail -1 $ephem | awk '{printf "%3.0f", $3}'`
  echo "$ephem elevation range for next $hours hours is $el1 to $el2"

echo " ----------------------------------------------------------"
echo "Frequency of LO $lo will be set to $freq MHz"
echo "ants="`slist.csh`
echo "antpols="`cat antpols`
echo " "
echo " >>>>>>>>>>>>>>> Observe time is $hours hours <<<<<<<<<<<<<"
echo " "

# set frequency, lnas and pams
echo "Set sky frequency to $freq using LO $lo"
atasetskyfreq $lo $freq | & tee -ia $vis.log
#echo "Setting focus to $focusfreq "
#atasetfocus $alist $focusfreq
#atalockserver lo$lo $vis
#echo "Setting pams to default values and turning all lnas on"
#atasetpams $alist; atalnaon $alist

# kill frot.rb if it is running
frot.csh $group $ephem $freq `pwd` kill

begin:          # begin infinite loop
set lab = $freq
  date | & tee -ia $vis.log
#  if (`stopnow.csh $begin $stop` == 'stop') goto finish
  echo "----------------------------------------------------" | & tee -ia $vis.log
  echo calibrator is $ephem, freq=$lab | & tee -ia $vis.log
  echo "----------------------------------------------------" | & tee -ia $vis.log
  set durhr=`echo $durcal | awk '{print ($1/3600)+.15}'`
  date | & tee -ia $vis.log
  echo " moving to $ephem - observe for $durcal sec"  | tee -ia $vis.log
  echo "------------------------------------------------"
#  atawrapephem $ephem

# kill frot.rb if running and start fringe rotation for current scan
echo "starting frot"
   frot.csh $group $ephem $freq `pwd` start &
echo "ending frot"
# begin tracking ephemeris
   atatrackephem $alist $ephem -w
    wait
   echo $freq $ephem $dump
# start atafx; let atafx pace it by running in foreground
   atafx $vis-$ephem-$freq $antpols $group $ephem -duration $durcal $switch
    wait
# kill frot.rb if running and turn fringe rotation off 
frot.csh $group $ephem $freq `pwd` stop

   if ($status) goto fail
endif

#goto begin	# end of infinite loop; must terminate script by finish or fail

finish:

#ataunlockserver lo$lo $vis
 rm -f radec check
 echo "-----------------------------------------------------" | tee -ia $vis.log
# echo "Finished -  the time is `date`, the stop time is $stop" | tee -ia $vis.log
 echo "$00 finished -  the time is `date`" | tee -ia $vis.log
exit 0

fail:
# kill frot.rb if running and turn fringe rotation off
frot.csh $group $ephem $freq `pwd` stop

  #ataunlockserver lo$lo $vis
  rm -f radec check
  echo "-----------------------------------------------------" | tee -ia $vis.log
  echo "$00 failed for some reason.  stopping observation" | tee -ia $vis.log
exit 1
