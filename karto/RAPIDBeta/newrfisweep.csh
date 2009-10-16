#! /usr/bin/tcsh -f
# $Id$

onintr fail

if ($#argv == 0) then
      #################################################################
echo "================================================================="
echo "RFISWEEP - All in one RFI flagging program"
echo "'It's high time someone cleaned up this spectrum.'"
echo ""
echo "CALLS - newrfi.csh, newrfi32.csh , newfracture.csh, MIRIAD"
echo "    (uvflag, uvaflag, uvaver)"
echo "PURPOSE - Identify channels with RFI pollution."
echo "RESPONSIBLE - Karto (karto@hcro.org)"
echo "================================================================="
echo ""
echo "RFISWEEP is designed as an 'all-in-one' flagging utility for RFI"
echo "and spectral corruption removal. RFISWEEP will uses RFILOCK,"
echo "RFISCAN and FRACTURE to find RFI and spectral corruption in the"
echo "data, and then flags the polluted channels within the source"
echo "dataset. RFISWEEP works best with datasets with continuum"
echo "emission only, and datasets with either passband corrections"
echo "previously applied or with datasets that have less that roughly"
echo "10 Jy of total emission in the primary beam/FOV."
echo ""
echo "RFISWEEP operates by dividing the data into smaller chunks based"
echo "on time, evaluating each chunk/cycle independently for RFI, and"
echo "removing polluted channels in each time chunk and the time"
echo "chucks immediate surrounding it (e.g. if polluted channels are"
echo "found in cycle 2, they are removed in cycles 1 and 3 as well)."
echo "RFISWEEP also looks at groups of cycles for spectral corruption,"
echo "removing it before RFI identification and removal begins."
echo ""
echo "RFISWEEP will modify flags files for datasets, although a backup"
echo "of the last flags solution is made in the data directory (under"
echo "the name 'flags.bu'). Users should be aware that RFISWEEP will"
echo "only look at the last 'specdata' file created (by RFISCAN) by"
echo "default. Users will need to rerun RFISCAN to capture any changes"
echo "made to the dataset (i.e.new flags or gains solutions)."
echo ""
echo "RFISWEEP may encounter problems when RFI exceeds 1000 sigma."
echo "Users can overcome this problem by rerunning RFISCAN and"
echo "RFISWEEP once extremely strong interference has been removed."
echo ""
echo "TECHNICAL NOTE: RFISWEEP creates a temporary directory to work"
echo "from, named rfi3XXXXX (where X is a random character). These"
echo "directories are supposed to be automatically deleted after"
echo "RFISCAN completes, but might remain in the event of a program"
echo "error. Remnant directories can be safely deleted."
echo ""
echo "CALLING SEQUENCE: newrfisweep.csh vis=vis (tvis=tvis scans=scans"
echo "    interval=interval subint=subint nsig=nsig npoly=npoly"
echo "    tsig=tsig csig=csig cpoly=cpoly crange=crange"
echo "    edgerfi=edgerfi device=device corrcycle=corrcycle options="
echo "    [corr,nocorr],[recover,destory,ignore],[pos,neg,mixed],"
echo "    rescan,debug,[outsource.insource],[autoedge,noautoedge],"
echo "   [seedcorr,noseedcorr]),noflag"
echo ""
echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo ""
echo ""
echo "REQUIRED INPUTS:"
echo " vis - Name of the files containing source data and specdata."
echo "    Information from these datasets WILL be used to create"
echo "    listings of channels to be flagged. Supports multiple files"
echo "    and wildcard expansion. No default."
echo ""
echo "OPTIONAL INPUTS:"
echo " tvis - Name of files containing source data only. Information"
echo "    from these datasets WILL NOT be used to create listings of"
echo "    channels to be flagged (i.e. they will be flagged only, not"
echo "    analyzed. Supports multiple files and wildcard expansion. No"
echo "    default."
echo ""
echo " scans - The number of scans to perform on each time interval."
echo "    Useful when there is particularly strong RFI that can"
echo "    dominate the scanner. Default is 1."
echo ""
echo " interval - Time period (in minutes) for an individual flagging"
echo "    cycle. The less constant the RFI believed to be in data, the"
echo "    shorter this length should be (e.g. at 1430 MHz, RFI changes"
echo "    drastically, so the interval should be 5-10 minutes. At 2750"
echo "    MHz, the RFI environment is quiet and unchanging, so the"
echo "    interval should be 20-30 minutes). Default is 12."
echo ""
echo " subint - Number of subintervals to scan. Useful for catching"
echo "    intermittent RFI or RFI that changes in frequency over time/"
echo "    position. Default is 3."
echo ""
echo " nsig - How far from the 'center' (in sigma) of the band at"
echo "    which to identify channels as 'bad' for RFI analysis. See"
echo "    RFILOCK for more details. Default is 3"
echo ""
echo " npoly - Order of polynomial to apply for passband feature"
echo "    removal in RFI analysis. Default is 6."
echo ""
echo " tsig - How far from the 'center' (in sigma) of the band at"
echo "    which to identify channels as 'bad' in subcycles. RFISWEEP"
echo "    divides each cycle into three equally sized (in terms of"
echo "    time) subcycles, each of which are scanned independently for"
echo "    RFI. This is done to better capture transient RFI that may"
echo "    otherwise go unremoved. Default is 4"
echo ""
echo " csig - How far from the 'center' (in sigma) of the band at"
echo "    which to identify channels as 'bad' for spectral corruption"
echo "    analysis. This parameter is normally put slightly higher"
echo "    than the nsig parameter so that RFI is not mistakenly IDed"
echo "    as spectral corruption. Default is 5."
echo ""
echo " cpoly - Order of polynomial to apply for passband feature"
echo "    removal in spectral corruption analysis. Default is 6."
echo ""
echo " edgerfi - Padding (in channels) around each RFI polluted"
echo "    channel to also identify as bad (e.g. if channel 3 is IDed"
echo "    as 'bad' and edgerfi=1, then channels 2,3 and 4 will be"
echo "    marked as bad. Helpful for protecting against RFI that"
echo "    shifts frequencies over time, and broadband RFI. Default is"
echo "    1."
echo ""
echo " crange - Channel range(s) to be analyzed by RFISWEEP. Individual"
echo "    ranges must be enclosed within a pair of parentheses, with a"
echo "    comma seperating different ranges (e.g. crange=(1),(2,5))."
echo "    Ranges can be either 'positive' or 'negative' (e.g. crange="
echo "    (100) will select only channel 100, while crange=-(100) will"
echo "    select everything but channel 100), and can give either a"
echo "    single channel or a range of channels (e.g. crange=(2,5) will"
echo "    select all channels between 2 and 5). This can be very"
echo "    useful for removing channels that are known to contain"
echo "    spectral line emission so that they are not mistakenly"
echo "    identified as RFI. Default is all channels."
echo ""
echo " device - Device to plot results to (e.g. /xw for x-window)."
echo '    Default is /null'
echo ""
echo " corrcycle - Number of cycles to scan over when looking for"
echo "    spectral corruption. If system stability is believed to be"
echo "    good, then this number should be increased (i.e. corrcycle="
echo "    10000 if the system is believed to be totally stable). Users"
echo "    can set corrcycle=0 if they wish to disable corruption"
echo "    scanning. Default is 4."
echo ""
echo " options=[corr,nocorr],[recover,destory,ignorecorr],[pos,neg,"
echo "    mixed],rescan,debug,[outsource.insource],[autoedge,"
echo "    noautoedge],[seedcorr,noseedcorr],noflag"
echo ""
echo "    corr - Correct for bandpass features via a polynomial fit."
echo "        (Default)"
echo "    nocorr - Don't correct for bandpass features."
echo "    recover - Attempt to recover antennas with spectral"
echo "        corruption by removing corrupted channels. (Default)."
echo "    destroy - Remove antennas with spectral corruption."
echo "    ignorecorr - Do no flagging based on spectral corruption."
echo "    pos - only ID those channels ABOVE the passband as being"
echo "        RFI/corruption candidates (e.g. channels several sigma"
echo "        below the passband will not be IDed as RFI). (Default)"
echo "    neg - only ID those channels BELOW the passband as being"
echo "        RFI/corruption candidates (i.e. channels several sigma"
echo "        above the passband will not be IDed as RFI)."
echo "    mixed - Channels above and below the passband that exceed"
echo "        the sigma threshhold are IDed as RFI/corruption."
echo "    rescan - Force a rescan (with RFISCAN) before processing the"
echo "        data. Useful if using multiple iterations of RFISWEEP"
echo "        to remove RFI, or if unsure about the the validity of"
echo "        the current 'specdata' file."
echo "    debug - Debugging switch to save processing files."
echo "    outsource - To speed up processing, RFISWEEP will divide the"
echo "        dataset into smaller chunks (based on time), and will"
echo "        process these smaller chunks independently. Ideal for"
echo "        larger datasets (e.g. single pointing observations)."
echo "        Users should be aware that this processing method"
echo "        requires additional hard drive space. (Default)"
echo "    insource - Flag datasets directly, without creating smaller"
echo "        temporary files. Ideal for wide-field mosaic"
echo "        observations, where the amount of integration time per"
echo "        pointing is small (i.e. a few minutes or less)."
echo "    autoedge - Automatically remove/flag remove edge channels"
echo "        from the dataset. (Default)"
echo "    noautoedge - Do not automatically remove/flag edge channels"
echo "        from the dataset."
echo "    seedcorr - For corruption scanning, use the results of only"
echo "        one cycle (i.e. the first cycle in the set) to flag the"
echo "        other time cycles. (Default)"
echo "    noseedcorr - For corruption scanning, use the results of all"
echo "        cycles for flagging and corruption removal."
echo "    noflag - Doesn't actually flag datasets, only displays"
echo "        scanning results."
exit 0
endif

set date1 = `date +%s.%N`

set fsel = ("pol(xx)" "pol(yy)")
set vis # Files to be scanned for RFI and flagged
set tvis # Files to be flagged for RFI, but NOT scanned!
set inttime = 12.5 # RFI integration time for the subinterval
set nsig = 4 # Number of sigma for RFI flagging in wide interval
set tsig = 0 # Number of sigma for RFI flagging in narrow interval
set csig = 6 # Number of sigma for corruption ID
set cpoly = 6 # Order of poly correction for corruption ID
set npoly = 6 # Order of poly correction for RFI flagging
set corr = "corr" # Use corrective polynomial for RFI scanning and final spectrum for spectral corruption scanning
set edgerfi = 1 # Protective "shield" around each RFI spike, channel range around RFI IDed channel to also flag
set csel # Channel range selection
set fracture = "recover" # Correct (recover), ignore or destory spectrally corrupted antennas
set display = 0 # To display or not to display, that is the question 
set corr = "corr" # Use corrective polynomial to remove bandpass features
set rfitype = "pos" # RFI above or below band?
set outsource = 1 # Split up file into smaller chunks, or mod files in place?
set debug = 0 # Save processing data?
set rescan = 0 # Remake specdata files
set corrcycle = 4 # Interval for scanning for corruption
set seedcorr = 0 # Use only the first interval for corruption scanning
set restart # Restart processing?
set autoedge = 1 # Use autoedge utility?
set autoedgechan = 100 # Number of channels on edges to flag
set device # Display device for stuff
set flag = 1 # Whether or not to flag
set subint = 3
set scans = 1

#Alright, lets see if I can finally properly comment this code...
#Below is the variable assignment listing, further documentation on this will be available shortly

#################################################################
# Here is the keyword/value pairing code. It basically operates
# by going through each argument, attempting to figure out which
# keyword matches (via an if arguement) and sets the value
# accordingly
#################################################################

varassign:

if ("$argv[1]" =~ 'vis='*) then
    set vis = "`echo '$argv[1]/' | sed 's/vis=//'`"
    set vis = (`echo $vis | sed 's/\/ / /g' | sed 's/\(.*\)\//\1/g' | tr ',' ' '`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'tvis='*) then
    set tvis = "`echo '$argv[1]/' | sed 's/tvis=//'`"
    set tvis = (`echo $tvis | sed 's/\/ / /g' | sed 's/\(.*\)\//\1/g' | tr ',' ' '`)
    shift argv; if ("$argv" == "") set argv = "finish"
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
	else if ($option == "nocorr") then
	    set corr = "nocorr"
	else if ($option == "pos") then
	    set rfitype = "pos"
	else if ($option == "neg") then
	    set rfitype = "neg"
	else if ($option == "mixed") then
	    set rfitype = "mixed"
	else if ($option == "verbose") then
	    set display = 2
	    if ("$device" == "") set device = 'device=/xs'
	else if ($option == "seedcorr") then
	    set seedcorr = 1
	else if ($option == "noseedcorr") then
	    set seedcorr = 0
	else if ($option == "outsource") then
	    set outsource = 1
	else if ($option == "insource") then
	    set outsource = 0
	else if ($option == "debug") then
	    set debug = 1
	else if ($option == "autoedge") then
	    set autoedge = 1
	else if ($option == "noautoedge") then
	    set autoedge = 0
	else if ($option == "noautoedge") then
	    set autoedge = 0
	else if ($option == "rescan") then
	    set rescan = 1
	else if ($option == "noflag") then
	    set flag = 0
	else if ($option == "maxsubint") then
	    set subint = 9999999
	else
	    set badopt = ($badopt $option)
	endif
    end
    if ("$badopt" != "") echo 'options='`echo $badopt | tr ' ' ','`' not recognized!'
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'device='*) then
    set display = 1
    set device = "$argv[1]"
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'scans='*) then
    set scans = `echo "$argv[1]" | sed 's/scans=//g' | awk '{print int($1*1)}'`
    if ($scans == 0) then
	echo "FATAL ERROR: Number of scans not recognized!"
	exit 1
    endif
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'interval='*) then
    set inttime = `echo "$argv[1]" | sed 's/interval=//g' | awk '{print $1*1}'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'subint='*) then
    set subint = `echo "$argv[1]" | sed 's/subint=//g' | awk '{print int($1*1)}'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'npoly='*) then
    set npoly = (`echo "$argv[1]" | sed 's/npoly=//g' | awk '{print 1+int($1*1)}'`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'cpoly='*) then
    set cpoly = (`echo "$argv[1]" | sed 's/cpoly=//g' | awk '{print 1+int($1*1)}'`)
    shift argv; if ("$argv" == "") set argv = "finish"
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

if ($listlim == 0) then
    echo "FATAL ERROR: No visibilities found!"
    exit 1
endif

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
            echo "FATAL ERROR: No specdata or visibilities found for $fulllist[$idx] !"
            exit 1
        endif
	if (! -e $fulllist[$idx]/specdata) then
	    echo "FATAL ERROR: No specdata or visibilities found for $fulllist[$idx]!"
	    exit 1
	endif
    endif
    @ idx++
end

# Make a temp directory to reduce data in (keeps things nice a neat)

#################################################################
# The program creates a temp directory to work in within the
# data directory being used. This is done to make operations
# "cleaner", as several MIRIAD results are dumped to temp files
# to be parsed later.
#################################################################

echo "Gathering observation information..."
set wd = `mktemp -d rfi3XXXXX`
set dmark = `date +%s`

foreach file ($vis $tvis)
    if !(-e $file/phoenix) mkdir -p $file/phoenix
    if (! -e $file/phoenix/flags.o && -e $file/flags) cp $file/flags $file/phoenix/flags.o
    echo "RFISWEEP $dmark" >> $file/phoenix/history
end


# Make spectral directories for all source and cal files - esp important for mosaiced observations... TOTH to Steve and Geoff

mkdir $wd/vis
mkdir $wd/tvis

# For each source file, use the specdata file to figure out when observations took place, and use that information to rebuild the actual obsrevation
#######################
set fulllist = (`echo $vis`)
set listlim = `echo $fulllist | wc -w`
set trlist
set idx = 1
touch $wd/vistimes
while ($idx <= $listlim)
    set filemark = `echo $idx | awk '{print $1+100000}' | sed 's/1//'`
    set trlist = ($trlist "vis$filemark")
    if ("head -n 1 $fulllist[$idx]/specdata" == "") then
	echo "WARNING: No specdata found for $fulllist[$idx], omitting data..."
    else
	cat $fulllist[$idx]/specdata >> $wd/vis/specdata
	cat $fulllist[$idx]/specdata | awk '{print filename,$4,($5-$4)*1440,"vis",tname}' filename=$fulllist[$idx] tname="vis$filemark" >> $wd/vistimes
    endif
    @ idx++
end
if (`head -n 1 $wd/vistimes` == "") then
    echo "FATAL ERROR: No data found (data may be entirely flagged)"
    goto fail
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
# If the autoedge parameter is used, figure out if dealing with a half or whole spectra, and flag edge channels accordingly
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
	set csel = "$csel,-(1,$autoedgechan),-("`echo $nchan $autoedgechan | awk '{print $1+1-$2","$1}'`"),-("`echo $nchan | awk '{print int($1/2)","int($1/2)+2}'`")"
    endif
    set csel = `echo "$csel" | sed 's/=,/=/'`
endif
# Now sort the timestamps from the dataset and figure out the "order" of the observation
set lim = `wc -l $wd/vistimes | awk '{print $1}'`
set idx = 1

sort -unk2 $wd/vistimes > $wd/timecheck2
echo "Reconstructing observational parameters..."
set slist
set clist
set tslist
set tclist


#################################################################
# The first goal of the program is to figure out how 'large' to
# make the time cycles for processing, and which files belong to
# which cycles. This is done for two reasons - first, so that
# the files can be divided into smaller chunks (if need be) and
# so the processor can catch RFI that is changing over time.
#################################################################

set lim = `wc -l $wd/timecheck2 | awk '{print $1}'`

set idx = 1
set vals = (`sed -n 1p $wd/timecheck2`)
set mastertime = `echo $vals[2] | awk '{printf "%7.6f\n",$1+2400000.5-(.5/86400)}'`
set mastertime2 = `echo $vals[2] | awk '{printf "%7.6f\n",$1-(.5/86400)}'`
set starttime = `echo $vals[2] | awk '{printf "%7.6f\n",$1-(.5/86400)}'`
set timeint = "$vals[3]"
if ($vals[4] == "vis") then
    set slist = $vals[1]; set tslist = $vals[5]
else if ($vals[4] == "tvis") then
    set clist = $vals[1]; set tclist = $vals[5]
endif

set idx = 2

while ($idx <= $lim) 
    set vals = (`sed -n {$idx}p $wd/timecheck2`)
    set timeint = `echo $timeint $vals[3] | awk '{print $1+$2}'`
    if (`echo $vals[2] $vals[3] $starttime | awk '{if (((1440*($1-$3))+$2) > inttime) print 1}' inttime=$inttime`) then
	set finstarttime = `echo $starttime | awk '{printf "%7.6f",$1+2400000.5}'`
	set finstoptime = `echo $vals[2] $vals[3] | awk '{printf "%7.6f",$1+($2/1440)+2400000.5+(.5/86400)}'`
	set finslist = `echo $slist | tr ' ' ','`","
 	set finclist = `echo $clist | tr ' ' ','`","
	set fintslist = `echo $tslist | tr ' ' ','`","
	set fintclist = `echo $tclist | tr ' ' ','`","
	echo $finstarttime $finstoptime $finslist $finclist $fintslist $fintclist >> $wd/obslist
	set starttime = `echo $vals[2] | awk '{printf "%7.6f\n",$1-(.5/86400)}'`
	set mastertime = ($mastertime `echo $vals[2] | awk '{printf "%7.6f\n",$1+2400000.5-(.5/86400)}'`)
	set mastertime2 = ($mastertime2 `echo $vals[2] | awk '{printf "%7.6f\n",$1-(.5/86400)}'`)
	set timeint = "$vals[3]"
	set slist
	set clist
	set tslist
	set tclist
    endif
    if  !(" $clist $slist " =~ *" $vals[1] "*) then
	if ($vals[4] == "vis") then
	    set slist = ($slist $vals[1])
	    set tslist = ($tslist $vals[5])
	else if ($vals[4] == "tvis") then
	    set clist = ($clist $vals[1])
	    set tclist = ($tclist $vals[5])
	endif
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

if !($outsource) goto recon

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
	if (! -e $wd/$tfilelist[$fileidx]$cycle && $flag) uvaver vis=$file out=$wd/$tfilelist[$fileidx]$cycle select=time"($starttime,$stoptime)" options=relax,nocal,nopass,nopol > /dev/null
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
    if ($outsource) then
	set flaglist = ($wd/`echo "$vals[5]$vals[6]," | sed 's/,,//g' | sed 's/\,/'$cycle' '$wd'\//g'`$cycle)
    else
	set flaglist = (`echo "$vals[3-4]" | sed 's/\,/ /g'`)
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
	set ulim = `echo $idx $lim $corrcycle | awk '{if  ($1+$3+int($3/2) >= $2) print 1+$2; else print $1+$3+int($3/2)}'`
	if ($seedcorr) set blim = $idx
	if ($seedcorr) set ulim = `echo $idx | awk '{print $1+1}'`
	set corrfilelist
	while ($blim <= `echo $ulim | awk '{print $1-1}'`)
	    set altcycle = `echo $blim | awk '{print 1000+$1}' | sed 's/1//'`
	    set corrvals = (`sed -n {$blim}p $wd/obslist`)
	    if ($corrvals[3] == ",") set corrvals[3]
	    if ($corrvals[4] == ",") set corrvals[4]
	    if ($corrvals[5] == ",") set corrvals[5]
	    if ($corrvals[6] == ",") set corrvals[6]
	    if ($outsource) set corrfilelist = ($corrfilelist $wd/`echo "$corrvals[5]$corrvals[6]," | sed 's/,,//g' | sed 's/\,/'$altcycle' '$wd'\//g'`$altcycle)
	    if !($outsource) set corrfilelist = ($corrfilelist `echo $corrvals[3]$corrvals[4] | tr ',' ' '`)
	    @ blim++
	end
	set timelim = ($mastertime2[$idx] $mastertime2[$ulim])
	echo "Beginning corruption detection and recovery..."
	touch $wd/badants
	if (`echo $vals[5] | wc -w`) then
	    newrfi32.csh vis=$wd/vis select="time($timelim[1],$timelim[2])" rawdata=$wd/specdata > /dev/null
	    newfracture.csh vis=$wd npoly=$cpoly nsig=$csig options=$corr,desel,recover,$rfitype,`if ($display == 2) echo "verbose"` $csel > $wd/badants
	    echo "time($timelim[1],$timelim[2])" >> $wd/badantshist
	    cat $wd/badants >> $wd/badantshist
	else
	    echo "No source files, using results from last cycle..."
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
		if ($flag) uvflag vis=$file flagval=f options=none "$flagparam[1]" "$flagparam[2]" > /dev/null
	    end
	    echo "Decorruption subcycle $idx.$jidx (of $jlim) complete..."
	    @ jidx++
	end
        echo "Corrupted antennas recovered..."
        set fsel = (`grep "DESEL:" $wd/badants | awk '{print $2,$3}'`)
	if ("$fsel" == "") set fsel = ("pol(xx)" "pol(yy)")
    endif
    # Improvements made here, no more subcycles, just main cycles
    echo "Beginning cycle $idx (of $lim) scanning..."
    set timesel = "time($starttime,$stoptime)"
    if (-e $wd/flagslist) cp $wd/flagslist $wd/flagslist.bu
    
    if ($flaglist[1] != "") then
	newrfi32.csh vis=$wd/vis options=flagopt,$corr,$rfitype chanlist=$wd/flagslist subint=$subint edgerfi=$edgerfi npoly=$npoly nsig=$nsig select="$timesel,$fsel[1] $timesel,$fsel[2]" $csel $device >& $wd/rfidebug
    else
	echo "No source information found, using the last results..."
	if (-e $wd/flagslist.bu) cp $wd/flagslist.bu $wd/flagslist
    endif
    if !(-e $wd/flagslist) touch $wd/flagslist
    if (! -e $wd/flagslist && -e $wd/flagslist.bu) cp $wd/flagslist.bu $wd/flagslist
    echo "Beginning cycle $idx (of $lim) flagging. "`grep line=chan $wd/flagslist | tr ',' ' ' | awk '{SUM += $2} END {print SUM*1}'`" channels to flag in "`grep line=chan $wd/flagslist | wc -l`" iterations."
    set starttime = "`julian options=quiet jday=$mastertime[$idx]`"
    set stoptime = "`julian options=quiet jday=$mastertime[$postidx]`"
    foreach linecmd (`grep "line=chan" $wd/flagslist`)
	foreach file (`echo $flaglist`)
	    if ($flag) uvflag $linecmd vis=$file options=none flagval=f select=time"($starttime,$stoptime)" > /dev/null
	end
	echo -n "."
    end
    echo "."
    set scanidx = 2
    if ($vals[5] != "" && $outsource && $flag) then
	while ($scanidx <= $scans)
	    echo "Beginning scanning pass $scanidx (of $scans)..."
	    foreach file (`echo $vals[5] | tr ',' ' '`)
		if ($autoedge) then
		    newrfi.csh vis=$wd/$file$cycle interval=1 options=autoedge >& /dev/null
		else
		    newrfi.csh vis=$wd/$file$cycle interval=1 >& /dev/null
		endif
	    end
	    set passtwo = `echo "$wd/"$vals[5]"$cycle" | sed "s/,vis/$cycle,$wd\/vis/g" | sed "s/,$cycle/$cycle/"`
	    newrfi32.csh vis=$passtwo options=flagopt,$corr,$rfitype chanlist=$wd/flagslist subint=$subint edgerfi=$edgerfi npoly=$npoly nsig=$nsig select="$timesel,$fsel[1] $timesel,$fsel[2]" $csel $device >& /dev/null
	    if !(-e $wd/flagslist) touch $wd/flagslist
	    if (! -e $wd/flagslist && -e $wd/flagslist.bu) cp $wd/flagslist.bu $wd/flagslist	    
	    echo "Beginning tier-$scanidx flagging. "`grep line=chan $wd/flagslist | tr ',' ' ' | awk '{SUM += $2} END {print SUM*1}'`" channels to flag in "`grep line=chan $wd/flagslist | wc -l`" iterations."
	    set starttime = "`julian options=quiet jday=$mastertime[$idx]`"
	    set stoptime = "`julian options=quiet jday=$mastertime[$postidx]`"
	    foreach linecmd (`grep "line=chan" $wd/flagslist`)
		foreach file (`echo $flaglist`)
		    if ($flag) uvflag $linecmd vis=$file options=none flagval=f select=time"($starttime,$stoptime)" > /dev/null
		end
		echo -n "."
	    end
	    echo "."
	    if (`grep line=chan $wd/flagslist | wc -l` == 0) then
		echo "No bad channels found! Moving forward..."
		set scanidx = $scans
	    endif
	    @ scanidx++
	end
    endif

    @ preidx++ idx++ postidx++ dpostidx++
    echo "Completed cycle. Processing time was "`date +%s | awk '{print int(($1-cycletime)/60)" minute(s) "int(($1-cycletime)%60)" second(s)."}' cycletime=$cycletime`
end

if (! $outsource || ! $flag) goto finish

set fulllist = (`echo $vis $tvis`)
set listlim = `echo $fulllist | wc -w`
set idx = 1
while ($idx <= $listlim)
    echo "$fulllist[$idx] final flagging..." 
    if ($flag) uvaver vis=$wd/$trlist[$idx]'*' options=relax,nocal,nopass,nopol out=$wd/s$trlist[$idx] 
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

foreach file ($vis $tvis)
    if (-e $file/flags) cp $file/flags $file/phoenix/flags.RFI$dmark
end

finish:
if !($debug) rm -r $wd
set times = (`date +%s.%N | awk '{print int(($1-date1)/60),int(($1-date1)%60)}' date1=$date1`)
echo "Flagging process took $times[1] minute(s) $times[2] second(s)."

exit 0

fail:

if !($debug) rm -r $wd

exit 1
