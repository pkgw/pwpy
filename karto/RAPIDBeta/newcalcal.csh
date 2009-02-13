#! /usr/bin/tcsh -f
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
echo "    olay=olay options=debug,display,autoref,polsplit,[outsource,"
echo "    insource],sefd)"
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
echo " olay - Overlay file for the autoimaging process. No default."
echo ""
echo ""
echo " device - Device to plot results to (e.g. /xw for x-window)."
echo '    Default is /null.'
echo ""
echo " options=debug,display,autoref,polsplit,outsource,insource,sefd"
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
	else if ($option == "sefd") then
	    set sefd = 1
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

if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.bu
if (-e $vis/gains) mv $vis/gains $vis/gains.bu

foreach tfile ($tvis)
    if (-e $tfile/flags) cp $tfile/flags $tfile/flags.bu
    if (-e $tfile/bandpass) mv $tfile/bandpass $tfile/bandpass.bu
    if (-e $tfile/gains) mv $tfile/gains $tfile/gains.bu
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

set rcount = 0
set iccount
set ibcount
set fbcount
set fccount

set pollist = ("xxyy")

echo -n "Preprocessing data..."

# If the polsplit option is used, split the individual pols into seperate files for processing.

if ($polsplit) then
    set pollist = ("xx" "yy")
    uvaver vis=$vis select='window(1),pol(xx)' out=$wd/tempcalxx options=relax,nocal,nopass,nopol >& /dev/null
    echo -n "."
    uvaver vis=$vis select='window(1),pol(yy)' out=$wd/tempcalyy options=relax,nocal,nopass,nopol >& /dev/null
    echo -n "."
else
    uvaver vis=$vis select='window(1),pol(xx,yy)' out=$wd/tempcalxxyy options=relax,nocal,nopass,nopol >& /dev/null
    echo -n "."
endif
echo ""
# Perform some error checking to make sure that "blank" datasets are created

if !(-e $wd/tempcalxxyy || -e $wd/tempcalxx || -e $wd/tempcalyy) then
    echo "FATAL ERROR: No visibilities exist!"
    goto fail
else if (! -e $wd/tempcalxx/visdata && -e $wd/tempcalyy/visdata) then
    set pollist = ("yy")
    echo "No x-pol data found, continuing..."
else if (! -e $wd/tempcalyy/visdata && -e $wd/tempcalxx/visdata) then
    set pollist = ("xx")
    echo "No y-pol data found, continuing..."
endif

# Below is some old code that needs to be rewritten for reporting.

#uvplt vis=$wd/tempcal select='window(1),pol(xx,yy),-auto' options=2pass,nobase device=/null >& $wd/tempcount
echo 1 > $wd/tempcount
#set count = `grep "visibilities from all files" $wd/tempcount | awk '{print $2}'`
set count = 0
set rcount = `echo $rcount $count | awk '{print $1+$2}'`
set iccount = ($iccount $count)

#set bcount = `uvplt vis=$wd/tempcal options=2pass select=-auto device=/null | grep Baseline | wc -l`
set bcount = 0
set ibcount = ($ibcount $bcount)
#uvplt vis=$wd/tempcal select=-auto select='pol(xx)' device=/null options=2pass | grep Baseline | tr "-" " " | awk '{print " "$2"X-"$3"X",$5}' > $wd/ibaselist
#uvplt vis=$wd/tempcal select=-auto select='pol(yy)' device=/null options=2pass | grep Baseline | tr "-" " " | awk '{print " "$2"Y-"$3"Y",$5}' >> $wd/ibaselist
echo "" > $wd/ibaselist
cat $wd/ibaselist | tr "-" " "| awk '{printf "%s\n%s\n",$1,$2}' | sort -nu > $wd/antlist

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
	if ("$ipol" =~ *"xx"*) then
	    uvplt vis=$file options=2pass device=/null options=2pass,all select='pol(xx),-auto' | grep Baseline | awk '{print $2,$3,$5}' | sed 's/-//g' > $wd/xbase # Get xx baselines
	endif
	if ("$ipol" =~ *"yy"*) then 
	    uvplt vis=$file options=2pass device=/null options=2pass,all select='pol(yy),-auto' | grep Baseline | awk '{print $2,$3,$5}' | sed 's/-//g' > $wd/ybase # Get yy baselines
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
	mfcal vis=$file refant=$refant options=interpolate minants=4 flux=$flux interval=$int >& /dev/null
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
	if ((`echo $sflags $linelim $lim | awk '{if ($1 > $2*(nchan^.5)) print "go"; else if ($2 < $3) print "go"}' nchan=$nchan` == "go" || `echo $intcheck $addflux $sysflux | awk '{if ($1/10 > ($2+$3)) print "go"}'` == "go") && $linelim != $linemax) then
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
	endif

    if ($polsplit && $sefd) then
        echo -n "Beginning SEFD calculation"
	uvflag vis=$file options=none flagval=u select=auto >& /dev/null
	uvcal vis=$file options=nocal,nopass,nopol,fxcal out=$wd/sefdcal >& /dev/null
	uvflag vis=$wd/sefdcal flagval=f select='amp(0,0.0000000000000001)' options=none >& /dev/null #This is here since uvcal is stupid, and this corresponds to a noise level of 80 dBS (SNR of 1:10^8)
	echo -n ", calculating gains tables..."
	mfcal vis=$wd/sefdcal refant=$refant options=interpolate minants=4 flux=$flux interval=$int >& /dev/null
	echo " Ant Pol  R-Gain Avg  R-Gain RMS  I-Gain Avg  I-Gain RMS   SEFD (Jy)" >> $wd/sefd.$ipol$cycle
	echo "====================================================================" >> $wd/sefd.$ipol$cycle

	gplist vis=$wd/sefdcal options=all | sed 's/^.\{10\}//g' | grep "Ant" | sort -nk2 | awk '{if (NR == 1 || ant == $2) {ant=$2;n++; re += $5; rs += $5*$5;im += $6;is += $6*$6}; if (ant != $2) {printf "%4s   %1s % .4e % .4e % .4e % .4e % .4e\n",ant,pol,re/n,sqrt((rs-n*(re/n)*(re/n))/n),im/n,sqrt((is-(n*(im/n)*(im/n)))/n),((re*re)+(im*im))/(n^2);ant=$2;n=1;re=$5;rs=$5*$5;im=$6;is=$6*$6}}' pol=`echo $ipol | sed -e 's/xx/x/g' -e 's/yy/y/g'`| awk '{if ($7*1 != 0) print $0}' >> $wd/sefd.$ipol$cycle
	rm -rf $wd/sefdcal
	echo "done!"
    endif


    	# If on the last cycle, then use uvaver to pull together all of the datasets. Otherwise, repeat with the next time cycle.
	if ($postidx >= $#regtimes) then
	    uvaver vis="$wd/tempcali$ipol*" out=$wd/tempcal2 options=relax > /dev/null
	    uvaflag vis=$wd/tempcal$ipol tvis=$wd/tempcal2 > /dev/null
	    rm -rf $wd/tempcal2
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
    # The final solution check, start with a dash of MFCAL
    set checkamp = 1000
    mfcal vis=$wd/tempcal$ipol refant=$refant options=interpolate minants=4 flux=$flux interval=$int >& /dev/null
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
	    uvflag vis=$file flagval=f options=none $rfiline > /dev/null
	end
        echo "."
        echo "WRATH cleaning complete!"
	set wrathcycle = 0
    endif
    
    # Horray again for MFCAL
    mfcal vis=$wd/tempcal$ipol refant=$refant options=interpolate minants=4 flux=$flux interval=$int >& /dev/null

    if ($polsplit && $sefd) then
        echo -n "Beginning SEFD calculation"
	uvflag vis=$wd/tempcal$ipol options=none flagval=u select=auto >& /dev/null
	uvcal vis=$wd/tempcal$ipol options=nocal,nopass,nopol,fxcal out=$wd/sefdcal >& /dev/null
	uvflag vis=$wd/sefdcal flagval=f select='amp(0,0.0000000000000001)' options=none >& /dev/null #This is here since uvcal is stupid, and this corresponds to a noise level of 80 dBS (SNR of 1:10^8)
	echo -n ", calculating gains tables..."
	mfcal vis=$wd/sefdcal refant=$refant options=interpolate minants=4 flux=$flux interval=$int >& /dev/null
	echo " Ant Pol  R-Gain Avg  R-Gain RMS  I-Gain Avg  I-Gain RMS   SEFD (Jy)" > $wd/sefd.$ipol
	echo "====================================================================" >> $wd/sefd.$ipol

	gplist vis=$wd/sefdcal options=all | sed 's/^.\{10\}//g' | grep "Ant" | sort -nk2 | awk '{if (NR == 1 || ant == $2) {ant=$2;n++; re += $5; rs += $5*$5;im += $6;is += $6*$6}; if (ant != $2) {printf "%4s   %1s % .4e % .4e % .4e % .4e % .4e\n",ant,pol,re/n,sqrt((rs-n*(re/n)*(re/n))/n),im/n,sqrt((is-(n*(im/n)*(im/n)))/n),((re*re)+(im*im))/(n^2);ant=$2;n=1;re=$5;rs=$5*$5;im=$6;is=$6*$6}}' pol=`echo $ipol | sed -e 's/xx/x/g' -e 's/yy/y/g'` | awk '{if ($7*1 != 0) print $0}' >> $wd/sefd.$ipol
	rm -rf $wd/sefdcal
	echo "done!"
    endif
    echo "Final cycle complete!"
    echo ""
end

# Pull together all polarizations
uvaver vis=`echo " $pollist" | sed -e 's/ /,'$wd'\/tempcal/g' -e 's/,//'` options=relax out=$wd/tempcalfin >& /dev/null

# Put the results of the mapping process into a specified directory
set outfile = "cal-$source-maps"

set idx = 0
while (-e $outfile)
    @ idx++
    set outfile = "cal-$source-maps.$idx"
end

#################################################################    
# Once the calibration cycle has completed, the program uses
# the automapper routine to produce an image,  make any
# neccessary fine tuning (due to imperfections in out cal model)
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

if (-e $wd/sefd.xx) cp $wd/sefd.xx $outfile/sefd.xx
if (-e $wd/sefd.xx) cp $wd/sefd.yy $outfile/sefd.yy

echo "Copying gains back to original file ($vis)"

if ($polsplit && $#pollist > 1) then # If pols were split and more than one pol exists
    foreach dp (xx yy)
	if (-e $outfile/$source.1.$dp/gains) then # If the automapping software had "tweaks" for the gains solution, apply those tweaks
	    puthd in=$outfile/$source.1.$dp/interval value=.1 > /dev/null
	    gpcopy vis=$outfile/$source.1.$dp out=$vis > /dev/null
	    if (-e $vis/gains) mv $vis/gains $vis/gains.{$dp}p
	    if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.{$dp}p
	endif
	puthd in=$wd/tempcal$dp/interval value=.1 > /dev/null 
	gpcopy vis=$wd/tempcal$dp out=$vis > /dev/null
    # Move pol-specific gains "out of the way" so that information isnb't overwritten by gpcopy
	if (-e $vis/gains) mv $vis/gains $vis/gains.$dp 
	if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.$dp
    end
else if ($polsplit) then # if polspilt was used, but only one pol was found
    if (-e $outfile/$source.1.$pollist[1]/gains) then # If the automapping software had "tweaks" for a single pol gains solution, apply those tweaks
	puthd in=$outfile/$source.1.$pollist[1]/interval value=.1 > /dev/null
	gpcopy vis=$outfile/$source.1.$pollist[1] out=$vis > /dev/null
	if (-e $vis/gains) mv $vis/gains $vis/gains.$pollist[1] 
	if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.$pollist[1]
    endif
    puthd in=$wd/tempcal$pollist[1]/interval value=.1 > /dev/null
    gpcopy vis=$wd/tempcal$pollist[1] out=$vis > /dev/null
    # Move pol-specific gains "out of the way" so that information isn't overwritten by gpcopy
    if (-e $vis/gains) mv $vis/gains $vis/gains.$pollist[1]
    if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.$pollist[1]
else
    foreach dp (xx yy)
	if (-e $outfile/$source.1.$dp/gains) then # If the automapping software had "tweaks" for the gains solution, apply those tweaks
	    puthd in=$outfile/$source.1.$dp/interval value=.1 > /dev/null
	    gpcopy vis=$outfile/$source.1.$dp out=$vis > /dev/null
	    # Move pol-specific gains "out of the way" so that information isn't overwritten by gpcopy
	    mv $vis/gains $vis/gains.$dp
	endif
    end
    # Copy over any "general" gains solutions (relating to multiple pols)
    puthd in=$wd/tempcal$pollist[1]/interval value=.1 > /dev/null
    gpcopy vis=$wd/tempcal$pollist[1] out=$vis > /dev/null
endif

# Repeat the gains copying process for each source file, first copying any pol-specific solutions first, then copying "general" (multi-pol) solutions
foreach tfile ($tvis)
    echo "Copying gains to $tfile"
    foreach dp (xx yy)
	if (-e $vis/gains.$dp || -e $vis/bandpass.$dp) then
	    if (-e $vis/gains) mv $vis/gains $vis/tempgains
	    if (-e $vis/bandpass) mv $vis/bandpass $vis/tempbandpass
	    if (-e $vis/gains.$dp) mv $vis/gains.$dp $vis/gains
	    if (-e $vis/bandpass.$dp) mv $vis/bandpass.$dp $vis/bandpass
	    gpcopy vis=$vis out=$tfile > /dev/null
	    if (-e $tfile/gains) mv $tfile/gains $tfile/gains.$dp
	    if (-e $tfile/bandpass) mv $tfile/bandpass $tfile/bandpass.$dp
	    if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.$dp
	    if (-e $vis/gains) mv $vis/gains $vis/gains.$dp
	    if (-e $vis/tempbandpass) mv $vis/tempbandpass $vis/bandpass
	    if (-e $vis/tempgains) mv $vis/tempgains $vis/gains
	endif
	if (-e $vis/gains.{$dp}p || -e $vis/bandpass.{$dp}p) then
	    gpcopy vis=$outfile/$source.1.$dp out=$tfile > /dev/null
	    if (-e $tfile/bandpass) mv $tfile/bandpass $tfile/bandpass.{$dp}p
	    if (-e $tfile/gains) mv $tfile/gains $tfile/gains.{$dp}p
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
	uvaflag vis=$tvis tvis=$wd/tvis$filemark > /dev/null
    end
endif

#

goto finish
# Below here is reporting information that needs to be upgraded... badly.
set count = `uvlist vis=$wd/tempcal recnum=0 select='window(1),pol(xx,yy),-auto' | grep -v CHAN | grep ":" | grep -v "e" | wc -l| awk '{print $1}'`
set fccount = ($fccount $count)
set bcount = `uvplt vis=$wd/tempcal select='pol(xx,yy),-auto' device=/null options=2pass | grep Baseline | wc -l`
set fbcount = ($fbcount $bcount)

#uvplt vis=$wd/tempcal select='pol(xx),-auto' device=/null options=2pass | grep Baseline | tr "-" " " | awk '{print " "$2"X-"$3"X",$5}' > $wd/fbaselist
echo " " > $wd/fbaselist
#uvplt vis=$wd/tempcal select='pol(yy),-auto' device=/null options=2pass | grep Baseline | tr "-" " " | awk '{print " "$2"Y-"$3"Y",$5}' >> $wd/fbaselist

foreach base (`cat $wd/ibaselist | awk '{print $1}'`)
    set ipts = `grep " $base" $wd/ibaselist | awk '{print $2}'`
    set fpts = " "`grep " $base" $wd/fbaselist | awk '{print $2}'`
    if (`echo $fpts | wc -w | awk '{print $1}'` != 0) then
	set pct = `echo $fpts $ipts | awk '{print 100*$1/$2}' | tr "." " " | awk '{print $1}'`
	echo " $base --- $fpts out of $ipts spectra preserved ($pct%)" >> $wd/rpttemp
    else
	set fpts = 0
	echo $base >> $wd/badbase 
	echo " $base --- $fpts out of $ipts spectra preserved (0%)" >> $wd/rpttemp
    endif
end

report: # Beyond here is pretty boring code, so we'll just "ignore" it for the time being

set scount = `uvlist vis=$wd/tempcal options=stat recnum=0 select=-auto | grep -v CHAN | grep ":" | grep -v "e" | wc -l| awk '{print $1}'`
echo "Calcal summary for $cal data" >> $cal.calrpt
echo "------------------------------------------------" >> $cal.calrpt
echo "$scount out of $rcount records left in image. (`calc -i 100'*'$scount/$rcount`%)" >> $cal.calrpt
echo " " >> $cal.calrpt
set bpct = `echo $fbcount[1] $ibcount[1] | awk '{print 100*$1/$2}' | tr "." " " | awk '{print $1}'` >> $cal.calrpt
set cpct = `echo $fccount[1] $iccount[1] | awk '{print 100*$1/$2}'| tr "." " " | awk '{print $1}'` >> $cal.calrpt
echo "Correlator file - $vis" >> $cal.calrpt
echo "--------------------------------------------------------------------" >> $cal.calrpt
echo " $fbcount[1] out of $ibcount[1] baselines preserved ($bpct%)" >> $cal.calrpt
echo " $fccount[1] out of $iccount[1] spectra preserved ($cpct%)" >> $cal.calrpt
echo "--------------------------------------------------------------------" >> $cal.calrpt
echo " " >> $cal.calrpt
echo "The following baselines in this file were not preserved (0% spectra):" >> $cal.calrpt
set badlist = `cat $wd/badbase`
echo $badlist | tr " " "," >> $cal.calrpt
echo " "  >> $cal.calrpt
echo "Antenna Counts" >> $cal.calrpt
echo "-------------------------"  >> $cal.calrpt
foreach antpol (`cat $wd/antlist`)
    set antcount = `cat $wd/badbase | tr "-" " "| awk '{print " "$1" "$2}' | grep " $antpol " | wc -l | awk '{print $1}'`
    if ($antcount != 0) echo "$antpol --- $antcount affected baseline(s)" >> $cal.calrpt
end
echo " "  >> $cal.calrpt
echo " " >> $cal.calrpt
echo "END SUMMARY" >> $cal.calrpt
echo "Full listing" >> $cal.calrpt
echo "Listing for $vis" >> $cal.calrpt
echo "--------------------------------------------------------------" >> $cal.calrpt
cat $wd/rpttemp >> $cal.calrpt

finish:
set times = (`date +%s.%N | awk '{print int(($1-date1)/60),int(($1-date1)%60)}' date1=$date1` 0 0)
echo "Calibration cycle took $times[1] minute(s) and $times[2] second(s)."
if !($debug) rm -rf $wd
exit 0 

fail:
echo "Calibration failed for unknown reason! Now exiting..."
if !($debug) rm -rf $wd
exit 1
