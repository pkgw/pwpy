#! /bin/tcsh -f
#
# Multi-part broadband spectra observations.
#
# Usage: mbbsf.csh [plan name] [mode] [stopHour]
# 
# The observations take place in subdirectories of PWD.

set planDir = /home/pkwill/plans
set obsbin = /home/obs/bin
set script = /home/obs/mmm/pwilliams/BBS/bbsf.py
set begin = `date +'%H %M' |awk '{print $1 + ($2/60) - 0.01}'`
set svnid = '$Id$'

if ($#argv != 4) then
    echo "Usage: $0 [planname] [mode] [instrument] [stopHour]"
    echo "  [planname] is the name of a directory in $planDir"
    echo "  [mode] is either 'debug' or 'real'"
    echo "  [instrument] is an fxconf instrument or 'default'"
    echo "  [stopHour] is a the time to stop in local time."
    echo "    (This is also specified in the observing plan,"
    echo "     but the redundancy prevents accidental overruns.)"
    exit 1
endif

set planDir = $planDir/$1
set mode = $2
set instr = $3
set stopHour = $4

if (! -d $planDir) then
    echo "Error: observing plan directory $planDir does not exist!"
    exit 1
endif

if ($mode != debug && $mode != real) then
    echo "Error: the 'mode' argument must be either 'debug' or 'real'."
    exit 1
endif

# Note our start

echo "Running $0 at `date`" |tee -ia mbbsf.log
echo "SVN ident: $svnid" |tee -ia mbbsf.log

# Scan the config files to make sure everything is cool

set stopHours = ()
@ part = 1

while (1)
    set cfg = $planDir/config$part.py

    if (! -f $cfg) break
    
    # Stop hour?

    set line = `egrep '^# stopHour [0-9.]+' $cfg`
    if ($%line == 0) then
	echo "Error: config file $cfg has no stopHour line!"
	exit 1
    endif
    set t = `echo $line |cut -d' ' -f3`
    set stopHours = ($stopHours $t)

    # UUID?

    set line = `egrep '^# uuid [-0-9a-fA-F]+' $cfg`
    if ($%line == 0) then
	echo "Error: config file $cfg has no uuid line!"
	exit 1
    endif

    @ part++
end

@ nparts = $part - 1

if ($t != $stopHour) then
    echo " - Warning: planned stop hour ($t) and command stop hour ($stopHour) disagree" |tee -ia mbbsf.log
endif

echo "$nparts part(s) to the observing plan." |tee -ia mbbsf.log
echo "Stop hours: $stopHours" |tee -ia mbbsf.log

# OK, now run, skipping up to what seems to be the best part

@ part = 1

while (($mode == debug || `$obsbin/stopnow.csh $begin $stopHour` != stop) && $part <= $nparts)
    set cfg = $planDir/config$part.py
    set partDir = part$part
    set stop = $stopHours[$part] # 1-based indices ...

    set now = `date +'%H %M' |awk '{print $1 + ($2/60)}'`

    # print y if $now is later than $stop with a 12 hour margin
    set skip = `echo $stop $now |awk '{if (($2 - $1 + 12) % 24 > 12) print "y"}'`

    if (($skip == y && $mode == real) || ($mode == debug && -d $partDir)) then
	echo "Advancing to next part: now = $now, stop for part $part = $stop." |tee -ia mbbsf.log
	@ part++
	continue
    endif

    # We should observe this guy

    mkdir -p $partDir
    cp -f $cfg $partDir/config.py
    egrep '^# uuid [-0-9a-fA-F]+' $cfg |cut -d' ' -f3 >$partDir/bbs.uuid
    echo " - $script $mode $instr $stop in $partDir" |tee -ia mbbsf.log
    (cd $partDir && $script $mode $instr $stop)
end

# If in debug mode, clean up the directories we created.
# This, well, cleans things up, and also allows us to rerun in debug
# mode since the loop above tests for the existence of the partN directories
# to know when to move to the next step.
#
# Avoid using rm -rf as a paranoia measure.

if ($mode == debug) then
    foreach n (`seq 1 $nparts`)
	set d = part$n
	rm $d/*.ephem $d/*.msephem $d/bbs.uuid $d/config.py $d/config.pyc
	rmdir $d
    end

    rm mbbsf.log
endif
