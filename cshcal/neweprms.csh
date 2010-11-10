#! /usr/bin/tcsh -f
#
# $Id: neweprms.csh 642 2009-09-17 18:41:54Z karto $
#    exit script cleanly  on interrupt

onintr fail

# Begin variable preset, determine what variables to populate. These are variables that the user has control over when calling the program

set vis # Name of file to be processed
set plim = (0.0001 20) # "Acceptable" phase RMS range for baselines
set clim = (-200 200) # "Acceptable closure range for baselines
set debug = 0 # Switch to prevent temp directory from being deleted
set stime
set etime
set printstats
set caloptions

if ($#argv == 0) then
      #################################################################
echo "================================================================="
echo "EPRMS - Baseline phase information scanner"
echo "'Because we all need closure... and possibly RMS.'"
echo ""
echo "CALLS - MIRIAD (uvplt)"
echo "PURPOSE - Derive statistical information for phase on baselines"
echo "    within a particular dataset"
echo "RESPONSIBLE - Karto (karto@hcro.org)"
echo "================================================================="
echo ""
echo "EPRMS is designed to derive statistics for individual baselines."
echo "Currently, EPRMS will give out a listing of baselines that exceed"
echo "some threshold for average and RMS phase. This listing is given"
echo "in a format that is 'MIRIAD-friendly', so that it can easily be"
echo "captured and used with UVFLAG."
echo ""
echo "EPRMS operates by looking at the phase information over all time"
echo "in the dataset, and calculates the RMS and average phase for"
echo "each baseline."
echo ""
echo "EPRMS results are returned to the terminal - no report/log files"
echo "are created"
echo ""
echo "EPRMS will be expanded in the near future to also include other"
echo "information on baselines and antennas. Only XX and YY baselines"
echo "are currently evaluated"
echo ""
echo "TECHNICAL NOTE: EPRMS creates a temporary directory to work"
echo "from, named eprmsXXXX (where X is a random character). These"
echo "directories are supposed to be automatically deleted after CALCAL"
echo "completes, but might remain in the event of a program error."
echo "Remnant directories can be safely deleted."
echo ""
echo "CALLING SEQUENCE: neweprms.csh vis=vis (plim=plim1,plim2"
echo "    clim=clim1,clim2 options=debug)"
echo ""
echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo ""
echo "REQUIRED INPUTS:"
echo " vis - Name of the file to be analyzed. No default"
echo ""
echo "OPTIONAL INPUTS"
echo " plim - Range of phase RMS values (in degrees) designated as "
echo "    'good'. Baselines with phase RMS exceeding this range are" 
echo "    reported as bad. If a single value is specified, then the"
echo "    'good' range is anything between zero and that value. Default"
echo "    is .0001 to 20."
echo " clim - Range of average phaes values (in degrees) designated as"
echo "    'good'. Baselines with an average exceeding this range are" 
echo "    reported as bad. If a single value is specified, then the"
echo "    'good' range is anything between zero and that value. Default"
echo "    is -200 to 200."
echo " options=debug"
echo "    debug - Don't delete temporary files created by EPRMS."
echo "    printstats - Print full baselines statistics."
exit 0
endif

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
else if ("$argv[1]" =~ 'plim='*) then
    set plim = (`echo $argv[1] | sed 's/plim=//' | tr '(,)' ' '`)
    if ($#plim == 2) set plim = (`echo $plim | awk '{if ($1 > $2) print $2,$1; else print $1,$2}'`)
    if ($#plim == 1) set plim = (0.0001 $plim)
    if (`echo $plim | awk '{if ($1*1 < 0 || $2*1 <=0 || $1 == $2 ) print 1; else print 0}'`) then
	echo "FATAL ERROR: Incorrect phase RMS range."
	exit 1
    endif
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'clim='*) then
    set clim = (`echo $argv[1] | sed 's/clim=//' | tr '(,)' ' '`)
    if ($#clim == 2) set clim = (`echo $clim | awk '{if ($1 < $2) print $1,$2; else print $2,$1}'`)
    if ($#clim == 1) set clim = (`echo $clim | awk '{if ($1 < 0) print $1,"0"; else print "0",$1}'`)
    if (`echo $clim | awk '{if ($1*1 == $2*1 ) print 1; else print 0}'`) then
	echo "FATAL ERROR: Incorrect average phase range."
	exit 1
    endif
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'options='*) then
    set options = `echo "$argv[1]" | sed 's/options=//g' | tr ',' ' ' | tr '[A-Z]' '[a-z]'`
    set badopt
    foreach option (`echo $options`)
	if ($option == debug) then
	    set debug = 1
	else if ($option == printstats) then
	    set printstats = 1
	else if ($option == nocal) then
	    set caloptions = "$caloptions,nocal"
	else if ($option == nopass) then
	    set caloptions = "$caloptions,nopass"
	else if ($option == nopol) then
	    set caloptions = "$caloptions,nopol"
	else
	    set badopt = ($badopt $option)
	endif
    end
    if ("$badopt" != "") echo 'options='`echo $badopt | tr ' ' ','`' not recognized!'
    shift argv; if ("$argv" == "") set argv = "finish"
else
    echo "FATAL ERROR: $argv[1] not recognized..."
    exit 1
endif

if ("$argv[1]" != "finish") goto varassign

#################################################################
# The program creates a temp directory to work in within the
# data directory being used. This is done to make operations
# "cleaner", as several MIRIAD results are dumped to temp files
# to be parsed later.
#################################################################

if ($vis == "") then
    echo "FATAL ERROR: No vis file specified!"
    exit 1
else if (! -e $vis/visdata) then
    echo "FATAL ERROR: Visibility data not found!"
    exit 1
endif

set wd = `mktemp -d "eprmsXXXX"`

#################################################################
# The program uses UVPLT to dump information on the baselines
# present, and their datapoints. These operations are split by
# polarization since UVPLT doesn't seperate information based on
# polarization without using the 'select' command. The info form
# UVPLT are run through a simple awk script to determine the
# average and RMS phase for each baseline.
#################################################################

# Time ranges are not currently supported, but will soon...
set timerange
if ("$stime" != "") set timerange = "time($stime,$etime),"
#    log phase vs time for given scan and pol for all baselines
# The wrap option is used to catch baselines what might have and average around -180 or 180
uvplt vis=$vis device=/null axis=time,pha options=log,2pass,unwrap$caloptions log=$wd/xphalog select="window(1),pol(xx),""$timerange""-auto" >& /dev/null 
uvplt vis=$vis device=/null axis=time,pha options=log,2pass,unwrap$caloptions log=$wd/yphalog select="window(1),pol(yy),""$timerange""-auto" >& /dev/null

# Sort out the baseline information from what UVPLT reports
if (-e $wd/xphalog) then
sed 1,7d $wd/xphalog | grep 'Baseline' | tr -d '-' | awk '{print ($2*1000)+$3,$2,$3,$5}' | sort -nk1 | awk '{print $2,$3,$4}' > $wd/xbase
sed 1,7d $wd/xphalog | grep -v 'Baseline' > $wd/xpha
endif
if (-e $wd/yphalog) then
sed 1,7d $wd/yphalog | grep 'Baseline' | tr -d '-' | awk '{print ($2*1000)+$3,$2,$3,$5}' | sort -nk1 | awk '{print $2,$3,$4}' > $wd/ybase
sed 1,7d $wd/yphalog | grep -v 'Baseline' > $wd/ypha
endif
 
# Gather which polarizations are present in the data
if (-e $wd/xphalog && -e $wd/yphalog) then
    set pols = (x y)
else if (-e $wd/xphalog) then
    set pols = (x)
else if (-e $wd/yphalog) then
    set pols = (y)
else
    set pols
endif

#    get phase vs time data from uvplt log file
touch $wd/baselist2
if ($printstats) echo "Ant1 Ant2 Pol P-Avg P-RMS Npoints"
foreach pol ($pols)
    set idx = 1
    set plidx = 1
    set puidx = 0
    set baselim = `wc -l $wd/${pol}base | awk '{print $1}'`
    set baselist
    while ($idx <= $baselim)
	set baseinfo = (`sed -n {$idx}p $wd/{$pol}base`)
	set puidx = `echo $puidx $baseinfo[3] | awk '{print $1+$2}'`
	set basestats = (`sed -n {$plidx},{$puidx}p $wd/{$pol}pha | awk '{n++; if (n==1) {sx=$2; sxx=$2*$2} else {sx=sx+$2; sxx=sxx+($2*$2)} if (n==nct) {m=sx/n; r=sqrt((sxx-n*m*m)/n); print m, r}}' nct=$baseinfo[3]`)
	set plidx = `echo $plidx $baseinfo[3] | awk '{print $1+$2}'`
	@ idx++
	if ($printstats) then
	    echo $baseinfo[1-2] $pol$pol $basestats $baseinfo[3]
	else
	    # Evaluate the baseline stats to see whether or not it's bad
	    echo $basestats $baseinfo $pol | awk '{if ($1 > uclim || $1 < lclim || $2 > uplim || $2 < lplim) print $3"-"$4}' uclim=$clim[2] uplim=$plim[2] lclim=$clim[1] lplim=$plim[1] >> $wd/baselist2
	endif
    end
    set antlist = (`sed 's/-/ /g' $wd/baselist2 | awk '{printf "%s\n%s\n",$1,$2}' | sort -n | uniq`)
    # The following groups together the bad baselines to minimize the neccessary select commands needed to "grab" them
    while (`wc -w $wd/baselist2 | awk '{print $1}'`)
	set idx = 0
	set nant = 0
	set mcount = 0
	set icount = 0
	# See which antenna has the most bad baselines, and use that as the basis for making the next select command
	foreach ant ($antlist)
	    @ idx++
	    set icount = `sed 's/-/ /g' $wd/baselist2 | awk '{if ($1 == ant || $2 == ant) idx += 1} END {print idx}' ant=$ant`
	    if ($icount > $mcount) then
		set nant = $idx
		set mcount = $icount
	    endif
	end
	set ant = $antlist[$nant]
	set flagcmds =(`sed 's/-/ /g' $wd/baselist2 | awk '{if ($1 == ant) {printf "%s,",$2; count += 1}; if ($2 == ant) {printf "%s,",$1; count += 1}; if ((count*1)%12 == 0) print ")"} END {if (count%12 != 0) print ")"}' ant=$ant | sed 's/,)//g' | tr -d ')'`)
	set flagcmds = ("ant($ant)("`echo $flagcmds`"),pol($pol$pol)")
	set flagcmd = `echo $flagcmds | sed 's/ /'"),pol($pol$pol) ant($ant)("'/g'`
	echo $flagcmd
	# Print the select command, and start over until no more bad baselines are present
	set antlist[$nant]
	set antlist = (`echo $antlist`)
	sed 's/-/ /g' $wd/baselist2 | awk '{if ($1 != ant && $2 != ant) print $1"-"$2}' ant=$ant > $wd/baselist3
	mv $wd/baselist3 $wd/baselist2
    end
end

finish:

fail:

if !($debug) rm -rf $wd

exit 0
