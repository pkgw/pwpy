#! /bin/tcsh -f
# $Id$
onintr fail

if ($#argv == 0) then
      #################################################################
echo "================================================================="
echo "RFILOCK - RFI spotting utility"
echo "'That's no moon, it's an interference signal...'"
echo ""
echo "CALLS - newrfi.csh, newrfi32.csh (recursive), WIP"
echo "PURPOSE - Identify channels with RFI pollution."
echo "RESPONSIBLE - Karto (karto@hcro.org)"
echo "================================================================="
echo ""
echo "RFILOCK is designed as simple scanner for finding RFI in"
echo "datasets. RFILOCK will use the results of the RFISCAN spectral"
echo "datasets to find possible RFI candidates. RFILOCK works best"
echo "with datasets with continuum emission only, and datasets with"
echo "either passband corrections previously derived or with datasets"
echo "that have less that roughly 10 Jy of total emission in the"
echo "primary beam/FOV."
echo
echo "RFILOCK operates by taking a selected portion of the spectral"
echo "occupancy data (count of the number of times each channel rises"
echo "4 sigma above the average of the band), doing some polynomial"
echo "fitting (to remove bandpass features), and finding channels with"
echo "spectral occupancies some sigma away from the median of the"
echo "distribution. This information is reported back to the user."
echo ""
echo "RFILOCK makes no modifications of datasets, and is therefore"
echo "'safe' to rerun on a dataset without consequence. Users should"
echo "be aware that RFILOCK will only look at the last 'specdata' file"
echo "created (by RFISCAN) by default. Users will need to rerun"
echo "RFISCAN to capture any changes made to the dataset (i.e. new"
echo "flags or gains solutions)."
echo ""
echo "TECHNICAL NOTE: RFILOCK creates a temporary directory to work"
echo "from, named rfi2XXXXX (where X is a random character). These"
echo "directories are supposed to be automatically deleted after"
echo "RFILOCK completes, but might remain in the event of a program"
echo "error. Remnant directories can be safely deleted."
echo ""
echo "CALLING SEQUENCE: newrfi.csh vis=vis (select=select nsig=nsig"
echo "    npoly=npoly crange=crange timefocus=(timefocus1,timefocus2)"
echo "    tsig=tsig chanlist=chanlist logfile=logfile optlim=optlim"
echo "    device=device options=[corr,nocorr],corrdisp,[pos,neg,mixed]"
echo "    ,flagopt)"
echo ""
echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo ""
echo "REQUIRED INPUTS:"
echo " vis - Name of the files containing source data. Supports"
echo "    multiple files and wildcard expansion. No default."
echo ""
echo "OPTIONAL INPUTS:"
echo " select - Data to be processed by RFILOCK. Supports MIRIAD style"
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
echo " nsig - How far from the 'center' (in sigma) of the band at"
echo "    which to identify channels as 'bad'. RFILOCK works by trying"
echo "    to fit a Gaussian distribution to the median channels"
echo "    (approximately the middle 10 percent), and derives sigma"
echo "    from this fit. Default is 3."
echo ""
echo " npoly - Order of polynomial to apply for passband feature"
echo "    removal. The polynomial correction is applied after a first"
echo "    pass through the data to remove any points that appear"
echo "    to be RFI. Default is 6." 
echo ""
echo " crange - Channel range(s) to be analyzed by RFILOCK. Individual"
echo "    ranges must be enclosed within a pair of parentheses, with"
echo "    a comma seperating different ranges (e.g. crange=(1),(2,5))."
echo "    Ranges can be either 'positive' or 'negative' (e.g. crange="
echo "    (100) will select only channel 100, while crange=-(100) will"
echo "    select everything but channel 100), and can give either a"
echo "    single channel or a range of channels (e.g. crange=(2,5)"
echo "    will select all channels between 2 and 5). This can be very"
echo "    useful for removing channels that are known to contain"
echo "    spectral line emission so that they are not mistakenly"
echo "    identified as RFI. Default is all channels."
echo ""
echo " timefocus - Range of times (in either Julian dates or time of"
echo "    day) to be reanalyzed. Time ranges must be enclosed in"
echo "    parentheses, and may be used to specify all data that"
echo "    'overlaps' a particular time (e.g. timefocus='(12:00)' will"
echo "    select any data taken at noon) or all data within a range of"
echo "    time (e.g. timefocus='(13,15)' will select all data between"
echo "    1300 and 1500). Multiple timefocus selections can be issued."
echo "    The timefocus parameter is useful for finding transient RFI"
echo "    that may be only located in one particular time range."
echo "    Channels identified as 'bad' will be added to the 'master'"
echo "    list of channels created when analyzing the entire dataset."
echo "    Default in none."
echo ""
echo " tsig - How far from the 'center' (in sigma) of the band at"
echo "    which to identify channels as 'bad' for the timefocus ranges"
echo "    specified by the user. This parameter is not used unless the"
echo "    user invokes the 'timefocus' parameter. Default is 4."
echo ""
echo " edgerfi - Padding (in channels) around each RFI polluted"
echo "    channel to also identify as bad (e.g. if channel 3 is IDed"
echo "    as 'bad' and edgerfi=1, then channels 2,3 and 4 will be"
echo "    marked as bad. Helpful for protecting against RFI that"
echo "    shifts frequencies over time, and broadband RFI. Default is"
echo "    1."
echo ""
echo " logfile - Name of log file to write debugging information to."
echo "    No default."
echo ""
echo " chanlist - Name of log file to write out a listing of bad"
echo "    channels. Useful if planning to pipe the results of RFILOCK"
echo "    to a flagging program."
echo ""
echo " optlim - Debugging parameter for 'flagopt' option, determines"
echo "    the minimum number of channels to be grouped together as bad"
echo "    in order to proceed with optimization."
echo ""
echo " device - Device to plot results to (e.g. /xw for x-window)."
echo '    Default is /null'
echo ""
echo " options=[corr,nocorr],corrdisp,[pos,neg,mixed],flagopt"
echo ""
echo "    corr - Correct for bandpass features via a polynomial fit."
echo "    nocorr - Don't correct for bandpass features. (Default)"
echo "    corrdisp - Display intermediate results of polynomial fit"
echo "        (Useful for debugging purposes)."
echo "    pos - only ID those channels ABOVE the passband as being"
echo "        RFI candidates (i.e. channels several sigma below the"
echo "        passband will not be IDed as RFI). (Default)"
echo "    neg - only ID those channels BELOW the passband as being"
echo "        RFI candidates (i.e. channels several sigma above the"
echo "        passband will not be IDed as RFI)."
echo "    mixed - Channels above and below the passband that exceed"
echo "        the sigma threshhold are IDed as RFI"
echo "    flagopt - Creates MIRIAD style line selection commands with"
echo "        a focus on minimizing the number of line-selections"
echo "        needed to 'cover' all polluted channels. This can be"
echo "        helpful in polluted bands where long strings of"
echo "        channels may be polluted."
echo "    debug - Keep intermediate processing files."
exit 0
endif

set file #File(s) to be scanned
set display = 0 # Whether or not to display results
set corr = "corr" # Switch to apply corrections to data
set csel # Option to select (or deselect) channel ranges
set msel #Selection parameter
set nsig = 4  # Number of sigma out to count channel as bad
set tsig = 0 # Number of sigma out to count channel as bad in timefocus
set edgerfi = 0 # Number of channels around each RFI spike to count as bad
set corrdisp = 0 #Display correctional information (debugging tool)
set flagopt = "noopt" # Optimize flagging commands?
set logfile #Switch for debug file
set chanlist #Switch for logfile/channel listing
set rfitype = "pos" # Ident RFI with counts that are too high, too low, or both?
set device = "/xs"
set timefocus # Allows user to "zoom in" to particular time. Useful if trying to catch more intermittent RFI as well as persistent RFI
set subint = 0 # Number of subintervals to scan for RFI in (mutually exclusive with the "timefocus" feature)
set npoly = 6 #What order polynomial to apply in correction stage
set rawdata
set optlim = 0
set debug = 0

#################################################################
# Here is the keyword/value pairing code. It basically operates
# by going through each argument, attempting to figure out which
# keyword matches (via an if arguement) and sets the value
# accordingly
#################################################################


varassign:

if ("$argv[1]" =~ 'vis='*) then
    set file = "`echo '$argv[1]/' | sed 's/vis=//g'`"
    set file = (`echo $file | sed 's/\/ / /g' | sed 's/\(.*\)\//\1/g'| sed 's/\.specdata//g' | tr ',' ' '`)
    set file = (`echo $file`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'select='*) then
    set msel = (`echo "$argv[1]" | sed 's/select=//g' | tr '[A-Z]' '[a-z]'`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'crange='*) then
    set csel = (`echo "$argv[1]" | sed 's/crange=//g' | sed 's/),/) /g'`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'timefocus='*) then
    set subint = 0
    set timefocus = (`echo "$argv[1]" | sed 's/timefocus=//g' | sed 's/),/) /g'`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'subint='*) then
    set timefocus
    set subint = `echo $argv[1] | sed 's/subint=//g' | awk '{print int($1*1)}'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'edgerfi='*) then
    set edgerfi = (`echo "$argv[1]" | sed 's/edgerfi=//g' | awk '{print int($1*1)}'`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'tsig='*) then
    set tsig = (`echo "$argv[1]" | sed 's/tsig=//g' | awk '{print $1*1}'`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'optlim='*) then
    set optlim = (`echo "$argv[1]" | sed 's/optlim=//g' | awk '{print int($1*1)}'`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'device='*) then
    set display = 1
    set device = `echo "$argv[1]" | sed 's/device=//g'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'npoly='*) then
    set npoly = (`echo "$argv[1]" | sed 's/npoly=//g' | awk '{print 1+int($1*1)}'`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'options='*) then
    set options = `echo "$argv[1]" | sed 's/options=//g' | tr ',' ' ' | tr '[A-Z]' '[a-z]'`
    set badopt
    foreach option (`echo $options`)
	if ($option == "corr") then
	    set corr = "corr"
	else if ($option == "nocorr") then
	    set corr = "nocorr"
	else if ($option == "corrdisp") then
	    set corrdisp = 1
	else if ($option == "flagopt") then
	    set flagopt = "flagopt"
	else if ($option == "pos") then
	    set rfitype = "pos"
	else if ($option == "neg") then
	    set rfitype = "neg"
	else if ($option == "mixed") then
	    set rfitype = "mixed"
	else if ($option == "debug") then
	    set debug = 1
	else	
	    set badopt = ($badopt $option)
	endif
    end
    if ("$badopt" != "") echo 'options='`echo $badopt | tr ' ' ','`' not recognized!'
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'log='*) then
    set logfile = `echo "$argv[1]" | sed 's/log=//g'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'rawdata='*) then
    set rawdata = `echo "$argv[1]" | sed 's/rawdata=//g'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'chanlist='*) then
    set chanlist = `echo "$argv[1]" | sed 's/chanlist=//g'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'nsig='*) then
    set nsig = `echo "$argv[1]" | sed 's/nsig=//g'`
    shift argv; if ("$argv" == "") set argv = "finish"
else
    echo "FATAL ERROR: $argv[1] not recognized..."
    exit 1
endif

if ("$argv[1]" != "finish") goto varassign

if ("$msel" == "") set msel

# All variables assigned, performing variable integrity check

if ("$file" == "") then # Check to see that there is an input for files
    echo "FATAL ERROR: No inputs files."
endif


if ($logfile != "") then # Can specified log file be created?
    rm -f $logfile
    if (-e $logfile) then
	echo "FATAL ERROR: Name of log file already exists..."
	exit 1
    endif
endif

#################################################################
# The program creates a temp directory to work in within the
# data directory being used. This is done to make operations
# "cleaner", as several MIRIAD results are dumped to temp files
# to be parsed later.
#################################################################

set wd = `mktemp -d rfi2XXXXX`

if ($wd == "") then # Can a temp work directory be created?
    echo "FATAL ERROR: Problems creating temp directory. Make sure you have permissions for the current directory..."
    exit 1
endif

if ($chanlist != "") then # Can specified chanlist file be created?
    rm -f $chanlist
    if (-e $chanlist) then
	echo "FATAL ERROR: Name of chanlist file already exists and can't be removed..."
	exit 1
    endif
else
    set chanlist = $wd/rfi32.log
endif


# Check to see that sigma ranges are reasonable

if (`echo $nsig | awk '{if ($1*1 < 2) print 1}'`) then
    echo "Sigma multiplier below minimum threshold (2 sigma). Setting nsig to 3..."
    set nsig = 3
endif

if ("$tsig" == 0 && ("$subint" != "0" || "$timefocus" != "")) then
    if ("$subint" != "0") set tsig = `echo $nsig $subint | awk '{print $1+log($2)}'`
    if ("$timefocus" != "") set tsig = `echo $nsig $#timefocus | awk '{print $1+log($2)}'`
endif
if ("$tsig" == "0") set tsig = `echo $nsig | awk '{print $1+1}'`

if (`echo $tsig $nsig | awk '{if ($1*1 < 2 || $1 < $2) print 1}'`) then
    echo "Time focus sigma multiplier below minimum threshold (2 sigma or nsig). Setting tsig to $nsig..."
    set tsig = $nsig
endif

# Check to see that number of coeff for correctional polynomial is reasonable
if (`echo $npoly | awk '{if ($1*1 < 3) print "nogo"}'` == "nogo") then
    echo "Polynomial correction below minimul threshold (2nd order). Setting npoly to 5..."
    set npoly = 6
endif
# Check to see that count spectra exist - if not attempt to create them 
foreach ifile (`echo $file`)
    if (! -e $ifile/specdata) then
	if (-e $ifile/visdata) then
	    echo "Spectral scanning data not found, running scanner..."
	    newrfi.csh vis=$ifile
	else
	    echo "FATAL ERROR: No specdata or visibilities found!"
	    goto fail
	endif
    endif
end

# Cat multiple files together into a single file
if ($#file > 1) then
    cat `echo $file | sed 's/ /\/specdata '/g`/specdata > $wd/specdata
    set file = "$wd"
endif

set midx = 1

filter:

#################################################################
# The scan utility needs to have support for selection commands,
# similar to what would be supported in MIRIAD. Below is my best
# attempt at such support. The selection parameters run the
# 'positive' selection commands before running 'negative'
# selection commands (e.g. if select=ant(1),-ant(2) the program
# will grab the results for antenna 1 before discarding the
# results for antenna 2). The biggest reason for this was to
# increase processing speed. Multiple selection commands (those
# seperated by a space) will run through this segment of code
# again. The handling of selection commands causes 'positive'
# commands to act as AND operators, and 'negative' commands
# to act like NOR operators.
#################################################################

set poscmd
set negcmd
set sel = `echo "$msel[$midx]"`
if ($logfile != "") then
    echo "The following parameters were issued..." >> $logfile
    echo "file = $file" >> $logfile
    echo "display = $display" >> $logfile
    echo "corr = $corr" >> $logfile
    echo "csel = $csel" >> $logfile
    echo "msel = $msel" >> $logfile
    echo "nsig = $nsig" >> $logfile
    echo "corrdisp = $corrdisp" >> $logfile
    echo "flagopt = $flagopt" >> $logfile
    echo "logfile = $logfile" >> $logfile
    echo "chanlist = $chanlist" >> $logfile
endif

#Start by sorting the aff commands from the neg commands

foreach selcmd (`echo $sel | sed 's/),/) /g' | sed 's/o,/o /g'`)
    if (`echo $selcmd` =~ -*) then
	set negcmd = ("$negcmd" "$selcmd")
	else
	set poscmd = ("$poscmd" "$selcmd")
	endif
    end



if (`echo $negcmd | wc -w` != 0) then # If no neg commands exists, skip to pos commands
    echo -n "cat $file/specdata" > $wd/neg.source 
else
    cp $file/specdata $wd/temp.neg
    endif

foreach neg (`echo "$negcmd"`) #Begin negative selections first
	if ("$neg" =~ '-ant'*) then #Are you an antenna?
	    if ("$neg" =~ *")("*) then #Are you a series of baselines?
		set ants1 = (`echo "$neg" | tr '()' ' ' | awk '{print $2}' | tr ',' ' '`) 
		set ants2 = (`echo "$neg" | tr '()' ' ' | awk '{print $3}' | tr ',' ' '`) 
		set bases
		foreach ant (`echo $ants1`)
		    set bases = ($bases `echo "$ants2 " | sed 's/ / '$ant' /g'`) 
		    end
		while ($#bases > 1)
		    if ($bases[1] < $bases[2]) echo -n ' | '"awk '{if ("'$1'" != "$bases[1]") if ("'$2'" != "$bases[2]") print "'$0'"}'" >> $wd/neg.source
		    if ($bases[1] >= $bases[2]) echo -n ' | '"awk '{if ("'$1'" != "$bases[2]") if ("'$2'" != "$bases[1]") print "'$0'"}'" >> $wd/neg.source
		    shift bases; shift bases
		    end
	    else #Then you must be a series of antennas
		set ants1
		set ants2
		foreach ant (`echo "$neg" | tr '()' ' ' | awk '{print $2}' | tr ',' ' '`)
		    set ants1 = ("$ants1 if ("'$1'" != $ant && "'$2'" != $ant )")
		    end
		echo -n ' | '"awk '{$ants1"' print $0}'"'" >> $wd/neg.source
 		endif

	else if ("$neg" =~ '-time'*) then #Are you a time selection?
	    set times = (`echo "$neg" | tr 'time(,)-' ' '`)
	    if ($#times > 2) echo "Failed to recognize time select command!"
	    if ($#times > 2) goto finish
	    if ($#times == 1) then
		if (`echo $times | tr ':' ' ' | wc -w` == 3) set times = (`echo $times | tr ':' ' '| awk '{print $1+$2/60+$3/3600}'`)
		echo -n ' | '"awk '{if (($times"'-(24*($5%1)))*((24*($4%1))-'"$times"')*(($5%1)-($4%1)) < 0) print $0}'"'" >> $wd/neg.source
	    else if (`echo $times | awk '{if ($1 <= 24 && $2 <= 24) print "go"}'` == "go" || `echo $times | tr ':' ' ' | wc -w` > 2) then
		if (`echo $times | tr ':' ' ' | wc -w` == 6) set times = (`echo $times | tr ':' ' '| awk '{print $1+$2/60+$3/3600,$4+$5/60+$6/3600}'`)
		if (`echo $times | awk '{if ($1 > $2) print "swap"}'` == swap) then
		    echo -n ' | '"awk '{if ("'24*($5%1)'" < $times[1] && "'24*($4%1)'" > $times[2] && "'24*($4%1)'" < "'24*($5%1)'") print "'$0'"}'" >> $wd/neg.source
		else
		    echo -n ' | '"awk '{if ("'24*($4%1)'" < $times[1] && "'24*($5%1)'" < $times[1]) print "'$0'";else if ("'24*($4%1)'" > $times[2] && "'24*($5%1)'" > $times[2]) print "'$0'";else if ("'24*($4%1)'" > $times[2] && "'24*($5%1)'" < $times[1]) print "'$0'"}'" >> $wd/neg.source
		endif
	    else
		echo -n ' | '"awk '{if ("'$4'" > $times[2] || "'$5'" < $times[1]) print "'$0'"}'" >> $wd/neg.source
	    endif
	else if ("$neg" =~ '-pol'*) then #Are you a pol selection?
	    set pols = (`echo $neg | tr 'pol(,)-' ' ' | tr '[a-z]' '[A-Z]'` )
	    set polsel = (' | '"awk '{")
	    foreach pol (`echo $pols`)
		set polsel = ("$polsel" 'if ($3 != "'$pol'")')
		end
	    echo "$polsel"' print $0}'"'" >> $wd/neg.source
	else #I have no idea what you want
	    echo "Failed to recognize select command!"
	    goto finish
	    endif
	end
echo >> $wd/neg.source

if (! -e $wd/temp.neg) then
    source $wd/neg.source > $wd/temp.neg
endif

if (`echo "$poscmd" | wc -w` == 0) then #If no pos commands exists, skip pos commands
    cp $wd/temp.neg $wd/temp.data
else
rm -f $wd/pos.source
endif

foreach pos (`echo "$poscmd"`)
	if ($pos =~ 'ant'*) then #Begin pos selection
	    if ("$pos" =~ *")("*) then #Are you a series of baselines?
		set ants1 = (`echo "$pos" | tr '()' ' ' | awk '{print $2}' | tr ',' ' '`) 
		set ants2 = (`echo "$pos" | tr '()' ' ' | awk '{print $3}' | tr ',' ' '`) 
		set bases
		foreach ant (`echo $ants1`)
		    set bases = ($bases `echo "$ants2 " | sed 's/ / '$ant' /g'`) 
		    end
		while ($#bases > 1)
		    if ($bases[1] < $bases[2]) echo "awk '{if ("'$1'" == "$bases[1]") if ("'$2'" == "$bases[2]") print "'$0'"}' $wd/temp.neg" >> $wd/pos.source3
		    if ($bases[1] >= $bases[2]) echo "awk '{if ("'$1'" == "$bases[2]") if ("'$2'" == "$bases[1]") print "'$0'"}' $wd/temp.neg" >> $wd/pos.source3
		    shift bases; shift bases
		    end
	    else #Then you must be a series of antennas
		set ants1
		set ants2
		foreach ant (`echo "$pos" | tr '()' ' ' | awk '{print $2}' | tr ',' ' '`)
		    if ("$ants1" != "") set ants1 = ("$ants1"'; else')
		    set ants1 = ("$ants1 if ("'$1'" == $ant) print "'$0')
 		    set ants2 = ("$ants2; else if ("'$2'" == $ant) print "'$0')
		    end
		echo "awk '{$ants1$ants2"'}'"' $wd/temp.neg" >> $wd/pos.source3
 		endif
	else if ($pos =~ 'time'*) then # Could you be a time selection?
	    set times = (`echo $pos | tr 'time(,)' ' '`)
	    if ($#times > 2) echo "Failed to recognize time select command!"
	    if ($#times > 2) goto finish
	    if ($#times == 1) then
		if (`echo $times | tr ':' ' ' | wc -w` == 3) set times = (`echo $times | tr ':' ' '| awk '{print $1+$2/60+$3/3600}'`)
		echo "awk '{if (($times"'-(24*($5%1)))*((24*($4%1))-'"$times"')*(($5%1)-($4%1)) > 0) print $0}'"' $wd/temp.neg" >> $wd/pos.source1
	    else if (`echo $times | awk '{if ($1 <= 24 || $2 <= 24) print "go"}'` == "go" || `echo $times | tr ':' ' ' | wc -w` > 2) then
		if (`echo $times | tr ':' ' ' | wc -w` == 6) set times = (`echo $times | tr ':' ' '| awk '{print $1+$2/60+$3/3600,$4+$5/60+$6/3600}'`)
		if (`echo $times | awk '{if ($1 > $2) print "swap"}'` == swap) then
		    echo "awk '{if ("'24*($4%1)'" >= $times[1] || "'24*($4%1)'" <= $times[2]) print "'$0'"; else if ("'24*($5%1)'" >= $times[1] || "'24*($5%1)'" <= $times[2]) print "'$0'"; else if ("'24*($5%1)'" >= $times[1] && "'24*($4%1)'" <= $times[2]) print "'$0'"}' $wd/temp.neg" >> $wd/pos.source1
		else
		    echo "awk '{if ("'24*($4%1)'" >= $times[1] && "'24*($4%1)'" <= $times[2]) print "'$0'"; else if ("'24*($5%1)'" >= $times[1] && "'24*($5%1)'" <= $times[2]) print "'$0'"; else if ("'24*($4%1)'" <= $times[1] && "'24*($5%1)'" >= $times[2]) print "'$0'"}' $wd/temp.neg" >> $wd/pos.source1
		endif
	    else
		echo "awk '{if ("'$4'" <= $times[1] && "'$5'" >= $times[1]) print "'$0'"; else if ("'$4'" <= $times[2] && "'$5'" >= $times[2]) print "'$0'"; else if ("'$4'" >= $times[1] && "'$5'" <= $times[2]) print "'$0'"}' $wd/temp.neg" >> $wd/pos.source1
	    endif
	else if ($pos =~ 'pol'*) then #Begin a poll of the pols
	    set pols = (`echo $pos | tr 'pol(,)' ' ' | tr '[a-z]' '[A-Z]'` )
	    set polsel = ("awk '{")
	    foreach pol (`echo $pols`)
		if ($#polsel != 1) set polsel = ("$polsel" '; else')
		set polsel = ("$polsel" 'if ($3 == "'$pol'") print $0')
	    end
	    echo "$polsel}' $wd/temp.neg" >> $wd/pos.source2
	else
	    echo "Failed to recognize select command!"
	    goto finish
	endif
end

#################################################################
# Positive commands are split into three sections, and run
# in a order designed to optimize processing speed (i.e. time
# selections are likely to narrow down the range of data more
# than pol selections). Negative commands are organized in a
# similar way.
#################################################################

if (! -e temp.data) then
    set idx = 1
    while ($idx <= 3)
	if (-e $wd/pos.source$idx) then
	    source $wd/pos.source$idx >> $wd/temp.pos
	    mv $wd/temp.pos $wd/temp.neg
	endif
	@ idx++
    end
    mv $wd/temp.neg $wd/temp.data
endif

if ($#msel > 1) then
    mv $wd/temp.data $wd/temp.datat$midx
    if ($#msel != $midx) then
	@ midx++
	cat $wd/pos.source* > $wd/pos$midx.source 
	rm -f $wd/pos.source*
	goto filter
    else
	cat $wd/temp.datat* > $wd/temp.data
    endif
endif

# Data is now limited to only that which the user is interested in

#################################################################
# With the data limited to that which we are only interested in,
# the program will now count the times that each channel is IDed
# as 'high'.
#################################################################

set chans = `head -n 1 $file/specdata | wc -w | awk '{print $1-14}'`
set idx = 1
set chan = 15
set ilim = 128
if ($chans < $ilim) set ilim = $chans
resume:

#Build source file for count spectra
echo -n "awk '{SUM$idx += "'$'"$chan" > $wd/side1
echo -n '{print SUM'"$idx" > $wd/side2
@ idx++ chan++

while ($idx <= $ilim)
    echo -n "; SUM$idx"' += $'"$chan" >> $wd/side1
    echo -n ",SUM$idx" >> $wd/side2
    @ idx++ chan++
end

echo '} END ' >> $wd/side1
echo "}' $wd/temp.data" >> $wd/side2
echo -n "`cat $wd/side1 $wd/side2`" >> $wd/temp.source
echo "" >> $wd/temp.source

if ($ilim < $chans) then
    set ilim = `echo $ilim | awk '{print $1+128}'`
    if ($ilim > $chans) set ilim = $chans
    goto resume
endif

set spec = (`source $wd/temp.source`)
set idx = 1

if ($#spec == 0) then
    echo "No spectra found!"
    goto fail
endif

cp $wd/temp.data $wd/specdata
set badsubchans
touch $wd/badsubchans
if ($subint) then
    if (`sort -unk4 $wd/temp.data | wc -l` <= 1) then
	echo "WARNING: Not enough datapoints to do subintervals..."
	set subint = 0
    else
	set subvals = (`sort -unk4 $wd/temp.data | awk '{if (NR == 1) printf "%s ",$4; else {idx += 1; fin=$4}} END {printf "%s %s\n",fin,idx}'` 0 0 0)
	if ($subint > $subvals[3]) set subint = $subvals[3]
	while ($idx < $subint)
	    set subtimes = (`echo $subvals[1-2] $subint $idx | awk '{printf "%5.6f %5.6f\n",$1+((($4-1)/$3)*($2-$1)),$1+(($4/$3)*($2-$1))}'`)
	    newrfi32.csh vis=$wd chanlist=$wd/subchans crange="$csel" select=time"($subtimes[1],$subtimes[2])" nsig=$tsig edgerfi=$edgerfi options=$corr,$rfitype > /dev/null
	    if (-e $wd/subchans) sed 1,2d $wd/subchans | awk '{print $1}' >> $wd/badsubchans
	    @ idx++
	end
	set subtimes = ($subtimes[2] $subvals[2])
	newrfi32.csh vis=$wd chanlist=$wd/subchans crange="$csel" select=time"($subtimes[1],$subtimes[2])" nsig=$tsig options=$corr,$rfitype edgerfi=$edgerfi > /dev/null
	if (-e $wd/subchans) sed 1,2d $wd/subchans | awk '{print $1}' >> $wd/badsubchans
	set badsubchans = (`sort -un $wd/badsubchans`)
    endif
endif

foreach timerange (`echo "$timefocus"`)
    newrfi32.csh vis=$wd select=time"$timerange" chanlist=$wd/subchans crange="$csel"  edgerfi=$edgerfi options=$corr,$rfitype nsig=$tsig > /dev/null
    if (-e $wd/subchans) sed 1,2d $wd/subchans | awk '{print $1}' >> $wd/badsubchans
end

set idx = 1

#Arrange data into a file so that wip can read it
while ($idx <= $chans)
    @ spec[$idx]++
    echo $idx $spec[$idx] >> $wd/temp.totspec
    if !("$spec[$idx]" == "1" || " $badsubchans " =~ *" $idx "*) echo $idx $spec[$idx] >> $wd/temp.spec
    @ idx++
end

if (`wc -l $wd/temp.spec | awk '{print int($1*1)}'` < `wc -l $wd/temp.totspec | awk '{print int($1*.1)}'`) then
    echo "WARNING: Too much data appears to have been culled out, eliminating subint processing"
    cp $wd/temp.totspec $wd/temp.spec
endif

rm -f $wd/pos.source

# Apply channel range selections

echo -n "cat $wd/temp.spec " > $wd/neg.source
foreach range (`echo "$csel"`)
    if ($range =~ '-'*) then
	set rvals = (`echo $range | tr '(),-' ' '`)
	if ($#rvals == 1) then
	    echo -n "| awk '"'{if ($1 != bchan) print $0}'"' bchan=$rvals[1] " >> $wd/neg.source
	else
	    echo -n "| awk '"'{if ($1 < lchan) print $0; else if ($1 > uchan) print $0}'"' lchan=$rvals[1] uchan=$rvals[2] " >> $wd/neg.source
	endif
    else
    	set rvals = (`echo $range | tr '(),' ' '`)
	if ($#rvals == 1) then
	    echo "awk '"'{if ($1 == bchan) print $0}'"' bchan=$rvals[1] $wd/neg.spec" >> $wd/pos.source
	else
	    echo "awk '"'{if ($1 >= lchan) if ($1 <= uchan) print $0}'"' lchan=$rvals[1] uchan=$rvals[2] $wd/neg.spec" >> $wd/pos.source
	endif
    endif
end

echo "" >> $wd/neg.source

cp $wd/temp.spec $wd/old.spec
source $wd/neg.source > $wd/neg.spec
if (-e $wd/pos.source) then
    source $wd/pos.source > $wd/temp.spec
else
    mv $wd/neg.spec $wd/temp.spec
endif

cat $wd/old.spec $wd/temp.spec | awk '{print $1,"old"}' | sort -n | uniq -u > $wd/old.spec2

# Spectra are built. User can now specify whether corrections need to be applied

if ($corr != "corr") then
    cp $wd/temp.spec $wd/temp.spec2 
    cp $wd/temp.totspec $wd/temp.totspec2
    goto aftercorr
endif

awk '{print $2}' $wd/temp.spec | sort -n > $wd/temp.power

#################################################################
# With the data now built, the program will attempt to derive
# a gaussian profile for the data. The data is 'bined' (since
# the PDF of the distribution should be Gaussian) and the
# program takes the natural log of each of the bins. This is
# done since ln(e^(a*x^2+B*x+c))=a*x^2+B*x+c, reducing the
# problem to a simple polynomial fit. After a first pass to
# determine channels that are significant outliers, the program
# can use WIP to derive a polynomial fit to the bandpass, and
# will take one more pass at deriving a Gaussian fit.
#################################################################

#Find median and try to build a gaussian profile
set cenchan = `wc -l $wd/temp.power | awk '{print int(.5+($1/2))}'`
set censpec = `awk '{CHAN += $1; CHANC += 1} END {print int(.5+(CHAN/CHANC))}' $wd/temp.spec `
set cenpower = `sed -n {$cenchan}p $wd/temp.power`
set delpower = `echo $cenpower | awk '{print int(.5+.5*($1^.5))}'`
if ($delpower < 3) then #Lower limit for correction to be applied
    echo "Below threshold limits for statistical correction of data, moving on..."
    cp $wd/temp.spec $wd/temp.spec2 
    cp $wd/temp.totspec $wd/temp.totspec2
    goto aftercorr
else
    set yvals = (`awk '{print $1-cenpower}' cenpower=$cenpower $wd/temp.power | awk '{if (($1+3*delpower)^2 < delpower^2) SUM0 += 1; else if (($1+1*delpower)^2 < delpower^2) SUM1 += 1; else if (($1-1*delpower)^2 < delpower^2) SUM2 += 1; else if (($1-3*delpower)^2 < delpower^2) SUM3 += 1} END {print SUM0,SUM1,SUM2,SUM3}' delpower=$delpower | awk '{print log($1),log($2),log($3),log($4)}'`)
    set alpha = (`echo $yvals | awk '{print ($2-$1)/delpower,($3-$2)/delpower,($4-$3)/delpower}' delpower=$delpower | awk '{print .5*($3-$1)/delpower}' delpower=$delpower`)
    if (`echo $alpha | awk '{if ($1 > 0) print "nogo"}'` == "nogo") then
	echo "Advanced detection of sigma during calibration cycle failed, switching to forced detection..."
	set finpower = $cenpower
	set lchan = `echo $chans | awk '{print 1+int($1*exp(-1))}'`
	set uchan = `echo $chans | awk '{print 1+int($1*(1-exp(-1)))}'`
	set lpower = `sed -n {$lchan}p $wd/temp.power`
	set upower = `sed -n {$uchan}p $wd/temp.power`
	set sigma = `echo $upower $lpower | awk '{print .5*($1-$2)}'`

    else
	set beta = (`echo $yvals | awk '{print (($2-$1)/delpower)+(alpha*delpower),($3-$2)/delpower,(($4-$3)/delpower)-(alpha*delpower)}' alpha=$alpha delpower=$delpower | awk '{print -1*($1+$2+$3)/(3*alpha)}' alpha=$alpha`)
	set finpower = `echo $cenpower $beta | awk '{print int(.5+$1+$2)}'`
	set sigma = `echo $alpha $delpower | awk '{print $2^.5*($1^2)^-.25}'`
	endif
    endif

echo $sigma $cenpower | awk '{if ($1 < $2^.5) print "Enforcing lower limit on sigma..."}'

set sigma = `echo $sigma $cenpower | awk '{if ($1 > $2^.5) print $1;else print $2^.5}'` 

awk '{if (($2-finpower)^2 < 4*(nsig^2)*sigma^2) print ($1-censpec)/1000,$2,($2-finpower)/sigma}' finpower=$finpower sigma=$sigma censpec=$censpec nsig=$nsig $wd/temp.spec > $wd/temp.good

if ($corrdisp) then
    echo "Displaying correctional data..."
    echo 'device $device' > $wd/temp.wip
endif
# Use wip to determine the best fit polynomial
echo "data $wd/temp.good" >> $wd/temp.wip
echo 'xcol 1' >> $wd/temp.wip
echo 'ycol 2' >> $wd/temp.wip
echo "fit poly $npoly" >> $wd/temp.wip
echo 'lim' >> $wd/temp.wip
echo 'box' >> $wd/temp.wip
echo 'conn' >> $wd/temp.wip
echo 'plotfit' >> $wd/temp.wip
echo 'end' >> $wd/temp.wip

set coeffs = ( `wip -d /null $wd/temp.wip | grep '+-' | awk '{print $3}'` 0 0 0 0 0 0 0 0 0 0 0 0 0)

if ($corrdisp == "corrdisp") then
    echo "Hit enter to continue..."
    set dummy = $<
endif

awk '{if ($2 == 1) print $1,$2; else print $1,$2-x1*(($1-censpec)/1000)-x2*(($1-censpec)/1000)^2-x3*(($1-censpec)/1000)^3-x4*(($1-censpec)/1000)^4-x5*(($1-censpec)/1000)^5-x6*(($1-censpec)/1000)^6-x7*(($1-censpec)/1000)^7-x8*(($1-censpec)/1000)^8-x9*(($1-censpec)/1000)^9-x10*(($1-censpec)/1000)^10-x11*(($1-censpec)/1000)^11-x12*(($1-censpec)/1000)^12}' x1=$coeffs[2] x2=$coeffs[3] x3=$coeffs[4] x4=$coeffs[5] x5=$coeffs[6] x6=$coeffs[7] x7=$coeffs[8] x8=$coeffs[9] x9=$coeffs[10] x10=$coeffs[11] x11=$coeffs[12] x12=$coeffs[13] censpec=$censpec $wd/temp.spec | awk '{if ($2 < 1) print $1,1; else print $0}' > $wd/temp.spec2
awk '{if ($2 == 1) print $1,$2; else print $1,$2-x1*(($1-censpec)/1000)-x2*(($1-censpec)/1000)^2-x3*(($1-censpec)/1000)^3-x4*(($1-censpec)/1000)^4-x5*(($1-censpec)/1000)^5-x6*(($1-censpec)/1000)^6-x7*(($1-censpec)/1000)^7-x8*(($1-censpec)/1000)^8-x9*(($1-censpec)/1000)^9-x10*(($1-censpec)/1000)^10-x11*(($1-censpec)/1000)^11-x12*(($1-censpec)/1000)^12}' x1=$coeffs[2] x2=$coeffs[3] x3=$coeffs[4] x4=$coeffs[5] x5=$coeffs[6] x6=$coeffs[7] x7=$coeffs[8] x8=$coeffs[9] x9=$coeffs[10] x10=$coeffs[11] x11=$coeffs[12] x12=$coeffs[13] censpec=$censpec $wd/temp.totspec | awk '{if ($2 < 1) print $1,1; else print $0}' > $wd/temp.totspec2

#Now that corrections have been applied, recalculate gaussian profile
aftercorr:
awk '{print $2}' $wd/temp.spec2 | sort -n > $wd/temp.power
set cenchan = `wc -l $wd/temp.power | awk '{print int(.5+($1/2))}'`
set cenpower = `sed -n {$cenchan}p $wd/temp.power`
set delpower = `echo $cenpower | awk '{print int(.5+.5*($1^.5))}'`

if ($delpower < 3) then
    echo "Outside of normal Gaussian range, forcing sigma values"
    set sigma = `echo $cenpower | awk '{print int(1.5+$1^.5)}'`
    set finpower = $cenpower
else
    set yvals = (`awk '{print $1-cenpower}' cenpower=$cenpower $wd/temp.power | awk '{if (($1+3*delpower)^2 < delpower^2) SUM0 += 1; else if (($1+1*delpower)^2 < delpower^2) SUM1 += 1; else if (($1-1*delpower)^2 < delpower^2) SUM2 += 1; else if (($1-3*delpower)^2 < delpower^2) SUM3 += 1} END {print SUM0,SUM1,SUM2,SUM3}' delpower=$delpower | awk '{print log($1),log($2),log($3),log($4)}'`)
    set alpha = (`echo $yvals | awk '{print ($2-$1)/delpower,($3-$2)/delpower,($4-$3)/delpower}' delpower=$delpower | awk '{print .5*($3-$1)/delpower}' delpower=$delpower`)

    if (`echo $alpha | awk '{if ($1 > 0) print "nogo"}'` == "nogo") then
	echo "Advanced detection of sigma failed, switching to forced detection..."
	set finpower = $cenpower
	set lchan = `echo $chans | awk '{print 1+int($1*exp(-1))}'`
	set uchan = `echo $chans | awk '{print 1+int($1*(1-exp(-1)))}'`
	set lpower = `sed -n {$lchan}p $wd/temp.power`
	set upower = `sed -n {$uchan}p $wd/temp.power`
	set sigma = `echo $upower $lpower | awk '{print .5*($1-$2)}'`
    else
	set beta = (`echo $yvals | awk '{print (($2-$1)/delpower)+(alpha*delpower),($3-$2)/delpower,(($4-$3)/delpower)-(alpha*delpower)}' alpha=$alpha delpower=$delpower | awk '{print -1*($1+$2+$3)/(3*alpha)}' alpha=$alpha`)
	set finpower = `echo $cenpower $beta | awk '{print int(.5+$1+$2)}'`
	set sigma = `echo $alpha $delpower | awk '{print $2^.2*($1^2)^-.25}'`
	endif
    endif

set sigma = `echo $sigma $cenpower | awk '{if ($1 > $2^.5) print $1;else print $2^.5}'`  

# Sort the wheat from the chaff, the good channels from the bad
awk '{if (($2-finpower)^2 > (nsig^2)*sigma^2) print $1,($2-finpower)/sigma}' finpower=$finpower sigma=$sigma nsig=$nsig $wd/temp.spec2 > $wd/temp.bad

awk '{print $0,($2-finpower)/sigma}' finpower=$finpower sigma=$sigma nsig=$nsig $wd/temp.spec2 | sort -nk1 > $wd/temp.spec3
awk '{print $0,($2-finpower)/sigma}' finpower=$finpower sigma=$sigma nsig=$nsig $wd/temp.totspec2 | sort -nk1 > $wd/temp.totspec3

touch $wd/temp.bad3
foreach badsubchan ($badsubchans)
    sed -n {$badsubchan}p $wd/temp.totspec3 >> $wd/temp.bad3
end

set idx = 1
set lim = `wc -l $wd/temp.bad | awk '{print $1}'`

if ($edgerfi != 0 && $lim != 0) then
    echo "EdgeRFI protection initiated with $edgerfi channel buffer zone..."
    while ($idx <= $lim)
	set vals = (`sed -n {$idx}p $wd/temp.bad | awk '{print $2; if ($1-edge < 1) print "1"; else print $1-edge; if ($1+edge > chans) print chans; else print $1+edge}' chans=$chans edge=$edgerfi`)
	sed -n "$vals[2],$vals[3]p" $wd/temp.totspec3 | awk '{print $0,prime}' prime=$vals[1] >> $wd/temp.badlist
	@ idx++
    end
    awk '{if ($4 < 0) print $1,$2,$3}' $wd/temp.badlist | sort -unk1 > $wd/temp.bad1
    awk '{if ($4 > 0) print $1,$2,$3}' $wd/temp.badlist | sort -unk1 > $wd/temp.bad2
    cat $wd/temp.bad1 $wd/temp.bad2 $wd/temp.bad3 | sort -nk1 | awk '{if ($1 == chan) print $0; else chan = $1}' > $wd/temp.2check
    cat $wd/temp.bad1 $wd/temp.bad2 $wd/temp.2check $wd/temp.spec3 | sort -nk1 | uniq -u > $wd/temp.good
else if ($lim != 0) then
    awk '{if ($3^2 <= (nsig^2)) print $0}' nsig=$nsig $wd/temp.spec3 > $wd/temp.good
    awk '{if ($3 < (-1*nsig)) print $0}' nsig=$nsig $wd/temp.spec3 > $wd/temp.bad1
    awk '{if ($3 > nsig) print $0}' nsig=$nsig $wd/temp.spec3 > $wd/temp.bad2
else
    awk '{if ($3^2 <= (nsig^2)) print $0}' nsig=$nsig $wd/temp.spec3 > $wd/temp.good
    touch $wd/temp.bad1
    touch $wd/temp.bad2
endif
#if the display parameter has been invoked...
touch $wd/temp.bad1
touch $wd/temp.bad2

if ($display) then
    echo "device $device" > $wd/temp.wip
    echo "data $wd/temp.spec2" >> $wd/temp.wip
    echo 'xcol 1' >> $wd/temp.wip
    echo 'ycol 2' >> $wd/temp.wip
    echo 'log y' >> $wd/temp.wip
    echo 'lim' >> $wd/temp.wip
    echo "data $wd/temp.totspec2" >> $wd/temp.wip
    echo 'xcol 1' >> $wd/temp.wip
    echo 'ycol 2' >> $wd/temp.wip
    echo 'log y' >> $wd/temp.wip
    echo 'box cbnst cbnstl' >> $wd/temp.wip
    echo 'conn' >> $wd/temp.wip
    echo 'mtext t 1 .5 .5 RFI counts' >> $wd/temp.wip
    echo 'mtext l 2.5 .5 .5 RFI Count' >> $wd/temp.wip
    echo 'mtext b 2.5 .5 .5 Channel Number' >> $wd/temp.wip
    echo 'color 7' >> $wd/temp.wip
    echo 'poi'  >> $wd/temp.wip
    if (`wc -l $wd/temp.bad1 | awk '{print $1}'` > 0) then
	echo "data $wd/temp.bad1" >> $wd/temp.wip
	echo 'color 4' >> $wd/temp.wip
	echo 'xcol 1' >> $wd/temp.wip
	echo 'ycol 2' >> $wd/temp.wip
	echo 'log y' >> $wd/temp.wip
	echo 'poi' >> $wd/temp.wip
    endif
    if (`wc -l $wd/temp.bad2 | awk '{print $1}'` > 0) then
	echo "data $wd/temp.bad2" >> $wd/temp.wip
	echo 'color 2' >> $wd/temp.wip
	echo 'xcol 1' >> $wd/temp.wip
	echo 'ycol 2' >> $wd/temp.wip
	echo 'log y' >> $wd/temp.wip
	echo 'poi' >> $wd/temp.wip
    endif
    if (`wc -l $wd/temp.bad3 | awk '{print $1}'` > 0) then
	echo "data $wd/temp.bad3" >> $wd/temp.wip
	echo 'color 8' >> $wd/temp.wip
	echo 'xcol 1' >> $wd/temp.wip
	echo 'ycol 2' >> $wd/temp.wip
	echo 'log y' >> $wd/temp.wip
	echo 'poi' >> $wd/temp.wip
    endif
    if (`wc -l $wd/temp.good | awk '{print $1}'` > 0) then
	echo "data $wd/temp.good" >> $wd/temp.wip
	echo 'color 3' >> $wd/temp.wip
	echo 'xcol 1' >> $wd/temp.wip
	echo 'ycol 2' >> $wd/temp.wip
	echo 'log y' >> $wd/temp.wip
	echo 'poi' >> $wd/temp.wip
    endif

    echo 'end' >> $wd/temp.wip
    wip $wd/temp.wip > /dev/null
endif

if ($rfitype == "pos") then
    set badscore = `cat $wd/temp.bad2 | awk '{if (NR == 1) print $1; else printf "%d\n%d ",$1,$1}' | awk '{if ($2-$1 == 1) C1 += 1; else if ($2-$1 == 2) C2 += 1; else if ($2-$1 == 3) C3 += 1; else if ($2-$1 == 4) C4 += 1} END {print (1*C1)+(1*C2)+(1*C3)+(1*C4)}'`
    set badchans = (`cat $wd/temp.bad2 | sort -nk1 | awk '{print $1}'`)
else if ($rfitype == "neg") then
    set badscore = `cat $wd/temp.bad1 | awk '{if (NR == 1) print $1; else printf "%d\n%d ",$1,$1}' | awk '{if ($2-$1 == 1) C1 += 1; else if ($2-$1 == 2) C2 += 1; else if ($2-$1 == 3) C3 += 1; else if ($2-$1 == 4) C4 += 1} END {print (1*C1)+(1*C2)+(1*C3)+(1*C4)}'`
    set badchans = (`cat $wd/temp.bad1 | sort -nk1 | awk '{print $1}'`)
else
    set badscore = `cat $wd/temp.bad1 $wd/temp.bad2 | sort -u | awk '{if (NR == 1) print $1; else printf "%d\n%d ",$1,$1}' | awk '{if ($2-$1 == 1) C1 += 1; else if ($2-$1 == 2) C2 += 1; else if ($2-$1 == 3) C3 += 1; else if ($2-$1 == 4) C4 += 1} END {print (1*C1)+(1*C2)+(1*C3)+(1*C4)}'`
    set badchans = (`cat $wd/temp.bad1 $wd/temp.bad2 | sort -nk1 | awk '{print $1}'`)
endif

echo `wc -l $wd/temp.bad | awk '{print $1}'` bad channels detected "("`wc -l $wd/temp.bad1 | awk '{print $1}'` low, `wc -l $wd/temp.bad2 | awk '{print $1}'` high", corruption score $badscore"')'

echo -n `wc -l $wd/temp.bad | awk '{print $1}'` bad channels detected "("`wc -l $wd/temp.bad1 | awk '{print $1}'` low, `wc -l $wd/temp.bad2 | awk '{print $1}'` high", corruption score $badscore" > $chanlist

if ($subint != 0 || "$timefocus" != "") echo `echo $badsubchans | wc -w`" bad channels identified in subintervals"

if ($subint != 0 || "$timefocus" != "") then
    echo ", $#badsubchans IDed as bad in subintervals)"  >> $chanlist
else
    echo ")"  >> $chanlist
endif

echo "Chan Counts Sigma" >> $chanlist
if ($rfitype == "pos") then
    cat $wd/temp.bad2 >> $chanlist
    awk '{print $0,"(subint)"}' $wd/temp.bad3 >> $chanlist
else if ($rfitype == "neg") then
    cat $wd/temp.bad1 >> $chanlist
    awk '{print $0,"(subint)"}' $wd/temp.bad3 >> $chanlist
else 
    cat $wd/temp.bad2 $wd/temp.bad1 >> $chanlist
    awk '{print $0,"(subint)"}' $wd/temp.bad3 >> $chanlist
endif

# If flagopt commands have been issued, invoke them now

if ($flagopt != "flagopt") goto finish

if ($edgerfi != 0 && $optlim == 0) set optlim = $chans

echo "" >> $chanlist
echo "MIRIAD optimized line flag commands:" >> $chanlist

grep -iv "o" $chanlist | awk '{print $1}' | sort -un | grep '.' > $wd/optlist

foreach badsubchan ($badsubchans)
    echo $badsubchan >> $wd/optlist
end

sort -un $wd/optlist > $wd/optlist2
mv $wd/optlist2 $wd/optlist

# Optimize flags by looking for patterns in bad channel ranges
set optcount = `wc -l $wd/optlist | awk '{print $1}'`
set optdelta = $optcount

while (`wc -l $wd/optlist | awk '{print $1}'` > 1 && $optlim <= $optdelta)
    set lim = `wc -l $wd/optlist | awk '{print $1}'`
    set cmax = 2
    set iidx = 1
    set jidx = 2
    set opts
    set chan1 = `sed -n {$iidx}p $wd/optlist`
    set chan2 = `sed -n {$jidx}p $wd/optlist`
    set opts = ($chan1 `echo $chan1 $chan2 | awk '{print $2-$1}'` 2)
    while (`echo $lim $iidx | awk '{print ($1-$2)+1}'` > $cmax)
	set chan1 = `sed -n {$iidx}p $wd/optlist`
	set chan2 = `sed -n {$jidx}p $wd/optlist`
	while (`echo $lim $jidx | awk '{print ($1-$2)+2}'` > $cmax && `echo $chan1 $chan2 $chans | awk '{print 1+int(($3-$1)/($2-$1))}'` > $cmax)
	    set chanlim = `echo $cmax $chan1 $chan2 | awk '{print (($1-1)*($3-$2))+$2}'` 
	    set counter = 2
	    set delta = `echo $chan2 $chan1 | awk '{print $1-$2}'`
	    if (`awk '{if ($1 == chanlim) print "go"}' chanlim=$chanlim $wd/optlist | head -n 1` == "go") then
#" $rfioptlist " =~ *" $chanlim "*) then
#
		while (`awk '{if ($1 == ((delta*counter)+chan1)) print "go"}' chan1=$chan1 delta=$delta counter=$counter $wd/optlist | head -n 1` == "go")
#" $rfioptlist " =~ *`echo $delta $counter $chan1 | awk '{print " "($1*$2)+$3" "}'`*) 
#
		    @ counter++
		end
	    endif
	    if ($counter > $cmax) set opts = ($chan1 $delta $counter)
	    if ($counter > $cmax) set cmax = $counter
	    @ jidx++
	    set chan2 = `sed -n {$jidx}p $wd/optlist`
	    if ($chan2 == "") set chan2 = $chans
	end
	echo -n "."
	@ iidx++
	set jidx = `echo $iidx | awk '{print $1+1}'`
    end
    echo "."
    echo "line=chan,$opts[3],$opts[1],1,$opts[2]" >> $chanlist
    echo `echo $lim $opts[3] | awk '{print $1-$2}'`" channel(s) left to go..."
    awk '{if ($1 < chan1) print $0; else if (($1-chan1)%delta != 0) print $0; else if (($1-chan1)/delta > counter) print $0}' chan1=$opts[1] delta=$opts[2] counter=$opts[3] $wd/optlist > $wd/opttemp
    mv $wd/opttemp $wd/optlist
    set optdelta = `wc -l $wd/optlist | awk '{print precou-$1}' precou=$optcount`
    set optcount = `wc -l $wd/optlist | awk '{print $1}'`
end

if (`wc -l $wd/optlist | awk '{print $1}'` > 0) then
    set lastchan = `wc -l $wd/optlist | awk '{print $1}'`
    if ($lastchan != 1) then
	awk '{if (NR == 1) {bchan=$1; idx=1} else if ((bchan+idx) == $1) {idx++} else {print "line=chan,"idx","bchan; bchan=$1; idx=1}; if (NR == lastchan) print "line=chan,"idx","bchan}' lastchan=$lastchan $wd/optlist >> $chanlist
    else if ($lastchan == 1) then
	echo "line=chan,1,"`head -n 1 $wd/optlist | awk '{print $1}'` >> $chanlist
    endif
endif

finish:

if ("$chanlist" == "$wd/rfi32.log") then
    echo ""
    echo "BADCHANS: $badchans"
    if ("$subint" != "0" || "$timefocus" != "") echo "BADSUBCHANS: $badsubchans"
endif
if ("$flagopt" == "flagopt" && "$chanlist" == "$wd/rfi32.log") then
    echo ""
    echo "MIRIAD optimized flagging commands"
    sed 1,2d $chanlist | awk '{if ($1*1 == 0) print $0}' | sed 1,2d
endif
if ("$rawdata" != "") then
    mv $wd/temp.data $rawdata
endif

if ("$logfile" != "") then
    echo "Final spectral counts:" >> $logfile
    cat $wd/temp.spec2 >> $logfile
    if ("$corr" == "corr") then
	echo "Uncorrected spectra:" >> $logfile
	cat $wd/temp.spec >> $logfile
    endif
endif

if !($debug) rm -r $wd

exit 0

fail:

if !($debug) rm -r $wd

exit 1
