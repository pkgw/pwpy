#! /usr/bin/tcsh -f
# $Id$

onintr fail

if ($#argv == 0) then
    echo "NEWRFISWEEP.CSH"
    echo "newrfisweep.csh is designed as an 'all-in-one' flagging routine."
    echo "Calling sequence: newfracture.csh vis=vis crange=crange select=select timefocus=timefocus corredge=corredge npoly=npoly nsig=nsig spoly=spoly ssig=ssig options={display, nodisplay, asel, desel, corr, nocorr, scorr, noscorr, pos, neg, mixed}"
    echo "REQUIRED INPUTS:"
    echo "vis - Name of the files that contain spectral count information."
    echo "tvis - Name of the files that contain data to be flagged, but should not be used for collecting spectral count information."
    echo "OPTIONAL INPUTS:"
    echo "interval - newrfisweep attempts to ID RFI and flag in time chunks (to better ID transient RFI)."
    echo "Default is 12 (minutes), although 15 is also good."
    echo "crange - allows for selection or deselection of ranges. Multiple ranges can be specified, seperated"
    echo "by commas. Useful for ignoring edge/corrupted channels e.g. crange='(100,800),-(512),-(620,640)'."
    echo "edgerfi - how many surrounding channels around each RFI candidate channel should be identified as RFI. Default is 0."
    echo "npoly - Order polynomial to use for correcting spectrum. Default is 5."
    echo "nsig - Number of sigma at which to ID RFI. Default is 3."
    echo "cpoly - Order polynomial to use for correcting spectrum in corruption detection. Default is 5."
    echo "csig - Number of sigma at which to ID corruption in individual antennas. Default is 3."
    echo "Options:"
	echo "display,nodisplay - display (or not) results of processing. Default is display"
	echo "corr,nocorr - polynomial correct (or not) final count spectrum. Default is no correction."
	echo "scorr,noscorr - polynomial correct (or not) individual antenna spectrum. Default is no correction."
	echo "pos,neg,mixed - identify RFI (or corruption) as having counts that are too high, too low or both. Default is high (pos)."
	echo "asel,desel - creates selection (or deselection) command for corrupted antennas in dataset."
	echo "recover - flag corrupted channels in corrupted antenna inputs. (default)"
	echo "destory - flag any antenna with corruption."
	echo "ignorecorr - perform no special flagging with corrupted antennas."
    exit 0
endif


set date1 = `date +%s.%N`

set fsel = ("pol(xx)" "pol(yy)")
set vis # Files to be scanned for RFI and flagged
set tvis # Files to be flagged for RFI, but NOT scanned!
set inttime = 12.5 # RFI integration time for the subinterval
set nsig = 3 # Number of sigma for RFI flagging in wide interval
set tsig = 4 # Number of sigma for RFI flagging in narrow interval
set csig = 5 # Number of sigma for corruption ID
set cpoly = 6 # Order of poly correction for corruption ID
set npoly = 6 # Order of poly correction for RFI flagging
set corr = "corr" # Use corrective polynomial for RFI scanning and final spectrum for spectral corruption scanning
set edgerfi = 1 # Protective "shield" around each RFI spike, channel range around RFI IDed channel to also flag
set csel # Channel range selection
set fracture = "recover" # Correct (recover), ignore or destory spectrally corrupted antennas
set display = "nodisplay" # To dispaly or 
set scorr = "scorr"
set corr = "corr"
set rfitype = "pos"
set outsource = "outsource"
set debug = 0
set rescan = 0
set corrcycle = 4
set seedcorr = 0
set restart
set autoedge = 0
set autoedgechan = 100

#Alright, lets see if I can finally properly comment this code...
#Below is the variable assignment listing, further documentation on this will be available shortly

varassign:

if ("$argv[1]" =~ 'vis='*) then
    set vis = "`echo '$argv[1]/' | sed 's/vis=//'`"
    set vis = (`echo $vis | sed 's/\/ / /g' | sed 's/\(.*\)\//\1/g' | tr ',' ' '`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'tvis='*) then
    set tvis = "`echo '$argv[1]/' | sed 's/tvis=//'`"
    set tvis = (`echo $tvis | sed 's/\/ / /g' | sed 's/\(.*\)\//\1/g' | tr ',' ' '`)
    shift argv; if ("$argv" == "") set argv = "finset csel = "$csel,-(1),-("`echo $nchan $autoedgechan | awk '{print $1+1-$2","$1}'`")"ish"
else if ("$argv[1]" =~ 'options='*) then
    set options = `echo "$argv[1]" | sed 's/options=//g' | tr ',' ' ' | tr '[A-Z]' '[a-z]'`
    set badopt
    foreach option (`echo $options`)
	if ($option == "recover") then
	    set fracture = "recover"
	else if ($option == "destroy") then
	    set fracture = "destroy"
	else if ($option == "ignorecorr") then
	    set fracture = "ignorecorr"
	else if ($option == "corr") then
	    set corr = "corr"
	else if ($option == "scorr") then
	    set scorr = "corr"
	else if ($option == "noscorr") then
	    set scorr = "noscorr"
	else if ($option == "nocorr") then
	    set corr = "nocorr"
	else if ($option == "pos") then
	    set rfitype = "pos"
	else if ($option == "neg") then
	    set rfitype = "neg"
	else if ($option == "mixed") then
	    set rfitype = "mixed"
	else if ($option == "display") then
	    set display = "display"
	else if ($option == "verbose") then
	    set display = "display,verbose"
	else if ($option == "seedcorr") then
	    set seedcorr = 1
	else if ($option == "nodisplay") then
	    set display = "nodisplay"
	else if ($option == "outsource") then
	    set outsource = "outsource"
	else if ($option == "insource") then
	    set outsource = "insource"
	else if ($option == "debug") then
	    set debug = 1
	else if ($option == "autoedge") then
	    set autoedge = 1
	else if ($option == "noautoedge") then
	    set autoedge = 0
	else if ($option == "rescan") then
	    set rescan = 1
	else
	    set badopt = ($badopt $option)
	endif
    end
    if ("$badopt" != "") echo 'options='`echo $badopt | tr ' ' ','`' not recognized!'
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'interval='*) then
    set inttime = `echo "$argv[1]" | sed 's/interval=//g' | awk '{print $1*1}'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'npoly='*) then
    set npoly = (`echo "$argv[1]" | sed 's/npoly=//g' | awk '{print 1+int($1*1)}'`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'cpoly='*) then
    set cpoly = (`echo "$argv[1]" | sed 's/cpoly=//g' | awk '{print 1+int($1*1)}'`)
else if ("$argv[1]" =~ 'crange='*) then
    set csel = `echo "$argv[1]"`
    shift argv; if ("$argv" == "") set argv = "finish"
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'nsig='*) then
    set nsig = `echo "$argv[1]" | sed 's/nsig=//g'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'corrcycle='*) then
    set corrcycle = `echo "$argv[1]" | sed 's/corrcycle=//g'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'tsig='*) then
    set tsig = `echo "$argv[1]" | sed 's/tsig=//g'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'restart='*) then
    set restart = `echo "$argv[1]" | sed 's/restart=//g'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'nsig='*) then
    set csig = `echo "$argv[1]" | sed 's/csig=//g'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'edgerfi='*) then
    set edgerfi = (`echo "$argv[1]" | sed 's/edgerfi=//g' | awk '{print int($1*1)}'`)
    shift argv; if ("$argv" == "") set argv = "finish"
else
    echo "FATAL ERROR: $argv[1] not recognized..."
    exit 1
endif

if ("$argv[1]" != "finish") goto varassign

#Ok variable assigments are done...

# Check to make sure that each "file" has a specdata file - or at least visiblities to be processed. All of the RFI programs can be "tricked" into accepting a folder that has a specdata file but not a visdata file.

set fulllist = (`echo $vis $tvis`)
set listlim = `echo $fulllist | wc -w`
set idx = 1

while ($idx <= $listlim)
    if (! -e $fulllist[$idx]/specdata || $rescan) then
        if (-e $fulllist[$idx]/visdata) then
            echo "Spectral scanning data not found, running scanner..."
            if ($autoedge) then
		newrfi.csh vis=$fulllist[$idx] interval=1 options=autoedge
	    else
		newrfi.csh vis=$fulllist[$idx] interval=1
	    endif
        else
            echo "FATAL ERROR: No specdata or visibilities found!"
            exit 1
        endif
    endif
    @ idx++
end

# Make a temp directory to reduce data in (keeps things nice a neat)

echo "Gathering observation information..."
set wd = `mktemp -d rfi3XXXXX`
# Make spectral directories for all source and cal files - esp important for mosaiced observations... TOTH to Steve and Geoff

mkdir $wd/vis
mkdir $wd/tvis

# For each source file, use the specdata file to figure out when observations took place, and use that information to rebuild the actual obsrevation

set fulllist = (`echo $vis`)
set listlim = `echo $fulllist | wc -w`
set trlist
set idx = 1

while ($idx <= $listlim)
    set filemark = `echo $idx | awk '{print $1+100000}' | sed 's/1//'`
    set trlist = ($trlist "vis$filemark")
    cat $fulllist[$idx]/specdata >> $wd/vis/specdata
    cat $fulllist[$idx]/specdata | awk '{print filename,$4,($5-$4)*1440,"vis",tname}' filename=$fulllist[$idx] tname="vis$filemark" >> $wd/vistimes
    @ idx++
end

if ($autoedge) then
    if ($csel == "") set csel = 'crange='
    set templist = (`head -n 1 $wd/vis/specdata`)
    set nchan = `echo $#templist | awk '{print $1-14}'`
    if (`echo $templist[9-10] | awk '{if ($1 == $2) print "go"}'` == "go") then
	set autoedgetype = 1
	set csel = "$csel,-(1),-("`echo $nchan $autoedgechan | awk '{print $1+1-$2","$1}'`")"
    else if (`echo $nchan $templist[8-10] | awk '{if (($1-1)*$2+$3 < $4) print "go"}'` == "go") then
	set autoedgetype = 2
	set csel = "$csel,-(1,$autoedgechan)"
    else
	set autoedgetype = 3
	set csel = "$csel,-(1,$autoedgechan),-("`echo $nchan $autoedgechan | awk '{print $1+1-$2","$1}'`"),-("`echo $nchan | awk '{print int($1/2)-1","int($1/2)+1}'`")"
    endif
    set csel = `echo "$csel" | sed 's/=,/=/'`
endif

set fulllist = (`echo $tvis`)
set listlim = `echo $fulllist | wc -w`
set idx = 1

while ($idx <= $listlim)
    set filemark = `echo $idx | awk '{print $1+100000}' | sed 's/1//'`
    set trlist = ($trlist "tvis$filemark")
    cat $fulllist[$idx]/specdata >> $wd/tvis/specdata
    cat $fulllist[$idx]/specdata | awk '{print filename,$4,($5-$4)*1440,"tvis",tname}' filename=$fulllist[$idx] tname="tvis$filemark" >> $wd/vistimes
    @ idx++
end

# Now sort the timestamps from the dataset and figure out the "order" of the observation

set lim = `wc -l $wd/vistimes | awk '{print $1}'`
set idx = 1

sort -unk2 $wd/vistimes > $wd/timecheck2
echo "Reconstructing observational parameters..."
set slist
set clist
set tslist
set tclist

set lim = `wc -l $wd/timecheck2 | awk '{print $1}'`
set idx = 2

# Now divide the dataset into smaller chunks that the processor will handle individually. Limits are currently hard coded, although that may change in the future. Limits are: 30 minutes total time elapsed, 15 minutes of data in hand.

set vals = (`head -n 1 $wd/timecheck2`)
set mastertime = `echo $vals[2] | awk '{printf "%7.6f\n",$1-(10/1440)+2400000.5}'`
set mastertime2 = `echo $vals[2] | awk '{printf "%7.6f\n",$1-(10/1440)}'`
set starttime = $vals[2]
set timeint = $vals[3]
if ($vals[4] == "vis") then
    set slist = ($slist $vals[1])
    set tslist = ($tslist $vals[5])
else if ($vals[4] == "tvis") then
    set clist = ($clist $vals[1])
    set tclist = ($tclist $vals[5])
endif

while ($idx <= $lim) 
    set vals = (`sed -n {$idx}p $wd/timecheck2`)
    if ($starttime == "0") then
	set starttime = `echo $vals[2] | awk '{printf "%7.6f\n",$1-(.5/86400)}'`
	set mastertime = ($mastertime `echo $vals[2] | awk '{printf "%7.6f\n",$1+2400000.5-(.5/86400)}'`)
	set mastertime2 = ($mastertime2 `echo $vals[2] | awk '{printf "%7.6f\n",$1-(.5/86400)}'`)
    endif
    set timeint = `echo $timeint $vals[3] | awk '{print $1+$2}'`
    if  !(" "`echo $clist $slist`" " =~ *" $vals[1] "*) then
	if ($vals[4] == "vis") then
	    set slist = ($slist $vals[1])
	    set tslist = ($tslist $vals[5])
	else if ($vals[4] == "tvis") then
	    set clist = ($slist $vals[1])
	    set tclist = ($tclist $vals[5])
	endif
    endif
    if (`echo $timeint | awk '{if ($1 > inttime) print "go"}' inttime=$inttime` == "go" || `echo $vals[2] $vals[3] $starttime | awk '{if (((1440*($1-$3))+$2) > 2*inttime) print "go"}' inttime=$inttime` == go) then
	set finstarttime = `echo $starttime | awk '{printf "%7.6f",$1+2400000.5}'`
	set finstoptime = `echo $vals[2] $vals[3] | awk '{printf "%7.6f",$1+($2/1440)+2400000.5+(.5/86400)}'`
	set finslist = `echo $slist | tr ' ' ','`","
 	set finclist = `echo $clist | tr ' ' ','`","
	set fintslist = `echo $tslist | tr ' ' ','`","
	set fintclist = `echo $tclist | tr ' ' ','`","
	echo $finstarttime $finstoptime $finslist $finclist $fintslist $fintclist >> $wd/obslist
	set starttime = 0
	set timeint = 0
	set slist
	set clist
	set tslist
	set tclist
    endif
    @ idx++
end

if ($starttime != "0") then
    set finstarttime = `echo $starttime | awk '{printf "%7.6f",$1+2400000.5}'`
    set finstoptime = `echo $vals[2] $vals[3] | awk '{printf "%7.6f",$1+($2/1440)+2400000.5}'`
    set finslist = `echo $slist | tr ' ' ','`","
    set finclist = `echo $clist | tr ' ' ','`","
    set fintslist = `echo $tslist | tr ' ' ','`","
    set fintclist = `echo $tclist | tr ' ' ','`","
    echo $finstarttime $finstoptime $finslist $finclist $fintslist $fintclist >> $wd/obslist
endif

set mastertime = ($mastertime `echo $finstoptime | awk '{printf "%7.6f\n",$1+(10/1440)}'`)
set mastertime2 = ($mastertime2 `echo $finstoptime | awk '{printf "%7.6f\n",$1+(10/1440)-2400000.5}'`)
set lim = `wc -l $wd/obslist | awk '{print $1}'`
set idx = 1
set jidx = 2

if ("$restart" != "") then
    set wd = "$restart"
    goto restart
endif

if ($outsource == "insource") goto recon

while ($idx <= $lim)
    set vals = (`sed -n {$idx}p $wd/obslist`)
    set cycle = `echo $idx | awk '{print 1000+$1}' | sed 's/1//'`
    echo "Building files for cycle $cycle..."
    set starttime = "`julian options=quiet jday=$mastertime[$idx]`"
    set stoptime = "`julian options=quiet jday=$mastertime[$jidx]`"
    set tfilelist = (`echo $vals[5] $vals[6] | tr ',' ' '`)
    set fileidx = 0
    foreach file (`echo $vals[3] $vals[4] | tr ',' ' '`)
	@ fileidx++
	if (! -e $wd/$tfilelist[$fileidx]$cycle) uvaver vis=$file out=$wd/$tfilelist[$fileidx]$cycle select=time"($starttime,$stoptime)" options=relax,nocal,nopass,nopol > /dev/null
    end
    @ idx++ jidx++
end

recon:
# This "restart" switch is just a simple debugging line, pay no attention to the man behind the curtain.
restart:
set lim = `wc -l $wd/obslist | awk '{print $1}'`

set preidx = 0
set idx = 1
set postidx = 2
set dpostidx = 3


################################################################
#Here begins flagging

while ($idx <= $lim)
    set cycle = `echo $idx | awk '{print 1000+$1}' | sed 's/1//'`
    set cycletime = `date +%s`

    echo "Beginning cycle $cycle (of $lim)..."
    set vals = (`sed -n {$idx}p $wd/obslist`)
    if ($vals[5] == ",") set vals[5]
    if ($vals[6] == ",") set vals[6]
    if ($outsource == "outsource") then
	set flaglist = ($wd/`echo "$vals[5]$vals[6]," | sed 's/,,//g' | sed 's/\,/'$cycle' '$wd'\//g'`$cycle)
    else
	set flaglist = (`echo "$vals[5-6]" | sed 's/\,/ /g'`)
    endif
    if ("$vals[3-4]" == " ") set flaglist
    if ($idx == 1) then
	set starttime = $mastertime2[1]
    else
	set starttime = $mastertime2[$preidx]
    endif

    if ($idx == $lim) then
	set stoptime = $mastertime2[$postidx]
    else
	set stoptime = $mastertime2[$dpostidx]
    endif
    # Here is corruption/decorruption cycle
    if (`echo $idx $corrcycle | awk '{if ($2 != 0) print $1%$2; else print 0}'` == 1) then
	set blim = `echo $idx $corrcycle| awk '{if  ($1 <= int($2/2)) print 1; else print $1-int($2/2)}'`
	set ulim = `echo $idx $lim $corrcycle | awk '{if  ($1+int($3/2) >= $2) print 1+$2; else print $1+int($3/2)}'`
	if ($seedcorr) set blim = $idx
	if ($seedcorr) set ulim = `echo $idx | awk '{print $1+1}'`
	set corrfilelist
	while ($blim <= `echo $ulim | awk '{print $1-1}'`)
	    set altcycle = `echo $blim | awk '{print 1000+$1}' | sed 's/1//'`
	    set corrvals = (`sed -n {$blim}p $wd/obslist`)
	    if ($corrvals[5] == ",") set corrvals[5]
	    if ($corrvals[6] == ",") set corrvals[6]
	    if ($outsource == "outsource") set corrfilelist = ($corrfilelist $wd/`echo "$corrvals[5]$corrvals[6]," | sed 's/,,//g' | sed 's/\,/'$altcycle' '$wd'\//g'`$altcycle)
	    if ($outsource != "outsource") set corrfilelist = ($corrfilelist `echo $corrvals[5]$corrvals[6] | tr ',' ' '`)
	    @ blim++
	end
	set timelim = ($mastertime2[$idx] $mastertime2[$ulim])
	echo "Beginning corruption detection and recovery..."
	if (`echo $vals[5] | wc -w`) then
	    newrfi32.csh vis=$wd/vis select="time($timelim[1],$timelim[2])" rawdata=$wd/specdata > /dev/null
	    newfracture.csh vis=$wd npoly=$cpoly nsig=$csig options=$corr,desel,recover,$rfitype,`if ($debug) echo "verbose"` $csel > $wd/badants
	    echo "time($timelim[1],$timelim[2])" >> $wd/badantshist
	    cat $wd/badants >> $wd/badantshist
	else
	    newrfi32.csh vis=$wd/vis,$wd/tvis select="time($timelim[1],$timelim[2])" rawdata=$wd/specdata
	    newfracture.csh vis=$wd npoly=$cpoly nsig=$csig options=$corr,desel,recover,$rfitype,`if ($debug) echo "verbose"` $csel > $wd/badants
	    echo "No source files, invoking failsafe (tvis) parameter..."
	endif
        echo `grep "DESEL" $wd/badants | tr -d '[a-z][A-Z]:().-' | tr ',' ' ' | wc -w`" potentially corrupted antennas found..."
	grep 'select=pol' $wd/badants > $wd/corrflag
	set jidx = 1
	set jlim = `wc -l $wd/corrflag | awk '{print $1}'`
	if ($fracture == "ignorecorr") set jidx = `echo $jlim | awk '{print $1+1}'`
	while ($jidx <= $jlim)
	    set flagparam = (`sed -n {$jidx}p $wd/corrflag`)
	    if ($fracture == "destroy") set $flagparam[2]
	    foreach file (`echo $corrfilelist`)
		uvflag vis=$file flagval=f options=none "$flagparam[1]" "$flagparam[2]" > /dev/null
	    end
	    echo "Decorruption subcycle $idx.$jidx (of $jlim) complete..."
	    @ jidx++
	end
        echo "Corrupted antennas recovered..."
        set fsel = (`grep "DESEL:" $wd/badants | awk '{print $2,$3}'`)
    endif
    # Improvements made here, no more subcycles, just main cycles
    echo "Beginning cycle $idx (of $lim) scanning..."
    set timesel = "time($starttime,$stoptime)"
    if ($lim == 1) then
	set timefocus
    else if ($idx == 1) then
	set timefocus = "($mastertime2[$idx],$mastertime2[$postidx]),($mastertime2[$postidx],$mastertime2[$dpostidx])"
    else if ($idx == $lim) then
	set timefocus = "($mastertime2[$idx],$mastertime2[$postidx]),($mastertime2[$preidx],$mastertime2[$idx])"
    else
	set timefocus = "($mastertime2[$preidx],$mastertime2[$idx]),($mastertime2[$idx],$mastertime2[$postidx]),($mastertime2[$postidx],$mastertime2[$dpostidx])"
    endif
    if (-e $wd/flagslist) cp $wd/flagslist $wd/flagslist.bu
    if ($flaglist[1] != "") then
	newrfi32.csh vis=$wd/vis options=flagopt,$corr,$rfitype chanlist=$wd/flagslist timefocus="$timefocus" edgerfi=$edgerfi npoly=$npoly nsig=$nsig select="$timesel,$fsel[1] $timesel,$fsel[2]" $csel > /dev/null
    else
#correct code here for display parameters
	echo "No source information found, zooming out..."
	newrfi32.csh vis=$wd/vis,$wd/tvis options=flagopt,$corr,$rfitype chanlist=$wd/flagslist timefocus="$timefocus" edgerfi=$edgerfi nsig=$nsig select="$timesel,$fsel[1] $timesel,$fsel[2]" $csel > /dev/null
    endif
    if (! -e $wd/flagslist && -e $wd/flagslist.bu) cp $wd/flagslist.bu $wd/flagslist
    echo "Beginning cycle $idx (of $lim) flagging. "`grep line=chan $wd/flagslist | tr ',' ' ' | awk '{SUM += $2} END {print SUM}'`" channels to flag in "`grep line=chan $wd/flagslist | wc -l`" iterations."
    set starttime = "`julian options=quiet jday=$mastertime[$idx]`"
    set stoptime = "`julian options=quiet jday=$mastertime[$postidx]`"
    foreach linecmd (`grep "line=chan" $wd/flagslist`)
	foreach file (`echo $flaglist`)
	    uvflag $linecmd vis=$file options=none flagval=f select=time"($starttime,$stoptime)" > /dev/null
	end
	echo -n "."
    end
    echo "."
    @ preidx++ idx++ postidx++ dpostidx++
    echo "Completed cycle. Processing time was "`date +%s | awk '{print int(($1-cycletime)/60)" minute(s) "int(($1-cycletime)%60)" second(s)."}' cycletime=$cycletime`
end

if ($outsource != "outsource") goto finish

set fulllist = (`echo $vis $tvis`)
set listlim = `echo $fulllist | wc -w`
set idx = 1
while ($idx <= $listlim)
    echo "$fulllist[$idx] final flagging..." 
    uvaver vis=$wd/$trlist[$idx]'*' options=relax,nocal,nopass,nopol out=$wd/s$trlist[$idx] 
    uvaflag vis=$fulllist[$idx] tvis=$wd/s$trlist[$idx] 
    if ($autoedge) then
    echo "Edge flagging $fulllist[$idx]"
	if ($autoedgetype == 1) then
	    uvflag vis=$fulllist[$idx] flagval=f options=none edge=1,$autoedgechan,0 > /dev/null
	else if ($autoedgetype == 2) then
	    uvflag vis=$fulllist[$idx] flagval=f options=none edge=$autoedgechan,0,0 > /dev/null
	else if ($autoedgetype == 3) then
	    uvflag vis=$fulllist[$idx] flagval=f options=none edge=$autoedgechan,$autoedgechan,3 > /dev/null
	endif
    endif
    echo "Flagging of $fulllist[$idx] complete!" 
    @ idx++
end

finish:
if !($debug) rm -r $wd
set times = (`date +%s.%N | awk '{print int(($1-date1)/60),int(($1-date1)%60)}' date1=$date1`)
echo "Flagging process took $times[1] minute(s) $times[2] second(s)."

exit 0

fail:

exit 1
