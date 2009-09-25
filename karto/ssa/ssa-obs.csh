#! /usr/bin/tcsh -f
#
# Obs script for SSA - welcome to fun...
#
#


onintr fail

set subarray = "fxa"
set inst1 = fx64a
set inst2 = fx64c
set inst1bw = 104.8576
set inst2bw = 104.8576
set inst1lo = "b"
set inst2lo = "a"
set inst1freq = 0
set inst2freq = 0
set targetfile
set inttime = 10
set npcals = 1
set nscals = 1
set necals = 1
set pcaltime = 60
set scaltime = 60
set ecaltime = 60
set sattime = 120
set ellim = (16.5 88)
set stoptime
set targetfile = $1
set primarycal = (`echo $2 | tr ',' ' '`)
set secondarycal = (`echo $3 | tr ',' ' '`)
set extendedcal = (`echo $4 | tr ',' ' '`)
set stoptime = "$5"
echo "Stoptime is "`date -d "$stoptime"`"!"
set stoptime = `date -d "$stoptime" +%s | awk '{print $1*1}'`
echo "($stoptime UTC seconds)"
set noinit = 0
set genswitch = "`cat ~/bin/genswitch`"

if ($stoptime < `date +%s`) then
    echo "FATAL ERROR: Stoptime has passed!"
    exit 1
endif

if (! -e $targetfile) then
    echo "FATAL ERROR: Satellite listing not found!"
    exit 1
endif

initblock:

echo -n "Collecting antennnas for observing..."
# Get the antennas and antpols for our observation
set ants = (`fxconf.rb sals | grep $subarray | sed s/$subarray//`)
set inst1antpols = (`fxconf.rb hookup_tab ${inst1}:${subarray} | awk '{if ($1 == "|") print $8}' | sed 's/\([0-9][a-z][a-z]\)\([a-z][0-9]\)/\1/g'`)
set inst2antpols = (`fxconf.rb hookup_tab ${inst2}:${subarray} | awk '{if ($1 == "|") print $8}' | sed 's/\([0-9][a-z][a-z]\)\([a-z][0-9]\)/\1/g'`)
set focusfreq = `awk '{printf "%s\n%s\n",$2,$3}' $targetfile | sort -n | tail -n 1`
echo "done!"
echo -n "Getting frequency and target information for observation..."
# Get the list of freqs for our observations
set inst1freqs = `awk '{print $2}' $targetfile | sort -un`
set inst2freqs = `awk '{print $3}' $targetfile | sort -un`

# Get the EXACT bandwitdh setting for each correlator
set inst1bw = `ebw.csh $inst1bw | awk '{print $9}'`
set inst2bw = `ebw.csh $inst2bw | awk '{print $9}'`

# Get the list of satellite names
set satlist = (`awk '{print $1}' $targetfile`)
echo "done!"

if ($noinit) goto primarycalobs

# Set the bandwidth and integration time for each correlator
echo -n "Setting up correlator for observation..."
bw.csh ${inst1}:${subarray} $inst1bw >& bw.$inst1
bw.csh ${inst2}:${subarray} $inst2bw >& bw.$inst2
setintfx.csh $inttime ${inst1}:${subarray} >& int.$inst1
setintfx.csh $inttime ${inst2}:${subarray} >& int.$inst2
echo "done!"
# Set up the antennas for observing
echo -n "Initializing antennas for observation"
atasetfocus --cal `echo $ants | tr ' ' ','` $focusfreq >& focus.$subarray
echo -n "."
atasetpams `echo $ants | tr ' ' ','` >& pams.$subarray
echo -n "."
atalnaon `echo $ants | tr ' ' ','` >& lna.$subarray
echo -n "."
atasetazel `echo $ants | tr ' ' ','` 0 41 -w >& np.$subarray
echo -n "."
waitfocus `echo $ants | tr ' ' ','` $focusfreq >& waitfocus.$subarray
echo "done!"

# Kill fringe rotation if it's cycling
frotnear.csh ${inst1}:${subarray} sun.ephem $inst1freq $PWD kill
frotnear.csh ${inst2}:${subarray} sun.ephem $inst2freq $PWD kill

echo -n "Getting nominal attenuation settings for iBobs..."
#Get the attenuation settings for each correlation at each freq
foreach freq ($inst1freqs)
    atasetskyfreq $inst1lo $freq >& freq.$inst1
    attenauto.csh ${inst1}:${subarray} >& atten.$inst1
    mv autoattenall.$inst1.log autoattenall.$inst1.log.$freq
    set inst1freq = $freq
    echo -n "."
end

foreach freq ($inst2freqs)
    atasetskyfreq $inst2lo $freq >& freq.$inst2
    attenauto.csh ${inst2}:${subarray} >& atten.$inst2
    mv autoattenall.$inst2.log autoattenall.$inst2.log.$freq
    set inst2freq = $freq
    echo -n "."
end
echo "done!"
# Generate ephems for the primary "VLA" calibrators
foreach target ($primarycal $secondarycal)
    ataephem $target --utcms --interval 10 --owner vla >> ephem.log
end

# Generate ephems for the "extended" cals and sat targets
foreach target($extendedcal $satlist)
    ataephem $target --utcms --interval 10 >> ephem.log
end

ataephem --notof --utcms --interval 10 sun >> ephem.log

# Start observing the primary calibrators
primarycalobs:
set calcount = 0
foreach caltarget ($primarycal)
    if ($npcals > $calcount) then
	set timenow = `date +%s000`
	set timefuture = `date +%s000 | awk '{print $1+300000+(caltime*1000)}' caltime=$pcaltime` 
	set posnow = (`ephemspline.rb $caltarget.ephem $timenow`)
	set posfuture = (`ephemspline.rb $caltarget.ephem $timefuture`)
	if (`echo $posnow $posfuture | awk '{if ($2 < lowlim || $4 < lowlim) print 1; else print 0}' lowlim=$ellim[1]`) then
	    echo "WARNING: Calibrator below observing horizon, moving on..."
	else if (`awk '{if (NR == 1) printf "%s ",$1; last = $1} END {print last}' $caltarget.ephem | awk '{if ($1 > timenow || $2 < timefuture) print 1; else print 0}' timenow=$timenow timefuture=$timefuture`) then
	    echo "WARNING: Calibrator below observing horizon, moving on..."
	else if (`awk '{if ($1 > timenow && $1 < timefuture && $3 > hilim) idx+=1} END {print idx*1}' timenow=$timenow timefuture=$timefuture hilim=$ellim[2] $caltarget.ephem`) then
	    echo "WARNING: Calibrator moves too close to zenith, moving on..."
	else
	    set freqidx = 1
	    atawrapephem $caltarget.ephem
	    atatrackephem `echo $ants | tr ' ' ','` $caltarget.ephem -w &
	    while ($freqidx <= $#inst1freqs || $freqidx <= $#inst2freqs)
		if ($freqidx <= $#inst1freqs) then
		    frotnear.csh ${inst1}:${subarray} sun.ephem $inst1freq $PWD kill
		    attenrestore.csh autoattenall.$inst1.log.$inst1freqs[$freqidx] ; frotnear.csh ${inst1}:${subarray} $caltarget.ephem $inst1freqs[$freqidx] $PWD start; sleep $inttime &
		    atasetskyfreq $inst1lo $inst1freqs[$freqidx] &
		    set inst1freq = $inst1freqs[$freqidx]
		endif
		if ($freqidx <= $#inst2freqs) then
		    frotnear.csh ${inst2}:${subarray} sun.ephem $inst2freq $PWD kill
		    attenrestore.csh autoattenall.$inst2.log.$inst2freqs[$freqidx] ; frotnear.csh ${inst2}:${subarray} $caltarget.ephem $inst2freqs[$freqidx] $PWD start; sleep $inttime &
		    atasetskyfreq $inst2lo $inst2freqs[$freqidx] &
		    set inst2freq = $inst2freqs[$freqidx]
		endif

		if (! -e ssa-$inst1-$caltarget-$inst1freq) then
		    echo "pcal,ssa-$inst1-$caltarget-$inst1freq,$inst1,$caltarget,$inst1freq" >> ssa.manifest
		endif
		if (! -e ssa-$inst2-$caltarget-$inst2freq) then
		    echo "pcal,ssa-$inst2-$caltarget-$inst2freq,$inst2,$caltarget,$inst2freq" >> ssa.manifest
		endif
		
		wait
		if ($freqidx <= $#inst1freqs) atafx ssa-$inst1-$caltarget-$inst1freqs[$freqidx] `echo $inst1antpols | tr ' ' ','` ${inst1}:${subarray} $caltarget.ephem -duration $pcaltime -bw $inst1bw $genswitch  >& $inst1.atafx.log &
		if ($freqidx <= $#inst2freqs) atafx ssa-$inst2-$caltarget-$inst2freqs[$freqidx] `echo $inst2antpols | tr ' ' ','` ${inst2}:${subarray} $caltarget.ephem -duration $pcaltime -bw $inst2bw $genswitch >& $inst2.atafx.log &
		sleep `echo $inttime | awk '{print ($1*3)+10}'`
		set starttime1 = (`grep 'Getting Dump 0' $inst1.atafx.log | awk '{print $1,$2}'`)
		set starttime2 = (`grep 'Getting Dump 0' $inst2.atafx.log | awk '{print $1,$2}'`)
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
		sleep `echo $currenttime $starttime1 $starttime2 $pcaltime $inttime | awk '{if (($2 == 0 && $3 == 0) || ($2+$4 < $1+(2*$5) && $3+$4 < $1+(2*$5))) {print 0; next}; if ($2 > $3) {print $2+$4-$1+2-(2*$5); next}; if ($2 >= $3) {print $3+$4-$1+2-(2*$5); next}}'`
		@ freqidx++
		if ($stoptime < `date +%s`) goto finish
	    end
	    @ calcount++
	endif
    endif
end

#Start observing the secondary calibrators
secondarycalobs:
set calcount = 0
foreach caltarget ($secondarycal)
    if ($nscals > $calcount) then
	set timenow = `date +%s000`
	set timefuture = `date +%s000 | awk '{print $1+300000+(caltime*1000)}' caltime=$scaltime` 
	set posnow = (`ephemspline.rb $caltarget.ephem $timenow`)
	set posfuture = (`ephemspline.rb $caltarget.ephem $timefuture`)
	if (`echo $posnow $posfuture | awk '{if ($2 < lowlim || $4 < lowlim) print 1; else print 0}' lowlim=$ellim[1]`) then
	    echo "WARNING: Calibrator below observing horizon, moving on..."
	else if (`awk '{if (NR == 1) printf "%s ",$1; last = $1} END {print last}' $caltarget.ephem | awk '{if ($1 > timenow || $2 < timefuture) print 1; else print 0}' timenow=$timenow timefuture=$timefuture`) then
	    echo "WARNING: Calibrator below observing horizon, moving on..."
	else if (`awk '{if ($1 > timenow && $1 < timefuture && $3 > hilim) idx+=1} END {print idx*1}' timenow=$timenow timefuture=$timefuture hilim=$ellim[2] $caltarget.ephem`) then
	    echo "WARNING: Calibrator moves too close to zenith, moving on..."
	else
	    set freqidx = 1
	    atawrapephem $caltarget.ephem
	    atatrackephem `echo $ants | tr ' ' ','` $caltarget.ephem -w &
	    while ($freqidx <= $#inst1freqs || $freqidx <= $#inst2freqs)
		if ($freqidx <= $#inst1freqs) then
		    frotnear.csh ${inst1}:${subarray} sun.ephem $inst1freq $PWD kill
		    attenrestore.csh autoattenall.$inst1.log.$inst1freqs[$freqidx] ; frotnear.csh ${inst1}:${subarray} $caltarget.ephem $inst1freqs[$freqidx] $PWD start; sleep $inttime &
		    atasetskyfreq $inst1lo $inst1freqs[$freqidx] &
		    set inst1freq = $inst1freqs[$freqidx]
		endif
		if ($freqidx <= $#inst2freqs) then
		    frotnear.csh ${inst2}:${subarray} sun.ephem $inst2freq $PWD kill
		    attenrestore.csh autoattenall.$inst2.log.$inst2freqs[$freqidx] ; frotnear.csh ${inst2}:${subarray} $caltarget.ephem $inst2freqs[$freqidx] $PWD start; sleep $inttime &
		    atasetskyfreq $inst2lo $inst2freqs[$freqidx] &
		    set inst2freq = $inst2freqs[$freqidx]
		endif

		if (! -e ssa-$inst1-$caltarget-$inst1freq) then
		    echo "scal,ssa-$inst1-$caltarget-$inst1freq,$inst1,$caltarget,$inst1freq" >> ssa.manifest
		endif
		if (! -e ssa-$inst2-$caltarget-$inst2freq) then
		    echo "scal,ssa-$inst2-$caltarget-$inst2freq,$inst2,$caltarget,$inst2freq" >> ssa.manifest
		endif

		wait
		if ($freqidx <= $#inst1freqs) atafx ssa-$inst1-$caltarget-$inst1freqs[$freqidx] `echo $inst1antpols | tr ' ' ','` ${inst1}:${subarray} $caltarget.ephem -duration $scaltime -bw $inst1bw $genswitch >& $inst1.atafx.log &
		if ($freqidx <= $#inst2freqs) atafx ssa-$inst2-$caltarget-$inst2freqs[$freqidx] `echo $inst2antpols | tr ' ' ','` ${inst2}:${subarray} $caltarget.ephem -duration $scaltime -bw $inst2bw $genswitch >& $inst2.atafx.log &
		sleep `echo $inttime | awk '{print ($1*3)+10}'`
		set starttime1 = (`grep 'Getting Dump 0' $inst1.atafx.log | awk '{print $1,$2}'`)
		set starttime2 = (`grep 'Getting Dump 0' $inst2.atafx.log | awk '{print $1,$2}'`)
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
		sleep `echo $currenttime $starttime1 $starttime2 $scaltime $inttime | awk '{if (($2 == 0 && $3 == 0) || ($2+$4 < $1+(2*$5) && $3+$4 < $1+(2*$5))) {print 0; next}; if ($2 > $3) {print $2+$4-$1+2-(2*$5); next}; if ($2 >= $3) {print $3+$4-$1+2-(2*$5); next}}'`
		@ freqidx++
		if ($stoptime < `date +%s`) goto finish
	    end
	    @ calcount++
	endif
    endif
end

# Start observing the extended calibrators
extendedcalobs:
set calcount = 0
foreach caltarget ($extendedcal)
    if ($necals > $calcount) then
	set timenow = `date +%s000`
	set timefuture = `date +%s000 | awk '{print $1+300000+(caltime*1000)}' caltime=$ecaltime` 
	set posnow = (`ephemspline.rb $caltarget.ephem $timenow`)
	set posfuture = (`ephemspline.rb $caltarget.ephem $timefuture`)
	if (`echo $posnow $posfuture | awk '{if ($2 < lowlim || $4 < lowlim) print 1; else print 0}' lowlim=$ellim[1]`) then
	    echo "WARNING: Calibrator below observing horizon, moving on..."
	else if (`awk '{if (NR == 1) printf "%s ",$1; last = $1} END {print last}' $caltarget.ephem | awk '{if ($1 > timenow || $2 < timefuture) print 1; else print 0}' timenow=$timenow timefuture=$timefuture`) then
	    echo "WARNING: Calibrator below observing horizon, moving on..."
	else if (`awk '{if ($1 > timenow && $1 < timefuture && $3 > hilim) idx+=1} END {print idx*1}' timenow=$timenow timefuture=$timefuture hilim=$ellim[2] $caltarget.ephem`) then
	    echo "WARNING: Calibrator moves too close to zenith, moving on..."
	else
	    set freqidx = 1
	    atawrapephem $caltarget.ephem
	    atatrackephem `echo $ants | tr ' ' ','` $caltarget.ephem -w &
	    while ($freqidx <= $#inst1freqs || $freqidx <= $#inst2freqs)
		if ($freqidx <= $#inst1freqs) then
		    frotnear.csh ${inst1}:${subarray} sun.ephem $inst1freq $PWD kill
		    attenrestore.csh autoattenall.$inst1.log.$inst1freqs[$freqidx] ; frotnear.csh ${inst1}:${subarray} $caltarget.ephem $inst1freqs[$freqidx] $PWD start; sleep $inttime &
		    atasetskyfreq $inst1lo $inst1freqs[$freqidx] &
		    set inst1freq = $inst1freqs[$freqidx]
		endif
		if ($freqidx <= $#inst2freqs) then
		    frotnear.csh ${inst2}:${subarray} sun.ephem $inst2freq $PWD kill
		    attenrestore.csh autoattenall.$inst2.log.$inst2freqs[$freqidx] ; frotnear.csh ${inst2}:${subarray} $caltarget.ephem $inst2freqs[$freqidx] $PWD start; sleep $inttime &
		    atasetskyfreq $inst2lo $inst2freqs[$freqidx] &
		    set inst2freq = $inst2freqs[$freqidx]
		endif

		if (! -e ssa-$inst1-$caltarget-$inst1freq) then
		    echo "ecal,ssa-$inst1-$caltarget-$inst1freq,$inst1,$caltarget,$inst1freq" >> ssa.manifest
		endif
		if (! -e ssa-$inst2-$caltarget-$inst2freq) then
		    echo "ecal,ssa-$inst2-$caltarget-$inst2freq,$inst2,$caltarget,$inst2freq" >> ssa.manifest
		endif

		wait
		if ($freqidx <= $#inst1freqs) atafx ssa-$inst1-$caltarget-$inst1freqs[$freqidx] `echo $inst1antpols | tr ' ' ','` ${inst1}:${subarray} $caltarget.ephem -duration $ecaltime -bw $inst1bw $genswitch >& $inst1.atafx.log &
		if ($freqidx <= $#inst2freqs) atafx ssa-$inst2-$caltarget-$inst2freqs[$freqidx] `echo $inst2antpols | tr ' ' ','` ${inst2}:${subarray} $caltarget.ephem -duration $ecaltime -bw $inst2bw $genswitch >& $inst2.atafx.log &
		sleep `echo $inttime | awk '{print ($1*3)+10}'`
		set starttime1 = (`grep 'Getting Dump 0' $inst1.atafx.log | awk '{print $1,$2}'`)
		set starttime2 = (`grep 'Getting Dump 0' $inst2.atafx.log | awk '{print $1,$2}'`)
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
		sleep `echo $currenttime $starttime1 $starttime2 $ecaltime $inttime | awk '{if (($2 == 0 && $3 == 0) || ($2+$4 < $1+(2*$5) && $3+$4 < $1+(2*$5))) {print 0; next}; if ($2 > $3) {print $2+$4-$1+2-(2*$5); next}; if ($2 >= $3) {print $3+$4-$1+2-(2*$5); next}}'`
		@ freqidx++
		if ($stoptime < `date +%s`) goto finish
	    end
	    @ calcount++
	endif
    endif
end

# Start observing satellites
satobs:
set satidx = 1
while ($satidx <= `wc -l $targetfile | awk '{print $1}'`)
    set vals = (`sed -n ${satidx}p $targetfile`)
    set sat = "$vals[1]"
    @ satidx++
    atawrapephem $sat.ephem
    atatrackephem `echo $ants | tr ' ' ','` $sat.ephem -w &
    if ("$vals[2]" != "$inst1freq" && "$vals[2]" != "$inst1freq") then
	frotnear.csh ${inst1}:${subarray} sun.ephem $inst1freq $PWD kill
	frotnear.csh ${inst2}:${subarray} sun.ephem $inst2freq $PWD kill
	set inst1freq = $vals[2]
	atasetskyfreq $inst1lo $inst1freq
	attenrestore.csh autoattenall.$inst1.log.$inst1freq &
	set inst2freq = $vals[3]
	atasetskyfreq $inst2lo $inst2freq
	attenrestore.csh autoattenall.$inst2.log.$inst2freq &
	wait
    else if ("$vals[2]" != "$inst1freq") then
	frotnear.csh ${inst1}:${subarray} sun.ephem $inst1freq $PWD kill
	set inst1freq = $vals[2]
	atasetskyfreq $inst1lo $inst1freq
	attenrestore.csh autoattenall.$inst1.log.$inst1freq
    else if ("$vals[3]" != "$inst2freq") then
	frotnear.csh ${inst2}:${subarray} sun.ephem $inst2freq $PWD kill
	set inst2freq = $vals[3]
	atasetskyfreq $inst2lo $inst2freq
	attenrestore.csh autoattenall.$inst2.log.$inst2freq
    endif
    frotnear.csh ${inst1}:${subarray} $sat.ephem $inst1freq $PWD start; sleep $inttime &
    frotnear.csh ${inst2}:${subarray} $sat.ephem $inst2freq $PWD start; sleep $inttime &

    if (! -e ssa-$inst1-$caltarget-$inst1freq) then
	echo "sat,ssa-$inst1-$sat-$inst1freq,$inst1,$sat,$inst1freq" >> ssa.manifest
    endif
    if (! -e ssa-$inst2-$caltarget-$inst2freq) then
	echo "sat,ssa-$inst2-$sat-$inst2freq,$inst2,$sat,$inst2freq" >> ssa.manifest
    endif

    wait

    atafx ssa-$inst1-$sat-$inst1freq `echo $inst1antpols | tr ' ' ','` ${inst1}:${subarray} $sat.ephem -duration $sattime -bw $inst1bw $genswitch >& $inst1.atafx.log &
    atafx ssa-$inst2-$sat-$inst2freq `echo $inst2antpols | tr ' ' ','` ${inst2}:${subarray} $sat.ephem -duration $sattime -bw $inst2bw $genswitch >& $inst2.atafx.log &

    sleep `echo $inttime | awk '{print ($1*3)+10}'`
    set starttime1 = (`grep 'Getting Dump 0' $inst1.atafx.log | awk '{print $1,$2}'`)
    set starttime2 = (`grep 'Getting Dump 0' $inst2.atafx.log | awk '{print $1,$2}'`)

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
    set satcheck = 0
    if ($satidx > `wc -l $targetfile | awk '{print $1}'`) set satcheck = 1
    while ($satcheck == 0)
	set ephemtime = `date +%s000`
	set sunpos = (`ephemspline.rb sun.ephem $ephemtime`)
	set satephemname = `sed -n ${satidx}p $targetfile | awk '{print $1".ephem"}'`
	set satpos = (`ephemspline.rb $satephemname $ephemtime`) 
	if (`echo $sunpos $satpos | awk '{print $1*PI/180,$2*PI/180,$3*PI/180,$4*PI/180}' PI=3.14159265 | awk '{print atan2(((cos($3)*sin($4-$2))^2+(cos($1)*sin($3)-sin($1)*cos($3)*cos($4-$2))^2)^.5,sin($1)*sin($3)+cos($1)*cos($3)*cos($4-$2))}'| awk '{print int($1*180/3.14159265)}'` <= 20) then
	    @ satidx++
	else
	    set satcheck = 1
	endif
	if ($satidx > `wc -l $targetfile | awk '{print $1}'`) set satcheck = 1
    end
    set currenttime = `date +%s`
    sleep `echo $currenttime $starttime1 $starttime2 $sattime $inttime | awk '{if (($2 == 0 && $3 == 0) || ($2+$4 < $1+(2*$5) && $3+$4 < $1+(2*$5))) {print 0; next}; if ($2 > $3) {print $2+$4-$1+2-(2*$5); next}; if ($2 >= $3) {print $3+$4-$1+2-(2*$5); next}}'`
    if ($stoptime < `date +%s`) goto finish
end

goto primarycalobs

finish:
frotnear.csh ${inst1}:${subarray} sun.ephem $inst1freq $PWD kill
frotnear.csh ${inst2}:${subarray} sun.ephem $inst2freq $PWD kill


fail:
frotnear.csh ${inst1}:${subarray} sun.ephem $inst1freq $PWD kill
frotnear.csh ${inst2}:${subarray} sun.ephem $inst2freq $PWD kill
