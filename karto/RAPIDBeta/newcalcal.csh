#! /bin/tcsh -f
# $Id$
# Calibrates a calibrator...

onintr fail

if ($#argv == 0) then
      #################################################################
echo "================================================================="
echo "CALCAL - All in one calibration program"
echo "'Building a gains solution for a better tomorrow'"
echo ""
echo "CALLS - newautomap.csh, neweprms.csh, MIRIAD (uvlist, uvplt,"
echo "    uvflag,uvaflag,mfcal,uvaver,gpcopy)"
echo "PURPOSE - Build gains and flags solutions based on calibrator"
echo "    data."
echo "REPSONSIBLE - Karto (karto@hcro.org)"
echo "================================================================="
echo ""    
echo "CALCAL is designed as an 'all-in-one' data reduction utility for"
echo "calibrator data. CALCAL will derive (and copy) gains solutions"
echo "and create maps of calibrator data. The reduction process works"
echo "best with a 'clean' calibrator field (where extended emission"
echo "is minimal) with minimal polarization."
echo ""
echo "CALCAL operates by spliting a calibrator dataset into small time"
echo "intervals, finding a gains solution for that interval, applying"
echo "that solution to that data and finding data points that do not"
echo "agree well with the solution. Those bad datapoints are flagged,"
echo "and the calibration is repeated until all 'bad' data is removed."
echo ""
echo "CALCAL will copy back a gains solution to the calibrator file,"
echo "gains and flags solutions for source files, and create a group"
echo "of maps (e.g. dirty and clean maps) for the calibrator file"
echo "using AUTOMAP; these will normally be located in a directory"
echo "called cal-'calibrator name'-maps. Maps - by default - will not"
echo "be overwritten, and the current flags/gains solutions are" 
echo "'backed-up' (users should note that the back-up copy of these"
echo "solutions WILL be overwritten). CALCAL will also create an"
echo "imaging report and calibration report in the directory"
echo "containing the images of the calibrator"
echo
echo "CALCAL does not currently support polarization calibration"
echo ""
echo "TECHNICAL NOTE: CALCAL creates a temporary directory to work"
echo "from, named calXXXXX (where X is a random character). These"
echo "directories are supposed to be automatically deleted after CALCAL"
echo "completes, but might remain in the event of a program error."
echo "Remnant directories can be safely deleted."
echo ""
echo "TECHNICAL NOTE: CALCAL may create gains/bandpass files in source"
echo "directories with the name 'gains.xx','gains.yy', etc. These are"
echo "to denote solns that are pol-specific, and can be used by simply"
echo "renaming the file (e.g. rename gains.xx to gains). Care should"
echo "be taken not to delete existing files (e.g. renaming gains.xx to"
echo "gains when a 'gains' file is already present)."
echo ""
echo "CALLING SEQUENCE: newcalcal.csh vis=vis (tvis=tvis flux=flux1,"
echo "    flux2,flux3 plim=plim int=int siglim=siglim refant=refant"
echo "    smooth=smooth olay=olay options=debug,autoref,polsplit,"
echo "    [outsource,insource],sefd)"
echo ""
echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo ""
echo "REQUIRED INPUTS:"
echo " vis - Name of the files containing calibrator data. Supports"
echo "    only one file at a time. No default."
echo ""
echo "OPTIONAL INPUTS"
echo " tvis - Name of the 'source' files to apply flags and gains to"
echo "    based on reduction of calibrator data. No default."
echo ""
echo " flux - Flux (in Jy) of calibrator data. Can be specified with"
echo "    a number only (e.g. flux=11) or a number, frequency of flux"
echo "    measurement in GHz and the spectral index (e.g. flux=10,1.4,"
echo "    -.5). Default is 1,1.4,0."
echo ""
echo " addflux - Additional flux (in Jy) expected in the calibrator"
echo "    field (e.g. extended emission). Default is 1."
echo ""
echo " sysflux - Expected variation (in Jy) of calibrator measurements"
echo "    due to system noise. Default is 5."
echo ""
echo " plim - Phase RMS limit (in degrees) for all 'good' baselines."
echo "    Baselines with phase RMS measurements above this limit are"
echo "    automatically flagged as bad. Default is 20"
echo ""
echo " int - Interval time (in minutes) for gains and flags solutions."
echo "    Deault is 10"
echo ""
echo " siglim - Percentage of data (in sigma) that must be identified"
echo "    as 'good' before moving on (e.g. if siglim=3 and there are"
echo "    100 data points, 95 of those datapoints must 'fit' the soln"
echo "    before moving on). Default is 5."
echo ""
echo " refant - Reference antenna (MIRIAD number) for solutions."
echo "    No default."
echo ""
echo " retlim - Retention limit (in percentage) that an element (pol,"
echo "    antenna, baseline) must keep in order to remain marked as"
echo "    'good'. Elements below this limit are flagged (i.e. for"
echo "    retlim=10, a baseline that has 19 of 20 datapoints flagged"
echo "    is removed from the dataset). Default is 20."
echo ""
echo " smooth - This gives three parameters of moving smooth"
echo "    calculation of the bandpass/gain curves"
echo "    smooth(1) = K  parameter k giving the length 2k+1 of the"
echo "        averaging interval; default is 3."
echo "    smooth(2) = L  order of the averaging polynomial l; default"
echo "        is 1."
echo "    smooth(3) = P  probability P for computing the confidence"
echo "        limits; default is 0.9."
echo ""
echo " olay - Overlay file for the autoimaging process. No default."
echo ""
echo ""
echo " device - Device to plot results to (e.g. /xw for x-window)."
echo '    Default is /null.'
echo ""
echo " options=debug,autoref,polsplit,outsource,insource,sefd"
echo "    debug - Don't delete temporary files created by CALCAL."
echo "    autoref - Have CALCAL automatically determine the best"
echo "        reference antenna (default unless refant is specified)."
echo "    polsplit - Process x and y pol data seperately."
echo "    outsource - Split tvis files into smaller chunks for faster"
echo "        processing (default, uses extra hard drive space)."
echo "    insource - Don't split tvis files into smaller chunks."
echo "    sefd - Calculate the SEFD for each antenna."
    exit 0
endif

# Begin variable preset, determine what variables to populate. These are variables that the user has control over when calling the program

set vis # The file to be processed
set tvis # Files to be flagged and gains copied to
set olay # Overlay file for display
set plim = 20 # Phase RMS limit for all baselines
set siglim = 5 # Sigma limit for datasets (i.e. continue when this sigma fraction of the dataset (or less) is flagged during an individual cycle
set int = 10 # Interval period for sol'ns
set flux # Flux for the calibrator (note, no longer automatically supplied!)
set refant # Reference antenna for calibration
set autoref = 1 # If not refant is provided, then calcal will attempt to choose one
set sysflux = 5 # Additional flux from tsys (at three sigma point, say)
set addflux = 1 # Additional flux in the field, definitely good to keep track o
set retlim = 20 # Data retention percentage limit for processing.
set outsource = 1 # Whether or not to split the datasets into smaller chunks
set mapopt = "options=savedata" # Mapping options
set display = 0 # Dispaly results while processing?
set polsplit = 0 # Split pol before processing (first x, then y)
set debug = 0 # Save temp data after running?
set device
set wrath = 0
set wrathcycle = 0
set sefd = 0
set smooth
set report = 1
set nogainants
set copymode = 0

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
else if ("$argv[1]" =~ 'olay='*) then
    set olay = "$argv[1]"
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'plim='*) then
    set plim = `echo $argv[1] | sed 's/plim=//'`
    if ("$plim" == "0") then
	echo "FATAL ERROR: Bad select for plim (0 degree limit)"
	exit 1
    endif
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'siglim='*) then
    set siglim = `echo $argv[1] | sed 's/siglim=//'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'int='*) then
    set int = `echo $argv[1] | sed 's/int=//'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'device='*) then
    set device = "$argv[1]"
    set display = 1
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'options='*) then
    set options = `echo "$argv[1]" | sed 's/options=//g' | tr ',' ' ' | tr '[A-Z]' '[a-z]'`
    set badopt
    foreach option (`echo $options`)
	if ($option == "insource") then
	    set outsource = 0
	else if ($option == "outsource") then
	    set outsource = 1
	else if ($option == "polsplit") then
	    set polsplit = 1
	else if ($option == "nopolsplit") then
	    set polsplit = 0
	else if ($option == "debug") then
	    set debug = 1
	else if ($option == "wrath") then
	    set wrath = 1
	else if ($option == "autocal") then
	    set mapopt = "$mapopt,autocal"
	else if ($option == "sefd") then
	    set sefd = 1
	    set mapopt = "$mapopt,sefd"
	else if ($option == "copy") then
	    set copymode = 1
	else if ($option == "lastcopy") then
	    set copymode = 2
	    set outsource = 0
	else
	    set badopt = ($badopt $option)
	endif
    end
    if ("$badopt" != "") echo 'options='`echo $badopt | tr ' ' ','`' not recognized!'
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'flux='*) then
    set flux = `echo $argv[1] | sed 's/flux=//'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'addflux='*) then
    set addflux = `echo $argv[1] | sed 's/addflux=//'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'sysflux='*) then
    set sysflux = `echo $argv[1] | sed 's/sysflux=//'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'retlim='*) then
    set retlim = `echo $argv[1] | sed 's/retlim=//' | awk '{print int($1)}'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'refant='*) then
    set refant = `echo $argv[1] | sed 's/refant=//'`
    set autoref = 0
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'smooth='*) then
    set smooth = `echo $argv[1]`
    shift argv; if ("$argv" == "") set argv = "finish"
else
    echo "FATAL ERROR: $argv[1] not recognized..."
    exit 1
endif

if ("$argv[1]" != "finish") goto varassign

if ("$vis" == "") then
    echo "Vis file needed"
    exit 1
else if !( -e $vis) then
    echo "Vis file needed!"
    exit 1
endif

#################################################################
# The cal program creates a temp directory to work in within the
# data directory being used. This is done to make operations
# "cleaner", as several MIRIAD results are dumped to temp files
# to be parsed later.
#################################################################


set wd = (`mktemp -d cal2XXXX`)

if !( -e $wd) then
    echo "FATAL ERROR: Unable to create working directory, please make sure that you have read/write permissions for this area."
    exit 1
endif

#################################################################
# If any gains solutions are found in the cal or source files,
# the program will attempt to back them up (in case the program
# fails to create a good gains/flags solution).
#################################################################

set date1 = `date +%s.%N`
set dmark = `date +%s`

if ($copymode) goto copymode

foreach file ($vis $tvis)
    if !(-e $file/phoenix) mkdir -p $file/phoenix
    if (! -e $file/phoenix/flags.o && -e $file/flags) cp $file/flags $file/phoenix/flags.o
    if (! -e $file/phoenix/gains.o && -e $file/flags) cp $file/flags $file/phoenix/gains.o
    if (! -e $file/phoenix/bandpass.o && -e $file/bandpass) cp $file/bandpass $file/phoenix/bandpass.o
    if !(-e $file/phoenix/header.o) cp $file/header $file/phoenix/header.o
    echo "CALCAL $dmark" >> $file/phoenix/history
end

#################################################################
# The program works by slicing the calibration data into smaller
# chunks according to observing time. The general idea is that
# each calibration cycle during the observation should be
# processed seperately. This is done for two reasons - to make
# data processing easier and more robust (a glitch during one
# scan could cause considerable problems if processed all at
# once), and to enable flagging of "bad" baselines/ants/pols
# in the source data).
#################################################################

echo "Looking up times for calibrator observations."
set regtimes = (`uvlist vis=$vis options=stat recnum=0 | awk '{if ($1*1 > 0) print day":"$2; else if ($1$2$3 == "Datavaluesfor") day = $4}' | sort | uniq`)
set jultimes
echo "Observation times found, splitting into time intervals"
foreach itime ($regtimes)
    julian date=$itime options=quiet >> $wd/jultimes # For SELECT commands, datates need to be formatted correctly
end
# Figure out the start and end time for each interval
set jultimes = (`awk '{if ($1-lastday-(1/86400) > interval/1440){if (NR == 1) printf "%7.6f\n",$1-1; lastday = $1; printf "%7.6f\n",$1-(1/86400)}; fin = $1} END {printf "%7.6f\n",fin+1}' interval=$int $wd/jultimes`) 
echo `echo $#jultimes | awk '{print $1-2}'`" time cycles confirmed."
set regtimes

foreach itime ($jultimes)
    set regtimes = ($regtimes `julian jday=$itime options=quiet`)
end

# Below, UVLIST is used to find out some metadata about the dataset being processed

set nchanline = (`uvlist vis=$vis options=var,full | grep nchan | tr ':' ' '`)
set nchan
# Get the number of channels
while ($nchan == "")
    if ($nchanline[1] == "nchan") then
	set nchan = "$nchanline[2]" 
    else if ($#nchanline == 1) then
	set nchan == 512 # Default to 512 channels if cannot be found
    else
	shift nchanline
    endif
end

set sourceline = (`uvlist vis=$vis options=var | grep "source" | tr ':' ' '`)
set source
#Get the name of the calibrator
while ($source == "")
    if ($sourceline[1] == "source") then
	set source = "$sourceline[2]" 
    else if ($#sourceline == 1) then
	set source == "UNK" # Default to name UNK if cannot be found
    else
	shift sourceline
    endif
end

set freqline = (`uvlist vis=$vis options=var | grep "freq    :" | tr ':' ' '`)
set freq
#Get the obs freq of the calibratior (in MHZ)
while ("$freq" == "")
    if ($freqline[1] == "freq") then
	set freq = `echo $freqline[2] | awk '{print $1}'` 
    else if ($#freqline == 1) then
	set freq == "1.42" # Default to 20 cm measurements
    else
	shift freqline
    endif
end

set inttimeline = (`uvlist vis=$vis options=var,full | grep "inttime" | tr ':' ' '`)
set inttime
while ("$inttime" == "")
    if ($inttimeline[1] == "inttime") then
	set inttime = `echo $inttimeline[2] | awk '{print ($1-.00001)/60}'` 
    else if ($#inttimeline == 1) then
	set inttime == `echo 10 | awk '{print ($1-.00001)/60}'` # Default to ATA
    else
	shift inttimeline
    endif
end

set nantsline = (`uvlist vis=$vis options=var | grep "nants" | tr ':' ' '`)
set nants
#Get the number of antennas
while ("$nants" == "")
    if ($nantsline[1] == "nants") then
	set nants = `echo $nantsline[2] | awk '{print $1}'` 
    else if ($#nantsline == 1) then
	set nants == "42" # Default to ATA
    else
	shift nantsline
    endif
end

set cal = $source
	
rm -f $cal.calrpt

#################################################################
# The flux is calculated below using the information provided at
# the initialization of the program. If a flux and observing 
# freq and spectral index are given, the program will use that
# with MFCAL and will calculate the appropriate flux for the obs
# frequency. If only the flux is given, then the program will
# add the obs freq and a spectral index of 0 so that it can be
# passed on to MFCAL. And finally, if no information is given,
# then the program will assume a flux of 1, a "clean" cal field
# (i.e. no extended emission or other point sources), and a
# moderate strength compared to the system noise.
#################################################################

if (`echo $flux | tr ',' ' ' | wc -w` == 3) then
    set calflux = `echo $freq $flux | tr ',' ' ' | awk '{print $2*($1/$3)^$4}'`
else if (`echo $flux | wc -w` == 1 ) then
    set calflux = "$flux"
    set flux = "$flux,$freq,0"
else if ("$flux" == "") then
    set calflux = 1
    set flux = 1
    set flux = "1,$freq,0"
    set addflux = 0
    set sysflux = .5
else
    echo "Flux option not recognized!" # Error out if flux isn't put in properly
    exit 1
endif


echo "Cal is $source - flux is $calflux Jy - nchan is $nchan - freq is $freq GHz"
set fullxants = (`uvplt vis=$vis device=/null select='pol(xx),-auto' | tr '-' ' ' | grep "Baseline" | awk '{print $2"\n"$3}' | sort -nu`)
set fullyants = (`uvplt vis=$vis device=/null select='pol(yy),-auto' | tr '-' ' ' | grep "Baseline" | awk '{print $2"\n"$3}' | sort -nu`)
set fullxret
set fullyret
set fullxpos
set fullypos

set idx = 1
set nantsarray = (0)

while ($nants > $#nantsarray)
    set nantsarray = (0 $nantsarray)
end

# A series of 42-element arrays to record data retention
set fullxaret = ($nantsarray)
set fullyaret = ($nantsarray)
set fullxapos = ($nantsarray)
set fullyapos = ($nantsarray)

set pollist = ("xxyy")

if ("$fullxants" == "" && "$fullyants" == "") then
    echo "FATAL ERROR: No visibilities present!"
    goto fail
endif

if ("$fullxants" == "") set pollist = ("yy")
if ("$fullyants" == "") set pollist = ("xx")

echo -n "Preprocessing data..."

# If the polsplit option is used, split the individual pols into seperate files for processing.

if ($polsplit) then
    set pollist = ("xx" "yy")
    uvaver vis=$vis select='window(1),pol(xx)' out=$wd/tempcalxx options=relax,nocal,nopass,nopol interval=$inttime >& /dev/null
    echo -n "."
    uvaver vis=$vis select='window(1),pol(yy)' out=$wd/tempcalyy options=relax,nocal,nopass,nopol interval=$inttime >& /dev/null
    echo -n "."
else
    uvaver vis=$vis select='window(1),pol(xx,yy)' out=$wd/tempcalxxyy options=relax,nocal,nopass,nopol interval=$inttime >& /dev/null
    echo -n "."
endif

echo ""
# Perform some error checking to make sure that "blank" datasets are created

if !(-e $wd/tempcalxxyy || -e $wd/tempcalxx || -e $wd/tempcalyy) then
    echo "FATAL ERROR: No visibilities exist!"
    goto fail
else if (! -e $wd/tempcalxx/visdata && -e $wd/tempcalyy/visdata) then
    set pollist = ("yy")
    set polsplit = 1
    echo "No x-pol data found, continuing..."
else if (! -e $wd/tempcalyy/visdata && -e $wd/tempcalxx/visdata) then
    set pollist = ("xx")
    set polsplit = 1
    echo "No y-pol data found, continuing..."
endif

set idx = 2; set postidx = 3
set tviscount = 0

# Split the source and cal data into smaller files (via the timestamps collected earlier)

while ($idx < $#regtimes)
    set cycle = `echo $idx | awk '{print 999+$1}' | sed 's/1//'` # The cycle number is there to files from a particular time range a unique marker
    echo -n "Preparing file "`echo $idx | awk '{print $1-1}'`" of "`echo $#regtimes | awk '{print $1-2}'`"..."
    foreach pol (`echo $pollist | sed 's/xxyy/xx,yy/g'`)
	uvaver vis=$wd/tempcal`echo $pol | tr -d ','` out=$wd/tempcali`echo $pol | tr -d ','`$cycle options=relax,nocal,nopass,nopol select="window(1),time($regtimes[$idx],$regtimes[$postidx]),pol($pol)" >& /dev/null
    end
    if ($outsource && "$tvis[1]" != "") then
        set tviscount = ($tviscount 0)
	set fileidx = 0
	foreach tfile ($tvis)
	    @ fileidx++
	    set filemark = `echo $fileidx | awk '{print $1+100000}' | sed 's/1//'`
	    @ tviscount[$idx]++
	    uvaver vis=$tfile out=$wd/tvis$filemark$cycle options=relax,nocal,nopass,nopol select="time($regtimes[$idx],$regtimes[$postidx])" >& /dev/null
	    if !(-e $wd/tvis$filemark$cycle/visdata) rm -rf $wd/tvis$filemark$cycle
	    if !(-e $wd/tvis$filemark$cycle/visdata) @ tviscount[$idx]--
        end
    endif
    echo "complete."
    @ idx++ postidx++
end

# If source data exists before the first calibration, grab that too
set fileidx = 0
if ($outsource && "$tvis[1]" != "") then
    foreach tfile ($tvis)
	@ fileidx++
	set filemark = `echo $fileidx | awk '{print $1+100000}' | sed 's/1//'`
	@ tviscount[1]++
        uvaver vis=$tfile out=$wd/tvis{$filemark}000 options=relax,nocal,nopass,nopol select="time($regtimes[1],$regtimes[2])" >& /dev/null
        if !(-e $wd/tvis{$filemark}000/visdata) rm -rf $wd/tvis{$filemark}000
        if !(-e $wd/tvis{$filemark}000/visdata) @ tviscount[1]--
    end
endif
echo " "
echo " "
echo "Starting flagging and calibration."

#################################################################
# This section begins the code for calibration and flagging. Up
# to this point, we have split the calibrator file into smaller
# chunks based on time (and possibly polarization). Each file is
# now processed individually. Once the data "passes" the
# flagging/calibration process (i.e. the amount of data flagged
# is below some threshold percentage, as established by the
# siglim switch), baselines, ants and pols are checked for their
# retention percentages. If some element's retention percentage
# falls below the limit, data corresponding to that element (in
# both the calibrator and source datasets)  are flagged, and the
# calibration cycle repeats, until no more elements need to be 
# flagged. The program then moves on to the next file, until
# all files have been processed.
#################################################################

set xrefant
set yrefant
set limtotal

foreach ipol ($pollist) # Work with only one pol at a time
    set idx = 0; set mididx = 1; set postidx = 2
    set wrathcycle = 1
    foreach file ($wd/tempcali{$ipol}*)
	@ idx++ mididx++ postidx++
	set cycletime = "`date +%s.%N`" # Counter for processing time
	set cycle =  `echo $idx | awk '{print 1000+$1}' | sed 's/1//'`
	set precycle =  `echo $idx | awk '{print 999+$1}' | sed 's/1//'`
	set sfilelist # Source files to be flagged
	set prefiles # Source files from observing immediately prior to cal cycle
	set postfiles # Source files from observing immediately following the cal cycle
	if ($outsource && "$tvis[1]" != "") then	
	    if ($tviscount[$idx]) set prefiles = "$wd/tvis*$precycle"
	    if ($tviscount[$mididx]) set postfiles = "$wd/tvis*$cycle"
	    set sfilelist = ($prefiles $postfiles) # "Paste" the two file sets together
	else
	    foreach sfile ($tvis) # Check to make sure that datasets have data from that time period relating to the calibration cycle
		if (`uvplt vis=$sfile select="time($regtimes[$idx],$regtimes[$postidx])" device=/null | grep -c "Baseline"`) set sfilelist = ($sfilelist $sfile)
	    end
	endif
	rm -f $wd/xbase $wd/ybase; touch $wd/xbase; touch $wd/ybase # Files for recording basica information about which baselines are present
	set pointmax = 0
	if ("$ipol" =~ *"xx"*) then
	    uvplt vis=$file options=2pass device=/null options=2pass,all select='pol(xx),-auto' | grep Baseline | awk '{print $2,$3,$5}' | sed 's/-//g' > $wd/xbase # Get xx baselines
	    set xmax = `awk '{print $3}' $wd/xbase | sort -n | tail -n 1`
	    if ($xmax > $pointmax) set pointmax = $xmax
	endif
	if ("$ipol" =~ *"yy"*) then 
	    uvplt vis=$file options=2pass device=/null options=2pass,all select='pol(yy),-auto' | grep Baseline | awk '{print $2,$3,$5}' | sed 's/-//g' > $wd/ybase # Get yy baselines
	    set ymax = `awk '{print $3}' $wd/ybase | sort -n | tail -n 1`
	    if ($ymax > $pointmax) set pointmax = $ymax
	endif
	echo -n "Starting $idx of "`echo $#regtimes | awk '{print $1-2}'`" cycles. Beginning phase RMS scanning."

#################################################################
# The first processing requirement is to get rid of baselines
# that appear to have no fringes. This is done by measuring the
# phase RMS on each baseline, and flagging those that exceed
# some limit (as specified by the "plim" switch). The phase RMS
# appears to be the best choice for finding the weakest
# baselines, since it should not be calibration dependant
# (MFCAL is attempting to find a solution for the entire time
# cycle, not just independant points).
#################################################################

	if ($idx != $#regtimes) then
	    foreach badbase (`neweprms.csh vis=$file plim=$plim`)
		uvflag vis=$file select="$badbase" flagval=f options=none > /dev/null
		echo -n "."
	    end
	endif

	echo "phase scanning/flagging complete."
# Gather the list of antennas from the baseline information
	set xants = (`awk '{printf "%s\n%s\n",$1,$2}' $wd/xbase | sort -n | uniq`)
	set yants = (`awk '{printf "%s\n%s\n",$1,$2}' $wd/ybase | sort -n | uniq`)
	set xantcount = $#xants
	set yantcount = $#yants
	if ("$xants" == "") set xantcount = 0
	if ("$yants" == "") set yantcount = 0
# Get rid of the autocorrelation data (for now)
	uvflag vis=$file select=auto options=none flagval=f >& /dev/null
# This starts the calibration part of the code
    jumper:
	touch $wd/amplog
	set checkamp = (1000 100000)

# If using autoref, find the antenna with the most number of points remaining in the dataset.

	if ($autoref) then
	    uvplt vis=$file options=2pass select='-auto' axis=ti,pha device=/null | grep "Baseline" | awk '{print $2,$3,$5}' | tr -d '-' > $wd/refantstat
	    set antstat = 0
	    set refant = 0
	    foreach ant (`awk '{printf "%s\n%s\n",$1,$2}' $wd/refantstat | sort -nu`)
		if ($antstat < `awk '{if ($1 == ant || $2 == ant) sum += $3} END {print sum}' ant=$ant $wd/refantstat`) then
		    set antstat = `awk '{if ($1 == ant || $2 == ant) sum += $3} END {print sum}' ant=$ant $wd/refantstat`
		    set refant = $ant
		endif
	    end
	    echo -n "Refant $refant choosen! "
	endif
# Horray for MFCAL!    
	mfcal vis=$file refant=$refant options=interpolate minants=4 flux=$flux interval=$int >& $wd/checkmfcal

	if (`grep "time order" $wd/checkmfcal | wc -l`) then
	    echo ""
	    echo "FATAL ERROR: Data not in time order!"
	    goto fail
	endif

# UVAVER is used to "apply" the gains solutions to the dataset.
	uvaver vis=$file out=$wd/tempcal2 options=relax >& /dev/null	
	set sflags = 0
	if ($display) uvplt vis=$wd/tempcal2 select='-auto' $device options=2pass,nobase,equal,source axis=re,im >& /dev/null # Display results if requested
#################################################################
# After calibration is achieved and applied, UVLIST is used to
# dump out the ampitude and phase information. Currently, the
# program assumes a simple point source model, and "subtracts"
# this model from the data. Data are then flagged based on the
# residual flux (from the addflux and sysflux parameters).
# Individual channels are flagged as well, with an appropriate
# increase to sysflux (roughly equal to (nchan^.5)*sysflux). The
# program will not flag more than 5% of the total data at a 
# time - this is done to prevent a "bad" solution from causing
# a catasrophic failure, resulting in all data being flagged.
#################################################################
	uvlist vis=$wd/tempcal2 select='-auto' recnum=0 line=chan,1,1,$nchan | sed 1,9d | awk '{if ($1*1 ==0); else if ($8*1 != 0 || $9*1 != 0) print $1,$9,(($8*cos(pi*$9/180)-flux)^2+($8*sin(pi*$9/180))^2)^.5}' flux=$calflux pi=3.141592 | sort -nk3 > $wd/ampinfo 
	# Gather some basic information about the data limits
	set curtotal = `wc -l $wd/ampinfo | awk '{print $1*1}'`
	if ("$limtotal" == "") set limtotal = `echo $curtotal $retlim | awk '{print int((2^int(log(100/$2)/log(2)))*.01*$1*$2)}'`
	set linecheck = `wc -l $wd/ampinfo | awk '{print int($1*.95)}'`
	set linelim = `wc -l $wd/ampinfo | awk '{print int($1*exp(-1*siglim))}' siglim=$siglim`
	set linemax = `wc -l $wd/ampinfo | awk '{print 1+int($1*.05)}'`
	set intcheck = `tail -n 1 $wd/ampinfo | awk '{print $3}'`
	# Enforce a limit on the minmum number of flags needed to pass to the next stage
	if ($linelim < 10) set linelim = 10
	if ($linemax < 10) set linemax = 10
	echo "Minimum flagging line is $linelim, maximum is $linemax."
	# Enforce the 5% limit for flagging.
	if (`sed -n {$linecheck}p $wd/ampinfo | awk '{if ($3*1 < (addflux+sysflux)) print "go"; else if ($3*1 < intcheck/10 && (addflux+sysflux) < intcheck/10) print "go"}' addflux=$addflux sysflux=$sysflux intcheck=$intcheck` == "go") then
	    if (`echo $intcheck $addflux $sysflux | awk '{if ($1/10 > ($2+$3)) print "go"}'` == "go") then
		awk '{if ($3 > (intcheck/10)) print $1}' intcheck=$intcheck $wd/ampinfo | sort -nk1 > $wd/amplog
		set checkamp[1] = `echo $intcheck | awk '{print $1/10}'`
	    else
		awk '{if ($3 > (addflux+sysflux)) print $1}' addflux=$addflux sysflux=$sysflux $wd/ampinfo | sort -nk1 > $wd/amplog
		set checkamp[1] = `echo $addflux $sysflux | awk '{print $1+$2}'`
	    endif
	else
	    sed 1,{$linecheck}d $wd/ampinfo | awk '{print $1}' | sort -nk1 > $wd/amplog
	    set checkamp[1] =  `sed -n {$linecheck}p $wd/ampinfo | awk '{print $3}'`
	endif
	set asel = `echo $checkamp[1] $intcheck $nchan | awk '{if ($2/10 > $1*1.25*($3^.5)) print "amp("$2/10")";else print "amp("$1*1.25*($3^.5)")"}'`
	set checkamp[2] = `echo $asel | tr -d 'amp()'`
	set sflags = `uvflag vis=$wd/tempcal2 select="$asel" options=brief,noquery flagval=f | grep "Changed to bad:" | awk '{sum += $7} END {print 1*sum}'`

#################################################################
# Flagging is a relatively simple task, since the previous step
# establishes which records sit outside the "nominal" range and
# need to be flagged. UVFLAG can only flag 50 records at a time
# currently, so the program has to move through increments 
# of data to be flagged. After individual records have been
# flagged, if the amount of data flagged falls below a certain
# threshold, the program checks for data retention with diff
# elements (i.e. pols, ants, baselines). To minimize redudant
# operations, the program first checks pols, then checks ants,
# then checks individual baselines. The program then checks for
# the retention rate of ants based on changes in baselines being
# flagged, and then checks the rate of retention on indv. pols,
# based on changes from antennas being flagged.
#################################################################

	flagging:
	echo "Flagging commencing, outer-limit for flux noise is $checkamp[1] Jy for integrated spectra, $checkamp[2] Jy for individual channels."
	set llim=1
	set ulim=50
	set lim = `wc -w $wd/amplog | awk '{print $1}'`
    
	echo -n "$lim integrated records to flag and $sflags spectral records to flag..."
	uvflag vis=$wd/tempcal2 flagval=f select='amp(0,0.0000000000000001)' options=none >& /dev/null #This is here since uvcal is stupid, and this corresponds to a noise level of 80 dBS (SNR of 1:10^8)
	while ($llim <= $lim)
	    set flags = `sed -n {$llim},{$ulim}p $wd/amplog | awk '{printf "%s","vis("$1"),"}' ulim=$ulim`
	    uvflag vis=$wd/tempcal2 flagval=f options=none select=$flags >& /dev/null
	    set llim = `echo $llim | awk '{print $1+50}'`
	    set ulim = `echo $ulim | awk '{print $1+50}'`
	    echo -n "."
	end
	echo " "
	# UVAFLAG is used here since we created a temp dataset to apply the gains to.
	uvaflag vis=$file tvis=$wd/tempcal2 >& /dev/null
	rm -rf $wd/tempcal2 $wd/amplog $wd/ampinfo
	
	set pols = (x y)
	if ("$retlim" == 0) set pols
	# If we haven't dropped below the repeat threshold, then repeat.
	if ($limtotal > $curtotal) then
	    set limtotal = `echo $curtotal | awk '{print int($1/2)}'`
	    echo "WARNING: Data retention has fallen below critical threshold..."
	else if ((`echo $sflags $linelim $lim | awk '{if ($1 > $2*(nchan^.5)) print "go"; else if ($2 < $3) print "go"}' nchan=$nchan` == "go" || `echo $intcheck $addflux $sysflux | awk '{if ($1/10 > ($2+$3)) print "go"}'` == "go") && $linelim != $linemax) then
	    echo " "
	    echo "Flagging complete, continuing cycle $idx of "`echo $#regtimes | awk '{print $1-2}'`"..."
	    goto jumper
	endif
	
	# Gather information on the number of datapoints for each baseline
	if ("$ipol" =~ *"xx"*) then
	    uvplt vis=$file options=2pass device=/null select='pol(xx),-auto' | grep Baseline | awk '{print $2,$3,$5}' | sed 's/-//g' > $wd/xbasetemp
	endif
	if ("$ipol" =~ *"yy"*) then	
	uvplt vis=$file options=2pass device=/null select='pol(yy),-auto' | grep Baseline | awk '{print $2,$3,$5}' | sed 's/-//g' > $wd/ybasetemp
	endif
    # Begin data retention check
	set badjump = 0
	set pols = (x y)
	if ("$xants" == "") set pols = (y)
	if ("$yants" == "") set pols = (x)
	if ("$xants" == ""  && "$yants" == "") set pols
	if ("$retlim" == 0) set pols
	foreach pol ($pols)
	    set jidx = 1
	    echo -n "Checking preliminary $pol pol retention..."
	    set antlist
	    set badants
	    set antlist = (`awk '{printf "%s\n%s\n",$1,$2}' $wd/{$pol}basetemp | sort -n | uniq`)
	    if ("$pol" == "x") set antcount = $xantcount
	    if ("$pol" == "y") set antcount = $yantcount
	    if ($#antlist <= 1) set antlist
	    if (`echo $#antlist $antcount | awk '{print int(100*$1/$2)}'` < $retlim) then # Check if number of ants falls below retention limit
		@ badjump++; @ badjump++ # This appears twice so that one baseline can be flagged without the need for repeating a calibration.
		echo "$pol-pol data appears to be unusable, beginning removal."
		uvflag vis=$file options=none flagval=f select="pol($pol$pol)" > /dev/null # Flag data with polarization below retention limit
		foreach sfile (`echo $sfilelist`)
		    uvflag vis=$sfile options=none flagval=f select="pol($pol$pol),time($regtimes[$idx],$regtimes[$postidx])" > /dev/null # Also flag source files if retention lim is not met
		end
		echo "" > $wd/{$pol}base
		# Reset the list of ants if a pol was entirely flagged
		if ("$pol" == "x") set xants
		if ("$pol" == "y") set yants
	    endif
	    echo " "
    ###
	    set jidx = 1
	    echo -n "Checking preliminary $pol antenna retention..."
	    set antlist
	    set badants
	    if ("$pol" == "x") set antlist = ($xants)
	    if ("$pol" == "y") set antlist = ($yants)
	    if ("$pol" == "x") set antcount = $xantcount
	    if ("$pol" == "y") set antcount = $yantcount
	    if ($#antlist <= 1) set antlist
	    foreach ant (`echo $antlist`)
		# Check to see the number of antennas associated with each baseline
		set vals = (`awk '{if ($1 == ant || $2 == ant) count += 1} END {print int(100*count/(ocount-1))}' ocount=$antcount ant=$ant $wd/{$pol}basetemp`)
		# If the number of baselines falls below the retention limit times it's theoretical threshold (N_ants-1), then flag it as bad.
		if ($vals[1] < $retlim) then
		    @ badjump++; @ badjump++
		    echo -n "."
		    set badants = ($badants $ant)
		    set antlist[$jidx]
		    if ("$pol" == "x") set xants[$jidx]
		    if ("$pol" == "y") set yants[$jidx]
		    awk '{if ($1 != ant && $2 != ant) print $0}' ant=$ant $wd/{$pol}base > $wd/{$pol}base2 # Remove baselines corresponding to removed antennas from listing of all baselines
		    mv $wd/{$pol}base2 $wd/{$pol}base
		endif
		@ jidx++
	    end
	    if ("$badants" != "") then
		# Reset the list of antennas to reflect removed ants
		if ("$pol" == "x") set xants = (`echo $xants`) 
		if ("$pol" == "y") set yants = (`echo $yants`)
		set antlist = (`echo $antlist`)
		set flagcmd = "ant("`echo $badants | tr ' ' ','`"),pol($pol$pol)"
		set flagcmd = `echo "$flagcmd"`
		# Flag bad ants
		uvflag vis=$file options=none flagval=f select="$flagcmd" > /dev/null
		foreach sfile (`echo $sfilelist`)
		    uvflag vis=$sfile options=none flagval=f select="$flagcmd,time($regtimes[$idx],$regtimes[$postidx])" > /dev/null
		end
	    endif
	    echo " "

######

	    set jidx = 1
	    echo -n "Checking $pol$pol baseline retention..."
	    rm -f $wd/bad{$pol}base; touch $wd/bad{$pol}base
	    while ($jidx < `wc -l $wd/{$pol}base | awk '{print $1}'`)
		# Check the number of datapoints per baseline
		set vals = (`sed -n {$jidx}p $wd/{$pol}base`)
		set vals2 = (`awk '{if ($1 == ant1 && $2 == ant2) npoint += $3} END {print int(100*npoint/opoint)}' ant1=$vals[1] ant2=$vals[2] opoint=$vals[3] $wd/{$pol}basetemp`)
		# If the number of points per baselines falls below threshold, flag.
		if ($vals2[1] < $retlim) then
		    @ badjump++ # Program can flag one baseline without needing to recalibrate (since the ammount of affected data is minimal
		    # Remove affected baselines from listing of all baselines
		    echo $vals >> $wd/bad{$pol}base
		    sed {$jidx}d $wd/{$pol}base > $wd/{$pol}base2
		    mv $wd/{$pol}base2 $wd/{$pol}base
		else
		    @ jidx++
		endif
	    end
	    # This ends the search for bad baselines
	    set antlist = (`sed 's/-/ /g' $wd/bad{$pol}base | awk '{printf "%s\n%s\n",$1,$2}' | sort -n | uniq`)
	    # Repeat original check for antenna retention
	    while (`wc -w $wd/bad{$pol}base | awk '{print $1}'`)
		set kidx = 0
		set nant = 0
		set mcount = 0
		set icount = 0
		foreach ant ($antlist)
		    @ kidx++
		    set icount = `sed 's/-/ /g' $wd/bad{$pol}base | awk '{if ($1 == ant || $2 == ant) lidx += 1} END {print lidx}' ant=$ant`
		    if ($icount > $mcount) then
			set nant = $kidx
			set mcount = $icount
		    endif
		end
		set ant = $antlist[$nant]
		set flagcmds = (`sed 's/-/ /g' $wd/bad{$pol}base | awk '{if ($1 == ant) {printf "%s,",$2; idx +=1}; if ($2 == ant) {printf "%s,",$1; idx +=1}; if (idx%11 == 10) print ")"} END {if (idx%11 != 10) print ")"}' ant=$ant | sed 's/,)//g' | tr -d ")"`)
		foreach flagcmd ($flagcmds)
		uvflag vis=$file options=none flagval=f select="ant($ant)($flagcmd),pol($pol$pol)" > /dev/null
		foreach sfile (`echo $sfilelist`)
		    uvflag vis=$sfile options=none flagval=f select="ant($ant)($flagcmd),pol($pol$pol),time($regtimes[$idx],$regtimes[$postidx])" > /dev/null
		end
		end
		echo -n "."
		set antlist[$nant]
		set antlist = (`echo $antlist`)
		sed 's/-/ /g' $wd/bad{$pol}base | awk '{if ($1 != ant && $2 != ant) print $1"-"$2}' ant=$ant > $wd/bad{$pol}base2
		mv $wd/bad{$pol}base2 $wd/bad{$pol}base
	    end
	    
	    echo " "
    ###
	
	    uvplt vis=$file options=2pass device=/null select="pol($pol$pol),-auto" | grep Baseline | awk '{print $2,$3,$5}' | sed 's/-//g' > $wd/{$pol}basetemp
	    # Repeat check for pol retention
	    set jidx = 1
	    echo -n "Checking secondary $pol antenna retention..."
	    set antlist
	    set badants
	    if ("$pol" == "x") set antlist = ($xants)
	    if ("$pol" == "y") set antlist = ($yants)
	    if ("$pol" == "x") set antcount = $xantcount
	    if ("$pol" == "y") set antcount = $yantcount
	    if ($#antlist <= 1) set antlist
	    foreach ant (`echo $antlist`)
		set vals = (`awk '{if ($1 == ant || $2 == ant) count += 1} END {print int(100*count/(ocount-1))}' ocount=$antcount ant=$ant $wd/{$pol}basetemp`)
		if ($vals[1] < $retlim) then
		    @ badjump++; @ badjump++
		    echo -n "."
		    set badants = ($badants $ant)
		    set antlist[$jidx]
		    if ("$pol" == "x") set xants[$jidx]
		    if ("$pol" == "y") set yants[$jidx]
		    awk '{if ($1 != ant && $2 != ant) print $0}' ant=$ant $wd/{$pol}base > $wd/{$pol}base2
		    mv $wd/{$pol}base2 $wd/{$pol}base
		endif
		@ jidx++
	    end
	    if ("$badants" != "") then
		if ("$pol" == "x") set xants = (`echo $xants`)
		if ("$pol" == "y") set yants = (`echo $yants`)
		set antlist = (`echo $antlist`)
		set flagcmd = "ant("`echo $badants | tr ' ' ','`"),pol($pol$pol)"
		set flagcmd = `echo "$flagcmd"`
		uvflag vis=$file options=none flagval=f select="$flagcmd" > /dev/null
		foreach sfile (`echo $sfilelist`)
		    uvflag vis=$sfile options=none flagval=f select="$flagcmd,time($regtimes[$idx],$regtimes[$postidx])" > /dev/null
		end
	    endif
	    echo " "
	
	    if (`echo $#antlist $antcount | awk '{print int (100*$1/$2)}'` < $retlim) then
		@ badjump++; @ badjump++
		echo "$pol-pol data appears to be unusable, beginning removal."
		uvflag vis=$file options=none flagval=f select="pol($pol$pol)" > /dev/null
		foreach sfile (`echo $sfilelist`)
		    uvflag vis=$sfile options=none flagval=f select="pol($pol$pol),time($regtimes[$idx],$regtimes[$postidx])" > /dev/null
		end
		echo "" > $wd/{$pol}base
		if ("$pol" == "x") set xants
		if ("$pol" == "y") set yants
	    endif
	end
    # End data retention check - if needed, repeat the calibration and retention checks
	if ($badjump) @ badjump--
	if ("$xants" == ""  && "$yants" == "") then
	    echo "Calibration for cycle failed! Moving on to next cycle"
	else if ($badjump) then
	    rm -f $wd/ampinfo $wd/amplog
	    echo "Culling complete, continuing cycle $idx of "`echo $#regtimes | awk '{print $1-2}'`"..."
	    echo " "
	    goto jumper
	else if ((`echo $sflags $linelim $lim | awk '{if ($1 > $2*(nchan^.5)) print "go"; else if ($2 < $3) print "go"}' nchan=$nchan` == "go" || `echo $intcheck $addflux $sysflux | awk '{if ($1/10 > ($2+$3)) print "go"}'` == "go") && $linelim != $linemax) then
	    rm -f $wd/ampinfo $wd/amplog
	    echo "Culling complete, continuing cycle $idx of "`echo $#regtimes | awk '{print $1-2}'`"..."
	    echo " "
	    goto jumper	    
	endif
#####################
	if ($report) then
	    echo "Recording flagging information"
	    if ("$ipol" =~ *"xx"*) then
		uvplt vis=$file device=/null select='pol(xx),-auto' | tr '-' ' ' | grep Baseline | awk '{print $2,$3,$5,$2*1000+$3}' | sort -nk4 > $wd/xbasereport
		echo 1000 1000 1000 10001000 >>$wd/xbasereport
		set ridx = 1
		set rvals = (`sed -n {$ridx}p $wd/xbasereport`)
		echo $pointmax >> $wd/xret$cycle
		foreach ant1 ($fullxants)
		    foreach ant2 ($fullxants)
			if ($ant1 >= $ant2) then
			else if ("$ant1 $ant2" == "$rvals[1] $rvals[2]") then
			    echo $rvals[3] $pointmax | awk '{print $1/$2}' >> $wd/xret$cycle
			    @ fullxaret[$ant1]+=$rvals[3] fullxaret[$ant2]+=$rvals[3] fullxapos[$ant1]+=$pointmax fullxapos[$ant2]+=$pointmax
			    @ ridx++
			    set rvals = (`sed -n {$ridx}p $wd/xbasereport`)
			else
			    echo 0 >> $wd/xret$cycle
			    @ fullxapos[$ant1]+=$pointmax fullxapos[$ant2]+=$pointmax
			endif
		    end
		end
		set fullxret = ($fullxret `sed 1d $wd/xret$cycle | awk '{ total += $1} END {print total*pointmax}' pointmax=$pointmax`)
		set fullxpos = ($fullxpos `wc -l $wd/xret$cycle | awk '{print ($1-1)*pointmax}' pointmax=$pointmax`)
		echo "X-pol retention at "`echo $fullxret[$idx] $fullxpos[$idx] | awk '{print int(1000*$1/$2)/10}'`"% for this cycle - "`echo $xants | wc -w | awk '{print fullcount-$1}' fullcount=$#fullxants`" ants (out of $#fullxants) and "`awk '{if ($1 == "0") idx += 1} END {print idx*1}' $wd/xret$cycle`" "`wc -l $wd/xret$cycle | awk '{print "(out of "$1-1")"}'`" baselines were removed."
	    endif
	    if ("$ipol" =~ *"yy"*) then
		uvplt vis=$file device=/null select='pol(yy),-auto' | tr '-' ' ' | grep Baseline | awk '{print $2,$3,$5,$2*1000+$3}' | sort -nk4 > $wd/ybasereport
		echo 1000 1000 1000 10001000 >>$wd/ybasereport
		set ridx = 1
		set rvals = (`sed -n {$ridx}p $wd/ybasereport`)
		echo $pointmax >> $wd/yret$cycle
		foreach ant1 ($fullyants)
		    foreach ant2 ($fullyants)
			if ($ant1 >= $ant2) then
			else if ("$ant1 $ant2" == "$rvals[1] $rvals[2]") then
			    echo $rvals[3] $pointmax | awk '{print $1/$2}' >> $wd/yret$cycle
			    @ fullyaret[$ant1]+=$rvals[3] fullyaret[$ant2]+=$rvals[3] fullyapos[$ant1]+=$pointmax fullyapos[$ant2]+=$pointmax
			    @ ridx++
			    set rvals = (`sed -n {$ridx}p $wd/ybasereport`)
			else
			    echo 0 >> $wd/yret$cycle
			    @ fullyapos[$ant1]+=$pointmax fullyapos[$ant2]+=$pointmax
			endif
		    end
		end
		set fullyret = ($fullyret `sed 1d $wd/yret$cycle | awk '{ total += $1} END {print total*pointmax}' pointmax=$pointmax`)
		set fullypos = ($fullypos `wc -l $wd/yret$cycle | awk '{print ($1-1)*pointmax}' pointmax=$pointmax`)
		echo "Y-pol retention at "`echo $fullyret[$idx] $fullypos[$idx] | awk '{print int(1000*$1/$2)/10}'`"% for this cycle - "`echo $yants | wc -w | awk '{print fullcount-$1}' fullcount=$#fullyants`" ants (out of $#fullyants) and "`awk '{if ($1 == "0") idx += 1} END {print idx*1}' $wd/yret$cycle`" "`wc -l $wd/yret$cycle | awk '{print "(out of "$1-1")"}'`" baselines were removed."
	    endif
	endif
#####################
	if ($polsplit && $sefd && ("$xants" != "" || "$yants" != "")) then
	    echo -n "Beginning SEFD calculation"
	    uvflag vis=$file options=none flagval=u select=auto >& /dev/null
	    uvcal vis=$file options=nocal,nopass,nopol,fxcal out=$wd/sefdcal >& /dev/null
	    uvflag vis=$wd/sefdcal flagval=f select='amp(0,0.0000000000000001)' options=none >& /dev/null #This is here since uvcal is stupid, and this corresponds to a noise level of 80 dB (SNR of 1:10^8)
	    echo -n ", calculating gains tables..."
	    mfcal vis=$wd/sefdcal refant=$refant options=interpolate minants=4 flux=$flux interval=$int >& $wd/checkmfcal
	    if (`grep "time order" $wd/checkmfcal | wc -l`) then
		echo ""
		echo "FATAL ERROR: Data not in time order!"
		goto fail
	    endif
	    echo "$freq $regtimes[$mididx] " > $wd/sefd.$ipol.$regtimes[$mididx]
	    echo " Ant Pol  R-Gain Avg  R-Gain RMS  I-Gain Avg  I-Gain RMS   SEFD (Jy)" >> $wd/sefd.$ipol.$regtimes[$mididx]
	    echo "====================================================================" >> $wd/sefd.$ipol.$regtimes[$mididx]
	    
	    gplist vis=$wd/sefdcal options=all | sed 's/^.\{10\}//g' | grep "Ant" | sort -nk2 | awk '{if (NR == 1 || ant == $2) {ant=$2;n++; re += $5; rs += $5*$5;im += $6;is += $6*$6}; if (ant != $2) {printf "%4s   %1s % .4e % .4e % .4e % .4e % .4e\n",ant,pol,re/n,sqrt((rs-n*(re/n)*(re/n))/n),im/n,sqrt((is-(n*(im/n)*(im/n)))/n),((re*re)+(im*im))/(n^2);ant=$2;n=1;re=$5;rs=$5*$5;im=$6;is=$6*$6}}' pol=`echo $ipol | sed -e 's/xx/x/g' -e 's/yy/y/g'`| awk '{if ($7*1 != 0) print $0}' >> $wd/sefd.$ipol.$regtimes[$mididx]
	    rm -rf $wd/sefdcal
	    echo "done!"
	else if ($sefd && ("$xants" != "" || "$yants" != "")) then
	    echo -n "Beginning SEFD calculation"
	    uvflag vis=$file options=none flagval=u select=auto >& /dev/null
	    if ("$xants" != "") uvcal vis=$file options=nocal,nopass,nopol,fxcal select='pol(xx)' out=$wd/sefdcalx >& /dev/null
	    if ("$yants" != "")uvcal vis=$file options=nocal,nopass,nopol,fxcal select='pol(xx)' out=$wd/sefdcaly >& /dev/null
	    uvflag vis="$wd/sefdcal*" flagval=f select='amp(0,0.0000000000000001)' options=none >& /dev/null #This is here since uvcal is stupid, and this corresponds to a noise level of 80 dB (SNR of 1:10^8)
	    echo -n ", calculating gains tables..."
	    touch $wd/checkmfcalx; touch $wd/checkmfcaly
	    if ("$xants" != "") mfcal vis=$wd/sefdcalx refant=$refant options=interpolate minants=4 flux=$flux interval=$int >& $wd/checkmfcalx
	    if ("$yants" != "") mfcal vis=$wd/sefdcaly refant=$refant options=interpolate minants=4 flux=$flux interval=$int >& $wd/checkmfcaly
	    if (`grep "time order" $wd/checkmfcalx | wc -l` || `grep "time order" $wd/checkmfcaly | wc -l` ) then
		echo ""
		echo "FATAL ERROR: Data not in time order!"
		goto fail
	    endif
	    echo "$freq $regtimes[$mididx] " > $wd/sefd.$ipol.$regtimes[$mididx]
	    echo " Ant Pol  R-Gain Avg  R-Gain RMS  I-Gain Avg  I-Gain RMS   SEFD (Jy)" >> $wd/sefd.$ipol.$regtimes[$mididx]
	    echo "====================================================================" >> $wd/sefd.$ipol.$regtimes[$mididx]
	    if ("$xants" != "") gplist vis=$wd/sefdcalx options=all | sed 's/^.\{10\}//g' | grep "Ant" | sort -nk2 | awk '{if (NR == 1 || ant == $2) {ant=$2;n++; re += $5; rs += $5*$5;im += $6;is += $6*$6}; if (ant != $2) {printf "%4s   %1s % .4e % .4e % .4e % .4e % .4e\n",ant,pol,re/n,sqrt((rs-n*(re/n)*(re/n))/n),im/n,sqrt((is-(n*(im/n)*(im/n)))/n),((re*re)+(im*im))/(n^2);ant=$2;n=1;re=$5;rs=$5*$5;im=$6;is=$6*$6}}' pol=x | awk '{if ($7*1 != 0) print $0}' >> $wd/sefd.$ipol.$regtimes[$mididx]
	    if ("$yants" != "") gplist vis=$wd/sefdcaly options=all | sed 's/^.\{10\}//g' | grep "Ant" | sort -nk2 | awk '{if (NR == 1 || ant == $2) {ant=$2;n++; re += $5; rs += $5*$5;im += $6;is += $6*$6}; if (ant != $2) {printf "%4s   %1s % .4e % .4e % .4e % .4e % .4e\n",ant,pol,re/n,sqrt((rs-n*(re/n)*(re/n))/n),im/n,sqrt((is-(n*(im/n)*(im/n)))/n),((re*re)+(im*im))/(n^2);ant=$2;n=1;re=$5;rs=$5*$5;im=$6;is=$6*$6}}' pol=y | awk '{if ($7*1 != 0) print $0}' >> $wd/sefd.$ipol.$regtimes[$mididx]
	    rm -rf $wd/sefdcalx $wd/sefdcaly
	    echo "done!"	    
	endif
	set limtotal
    	# If on the last cycle, then use uvaver to pull together all of the datasets. Otherwise, repeat with the next time cycle.
	if ($postidx >= $#regtimes) then
	    rm -rf $wd/tempcal$ipol
	    uvaver vis="$wd/tempcali$ipol*" out=$wd/tempcal$ipol options=nocal,nopass,nopol > /dev/null
	    echo "Moving to final cycle!"
	else
	    set cycletimes = (`date +%s.%N | awk '{print int(($1-date1)/60),int(($1-date1)%60)}' date1=$cycletime` 0 0)
	    echo "Cycle complete! Calibration cycle took $cycletimes[1] minute(s) and $cycletimes[2] second(s). Moving on..."    
	endif
	echo " "
    end

    #Final cycle for a pol, use autoref to find the best ref antenna for the whole dataset
    poljumper:
    if ($autoref) then
	uvplt vis=$wd/tempcal$ipol options=2pass select='-auto' axis=ti,pha device=/null | grep "Baseline" | awk '{print $2,$3,$5}' | tr -d '-' > $wd/refantstat
	set antstat = 0
	set refant = 0
	foreach ant (`awk '{printf "%s\n%s\n",$1,$2}' $wd/refantstat | sort -nu`)
	    if ($antstat < `awk '{if ($1 == ant || $2 == ant) sum += $3} END {print sum}' ant=$ant $wd/refantstat`) then
		set antstat = `awk '{if ($1 == ant || $2 == ant) sum += $3} END {print sum}' ant=$ant $wd/refantstat`
		set refant = $ant
	    endif
	end
	echo -n "Refant $refant choosen! "
    endif
    if ($ipol == "xx") set xrefant = "$refant"
    if ($ipol == "yy") set yrefant = "$refant"
    # The final solution check, start with a dash of MFCAL
    set checkamp = 100
    mfcal vis=$wd/tempcal$ipol refant=$refant options=interpolate minants=4 flux=$flux interval=$int >& $wd/checkmfcal
    if (`grep "time order" $wd/checkmfcal | wc -l`) then
	echo ""
	echo "FATAL ERROR: Data not in time order!"
	goto fail
    endif
    # Add a pinch of UVAVER to apply the gains
    uvaver vis=$wd/tempcal$ipol out=$wd/tempcal2 options=relax >& /dev/null
    #Display if neccessary
    if ($display) uvplt vis=$wd/tempcal2 select='-auto' $device options=2pass,nobase,equal,source axis=re,im >& /dev/null
    # Error capture if no records to be flagged
    touch $wd/amplog
    # Get listing of all amps from datasset
    uvlist vis=$wd/tempcal2 select='-auto' recnum=0 line=chan,1,1,$nchan | sed 1,9d | awk '{if ($1*1 ==0); else if ($8*1 != 0 || $9*1 != 0) print $1,$9,(($8*cos(pi*$9/180)-flux)^2+($8*sin(pi*$9/180))^2)^.5}' flux=$calflux pi=3.141592 | sort -nk3 > $wd/ampinfo
    # Gather some basic information about the data limits
    set linecheck = `wc -l $wd/ampinfo | awk '{print int($1*.95)}'`
    set linelim = `wc -l $wd/ampinfo | awk '{print int($1*exp(-1*siglim))}' siglim=$siglim`
    set linemax = `wc -l $wd/ampinfo | awk '{print 1+int($1*.05)}'`
    set intcheck = `tail -n 1 $wd/ampinfo | awk '{print $3}'`
    # Enforce a limit on the minmum number of flags needed to pass to the next stage
    if ($linelim < 10) set linelim = 10
    if ($linemax < 10) set linemax = 10
    echo "Minimum flagging line is $linelim, maximum is $linemax."
    if (`sed -n {$linecheck}p $wd/ampinfo | awk '{if ($3*1 < (addflux+sysflux)) print "go"; else if ($3*1 < intcheck/10 && (addflux+sysflux) < intcheck/10) print "go"}' addflux=$addflux sysflux=$sysflux intcheck=$intcheck` == "go") then
	if (`echo $intcheck $addflux $sysflux | awk '{if ($1/10 > ($2+$3)) print "go"}'` == "go") then
	    awk '{if ($3 > (intcheck/10)) print $1}' intcheck=$intcheck $wd/ampinfo | sort -nk1 > $wd/amplog
	    set checkamp = `echo $intcheck | awk '{print $1/10}'`
	else
	    awk '{if ($3 > (addflux+sysflux)) print $1}' addflux=$addflux sysflux=$sysflux $wd/ampinfo | sort -nk1 > $wd/amplog
	    set checkamp = `echo $addflux $sysflux | awk '{print $1+$2}'`
	endif
    else
	sed 1,{$linecheck}d $wd/ampinfo | awk '{print $1}' | sort -nk1 > $wd/amplog
        set checkamp =  `sed -n {$linecheck}p $wd/ampinfo | awk '{print $3}'`
    endif
    echo "Flagging commencing, outer-limit for flux noise is $checkamp Jy for integrated spectra."
    set llim=1
    set ulim=50
    set lim = `wc -w $wd/amplog | awk '{print $1}'`
    uvflag vis=$wd/tempcal2 flagval=f select='amp(0,0.0000000000000001)' options=none >& /dev/null #This is here since uvcal is stupid, and this corresponds to a noise level of 80 dBS (SNR of 1:10^8)    
    echo -n "$lim integrated records to flag..."
    while ($llim <= $lim)
        set flags = `sed -n {$llim},{$ulim}p $wd/amplog | awk '{printf "%s","vis("$1"),"}' ulim=$ulim`
        uvflag vis=$wd/tempcal2 flagval=f options=none select=$flags >& /dev/null
        set llim = `echo $llim | awk '{print $1+50}'`
        set ulim = `echo $ulim | awk '{print $1+50}'`
        echo -n "."
    end
    echo " "
    # UVAFLAG is used here since we created a temp dataset to apply the gains
    uvaflag vis=$wd/tempcal$ipol tvis=$wd/tempcal2 >& /dev/null
    rm -rf $wd/tempcal2 $wd/amplog $wd/ampinfo
    if ((`echo $linelim $lim | awk '{if ($1 < $2) print "go"}'` == "go" || `echo $intcheck $addflux $sysflux | awk '{if ($1/10 > ($2+$3)) print "go"}'` == "go") && $linelim != $linemax) then
	echo " "
        echo "Flagging complete, continuing final cycle for $ipol data..."
	goto poljumper
    endif
    # Use AUTOMAP's onboard RFI excision to attempt to nuke any more channels that have RFI in it.
    if ($wrath && $wrathcycle) then
        echo "Beginning WRATH flagging"
        newautomap.csh vis=$wd/tempcal$ipol options=noflag,nocal,wrath,junk >& $wd/wrathlog
        set rfilist = (`grep WRATHCHAN $wd/wrathlog`)
        shift rfilist
        echo -n "$#rfilist polluted image planes found, beginning removal."
        set rfilist = `echo $rfilist | tr ' ' ','`
        set rfiflags = (`newoptfchan.csh chanlist=$rfilist`)
        foreach rfiline ($rfiflags)
	    echo -n "."
	    uvflag vis=$wd/tempcal$ipol flagval=f options=none $rfiline > /dev/null
	end
        echo "."
        echo "WRATH cleaning complete!"
	set wrathcycle = 0
    endif
    
    # Horray again for MFCAL
    if ("$smooth" == "") mfcal vis=$wd/tempcal$ipol refant=$refant options=interpolate minants=4 flux=$flux interval=$int >& $wd/checkmfcal
    if (`grep "time order" $wd/checkmfcal | wc -l`) then
	echo ""
	echo "FATAL ERROR: Data not in time order!"
	goto fail
    endif
    if ("$smooth" != "") smamfcal vis=$wd/tempcal$ipol refant=$refant options=interpolate,msmooth minants=4 flux=$flux interval=$int $smooth weight=-1 >& /dev/null
    if ($polsplit && $sefd) then
        echo -n "Beginning SEFD calculation"
	uvflag vis=$wd/tempcal$ipol options=none flagval=u select=auto >& /dev/null
	uvcal vis=$wd/tempcal$ipol options=nocal,nopass,nopol,fxcal out=$wd/sefdcal >& /dev/null
	uvflag vis=$wd/sefdcal flagval=f select='amp(0,0.0000000000000001)' options=none >& /dev/null #This is here since uvcal is stupid, and this corresponds to a noise level of 80 dBS (SNR of 1:10^8)
	echo -n ", calculating gains tables..."
	mfcal vis=$wd/sefdcal refant=$refant options=interpolate minants=4 flux=$flux interval=$int >& $wd/checkmfcal
	if (`grep "time order" $wd/checkmfcal | wc -l`) then
	    echo ""
	    echo "FATAL ERROR: Data not in time order!"
	    goto fail
	endif
	echo "$freq" > $wd/sefd.$ipol
	echo " Ant Pol  R-Gain Avg  R-Gain RMS  I-Gain Avg  I-Gain RMS   SEFD (Jy)" > $wd/sefd.$ipol
	echo "====================================================================" >> $wd/sefd.$ipol

	gplist vis=$wd/sefdcal options=all | sed 's/^.\{10\}//g' | grep "Ant" | sort -nk2 | awk '{if (NR == 1 || ant == $2) {ant=$2;n++; re += $5; rs += $5*$5;im += $6;is += $6*$6}; if (ant != $2) {printf "%4s   %1s % .4e % .4e % .4e % .4e % .4e\n",ant,pol,re/n,sqrt((rs-n*(re/n)*(re/n))/n),im/n,sqrt((is-(n*(im/n)*(im/n)))/n),((re*re)+(im*im))/(n^2);ant=$2;n=1;re=$5;rs=$5*$5;im=$6;is=$6*$6}}' pol=`echo $ipol | sed -e 's/xx/x/g' -e 's/yy/y/g'` | awk '{if ($7*1 != 0) print $0}' >> $wd/sefd.$ipol

	if ($ipol == xx) then
	    foreach antcheck ($fullxants)
		if !(`awk '{if ($1 == antcheck) idx += 1} END {print idx*1}' antcheck=$antcheck $wd/sefd.$ipol`) set nogainants = ($nogainants {$antcheck}X)
	    end
	else if ($ipol == yy) then
	    foreach antcheck ($fullyants)
		if !(`awk '{if ($1 == antcheck) idx += 1} END {print idx*1}' antcheck=$antcheck $wd/sefd.$ipol`) set nogainants = ($nogainants {$antcheck}Y)
	    end
	endif

	rm -rf $wd/sefdcal
	echo "done!"
    else if ($sefd) then
        echo -n "Beginning SEFD calculation"
	uvflag vis=$wd/tempcal$ipol options=none flagval=u select=auto >& /dev/null
	uvcal vis=$wd/tempcal$ipol options=nocal,nopass,nopol,fxcal select='pol(xx)' out=$wd/sefdcalx >& /dev/null
	uvcal vis=$wd/tempcal$ipol options=nocal,nopass,nopol,fxcal select='pol(xx)' out=$wd/sefdcaly >& /dev/null

	uvflag vis=$wd/sefdcalx,$wd/sefdcaly flagval=f select='amp(0,0.0000000000000001)' options=none >& /dev/null #This is here since uvcal is stupid, and this corresponds to a noise level of 80 dBS (SNR of 1:10^8)
	echo -n ", calculating gains tables..."
	mfcal vis=$wd/sefdcalx refant=$refant options=interpolate minants=4 flux=$flux interval=$int >& $wd/checkmfcalx
	mfcal vis=$wd/sefdcaly refant=$refant options=interpolate minants=4 flux=$flux interval=$int >& $wd/checkmfcaly
	if (`grep "time order" $wd/checkmfcalx | wc -l` || `grep "time order" $wd/checkmfcaly | wc -l`) then
	    echo ""
	    echo "FATAL ERROR: Data not in time order!"
	    goto fail
	endif
	echo "$freq" > $wd/sefd
	echo " Ant Pol  R-Gain Avg  R-Gain RMS  I-Gain Avg  I-Gain RMS   SEFD (Jy)" > $wd/sefd
	echo "====================================================================" >> $wd/sefd
	gplist vis=$wd/sefdcalx options=all | sed 's/^.\{10\}//g' | grep "Ant" | sort -nk2 | awk '{if (NR == 1 || ant == $2) {ant=$2;n++; re += $5; rs += $5*$5;im += $6;is += $6*$6}; if (ant != $2) {printf "%4s   %1s % .4e % .4e % .4e % .4e % .4e\n",ant,pol,re/n,sqrt((rs-n*(re/n)*(re/n))/n),im/n,sqrt((is-(n*(im/n)*(im/n)))/n),((re*re)+(im*im))/(n^2);ant=$2;n=1;re=$5;rs=$5*$5;im=$6;is=$6*$6}}' pol=x | awk '{if ($7*1 != 0) print $0}' >> $wd/sefd
	gplist vis=$wd/sefdcaly options=all | sed 's/^.\{10\}//g' | grep "Ant" | sort -nk2 | awk '{if (NR == 1 || ant == $2) {ant=$2;n++; re += $5; rs += $5*$5;im += $6;is += $6*$6}; if (ant != $2) {printf "%4s   %1s % .4e % .4e % .4e % .4e % .4e\n",ant,pol,re/n,sqrt((rs-n*(re/n)*(re/n))/n),im/n,sqrt((is-(n*(im/n)*(im/n)))/n),((re*re)+(im*im))/(n^2);ant=$2;n=1;re=$5;rs=$5*$5;im=$6;is=$6*$6}}' pol=y | awk '{if ($7*1 != 0) print $0}' >> $wd/sefd
	foreach antcheck ($fullxants)
	    if !(`awk '{if ($1 == antcheck) idx += 1} END {print idx*1}' antcheck=$antcheck $wd/sefd`) set nogainants = ($nogainants {$antcheck}X)
	end
	foreach antcheck ($fullyants)
	    if !(`awk '{if ($1 == antcheck) idx += 1} END {print idx*1}' antcheck=$antcheck $wd/sefd`) set nogainants = ($nogainants {$antcheck}Y)
	end
	rm -rf $wd/sefdcalx $wd/sefdcaly
	echo "done!"
    endif

    echo "Final cycle complete!"
    echo ""
end

# Pull together all polarizations
uvaver vis=`echo " $pollist" | sed -e 's/ /,'$wd'\/tempcal/g' -e 's/,//'` options=relax out=$wd/tempcalfin >& /dev/null

# Put the results of the mapping process into a specified directory
set outfile = "cal-$source-"`echo $freq | awk '{print int($1*1000)}'`"-maps"

set idx = 0
while (-e $outfile)
    @ idx++
    set outfile = "cal-$source-"`echo $freq | awk '{print int($1*1000)}'`"-maps.$idx"
end

if (-e $wd/sefd.xx && -e $wd/sefd.yy) then
    cat $wd/sefd.xx > $wd/sefd
    sed 1,2d $wd/sefd.yy >> $wd/sefd
else if (-e $wd/sefd.xx) then
    cp -rf $wd/sefd.xx $wd/sefd
else if (-e $wd/sefd.yy) then
    cp -rf $wd/sefd.yy $wd/sefd
endif

if (-e $wd/sefd) cp -rf $wd/sefd $wd/tempcalfin/sefd

#################################################################    
# Once the calibration cycle has completed, the program uses
# the automapper routine to produce an image,  make any
# neccessary fine tuning (due to imperfections in the cal model)
# and give some information about how good the calibration/
# imaging processes went (via the imaging report). After this
# begins the long process of merging all of the gains info
# together, and applying them to the neccessary source files.
# This is a slightly convoluted process, since gains tables
# have to be transfered via GPCOPY. So there is some shuffling
# around of files that are applicable to the dataset as a whole
# (named "gains" and "bandpass"), files only applicable to
# x-pols (named "gains.xx" and "bandpass.xx") and files only
# applicable to y-pols (named "gains.yy" and "bandpass.yy").
# The automaping software is aware of this fact, and will apply
# pol-specfic information appropriately, but will need to be
# done manually by users not using that software.
#################################################################

newautomap.csh vis=$wd/tempcalfin mode=auto outdir=$outfile $mapopt $olay $device `if ($debug) echo "options=debug"`

if !(-e $outfile/imgrpt) then
    echo "FATAL ERROR: Automapping stage has failed!"
    goto fail
endif

if (-e $wd/sefd) cp $wd/sefd $outfile/sefd

echo "Copying gains back to original file ($vis)"

if ($polsplit && $#pollist > 1) then # If pols were split and more than one pol exists
    foreach dp (xx yy)
	if (-e $outfile/$source.1.$dp/gains) then # If the automapping software had "tweaks" for the gains solution, apply those tweaks
	    puthd in=$outfile/$source.1.$dp/interval value=.5 > /dev/null
	    gpcopy vis=$outfile/$source.1.$dp out=$vis > /dev/null
	    if (-e $vis/gains) mv $vis/gains $vis/gains.{$dp}p
	    if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.{$dp}p
	    if (-e $vis/header) cp $vis/header $vis/header.{$dp}p
	endif
	puthd in=$wd/tempcal$dp/interval value=.5 > /dev/null 
	gpcopy vis=$wd/tempcal$dp out=$vis > /dev/null
    # Move pol-specific gains "out of the way" so that information isnb't overwritten by gpcopy
	if (-e $vis/gains) mv $vis/gains $vis/gains.$dp 
	if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.$dp
	if (-e $vis/header) cp $vis/header $vis/header.$dp
    end
else if ($polsplit) then # if polspilt was used, but only one pol was found
    if (-e $outfile/$source.1.$pollist[1]/gains) then # If the automapping software had "tweaks" for a single pol gains solution, apply those tweaks
	puthd in=$outfile/$source.1.$pollist[1]/interval value=.5 > /dev/null
	gpcopy vis=$outfile/$source.1.$pollist[1] out=$vis > /dev/null
	if (-e $vis/gains) mv $vis/gains $vis/gains.{$pollist[1]}p 
	if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.{$pollist[1]}p
	if (-e $vis/header) cp $vis/header $vis/header.{$pollist[1]}p
    endif
    puthd in=$wd/tempcal$pollist[1]/interval value=.5 > /dev/null
    gpcopy vis=$wd/tempcal$pollist[1] out=$vis > /dev/null
    # Move pol-specific gains "out of the way" so that information isn't overwritten by gpcopy
    if (-e $vis/gains) mv $vis/gains $vis/gains.$pollist[1]
    if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.$pollist[1]
    if (-e $vis/header) cp $vis/header $vis/header.$pollist[1]
else
    foreach dp (xx yy)
	if (-e $outfile/$source.1.$dp/gains) then # If the automapping software had "tweaks" for the gains solution, apply those tweaks
	    puthd in=$outfile/$source.1.$dp/interval value=.5 > /dev/null
	    gpcopy vis=$outfile/$source.1.$dp out=$vis > /dev/null
	    # Move pol-specific gains "out of the way" so that information isn't overwritten by gpcopy
	    mv $vis/gains $vis/gains.{$dp}p
	endif
    end
    # Copy over any "general" gains solutions (relating to multiple pols)
    puthd in=$wd/tempcal$pollist[1]/interval value=.5 > /dev/null
    gpcopy vis=$wd/tempcal$pollist[1] out=$vis > /dev/null
endif

# Repeat the gains copying process for each source file, first copying any pol-specific solutions first, then copying "general" (multi-pol) solutions
foreach tfile ($tvis)
    echo "Copying gains to $tfile"
    foreach dp (xx yy)
	if (-e $wd/tempcal$dp/gains || -e $wd/tempcal$dp/bandpass) then
	    gpcopy vis=$wd/tempcal$dp out=$tfile > /dev/null
	    if (-e $tfile/gains) mv $tfile/gains $tfile/gains.$dp
	    if (-e $tfile/bandpass) mv $tfile/bandpass $tfile/bandpass.$dp
	    cp $tfile/header $tfile/header.$dp
	endif
	if (-e $vis/gains.{$dp}p || -e $vis/bandpass.{$dp}p) then
	    gpcopy vis=$outfile/$source.1.$dp out=$tfile > /dev/null
	    if (-e $tfile/bandpass) mv $tfile/bandpass $tfile/bandpass.{$dp}p
	    if (-e $tfile/gains) mv $tfile/gains $tfile/gains.{$dp}p
	    cp $tfile/header $tfile/header.{$dp}p
	endif
    end
    if (-e $vis/gains) then
	gpcopy vis=$vis out=$tfile > /dev/null
    endif
end

# If the outsource switch was used, apply the flags from the source template files
if ($outsource && "$tvis[1]" != "") then
    set fileidx = 0
    foreach tfile ($tvis)
	@ fileidx++
	set filemark = `echo $fileidx | awk '{print $1+100000}' | sed 's/1//'`
	echo "Applying flags for $tfile..."
        uvaver vis="$wd/tvis$filemark*" out=$wd/tvis$filemark options=relax,nocal,nopass,nopol >& /dev/null
	uvaflag vis=$tfile tvis=$wd/tvis$filemark > /dev/null
    end
endif

foreach file ($vis $tvis)
    if (-e $wd/sefd) cp $wd/sefd $file/sefd
    if (-e $wd/sefd) cp $wd/sefd $file/phoenix/sefd.CAL$dmark
    if (-e $file/gains) cp $file/gains $file/phoenix/gains.CAL$dmark
    if (-e $file/bandpass) cp $file/bandpass $file/phoenix/bandpass.CAL$dmark
    if (-e $file/gains.xx) cp $file/gains.xx $file/phoenix/gains.xx.CAL$dmark
    if (-e $file/bandpass.xx) cp $file/bandpass.xx $file/phoenix/bandpass.xx.CAL$dmark
    if (-e $file/gains.xxp) cp $file/gains.xxp $file/phoenix/gains.xxp.CAL$dmark
    if (-e $file/bandpass.xxp) cp $file/bandpass.xxp $file/phoenix/bandpass.xxp.CAL$dmark
    if (-e $file/gains.yy) cp $file/gains.yy $file/phoenix/gains.yy.CAL$dmark
    if (-e $file/bandpass.yy) cp $file/bandpass.yy $file/phoenix/bandpass.yy.CAL$dmark
    if (-e $file/gains.yyp) cp $file/gains.yyp $file/phoenix/gains.yyp.CAL$dmark
    if (-e $file/bandpass.yyp) cp $file/bandpass.yyp $file/phoenix/bandpass.yyp.CAL$dmark
    if (-e $file/header) cp $file/header $file/phoenix/header.CAL$dmark
    if (-e $file/header.xx) cp $file/header.xx $file/phoenix/header.xx.CAL$dmark
    if (-e $file/header.xxp) cp $file/header.xxp $file/phoenix/header.xxp.CAL$dmark
    if (-e $file/header.yy) cp $file/header.yy $file/phoenix/header.yy.CAL$dmark
    if (-e $file/header.yyp) cp $file/header.yyp $file/phoenix/header.yyp.CAL$dmark
end

foreach file ($tvis)
    if (-e $file/flags) cp $file/flags $file/phoenix/flags.CAL$dmark
end

if ($report) then
    set preidx = 1; set idx = 2; set postidx = 3
    while ($idx < $#regtimes)
	set cycle = `echo $preidx | awk '{print 1000+$1}' | sed 's/1//'`
	echo $regtimes[$preidx] >> $wd/ret$cycle
	echo $regtimes[$idx] >> $wd/ret$cycle
	echo $regtimes[$postidx] >> $wd/ret$cycle
	if (-e $wd/xret$cycle && -e $wd/yret$cycle) then
	    echo `head -n 1 $wd/xret$cycle` `head -n 1 $wd/yret$cycle ` | awk '{if ($1*1 > $2*1) print $1*1; else print $2*1}' >> $wd/ret$cycle
	    awk '{if (NR ==1) sca = $1; else print $1*sca}' $wd/xret$cycle >> $wd/ret$cycle
	    awk '{if (NR ==1) sca = $1; else print $1*sca}' $wd/yret$cycle >> $wd/ret$cycle
	else if (-e $wd/xret$cycle) then
	    awk '{if (NR == 1) {sca = $1; print sca} else print $1*sca}' $wd/xret$cycle >> $wd/ret$cycle
	else if (-e $wd/yret$cycle) then
	    awk '{if (NR == 1) {sca = $1; print sca} else print $1*sca}' $wd/yret$cycle >> $wd/ret$cycle
	endif
	@ preidx++ idx++ postidx++
    end
endif

echo "#" >> $wd/ret000
echo "#" >> $wd/ret000
echo "#" >> $wd/ret000
echo "#" >> $wd/ret000

foreach ant1 ($fullxants)
    foreach ant2 ($fullxants)
	if ($ant1 < $ant2) then
	    echo {$ant1}"-"{$ant2}"-XX"  >> $wd/ret000
	endif
    end
end
foreach ant1 ($fullyants)
    foreach ant2 ($fullyants)
	if ($ant1 < $ant2) then
	    echo {$ant1}"-"{$ant2}"-YY"  >> $wd/ret000
	endif
    end
end

paste $wd/ret* > $wd/retmap
cp $wd/retmap $vis/retmap
cp $wd/retmap $vis/phoenix/retmap.CAL$dmark
set orc = `echo 500 $freq | awk '{print int($1*1.43/$2)}'`
set tnoise = `imfit in=$outfile/$source.cm region=relcen,arcsec,"box(-$orc,-$orc,$orc,$orc)" object=point | grep residual | awk '{print $9*1000}'`
set noise = `imstat in=$outfile/$source.rs | awk '{if (check == 1) print $0; else if ($1 == "Total") check = 1}' | tr '*' ' ' | sed 's/\([0-9][0-9]\)-/\1 -/g' | awk '{print $3*1000}'`
set maxmin = (`imstat in=$outfile/$source.cm | awk '{if (check == 1) print $0; else if ($1 == "Total") check = 1}' | tr '*' ' ' | sed 's/\([0-9][0-9]\)-/\1 -/g' | awk '{print $4*1000,$5*1000}'`)
set derflux = (`imfit in=$outfile/$source.cm region=relcen,arcsec,"box(-$orc,-$orc,$orc,$orc)" object=point | grep Peak | awk '{print $3,$5}'`)
set derpos = (`imfit in=$outfile/$source.cm region=relcen,arcsec,"box(-$orc,-$orc,$orc,$orc)" object=point | grep Offset | awk '{print $4,$5}'`)
set derpos = ($derpos `imfit in=$outfile/$source.cm region=relcen,arcsec,"box(-$orc,-$orc,$orc,$orc)" object=point | grep errors | awk '{print $4,$5}'`)

report:
echo "" 
echo "CALIBRATION REPORT" | tee -ia $wd/calrpt
echo "================================================================" | tee -ia $wd/calrpt
echo "Calibration of $cal was successfully completed." | tee -ia $wd/calrpt
echo "Image noise is $noise mJy, with a dynamic range of "`echo $maxmin[1] $noise | awk '{print $1/$2}'` | tee -ia $wd/calrpt
echo "(theoretical noise limit is $tnoise mJy) ." | tee -ia $wd/calrpt
echo "Derived flux is $derflux[1] +/- $derflux[2] Jy (Provided value was $calflux)" | tee -ia $wd/calrpt
echo "Positional offsets are "$derpos[1]","$derpos[2]" +/- "$derpos[3]","$derpos[4]" arcsec." | tee -ia $wd/calrpt
echo "(flux was $flux, addflux was $addflux, sysflux was $sysflux, plim was $plim)" | tee -ia $wd/calrpt
if ("$pollist" == "xxyy" || "$xrefant" == "$yrefant") then
    echo "Antenna $refant is the reference antenna for both X and Y pols." | tee -ia $wd/calrpt
else
    if ("$xrefant" != "") echo "Antenna $xrefant is the reference antenna for X-pol." | tee -ia $wd/calrpt
    if ("$yrefant" != "") echo "Antenna $yrefant is the reference antenna for Y-pol." | tee -ia $wd/calrpt
endif

echo "Data for $#fullxants x-pol and $#fullyants y-pol inputs were processed"  | tee -ia $wd/calrpt

if ($sefd) then
    if ("$nogainants" == "") then
	echo "All antennas have gains solutions." | tee -ia $wd/calrpt
    else if ($#nogainants == 1) then
	echo "Antenna $nogainants has no gains solution." | tee -ia $wd/calrpt
    else
	echo "Antennas "`echo $nogainants | tr ' ' ','`" have no gains solutions." | tee -ia $wd/calrpt
    endif
    
endif

set badants
if !($sefd) then
    set idx = 1
    while ($idx <= $nants)
	if ($fullxaret[$idx] == 0 && $fullxapos[$idx] != 0) set badants = ($badants {$idx}X)
	if ($fullyaret[$idx] == 0 && $fullyapos[$idx] != 0) set badants = ($badants {$idx}Y)
	@ idx++
    end
    if ("$badants" == "") then
	echo "No antennas were entirely flagged." | tee -ia $wd/calrpt
    else if ($#badants == 1) then
	echo "Antenna $badants was entirely flagged." | tee -ia $wd/calrpt
    else
	echo "Antennas "`echo $badants | tr ' ' ','`" were entirely flagged" | tee -ia $wd/calrpt
    endif
endif

echo "" | tee -ia $wd/calrpt
echo "DATA RETENTION RATES:" | tee -ia $wd/calrpt
echo "+++++++++++++++++++++++++++++++++" | tee -ia $wd/calrpt
set totalret; set totalpos; set totalxret; set totalxpos; set totalyret; set totalypos
foreach tick ($fullxret)
    @ totalret+=$tick totalxret+=$tick
end
foreach tick ($fullyret)
    @ totalret+=$tick totalyret+=$tick
end
foreach tick ($fullxpos)
    @ totalpos+=$tick totalxpos+=$tick
end
foreach tick ($fullypos)
    @ totalpos+=$tick totalypos+=$tick
end
echo "All polarizations: "`echo $totalret $totalpos | awk '{print .1*int(1000*$1/$2)"% ("$1" of "$2" datapoints)"}'` | tee -ia $wd/calrpt
echo "   X-Pol: "`echo $totalxret $totalxpos | awk '{print .1*int(1000*$1/$2)"% ("$1" of "$2" datapoints)"}'` | tee -ia $wd/calrpt
echo "   Y-Pol: "`echo $totalyret $totalypos | awk '{print .1*int(1000*$1/$2)"% ("$1" of "$2" datapoints)"}'` | tee -ia $wd/calrpt
echo ""

set idx = 1
while ($idx <= $#fullxapos)
    if ($fullxapos[$idx] == "0") then
	echo "Ant "{$idx}"X -- N/A                 " >> $wd/xfinalret
    else
	echo "Ant "{$idx}"X -- "`echo $fullxaret[$idx] $fullxapos[$idx] | awk '{print .1*int(1000*$1/$2)"% ("$1" of "$2")"}'` >> $wd/xfinalret
    endif
    if ($fullyapos[$idx] == "0") then
	echo "Ant "{$idx}"Y -- N/A                 " >> $wd/yfinalret
    else
	echo "Ant "{$idx}"Y -- "`echo $fullyaret[$idx] $fullyapos[$idx] | awk '{print .1*int(1000*$1/$2)"% ("$1" of "$2")"}'` >> $wd/yfinalret
    endif
    @ idx++
end

paste $wd/xfinalret $wd/yfinalret | tee -ia $wd/calrpt

echo ""

set idx = 1
set times = (`sed -n 2p $wd/retmap`); shift times

while ($idx <= $#times)
    if ($idx != 1) echo "----------" | tee -ia $wd/calrpt
    echo "Cycle "`echo $idx | awk '{print $1+1000}' | sed 's/1//'`" (timestamp $times[$idx])" | tee -ia $wd/calrpt
    if ($idx <= $#fullxret) echo -n "  X-Pol: "`echo $fullxret[$idx] $fullxpos[$idx] | awk '{print .1*int(1000*$1/$2)"% ("$1" of "$2" datapoints)"}'` | tee -ia $wd/calrpt

    if ($idx <= $#fullyret) echo -n "  Y-Pol: "`echo $fullyret[$idx] $fullypos[$idx] | awk '{print .1*int(1000*$1/$2)"% ("$1" of "$2" datapoints)"}'` | tee -ia $wd/calrpt
    if ($idx > $#fullxret && $idx > $#fullyret) echo -n "    NO DATA" | tee -ia $wd/calrpt
    echo "" | tee -ia $wd/calrpt
    @ idx++
end
echo "+++++++++++++++++++++++++++++++++" | tee -ia $wd/calrpt
cp $wd/calrpt $outfile/calrpt
echo ""

copymode:

if ($copymode) then
    if !(-e $vis/retmap) then
	echo "FATAL ERROR: This calibrator dataset has not been processed with CALCAL yet!"
	goto fail
    endif
    if ("$tvis" == "") then
	echo "FATAL ERROR: No tvis files provided"
	goto fail
    endif
    foreach file ($tvis)
	if !(-e $file/phoenix) mkdir -p $file/phoenix
	if (! -e $file/phoenix/flags.o && -e $file/flags) cp $file/flags $file/phoenix/flags.o
	if (! -e $file/phoenix/gains.o && -e $file/flags) cp $file/flags $file/phoenix/gains.o
	if (! -e $file/phoenix/bandpass.o && -e $file/bandpass) cp $file/bandpass $file/phoenix/bandpass.o
	if !(-e $file/phoenix/header.o) cp $file/header $file/phoenix/header.o
	echo "CALCAL $dmark" >> $file/phoenix/history
    end
    foreach file ($tvis)
	echo -n "Copying gains solution to $file..."
	foreach pol (xx yy xxp yyp)
	    if (-e $vis/gains.$pol || -e $vis/bandpass.$pol) then
		if (-e $vis/header) cp $vis/header $vis/tempheader
		if (-e $vis/gains) cp $vis/gains $vis/tempgains
		if (-e $vis/bandpass) cp $vis/bandpass $vis/tempbandpass
		if (-e $vis/header.$pol) cp $vis/header.$pol $vis/header
		if (-e $vis/gains.$pol) cp $vis/gains.$pol $vis/gains
		if (-e $vis/bandpass.$pol) cp $vis/bandpass.$pol $vis/bandpass
		gpcopy vis=$vis out=$file > /dev/null
		if (-e $vis/tempheader) mv $vis/tempheader $vis/header
		if (-e $vis/tempgains) mv $vis/tempgains $vis/gains
		if (-e $vis/tempbandpass) mv $vis/tempbandpass $vis/bandpass
		if (-e $file/header) cp $file/header $file/header.$pol
		if (-e $file/gains) mv $file/gains $file/gains.$pol
		if (-e $file/bandpass) mv $file/bandpass $file/bandpass.$pol
	    endif
	end
	echo "done!"
    end
    cp $vis/retmap $wd/retmap
    awk '{if (NR > 4) print $1}' $wd/retmap > $wd/basemap
    echo -n "Beginning flagging sequence..."
    if ($outsource) then
	set fidx = 1
	set stime = `sed -n 1p $wd/retmap | awk '{print $2}'`
	set etime = `sed -n 2p $wd/retmap | awk '{print $2}'`
	foreach file ($tvis)
	    set fcycle = `echo $fidx | awk '{print $1+999}' | sed 's/1//'`
	    uvaver vis=$file out=$wd/tvis{$fcycle}001 select="time($stime,$etime)" options=relax,nocal,nopass,nopol >& /dev/null
	    if !(-e $wd/tvis{$fcycle}001/visdata) rm -rf wd/tvis{$fcycle}001
	    @ fidx++
	end
    endif
    set preidx = 1
    set idx = 2
    if ($copymode == 2) then
	set idx = `sed -n 1p $wd/retmap | wc -w`
	set preidx = `echo $idx | awk '{print $1-1}'`
    endif
    while ($idx <= `sed -n 1p $wd/retmap | wc -w`)
	set ptime = (`sed -n 1p $wd/retmap`)
	set ptime = $ptime[$idx]
	set stime = (`sed -n 2p $wd/retmap`)
	set stime = $stime[$idx]
	set etime = (`sed -n 3p $wd/retmap`)
	set etime = $etime[$idx]
	set pointmax = (`sed -n 4p $wd/retmap`)
	set pointmax = $pointmax[$idx]
        echo "awk '{if (NR > 4) print "'$1,$'$idx"/pointmax}' pointmax=$pointmax $wd/retmap" > $wd/source.flag
	set precycle = `echo $idx | awk '{print $1+999}' | sed 's/1//'`
        set cycle = `echo $idx | awk '{print $1+1000}' | sed 's/1//'`
        source $wd/source.flag > $wd/ret$cycle
	set badbases = (`awk '{if (retlim > 100*$2) print NR}' retlim=$retlim  $wd/ret$cycle`)
	rm -f $wd/badbaselist
	foreach badbase ($badbases)
	    sed -n {$badbase}p $wd/basemap | tr '-' ' ' | awk '{print "ant("$1")("$2"),pol("$3"),time("ptime","etime")"}' ptime=$ptime etime=$etime >> $wd/badbaselist
	end
	if (-e $wd/badbaselist) then
	    grep -i "xx" $wd/badbaselist > $wd/xflags
	    if !(`wc -l $wd/xflags | awk '{print $1}'`) rm -f $wd/xflags
	    grep -i "yy" $wd/badbaselist > $wd/yflags
	    if !(`wc -l $wd/yflags | awk '{print $1}'`) rm -f $wd/yflags
	    set filelist
	    set fidx = 1
	    foreach file ($tvis)
		set fcycle = `echo $fidx | awk '{print $1+999}' | sed 's/1//'`
		if ($outsource) then
		    uvaver vis=$file out=$wd/tvis$fcycle$cycle options=relax,nocal,nopass,nopol select="time($stime,$etime)" >& /dev/null
		    if !(-e $wd/tvis$fcycle$cycle/visdata) rm -rf $wd/tvis$fcycle$cycle  
		endif
		if ($outsource && -e $wd/tvis$fcycle$cycle) set filelist = ($filelist $wd/tvis$fcycle$cycle)
		if ($outsource && -e $wd/tvis$fcycle$precycle) set filelist = ($filelist $wd/tvis$fcycle$precycle)
		if !($outsource) set filelist = ($filelist $file)
		@ fidx++
	    end
	    foreach file ($filelist)
		if (-e $wd/xflags) uvflag vis=$file select=@$wd/xflags flagval=f options=none > /dev/null
		if (-e $wd/yflags) uvflag vis=$file select=@$wd/xflags flagval=f options=none > /dev/null
		echo -n "."
	    end
	    @ fidx++
	endif
	@ idx++
    end
    if ($outsource) then
	set fidx = 1
	foreach file ($tvis)
	    set fcycle = `echo $fidx | awk '{print $1+999}' | sed 's/1//'`
	    uvaver vis="$wd/tvis$fcycle*" out=$wd/tvis$fcycle options=relax,nocal,nopass,nopol >& /dev/null
	    if (-e $wd/tvis$fcycle/visdata) uvaflag  vis=$file tvis=$wd/tvis$fcycle > /dev/null
	    @ fidx++
	end
    endif
    echo "done!"
endif

finish:
set times = (`date +%s.%N | awk '{print int(($1-date1)/60),int(($1-date1)%60)}' date1=$date1` 0 0)
echo "Calibration cycle took $times[1] minute(s) and $times[2] second(s)."
if !($debug) rm -rf $wd
exit 0 

fail:
echo "Calibration failed! Now exiting..."
if !($debug) rm -rf $wd
exit 1
