#! /usr/bin/tcsh -f
# $Id$
set date1 = `date +%s.%N`

onintr fail
      #################################################################
echo "================================================================="
echo "FRACTURE - Spectral corruption spotting utility"
echo "'Yup, looks like a broken spectra, looks like we're gonna have to"
echo " put 'er down.'"
echo ""
echo "CALLS - newrfi.csh,newrfi32.csh"
echo "PURPOSE - Identify antennas with spectral corruption."
echo "RESPONSIBLE - Karto (karto@hcro.org)"
echo "================================================================="
echo ""
echo "FRACTURE is designed as a scanning utility for finding spectral"
echo "corruption in datasets. FRACTURE uses the results of RFILOCK to"
echo "find possible corruption candidates. FRACTURE works best with"
echo "datasets with continuum emission only, and datasets with"
echo "either passband corrections previously derived or with datasets"
echo "that have less that roughly 10 Jy of total emission in the"
echo "primary beam/FOV. FRACTURE also requires a moderate number of"
echo "antennas (upwards of a dozen) in order to be effective."
echo ""
echo "FRACTURE operates by running the RFILOCK scanning utility for"
echo "finding polluted channel for each antenna in the dataset. The"
echo "program will then compare the results of each scan (the number"
echo "of high channels and the so-called 'corruption score', which is"
echo "a count of the number of RFI channels that appear within 4"
echo "channels of other RFI channels) to find possible candidates for"
echo "spectral corruption. The program can also be used to evaluate"
echo "where the corruption exists, using RFILOCK's 'flagopt' switch"
echo "to find ranges of bad channels that meet certain requirements"
echo "(i.e. ranges must contain a minimum number of channels)."
echo ""
echo "FRACTURE makes no modifications of datasets, and is therefore"
echo "'safe' to rerun on a dataset without consequence. Users should"
echo "be aware that FRACTURE will only look at the last 'specdata' file"
echo "created (by RFISCAN) by default. Users will need to rerun"
echo "RFISCAN to capture any changes made to the dataset (i.g. new"
echo "flags or gains solutions)."
echo ""
echo "TECHNICAL NOTE: FRACTURE creates a temporary directory to work"
echo "from, named rfi4XXXXX (where X is a random character). These"
echo "directories are supposed to be automatically deleted after"
echo "RFILOCK completes, but might remain in the event of a program"
echo "error. Remnant directories can be safely deleted."
echo ""
echo "CALLING SEQUENCE: newfracture.csh vis=vis (select=select"
echo "    corredge=corredge npoly=npoly nsig=nsig crange=crange "
echo "    options=asel,desel,[corr, nocorr],[pos,neg, mixed],recover)"
echo ""
echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo ""
echo "REQUIRED INPUTS:"
echo " vis - Name of the files containing source data. Supports"
echo "    multiple files and wildcard expansion. No default."
echo ""
echo "OPTIONAL INPUTS:"
echo " select - Data to be processed by FRACTURE. Supports MIRIAD style"
echo "    selection of antennas (e.g. ant(1),-ant(1)(2) will select all"
echo "    baselines for antenna 1 EXCEPT for baseline 1-2), time"
echo "    selection (e.g. time(12,13) will select all data between"
echo "    1200 and 1300), polarization selection (e.g. pol(xy,yx) will"
echo "    select all cross-pol baselines) and auto/crosscorrelation"
echo "    (e.g. -auto for all cross correlatrions). Multiple select"
echo "    commands can be put together using a comma (which acts as an"
echo "    AND operator) or a space (which operates as an OR operator)."
echo "    All select commands must be entered as a single string (e.g."
echo "    select='ant(1),pol(xx) ant(2),pol(yy)' will select all XX"
echo "    baselines for antenna 1 and all YY baselines for antenna 2)."
echo "    Default is all data."
echo ""
echo " crange - Channel range(s) to be analyzed by FRACTURE. Individual"
echo "    ranges must be enclosed within a pair of parentheses, with"
echo "    a comma seperating different ranges (e.g. crange=(1),(2,5))."
echo "    Ranges can be either 'positive' or 'negative' (e.g. crange="
echo "    (100) will select only channel 100, while crange=-(100) will"
echo "    select everything but channel 100), and can give either a"
echo "    single channel or a range of channels (e.g. crange=(2,5)"
echo "    will select all channels between 2 and 5). This can be very"
echo "    useful for removing channels that are known to contain"
echo "    spectral line emission so that they are not mistakenly"
echo "    identified as corruption. Default is all channels."
echo ""
echo " corredge - Minimum expected length of corruption (in number of"
echo "    channels). This parameter filters out smaller channel blocks"
echo "    (which are normally RFI, NOT corruption) from being IDed as"
echo "    spectral corruption. Default is 16."
echo ""
echo " nsig - How far from the 'center' (in sigma) of the band at"
echo "    which to identify channels as 'bad'. See documentation for"
echo "    RFILOCK for further details."
echo ""
echo " npoly - Order of polynomial to apply for passband feature"
echo "    removal. See documentation for RFILOCK for further details" 
echo ""
echo " options=asel,desel,[corr, nocorr],[pos,neg, mixed],debug,"
echo "    recover"
echo "    asel - Generate a MIRIAD style select command for antennas"
echo "        with spectral corruption (e.g. if ant 1X & 2Y are IDed"
echo "        as bad, FRACTURE will print out 'ASEL: ant(1),pol(xx)"
echo "        ant(2),pol(yy)' to the terminal)."
echo "    desel -  Generate a MIRIAD style select command for antennas"
echo "        without corruption (e.g. if ant 1X & 2Y are IDed as bad,"
echo "        FRACTURE will print out 'ASEL: -ant(1),pol(xx) -ant(2),"
echo "        pol(yy)')."
echo "    corr - Correct for bandpass features via a polynomial fit."
echo "    nocorr - Don't correct for bandpass features. (Default)"
echo "    pos - only ID those channels ABOVE the passband as being"
echo "        corruption candidates (i.e. channels several sigma below"
echo "        the passband will not be IDed as corruption). (Default)"
echo "    neg - only ID those channels BELOW the passband as being"
echo "        corruption candidates (i.e. channels several sigma above"
echo "        the passband will not be IDed as corruption)."
echo "    mixed - Channels above and below the passband that exceed"
echo "        the sigma threshhold are IDed as corruption."
echo "    recover - Attempt to determine which channel ranges are"
echo "        corrupted for each bad antenna. Results are returned"
echo "        as a MIRIAD style line-selection command for easy"
echo "        capture for flagging programs."
exit 0
endif

set csel # Channel range selection
set vis # Name of files to be processed
set msel # MIRIAD style selection commands
set display = 1 # Display results?
set recover = 0 # Attempt to recover bad ants?
set quiet = "quiet" # Do debugging display
set desel = 0 # Provide deselection command?
set asel = 0 # Provide bad ant selection command?
set corredge = 32 # Minimum length of corruption
set npoly = 5 # order polynomial correction to apply to passbands
set nsig = 5 # number of sigma out to be IDed as bad
set rfitype = "pos" # channels above, below (or both) band to be IDed as bad?
set corr = "corr" # use corrective polynomial to remove passband features?
set badlim = 5 # debugging parameter

#################################################################
# Here is the keyword/value pairing code. It basically operates
# by going through each argument, attempting to figure out which
# keyword matches (via an if arguement) and sets the value
# accordingly
#################################################################

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
else if ("$argv[1]" =~ 'device='*) then
    set device = "$argv[1]"
    set display = 1
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'options='*) then
    set options = `echo "$argv[1]" | sed 's/options=//g' | tr ',' ' ' | tr '[A-Z]' '[a-z]'`
    set badopt
    foreach option (`echo $options`)
	if ($option == "recover") then
	    set recover = 1
	else if ($option == "verbose") then
	    set quiet = "verb"	    
	else if ($option == "desel") then
	    set desel = 1
	else if ($option == "asel") then
	    set asel = 1
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

#################################################################
# The program creates a temp directory to work in within the
# data directory being used. This is done to make operations
# "cleaner", as several MIRIAD results are dumped to temp files
# to be parsed later.
#################################################################

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

# Use RFILOCK to concatonate all of the possible specdata files together, and remove any unneeded data

newrfi32.csh vis="$vis" select="$msel" rawdata=$wd/specdata  "$csel" > /dev/null

set fants
set sel

# Determine how many antennas there are to sort through

cat $wd/specdata | awk '{if ($3 == "XX") printf "%s\n%s\n",$1"-x",$2"-x"; else if ($3 == "YY") printf "%s\n%s\n",$1"-y",$2"-y"; else if ($3 == "XY") printf "%s\n%s\n",$1"-x",$2"-y"; else if ($3 == "YX") printf "%s\n%s\n",$1"-y",$2"-x"}' | sort -u | tr '-' ' ' > $wd/antslist

set lim = `wc -l $wd/antslist | awk '{print $1}'`
set iidx = 1
if ($quiet == "verb") echo "$lim inputs to sort through."


#################################################################
# One the program has all of the data together, it will move
# antpol by antpol and process spectra, grabbing the number of
# bad channels and the corruption score for each result. Of
# course, each antenna is going to have baselines with all other
# antennas, so corruption will technically be seen in all
# antennas. This is why a higher number of antennas is important
# since a greater number of 'good' baselines will wash away the
# corruption seen in the bad antennas, so that only the bad
# antenna will show up with significant corruption. After the
#################################################################

while ($iidx <= $lim)
    set vals = (`sed -n {$iidx}p $wd/antslist`)
    if ($quiet == "verb") echo "Moving on to $vals"
    set sel = "`echo ' $msel' | sed 's/ / pol('$vals[2]$vals[2]'),ant('$vals[1]'),/g'`"
    echo -n "$vals " >> $wd/badlist
    set pvals = (`newrfi32.csh vis=$wd options=$corr,$rfitype select="$sel" npoly=$npoly nsig=$nsig "$csel" | grep "bad channels detected" | tr '()' ' ' | awk '{print $5,$7,$11}'`)
    if ($quiet == "verb") echo -n "Antenna $vals "
    if ($quiet == "verb") newrfi32.csh vis=$wd display=/xs options=$rfitype,$corr npoly=$npoly nsig=$nsig select="$sel" "$csel" | grep "bad channels detected"
    echo $pvals >> $wd/badlist

    @ iidx++
end

# Gather some stats, calculate what the 'nominal' bad number of channels and corruption scores are
set midchan = `wc -l $wd/badlist | awk '{print int($1/2)}'`
set midbad = `sort -nk4 $wd/badlist | awk '{if (NR == midchan) print $4^.5}' midchan=$midchan`
if ($midbad == 0) set midbad = 1
set midcorr = `sort -nk5 $wd/badlist | awk '{if (NR == midchan) print $5}' midchan=$midchan`
if ($midcorr == 0) set midcorr = 1
set sigbad = `awk '{if ($4^.5 <= midbad) SIG += ($4^.5-midbad)^2} END {if ((SIG/midchan)^.5 > 1) print (SIG/midchan)^.5; else print "1"}' midbad=$midbad midchan=$midchan $wd/badlist`
set sigcorr = `awk '{if ($5 <= midcorr) SIG += ($5-midcorr)^2} END {if ((SIG/midchan)^.5 > 1) print (SIG/midchan)^.5; else print "1"}' midcorr=$midcorr midchan=$midchan $wd/badlist`

# Find any antennas that exceed a certain 'badness' rating

set badants = ("dummy" `awk '{if ($4^.5 > midbad) if ($5 > midcorr) print $1$2,($4^.5-midbad)/sigbad+($5-midcorr)/sigcorr}'  midcorr=$midcorr midbad=$midbad midchan=$midchan sigcorr=$sigcorr sigbad=$sigbad $wd/badlist | awk '{if ($2 > badlim) print $1,.5*int(2*$2)}' badlim=$badlim`)
set xbad
set ybad

# Spew out results of bad antennas

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

# If the user wants, show count spectra from good and bad antennas

if ($display && $quiet != "verb") then
    newrfi32.csh vis=$wd options=$corr npoly=$npoly select="$xdsel $ydsel" chanlist=$wd/goodbadchans $device "$csel"
    if ("$xdsel $ydsel" != "pol(xx) pol(yy)") then
	echo "Displaying good antenna spectra"
	foreach xant (`echo $xbad`)
	    echo "Press ENTER to see corrupted count spectra for antenna $xant-X"
	    set dummy = $<
	    set sel = "`echo ' $msel' | sed 's/ / pol(xx),ant('$xant'),/g'`"
	    newrfi32.csh vis=$wd options=$corr npoly=$npoly select="$sel" $display "$csel"
	end
	foreach yant (`echo $ybad`)
	    echo "Press ENTER to see corrupted count spectra for antenna $yant-Y"
	    set dummy = $<
	    set sel = "`echo ' $msel' | sed 's/ / pol(yy),ant('$yant'),/g'`"
	    newrfi32.csh vis=$wd options=$corr npoly=$npoly select="$sel" $display "$csel"
	end
    endif
else
    newrfi32.csh vis=$wd options=$corr npoly=$npoly select="$xdsel $ydsel" chanlist=$wd/goodbadchans "$csel" > /dev/null
endif

if ($desel) then
    echo "Deselection parameters for bad antennas are:"
    echo "DESEL: $xdsel $ydsel"
endif

if ($asel) then
    echo "Selection parameters for bad antennas are:"
    if ("$xdsel" != "pol(xx)" || "$ydsel" != "pol(yy)" ) then
	echo "ASEL: $xdsel $ydsel " | sed -e 's/pol(..) //g' -e 's/-//g'

    else
    echo "No corrupted antennas found - no selection parameters!"
    endif
endif

if !($recover) goto finish

#################################################################
# If the 'recover' parameter is invoked, the program will use
# RFILOCK to ID bad channel ranges in the corrupted antennas,
# deselecting channels with RFI and looking for 'chains' of bad
# channels that exceed the 'edgerfi' limit. This can serve as
# a useful 'doublecheck' for making sure that antennas IDed
# as bad have actually corruption within them. Results are
# returned to the terminal, for easy capture for flagging.
#################################################################

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
    newrfi32.csh vis=$wd options=$corr,$rfitype,flagopt select="$sel" edgerfi=$corredge npoly=$npoly nsig=$nsig chanlist=$wd/badchanlist optlim=$chans "$csel" > /dev/null
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
    newrfi32.csh vis=$wd options=$corr,$rfitype,flagopt select="$sel" edgerfi=$corredge npoly=$npoly nsig=$nsig chanlist=$wd/badchanlist optlim=$chans "$csel" > /dev/null
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
