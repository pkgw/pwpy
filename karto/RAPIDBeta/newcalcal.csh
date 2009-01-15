#! /usr/bin/tcsh -f
# $Id$
#Calibrates a calibrator...

onintr fail

if ($#argv == 0) then
    echo "NEWCALCAL.CSH"
    echo "newcalcal.csh is designed as an 'all-in-one' data reduction utility for calibrator data. newcalcal will derive (and copy) gains solutions and create maps of calibrator data. Note: newcalcal is currently designed for calibrators with at least 4 Jy worth of flux, although a minimum of 12 Jy is much more preferable"
    echo "Calling sequence: newcalcal.csh vis=vis plim=plim clim=clim calint=calint flux=flux addflux=addflux refant=refant"
    echo "REQUIRED INPUTS:"
    echo "vis - Name of the files containing calibrator data"
    echo "OPTIONAL INPUTS"
    echo "plim - RMS phase scatter limit (in degrees) for baselines before being flagged. Default is 20."
    echo "clim - Closure offset limit (in degrees) for baselines before being flagged. Default is 20"
    echo "calint - Interval (in min) for calibrator observations. Default in 15."
    echo "flux - either one or three numbers (comma seperated) listing the flux (in Jy), then the frequency (in GHz), then the spectral index. Default is 1,obsfreq,0"
    echo "addflux - Parameter to define both additional flux (in Jy) in the field and establish a buffer for 'noisier' data points. Will expand the flagging boundaries and both the lower and upper amplitude limits. Default is 4."
    echo "refant - Reference antenna. If not specified, newcalcal will automatically determine a 'best choice' every cycle."
    exit 0
endif

set vis # The file to be processed
set tvis # Files to be flagged and gains copied to
set olay # Overlay file for display
set plim = 20 # Phase RMS limit for all baselines
set siglim = 5
set calint = 10 # Interval period for sol'ns
set flux # Flux for the calibrator (note, no longer automatically supplied!)
set refant # Reference antenna for calibration
set autoref = 1 # If not refant is provided, then calcal will attempt to choose one
set sysflux = 5 # Additional flux from tsys (at three sigma point, say)
set addflux = 1 # Additional flux in the field, definitely good to keep track of
set retlim = 20
set outsource = 1
set mapopt = "options=savedata"
set display = 0
set polsplit = 0

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
else if ("$argv[1]" =~ 'calint='*) then
    set calint = `echo $argv[1] | sed 's/calint=//'`
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
	else if ($option == "savedata") then
	    set mapopt = "$mapopt"",savedata"
	else if ($option == "display") then
	    set display = 1
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
    set refant = `echo $argv[1] | sed 's/clim=//'`
    set autoref = 0
    shift argv; if ("$argv" == "") set argv = "finish"
else
    echo "FATAL ERROR: $argv[1] not recognized..."
    exit 1
endif

if ("$argv[1]" != "finish") goto varassign

if ($vis == "") then
    echo "Vis file needed"
    exit 1
else if !( -e $vis) then
    echo "Vis file needed!"
    exit 1
endif

###################################

set wd = (`mktemp -d calXXXXX`)

if !( -e $wd) then
    echo "FATAL ERROR: Unable to create working directory, please make sure that you have read/write permissions for this area."
    exit 1
endif

###################################

set date1 = `date +%s.%N`

if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.bu
if (-e $vis/gains) mv $vis/gains $vis/gains.bu

foreach tfile ($tvis)
    if (-e $tfile/flags) cp $tfile/flags $tfile/flags.bu
    if (-e $tfile/bandpass) mv $tfile/bandpass $tfile/bandpass.bu
    if (-e $tfile/gains) mv $tfile/gains $tfile/gains.bu
end

echo "Looking up times for calibrator observations."
set regtimes = (`uvlist vis=$vis options=stat recnum=0 | awk '{if ($1*1 > 0) print day":"$2; else if ($1$2$3 == "Datavaluesfor") day = $4}' | sort | uniq`)
set jultimes
echo "Observation times found, splitting into time intervals"
foreach itime ($regtimes)
    julian date=$itime options=quiet >> $wd/jultimes
end
set jultimes = (`awk '{if ($1-lastday-(1/86400) > calint/1440){if (NR == 1) printf "%7.6f\n",$1-1; lastday = $1; printf "%7.6f\n",$1-(1/86400)}; fin = $1} END {printf "%7.6f\n",fin+1}' calint=$calint $wd/jultimes`)
echo `echo $#jultimes | awk '{print $1-2}'`" time cycles confirmed."
set regtimes

foreach itime ($jultimes)
    set regtimes = ($regtimes `julian jday=$itime options=quiet`)
end

set nchanline = (`uvlist vis=$vis options=var,full | grep nchan | tr ':' ' '`)
set nchan

while ($nchan == "")
    if ($nchanline[1] == "nchan") then
	set nchan = "$nchanline[2]" 
    else if ($#nchanline == 1) then
	set nchan == 512
    else
	shift nchanline
    endif
end

set sourceline = (`uvlist vis=$vis options=var | grep "source" | tr ':' ' '`)
set source

while ($source == "")
    if ($sourceline[1] == "source") then
	set source = "$sourceline[2]" 
    else if ($#sourceline == 1) then
	set source == "UNK"
    else
	shift sourceline
    endif
end

set freqline = (`uvlist vis=$vis options=var | grep "freq    :" | tr ':' ' '`) # Set the freq in MHz
set freq

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
    echo "Flux option not recognized!"
    exit 1
endif


echo "Cal is $source - flux is $calflux Jy - nchan is $nchan - freq is $freq GHz"

set rcount = 0
set iccount
set ibcount
set fbcount
set fccount

set pollist = ("xxyy")

if ($polsplit) then
    set pollist = ("xx" "yy")
    uvaver vis=$vis select='window(1),pol(xx),-auto' out=$wd/tempcalxx options=relax,nocal,nopass,nopol >& /dev/null
    uvaver vis=$vis select='window(1),pol(xx,yy),-auto' out=$wd/tempcalyy options=relax,nocal,nopass,nopol >& /dev/null
else
    uvaver vis=$vis select='window(1),pol(xx,yy),-auto' out=$wd/tempcalxxyy options=relax,nocal,nopass,nopol >& /dev/null
endif

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


while ($idx < $#regtimes)
    set cycle = `echo $idx | awk '{print 999+$1}' | sed 's/1//'`
    echo -n "Preparing file "`echo $idx | awk '{print $1-1}'`" of "`echo $#regtimes | awk '{print $1-2}'`"..."
    foreach pol (`echo $pollist | sed 's/xxyy/xx,yy/'`)
	uvaver vis=$wd/tempcal`echo $pol | tr -d ','` out=$wd/tempcali`echo $pol | tr -d ','`$cycle options=relax,nocal,nopass,nopol select="window(1),time($regtimes[$idx],$regtimes[$postidx]),pol($pol)" >& /dev/null
    end
    if ($outsource && "$tvis[1]" != "") then
        set tviscount = ($tviscount 0)
	foreach tfile ($tvis)
	    @ tviscount[$idx]++
	    uvaver vis=$tfile out=$wd/tvis$tfile$cycle options=relax,nocal,nopass,nopol select="time($regtimes[$idx],$regtimes[$postidx])" >& /dev/null
	    if !(-e $wd/tvis$tfile$cycle/visdata) rm -rf $wd/tvis$tfile$cycle
	    if !(-e $wd/tvis$tfile$cycle/visdata) @ tviscount[$idx]--
        end
    endif
    echo "complete."
    @ idx++ postidx++
end


echo " "
echo " "
echo "Starting flagging and calibration."
if ($outsource && "$tvis[1]" != "") then
    foreach tfile ($tvis)
	@ tviscount[1]++
        uvaver vis=$tfile out=$wd/tvis{$tfile}000 options=relax,nocal,nopass,nopol select="time($regtimes[1],$regtimes[2])" >& /dev/null
        if !(-e $wd/tvis{$tfile}000/visdata) rm -rf $wd/tvis{$tfile}000
        if !(-e $wd/tvis{$tfile}000/visdata) @ tviscount[1]--
    end
endif

foreach ipol ($pollist)
    set idx = 0; set mididx = 1; set postidx = 2
    foreach file ($wd/tempcali{$ipol}*)
	@ idx++ midxidx++ postidx++
	set cycletime = "`date +%s.%N`"
	set cycle =  `echo $idx | awk '{print 1000+$1}' | sed 's/1//'`
	set precycle =  `echo $idx | awk '{print 999+$1}' | sed 's/1//'`
	set sfilelist
	set prefiles
	set postfiles
	if ($outsource && "$tvis[1]" != "") then
	    if ($tviscount[$idx]) set prefiles = "$wd/tvis*$precycle"
	    if ($tviscount[$mididx]) set postfiles = "$wd/tvis*$cycle"
	    set sfilelist = ($prefiles $postfiles)
	else
	    foreach sfile ($tvis)
		if (`uvplt vis=$sfile select="time($regtimes[$idx],$regtimes[$postidx])" device=/null | grep -c "Baseline"`) set sfilelist = ($sfilelist $sfile
	    end
	endif
	touch $wd/xbase; touch $wd/ybase
	if ("$pollist" =~ *"xx"*) uvplt vis=$file options=2pass device=/null options=2pass,all select='pol(xx),-auto' | grep Baseline | awk '{print $2,$3,$5}' | sed 's/-//g' > $wd/xbase
	if ("$pollist" =~ *"yy"*) uvplt vis=$file options=2pass device=/null options=2pass,all select='pol(yy),-auto' | grep Baseline | awk '{print $2,$3,$5}' | sed 's/-//g' > $wd/ybase
	echo -n "Starting $idx of "`echo $#regtimes | awk '{print $1-2}'`" cycles. Beginning phase RMS scanning."

	if ($idx != $#regtimes) then
	    foreach badbase (`neweprms.csh $file $plim`)
		uvflag vis=$file select="$badbase" flagval=f options=none > /dev/null
		echo -n "."
	    end
	endif

	echo "phase scanning/flagging complete."

	set xants = (`awk '{printf "%s\n%s\n",$1,$2}' $wd/xbase | sort -n | uniq`)
	set yants = (`awk '{printf "%s\n%s\n",$1,$2}' $wd/ybase | sort -n | uniq`)
	set xantcount = $#xants
	set yantcount = $#yants
	if ("$xants" == "") set xantcount = 0
	if ("$yants" == "") set yantcount = 0

    jumper:
	touch $wd/phaselog
	touch $wd/amplog
	set checkamp = (1000 100000)

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
    
	mfcal vis=$file refant=$refant options=interpolate minants=4 flux=$flux interval=$calint >& /dev/null
	
	uvaver vis=$file out=$wd/tempcal2 options=relax >& /dev/null
	
	set sflags = 0
	if ($display) uvplt vis=$wd/tempcal2 select='-auto' device=/xs options=2pass,nobase,equal,source axis=re,im >& /dev/null
	uvlist vis=$wd/tempcal2 select='-auto' recnum=0 line=chan,1,1,$nchan | sed 1,9d | awk '{if ($1*1 ==0); else if ($8*1 != 0 || $9*1 != 0) print $1,$9,(($8*cos(pi*$9/180)-flux)^2+($8*sin(pi*$9/180))^2)^.5}' flux=$calflux pi=3.141592 | sort -nk3 > $wd/ampinfo
    
	set linecheck = `wc -l $wd/ampinfo | awk '{print int($1*.95)}'`
	set linelim = `wc -l $wd/ampinfo | awk '{print int($1*exp(-1*siglim))}' siglim=$siglim`
	set linemax = `wc -l $wd/ampinfo | awk '{print 1+int($1*.05)}'`
	set intcheck = `tail -n 1 $wd/ampinfo | awk '{print $3}'`
    
	if ($linelim < 10) set linelim = 10
	echo "Minimum flagging line is $linelim, maximum is $linemax."
	
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

#########################################################################
	flagging:
	echo "Flagging commencing, outer-limit for flux noise is $checkamp[1] Jy for integrated spectra, $checkamp[2] Jy for individual channels."
	set llim=1
	set ulim=50
	set lim = `wc -w $wd/amplog | awk '{print $1}'`
    
	echo -n "$lim integrated records to flag and $sflags spectral records to flag..."
	cat $wd/phaselog >> $wd/amplog
	while ($llim <= $lim)
	    set flags = `sed -n {$llim},{$ulim}p $wd/amplog | awk '{printf "%s","vis("$1"),"}' ulim=$ulim`
	    uvflag vis=$wd/tempcal2 flagval=f options=none select=$flags >& /dev/null
	    set llim = `echo $llim | awk '{print $1+50}'`
	    set ulim = `echo $ulim | awk '{print $1+50}'`
	    echo -n "."
	end
	echo " "
	uvaflag vis=$file tvis=$wd/tempcal2 >& /dev/null
	rm -rf $wd/tempcal2 $wd/amplog $wd/ampinfo $wd/phaselog $wd/phaseinfo
    
	set pols = (x y)
	if ("$retlim" == 0) set pols
    
	if (`echo $sflags $linelim $lim | awk '{if ($1 > $2*(nchan^.5)) print "go"; else if ($2 < $3) print "go"}' nchan=$nchan` == "go" || `echo $intcheck $addflux $sysflux | awk '{if ($1/10 > ($2+$3)) print "go"}'` == "go") then
	    echo " "
	    rm -f $wd/ampinfo $wd/amplog $wd/phaseinfo $wd/phaselog
	    echo "Flagging complete, continuing cycle $idx of "`echo $#regtimes | awk '{print $1-2}'`"..."
	    goto jumper
	endif
    
	uvplt vis=$file options=2pass device=/null select='pol(xx),-auto' | grep Baseline | awk '{print $2,$3,$5}' | sed 's/-//g' > $wd/xbasetemp
	uvplt vis=$file options=2pass device=/null select='pol(yy),-auto' | grep Baseline | awk '{print $2,$3,$5}' | sed 's/-//g' > $wd/ybasetemp
    
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
		set vals = (`awk '{if ($1 == ant || $2 == ant) count += 1} END {print int(100*count/(ocount-1))}' ocount=$#antlist ant=$ant $wd/{$pol}basetemp`)
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

######

	    set jidx = 1
	    echo -n "Checking $pol$pol baseline retention..."
	    rm -f $wd/bad{$pol}base; touch $wd/bad{$pol}base
	    while ($jidx < `wc -l $wd/{$pol}base | awk '{print $1}'`)
		set vals = (`sed -n {$jidx}p $wd/{$pol}base`)
		set vals2 = (`awk '{if ($1 == ant1 && $2 == ant2) npoint += $3} END {print int(100*npoint/opoint)}' ant1=$vals[1] ant2=$vals[2] opoint=$vals[3] $wd/{$pol}basetemp`)
		if ($vals2[1] < $retlim) then
		    @ badjump++
		    echo $vals >> $wd/bad{$pol}base
		    sed {$jidx}d $wd/{$pol}base > $wd/{$pol}base2
		    mv $wd/{$pol}base2 $wd/{$pol}base
		else
		    @ jidx++
		endif
	    end
	    # This ends the search for bad baselines
	    set antlist = (`sed 's/-/ /g' $wd/bad{$pol}base | awk '{printf "%s\n%s\n",$1,$2}' | sort -n | uniq`)
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
		set vals = (`awk '{if ($1 == ant || $2 == ant) count += 1} END {print int(100*count/(ocount-1))}' ocount=$#antlist ant=$ant $wd/{$pol}basetemp`)
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
    # End data retention check - trying to do it one cycle at a time might be a bad idea...
	if ($badjump) @ badjump--
	if ($badjump) then
	    rm -f $wd/ampinfo $wd/amplog
	    echo "Culling complete, continuing cycle $idx of "`echo $#regtimes | awk '{print $1-2}'`"..."
	    echo " "
	    goto jumper
	endif
    
	if ($postidx >= $#regtimes) then
	    uvaver vis="$wd/tempcali$ipol*" out=$wd/tempcal2 options=relax > /dev/null
	    uvaflag vis=$wd/tempcal$ipol tvis=$wd/tempcal2 > /dev/null
	    echo "Moving to final cycle!"
	    rm -rf $wd/tempcal2
	else
	    set cycletimes = (`date +%s.%N | awk '{print int(($1-date1)/60),int(($1-date1)%60)}' date1=$cycletime` 0 0)
	    echo "Cycle complete! Calibration cycle took $cycletimes[1] minute(s) and $cycletimes[2] second(s). Moving on..."    
	endif
	echo " "
    end
#Final cycle

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

    mfcal vis=$wd/tempcal$ipol refant=$refant options=interpolate minants=4 flux=$flux interval=$calint >& /dev/null
end

uvaver vis=`echo " $pollist" | sed -e 's/ /,'$wd'\/tempcal/g' -e 's/,//'` options=relax out=$wd/tempcalfin

set outfile = "cal-$source-maps"

set idx = 0
while (-e $outfile)
    @ idx++
    set outfile = "cal-$source-maps.$idx"
end
    
newautomap.csh vis=$wd/tempcalfin mode=auto outdir=$outfile $mapopt $olay

echo "Copying gains back to original file ($vis)"

if ($polsplit && $#pollist > 1) then
    if (-e $outfile/$source.1.xx/gains) then
	puthd in=$outfile/$source.1.xx/interval value=.5 > /dev/null
	gpcopy vis=$outfile/$source.1.xx out=$wd/tempcalxx mode=apply
	puthd in=$wd/tempcalxx value=.5 > /dev/null
	gpcopy vis=$wd/tempcalxx out=$vis
	if (-e $vis/gains) mv $vis/gains $vis/gains.xx
	if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.xx
    endif
    if (-e $outfile/$source.1.yy/gains) then
	puthd in=$outfile/$source.1.yy/interval value=.5 > /dev/null
	gpcopy vis=$outfile/$source.1.yy out=$wd/tempcalyy mode=apply
	puthd in=$wd/tempcalyy value=.5 > /dev/null
	gpcopy vis=$outfile/$source.1.yy out=$vis
	if (-e $vis/gains) mv $vis/gains $vis/gains.yy
	if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.yy
    endif
else if ($polsplit) then
    if (-e $outfile/$source.1.$pollist[1]/gains) then
	puthd in=$outfile/$source.1.$pollist[1]/interval value=.5 > /dev/null
	gpcopy vis=$outfile/$source.1.$pollist[1] out=$wd/tempcal$pollist[1] mode=apply
	puthd in=$wd/tempcal$pollist[1] value=.5 > /dev/null
	gpcopy vis=$outfile/$source.1.$pollist[1] out=$vis
	if (-e $vis/gains) mv $vis/gains $vis/gains.$pollist[1]
	if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.$pollist[1]
    endif
else
    if (-e $outfile/$source.1.xx/gains) then
	puthd in=$outfile/$source.1.xx/interval value=.5 > /dev/null
	gpcopy vis=$outfile/$source.1.xx out=$vis
	mv $vis/gains $vis/gains.xx
    endif
    if (-e $outfile/$source.1.yy/gains) then
	puthd in=$outfile/$source.1.yy/interval value=.5 > /dev/null
	gpcopy vis=$outfile/$source.1.yy out=$vis
	mv $vis/gains $vis/gains.yy
    endif
    puthd in=$wd/tempcal$pollist[1]/interval value=.5 > /dev/null
    gpcopy vis=$wd/tempcal$pollist[1] out=$vis > /dev/null
endif

foreach tfile ($tvis)
    echo "Copying gains to $tfile"
    if (-e $vis/gains) then
	gpcopy vis=$vis out=$tfile
    endif
    if (-e $vis/gains.xx || -e $vis/bandpass.xx) then
	if (-e $vis/gains) mv $vis/gains $vis/tempgains
	if (-e $vis/bandpass) mv $vis/bandpass $vis/tempbandpass
	if (-e $vis/gains.xx) mv $vis/gains.xx $vis/gains
	if (-e $vis/bandpass.xx) mv $vis/bandpass.xx $vis/bandpass
	if (-e $tfile/gains) mv $tfile/gains $tfile/tempgains
	if (-e $tfile/bandpass) mv $tfile/bandpass $tfile/tempbandpass
	gpcopy vis=$vis out=$tfile
	if (-e $tfile/gains) mv $tfile/gains $tfile/gains.xx
	if (-e $tfile/bandpass) mv $tfile/bandpass $tfile/bandpass.xx
	if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.xx
	if (-e $vis/gains) mv $vis/gains $vis/gains.xx
	if (-e $vis/tempbandpass) mv $vis/tempbandpass $vis/bandpass
	if (-e $vis/tempgains) mv $vis/tempgains $vis/gains
    endif
    if (-e $vis/gains.yy || -e $vis/bandpass.yy) then
	if (-e $vis/gains) mv $vis/gains $vis/tempgains
	if (-e $vis/bandpass) mv $vis/bandpass $vis/tempbandpass
	if (-e $vis/gains.yy) mv $vis/gains.yy $vis/gains
	if (-e $vis/bandpass.yy) mv $vis/bandpass.yy $vis/bandpass
	if (-e $tfile/gains) mv $tfile/gains $tfile/tempgains
	if (-e $tfile/bandpass) mv $tfile/bandpass $tfile/tempbandpass
	gpcopy vis=$vis out=$tfile
	if (-e $tfile/gains) mv $tfile/gains $tfile/gains.yy
	if (-e $tfile/bandpass) mv $tfile/bandpass $tfile/bandpass.yy
	if (-e $vis/bandpass) mv $vis/bandpass $vis/bandpass.yy
	if (-e $vis/gains) mv $vis/gains $vis/gains.yy
	if (-e $vis/tempbandpass) mv $vis/tempbandpass $vis/bandpass
	if (-e $vis/tempgains) mv $vis/tempgains $vis/gains
    endif
end

if ($outsource && "$tvis[1]" != "") then
    foreach tfile ($tvis)
	echo "Applying flags for $tfile..."
        uvaver vis="$wd/tvis$tfile*" out=$wd/tvis$tfile options=relax,nocal,nopass,nopol >& /dev/null
	uvaflag vis=$tvis tvis=$wd/tvis$tfile > /dev/null
    end
endif

#

goto finish

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
rm -rf $wd
exit 0 

fail:
echo "Calibration failed for unknown reason! Now exiting..."
#rm -rf $wd
exit 1
