#! /usr/bin/tcsh -f

set date1 = `date +%s.%N`

onintr fail

if ($#argv == 0) then
    echo "NEWFRACTURE.CSH"
    echo "newfracture.csh is a tool to identify potentially corrupted antennas via spectral count information."
    echo "newfracture uses newrfi32 to look at count spectra on an antenna-by-antenna basis, and identify those"
    echo "antennas that do not appear to have a similar RFI pattern as other antennas." 
    echo "Calling sequence: newfracture.csh vis=vis crange=crange select=select timefocus=timefocus corredge=corredge npoly=npoly nsig=nsig spoly=spoly ssig=ssig options={display, nodisplay, asel, desel, corr, nocorr, scorr, noscorr, pos, neg, mixed}"
    echo "REQUIRED INPUTS:"
    echo "vis - Name of the files that contain spectral count information"
    echo "OPTIONAL INPUTS:"
    echo "crange - allows for selection or deselection of ranges. Multiple ranges can be specified, seperated"
    echo "by commas. Useful for ignoring edge/corrupted channels e.g. crange='(100,800),-(512),-(620,640)'."
    echo "select - MIRIAD style selection. Current support for pol,ant and time selection. Multiple subselect"
    echo "commands should be seperated by commas, multiple independant select commands can be entered and"
    echo "seperated by spaces (but enclosed with quotes). e.g. select='time(12,13) time(14,15),ant(12)(35)'."
    echo "corredge - Minimum number of channels (in a block) required to be identified as corruption. Default"
    echo "is 32, although 16 works well also."
    echo "npoly - Order polynomial to use for correcting spectrum. Default is 5."
    echo "nsig - Number of sigma at which to ID RFI. Default is 3."
    echo "spoly - Order polynomial to use for correcting spectrum of individual antennas. Default is 5."
    echo "Options:"
	echo "display,nodisplay - display (or not) results of processing. Default is display"
	echo "corr,nocorr - polynomial correct (or not) final count spectrum. Default is no correction."
	echo "scorr,noscorr - polynomial correct (or not) individual antenna spectrum. Default is no correction."
	echo "pos,neg,mixed - identify RFI (or corruption) as having counts that are too high, too low or both." 	
	echo "Default is high (pos)."
	echo "asel,desel - creates selection (or deselection) command for corrupted antennas in dataset."
	echo "recover - fracture can attempt to generate line selection commands for flagging of corruption in"
	echo "individual antennas"
	echo "verbose - move into debugging mode (displays individual antenna spectra)."
    exit 0
endif

set csel
set vis
set msel
set display = "display"
set recover = "norecover"
set quiet = "quiet"
set desel = "nosel"
set asel = "nosel"
set corredge = 32
set spoly = 5
set npoly = 5
set nsig = 5
set rfitype = "pos"
set corr = "corr"
set scorr = "corr"
set badlim = 5

varassign:

if ("$argv[1]" =~ 'vis='*) then
    set vis = "`echo '$argv[1]/' | sed 's/vis=//g'`"
    set vis = (`echo $vis | sed 's/\/ / /g' | sed 's/\(.*\)\//\1/g'| sed 's/\.specdata//g' | tr ',' ' '`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'select='*) then
    set msel = (`echo "$argv[1]" | sed 's/select=//g' | tr '[A-Z]' '[a-z]'`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'crange='*) then
    set csel = `echo "$argv[1]"`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'corredge='*) then
    set corredge = `echo "$argv[1]" | sed 's/corredge=//g' | awk '{print int($1*1)}'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'options='*) then
    set options = `echo "$argv[1]" | sed 's/options=//g' | tr ',' ' ' | tr '[A-Z]' '[a-z]'`
    set badopt
    foreach option (`echo $options`)
	if ($option == "display") then
	    set display = "display"
	else if ($option == "nodisplay") then
	    set display = "nodisplay"
	else if ($option == "recover") then
	    set recover = "recover"
	else if ($option == "verbose") then
	    set quiet = "verb"	    
	else if ($option == "desel") then
	    set desel = "desel"
	else if ($option == "asel") then
	    set asel = "asel"
	else if ($option == "corr") then
	    set corr = "corr"
	else if ($option == "scorr") then
	    set scorr = "corr"
	else if ($option == "noscorr") then
	    set scorr = "nocorr"
	else if ($option == "nocorr") then
	    set corr = "nocorr"
	else if ($option == "pos") then
	    set rfitype = "pos"
	else if ($option == "neg") then
	    set rfitype = "neg"
	else if ($option == "mixed") then
	    set rfitype = "mixed"
	else
	    set badopt = ($badopt $option)
	endif
    end
    if ("$badopt" != "") echo 'options='`echo $badopt | tr ' ' ','`' not recognized!'
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'npoly='*) then
    set npoly = (`echo "$argv[1]" | sed 's/npoly=//g' | awk '{print 1+int($1*1)}'`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'spoly='*) then
    set spoly = (`echo "$argv[1]" | sed 's/spoly=//g' | awk '{print 1+int($1*1)}'`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'nsig='*) then
    set nsig = `echo "$argv[1]" | sed 's/nsig=//g'`
    shift argv; if ("$argv" == "") set argv = "finish"
else
    echo "FATAL ERROR: $argv[1] not recognized..."
    exit 1
endif

if ("$argv[1]" != "finish") goto varassign


if ("$vis" == "") then
    echo "FATAL ERROR: No inputs files."
endif

    
foreach ifile (`echo $vis`)
    if (! -e $ifile/specdata) then
        if (-e $ifile/visdata) then
            echo "Spectral scanning data not found, running scanner..."
            newrfi.csh vis=$ifile
        else
            echo "FATAL ERROR: No specdata or visibilities found!"
            exit 1
        endif
    endif
end

set wd = `mktemp -d rfi4XXXXX`

if ($wd == "") then #Can the program create a temp directory?
    echo "FATAL ERROR: Problems creating temp directory. Make sure you have permissions for the current directory. Now exiting..."
    goto fail
endif

if (`echo $corredge | awk '{if ($1*1 < 4) print "nogo"}'` == "nogo") then
    echo "Edge corruption detection below minimum threshold (4). Setting corredge to 8..."
    set corredge = 8
endif

if (`echo $vis | wc -w` > 1) then
    set vis = `echo $vis | tr ' ' ','`
endif 

if ("$msel" == "") set msel

newrfi32.csh vis="$vis" options=nodisplay select="$msel" rawdata=$wd/specdata  "$csel" > /dev/null

set fants
set sel

cat $wd/specdata | awk '{if ($3 == "XX") printf "%s\n%s\n",$1"-x",$2"-x"; else if ($3 == "YY") printf "%s\n%s\n",$1"-y",$2"-y"; else if ($3 == "XY") printf "%s\n%s\n",$1"-x",$2"-y"; else if ($3 == "YX") printf "%s\n%s\n",$1"-y",$2"-x"}' | sort -u | tr '-' ' ' > $wd/antslist

set lim = `wc -l $wd/antslist | awk '{print $1}'`
set iidx = 1
if ($quiet == "verb") echo "$lim inputs to sort through."

while ($iidx <= $lim)
    set vals = (`sed -n {$iidx}p $wd/antslist`)
    if ($quiet == "verb") echo "Moving on to $vals"
    set sel = "`echo ' $msel' | sed 's/ / pol('$vals[2]$vals[2]'),ant('$vals[1]'),/g'`"
    echo -n "$vals " >> $wd/badlist
    set pvals = (`newrfi32.csh vis=$wd options=nodisplay,$scorr,$rfitype select="$sel" npoly=$spoly nsig=$nsig "$csel" | grep "bad channels detected" | tr '()' ' ' | awk '{print $5,$7,$11}'`)
    if ($quiet == "verb") echo -n "Antenna $vals "
    if ($quiet == "verb") newrfi32.csh vis=$wd options=display,$rfitype,$scorr npoly=$spoly nsig=$nsig select="$sel" "$csel" | grep "bad channels detected"
    echo $pvals >> $wd/badlist

    @ iidx++
end
set midchan = `wc -l $wd/badlist | awk '{print int($1/2)}'`
set midbad = `sort -nk4 $wd/badlist | awk '{if (NR == midchan) print $4^.5}' midchan=$midchan`
if ($midbad == 0) set midbad = 1
set midcorr = `sort -nk5 $wd/badlist | awk '{if (NR == midchan) print $5}' midchan=$midchan`
if ($midcorr == 0) set midcorr = 1
set sigbad = `awk '{if ($4^.5 <= midbad) SIG += ($4^.5-midbad)^2} END {if ((SIG/midchan)^.5 > 1) print (SIG/midchan)^.5; else print "1"}' midbad=$midbad midchan=$midchan $wd/badlist`
set sigcorr = `awk '{if ($5 <= midcorr) SIG += ($5-midcorr)^2} END {if ((SIG/midchan)^.5 > 1) print (SIG/midchan)^.5; else print "1"}' midcorr=$midcorr midchan=$midchan $wd/badlist`
set badants = ("dummy" `awk '{if ($4^.5 > midbad) if ($5 > midcorr) print $1$2,($4^.5-midbad)/sigbad+($5-midcorr)/sigcorr}'  midcorr=$midcorr midbad=$midbad midchan=$midchan sigcorr=$sigcorr sigbad=$sigbad $wd/badlist | awk '{if ($2 > badlim) print $1,.5*int(2*$2)}' badlim=$badlim`)
set xbad
set ybad
if ($#badants >= 2) then
    shift badants
    echo `echo $#badants | awk '{print int($1/2)}'`" corrupted antennas found"
    set iidx = 1
    echo "Antenna   Corruption Score"
    while ($iidx < $#badants)
	echo -n "$badants[$iidx]       "
	if ($badants[$iidx] =~ *x) set xbad = ($xbad `echo $badants[$iidx] | tr -d 'x'`)
	if ($badants[$iidx] =~ *y) set ybad = ($ybad `echo $badants[$iidx] | tr -d 'y'`)
	@ iidx++
	echo "$badants[$iidx]"
	@ iidx++
    end
else 
    echo "0 corrupted antennas found!"
endif

if ("$xbad" == "") then
    set xdsel = "pol(xx)"
else
    set xdsel = "pol(xx),-ant("`echo $xbad | tr ' ' ','`")"
endif

if ("$ybad" == "") then
    set ydsel = "pol(yy)"
else
    set ydsel = "pol(yy),-ant("`echo $ybad | tr ' ' ','`")"
endif

if ($display == "display" && $quiet != "verb") then
    newrfi32.csh vis=$wd options=display,$corr npoly=$npoly select="$xdsel $ydsel" edgerfi=$patedge chanlist=$wd/goodbadchans "$csel"
    if ("$xdsel $ydsel" != "pol(xx) pol(yy)") then
	echo "Displaying good antenna spectra"
	foreach xant (`echo $xbad`)
	    echo "Press ENTER to see corrupted count spectra for antenna $xant-X"
	    set dummy = $<
	    set sel = "`echo ' $msel' | sed 's/ / pol(xx),ant('$xant'),/g'`"
	    newrfi32.csh vis=$wd options=display,$scorr npoly=$spoly select="$sel" "$csel"
	end
	foreach yant (`echo $ybad`)
	    echo "Press ENTER to see corrupted count spectra for antenna $yant-Y"
	    set dummy = $<
	    set sel = "`echo ' $msel' | sed 's/ / pol(yy),ant('$yant'),/g'`"
	    newrfi32.csh vis=$wd options=display,$scorr npoly=$spoly select="$sel" "$csel"
	end
    endif
else
    newrfi32.csh vis=$wd options=nodisplay,$corr npoly=$npoly select="$xdsel $ydsel" chanlist=$wd/goodbadchans "$csel" > /dev/null
endif

if ($desel == "desel") then
    echo "Deselection parameters for bad antennas are:"
    echo "DESEL: $xdsel $ydsel"
endif

if ($asel == "asel") then
    echo "Selection parameters for bad antennas are:"
    if ("$xdsel" != "pol(xx)" || "$ydsel" != "pol(yy)" ) then
	echo "ASEL: $xdsel $ydsel " | sed -e 's/pol(..) //g' -e 's/-//g'

    else
    echo "No corrupted antennas found - no selection parameters!"
    endif
endif

if ($recover != "recover") goto finish

set dchans = (`grep -v o $wd/goodbadchans | awk '{print "-("$1")"}'`)
set dchansel = `echo "$dchans" | tr ' ' ','`

if ("$csel" == "") then
    set csel = "crange=$dchansel"
else
    set csel = "$csel,$dchansel"
endif

set chans = `head -n 1 $wd/specdata | wc -w | awk '{print $1-14}'`
set edgelim = `echo $corredge | awk '{print int(2.5*$1)}'`
set chanlim = `echo $chans $corredge | awk '{print $1-((2*$2)+1)}'`
set chanlim2 = `echo $chans $corredge | awk '{print $1-($2+1)}'`

foreach xant (`echo $xbad`)
    set marker = 0
    set fmarker = 0
    set fomarker = 0
    echo "Flagging parameters for $xant-X" 
    set sel = "`echo ' $msel' | sed 's/ / pol(xx),ant('$xant'),/g'`"
    newrfi32.csh vis=$wd options=nodisplay,$scorr,$rfitype,flagopt select="$sel" edgerfi=$corredge npoly=$spoly nsig=$nsig chanlist=$wd/badchanlist optlim=$chans "$csel" > /dev/null
    foreach linecmd (`grep line $wd/badchanlist | grep -v MIRIAD`)
	set vals = (`echo $linecmd | sed -e 's/line=chan,//g' -e 's/,/ /g'`)
	if ($vals[1] > $edgelim || `echo $vals[1] $vals[2] | awk '{if ($2 > chanlim2 || $1 == 1) print "0"; else print $1+$2-1}' chanlim2=$chanlim2` == $chans) then
	    echo "select=pol(xx),ant($xant) line=chan,"`echo $vals[1] $vals[2] | awk '{if (($1+$2-1) == chans) print $1-int(corredge/2)","$2+int(corredge/2); else print $1-corredge","$2+int(corredge/2)}' chans=$chans corredge=$corredge`
	    @ marker++
	else if ($fomarker == $vals[2]) then
	    @ fomarker++
	else if ($vals[1] == 1 && $vals[2] <= $chanlim2) then
	    set fmarker = $vals[2]
	    set fomarker = $vals[2]
	    @ fomarker++	    
	endif
	while ("$dchans" =~ *"-($fomarker)"*)
	    @ fomarker++
	end
	if ($fomarker > $chans) then
	    echo "select=pol(xx),ant($xant) line=chan,"`echo $fomarker $fmarker | awk '{print $1-$2-int(corredge/2)","$2+int(corredge/2)}' corredge=$corredge`
	    @ marker++
	endif
    end
    if ($marker == 0) echo "No corruption patterns found!"
end

foreach yant (`echo $ybad`)
    set marker = 0
    set fmarker = 0
    set fomarker = 0
    echo "Flagging parameters for $yant-Y"
    set sel = "`echo ' $msel' | sed 's/ / pol(yy),ant('$yant'),/g'`"
    newrfi32.csh vis=$wd options=nodisplay,$scorr,$rfitype,flagopt select="$sel" edgerfi=$corredge npoly=$spoly nsig=$nsig chanlist=$wd/badchanlist optlim=$chans "$csel" > /dev/null
    foreach linecmd (`grep line $wd/badchanlist | grep -v MIRIAD`)
	set vals = (`echo $linecmd | sed -e 's/line=chan,//g' -e 's/,/ /g'`)
	if ($vals[1] > $edgelim || `echo $vals[1] $vals[2] | awk '{if ($2 > chanlim2 || $1 == 1) print "0"; else print $1+$2-1}' chanlim2=$chanlim2` == $chans) then
	    echo "select=pol(yy),ant($yant) line=chan,"`echo $vals[1] $vals[2] | awk '{if (($1+$2-1) == chans) print $1-int(corredge/2)","$2+int(corredge/2); else print $1-corredge","$2+int(corredge/2)}' chans=$chans corredge=$corredge`
	    @ marker++
	else if ($fomarker == $vals[2]) then
	    @ fomarker++
	else if ($vals[1] == 1 && $vals[2] <= $chanlim2) then
	    set fmarker = $vals[2]
	    set fomarker = $vals[2]
	    @ fomarker++
	endif
	if ($fomarker > $chans) then
	    echo "select=pol(yy),ant($yant) line=chan,"`echo $fomarker $fmarker | awk '{print $1-$2-int(corredge/2)","$2+int(corredge/2)}' corredge=$corredge`
	    @ marker++
	endif
    end
    if ($marker == 0) echo "No corruption patterns found!"
end

finish:

set times = (`date +%s.%N | awk '{print int(($1-date1)/60),int(($1-date1)%60)}' date1=$date1`)
echo "Scanning process took $times[1] minute(s) $times[2] second(s)."

rm -r $wd

exit 0

fail:
rm -r $wd
echo "Houston, we have a problem"
exit 1
