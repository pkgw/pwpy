#! /usr/bin/tcsh -f
# $Id$
onintr fail

if ($#argv == 0) then
    echo "NEWRFI.CSH"
    echo "newrfi.csh is a tool to build count specta (spectral occupancy spectra). This is the base tool for"
    echo "performing spectral occupancy based flagging. This style of flagging is effective against persistent"
    echo "RFI (lasting longer than a few minutes), as well as spectral corruption. newrfi has no program"
    echo "dependancies, other than MIRIAD. newrfi places a 'specdata' file in the folder containing the MIRIAD"
    echo "visibilities."
    echo " "
    echo "Calling sequence: newrfi.csh vis=vis interval=interval options={cal, pass, pol, normal, nocal, nopass, nonormal, nopol, crosspol, nocrosspol}"
    echo "REQUIRED INPUTS:"
    echo "vis - Name of the files that contain visibilities"
    echo "OPTIONAL INPUTS:"
    echo "interval - length (in minutes) to integrate count spectra."
    echo "Options:"
	echo "nocal,nopass,nopol - don't apply gains corrections to data before processing (default)"
	echo "cal,pass,pol - do apply gains corrections to data before processing"
	echo "normal - normalize data before analysis (default)"
	echo "nonormal - don't normalize data"
	echo "nocrosspol - don't process  XY and YX data (default)"
	echo "crosspol - process all polarization data"
    exit 0
endif


set date1 = `date +%s.%N`

#Preassigment of variables so that optional inputs will revert to defaults
set vis #File to be scanned
set inttime = 5 #Integration time
set nonormal = "normal" #Switch to normalize spectra
set nocal = "nocal" #Switch to apply gains to data
set nopass = "nopass" #Switch to apply bandpass corrections to data
set nopol = "nopol" #Switch to apply polarization corrections to data
set crosspol = "nocross" #Swtich to exclude XY and YX polarization - should be done if bandpass and pol correction information are not available
set autoedge = 0
set autoedgechan = 100

varassign:

if ($#argv == 0) then
    echo "FATAL ERROR: No inputs detected..."
    exit 1
endif

if ("$argv[1]" =~ 'vis='*) then
    set vis = "`echo '$argv[1]/' | sed 's/vis=//'`"
    set vis = (`echo $vis | sed 's/\/ / /g' | sed 's/\(.*\)\//\1/g' | tr ',' ' '`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'interval='*) then
    set inttime = `echo "$argv[1]" | sed 's/interval=//g' | awk '{print $1*1}'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'options='*) then
    set options = `echo "$argv[1]" | sed 's/options=//g' | tr ',' ' ' | tr '[A-Z]' '[a-z]'`
    set badopt
    foreach option (`echo $options`)
	if ($option == "normal") then
	    set nonormal = "normal"
	else if ($option == "nonormal") then
	    set nonormal = "nonormal"
	else if ($option == "cal") then
	    set nocal
	else if ($option == "nocal") then
	    set nocal = "nocal"
	else if ($option == "pass") then
	    set nopass
	else if ($option == "nopass") then
	    set nopass = "nopass"
	else if ($option == "pol") then
	    set nopol
	else if ($option == "nopol") then
	    set nopol = "nopol"
	else if ($option == "crosspol") then
	    set crosspol = "crosspol"
	else if ($option == "autoedge") then
	    set autoedge = 1
	else if ($option == "noautoedge") then
	    set autoedge = 0
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

# Variables have been assigned, check the integrity of variables



if ("$vis" == "") then #Are there any files?
    echo "FATAL ERROR: No input files..."
    exit 1
else
    foreach file (`echo $vis`)
	if (! -e $file/visdata) echo "FATAL ERROR: $file has no visibilities!"
	if (! -e $file/visdata) exit 1
    end
endif

if ("$inttime" == 0) then #Does the time interval make sense?
    echo "Interval time not recognized, setting interval equal to 10 minutes."
    set inttime = 10
endif

set wd = `mktemp -d rfiXXXXX`
if ($wd == "") then #Can the program create a temp directory?
    echo "FATAL ERROR: Problems creating temp directory. Make sure you have permissions for the current directory. Now exiting..."
    goto finish
endif

#Preliminary Error checking should be good at this point, preperation of the data can begin, program moves calibrated/normalized data to a temp directory
set options = ($nocal $nopass $nopol)
echo "Beginning data processing..."

foreach file (`echo $vis`)
    if ($nonormal != "nonormal") then
	echo "Beginning normalization of data..."
	uvcal vis=$file options=fxcal,`echo $options | tr ' ' ','` select='pol(xx)' out=$wd/$file-xpol >& /dev/null
	uvcal vis=$file options=fxcal,`echo $options | tr ' ' ','` select='pol(yy)' out=$wd/$file-ypol >& /dev/null
    else if ($crosspol != "crosspol") then
	uvaver vis=$file options=relax,`echo $options | tr ' ' ','` select='pol(xx)' out=$wd/$file-xpol > /dev/null
    	uvaver vis=$file options=relax,`echo $options | tr ' ' ','` select='pol(yy)' out=$wd/$file-ypol > /dev/null
    else
	uvaver vis=$file options=relax,`echo $options | tr ' ' ','` select='pol(xx,xy)' out=$wd/$file-xpol > /dev/null
	uvaver vis=$file options=relax,`echo $options | tr ' ' ','` select='pol(yy,yx)' out=$wd/$file-ypol > /dev/null
    endif
    echo "Preliminary processing for $file complete..."
end

#Data is prepared, file scanning begins

foreach file (`echo $vis`)

    #First step is collecting meta-data, program attempts to speed this up by collecting metadata from a single antenna first
    echo "Performing Az/El/UTC data scan..."
    set ants = ( `uvlist vis=$file options=list | sed '1,9d' | awk '{print $7,$8}'` )
    uvlist vis=$file select="ant($ants[1])($ants[2])" options=list recnum=0 | sed '1,9d' | awk '{if ($1*1 > 0 && $3 != last) {printf "%s %3.2f %3.2f\n",$3,(540-$12)%360,$13*1; last=$3}}' | awk '{print $2,$3}' > $wd/$file.obstimes #Get Az/El information
    echo "Scanning source/freq information..."
    uvlist vis=$file recnum=0 select="ant($ants[1])($ants[2])" options=var,full | sed -e '/Header/b' -e '/source  :/b' -e '/sfreq   :/b' -e '/sdf     :/b' -e '/dec     :/b' -e '/ra      :/b' -e '/freq    :/b' -e d | uniq | tr -d '()' | awk '{if ($1 == "Header") printf "\n%s %s\n",$1,$4; else printf "%s ",$0}' | sed '1d' | awk '{if ($1 == "Header") system("julian options=quiet date="$2); else print $0}' | grep '.' | sed 's/ : /   /g' > $wd/details #Get source/freq information
    #Convert dates to Julian Date, and combine metadata
    set idx = 1
    set lim = `wc -l $wd/details | awk '{print $1}'`
    rm -f $wd/moredetails
    while ($idx <= $lim)
	set vars = (`sed -n {$idx}p $wd/details` "dummy")
	if ("$idx$#vars" == 12) then	
	    set time = `echo $vars[1] | awk '{printf "%5.6f\n",$1-2400000.5}'`
	else if ("$#vars$idx" == "2$lim") then
	    echo $time $pvars >> $wd/moredetails
	    set time = `echo $vars[1] | awk '{printf "%5.6f\n",$1-2400000.5}'`
   	    echo $time $pvars >> $wd/moredetails
	else if ($#vars == 2) then
	    echo $time $pvars >> $wd/moredetails
	    set time = `echo $vars[1] | awk '{printf "%5.6f\n",$1-2400000.5}'`
	endif
	while ($#vars > 2)
	    if ($vars[1] == "sdf") then
		set sdf = $vars[2]
		shift vars; shift vars
	    else if ($vars[1] == "sfreq") then
		set sfreq = $vars[2]
		shift vars; shift vars
	    else if ($vars[1] == "source") then
		set source = `echo $vars[2] | sed 's/://'`
		shift vars; shift vars
	    else if ($vars[1] == "ra") then
		set ra = $vars[2]
		shift vars; shift vars
	    else if ($vars[1] == "dec") then 
		set dec = $vars[2]
		shift vars; shift vars
	    else if ($vars[1] == "freq") then
		set freq = $vars[2]
		shift vars; shift vars
	    else
		shift vars
	    endif
	end
	if ($idx == 1) then
	else if ($idx == 2) then
	    set pvars = ($sdf $sfreq $freq $source $ra $dec)
	else if ("$sdf $sfreq $freq $source $ra $dec" != "$pvars") then
	    set pvars = ($sdf $sfreq $freq $source $ra $dec)
	endif
	@ idx++
    end
    cat $wd/moredetails | uniq > $wd/emoredetails

    perl -e ' $separator="\t"; ($file1, $file2) = @ARGV; open (F1, $file1) or die; open (F2, $file2) or die; while (<F1>) { if (eof(F2)) { warn "WARNING: File $file2 ended early\n"; last } $line2 = <F2>; s/\r?\n//; print "$_$separator$line2" } if (! eof(F2)) { warn "WARNING: File $file1 ended early\n"; } warn "Metadata scanning complete...\n" ' $wd/emoredetails $wd/$file.obstimes | sort -nk1 > $wd/meta.full
    #Preliminary metadata has been built
    echo "Processing $file, detecting high channels for each spectrum." 

    set chan
    set ilim = 0
    set grabchan = (`uvlist vis=$file options=var | grep nchan | tr ':' ' '`)

    while ($ilim == 0 && $#grabchan != 0)
	if ($grabchan[1] == "nchan") set ilim = $grabchan[2]
	shift grabchan
    end

    if ($autoedge) then
	if (`echo $sfreq $freq | awk '{if ($1 == $2) print "go"}'` == "go") then
	    if (-e $wd/$file-xpol/visdata) uvflag vis=$wd/$file-xpol edge=1,$autoedgechan,0 options=none flagval=f > /dev/null
	    if (-e $wd/$file-ypol/visdata) uvflag vis=$wd/$file-ypol edge=1,$autoedgechan,0 options=none flagval=f > /dev/null
	else if (`echo $ilim $sdf $sfreq $freq | awk '{if ((($1-1)*$2)+$3 < $freq) print "go"}'` == "go") then
	    if (-e $wd/$file-xpol/visdata) uvflag vis=$wd/$file-xpol edge=$autoedgechan,0,0 options=none flagval=f > /dev/null
	    if (-e $wd/$file-ypol/visdata) uvflag vis=$wd/$file-ypol edge=$autoedgechan,0,0 options=none flagval=f > /dev/null
	else
	    if (-e $wd/$file-xpol/visdata) uvflag vis=$wd/$file-xpol edge=$autoedgechan,$autoedgechan,3 options=none flagval=f > /dev/null
	    if (-e $wd/$file-ypol/visdata) uvflag vis=$wd/$file-ypol edge=$autoedgechan,$autoedgechan,3 options=none flagval=f > /dev/null
	endif
    endif

    set idx = 1

    #Build an empty spectra to reset count spectra each time cycle
    while ($idx <= $ilim)
	set chan = ($chan 0)
	@ idx++
    end

    #Dump uvlist data to a temp file
    if (-e $wd/$file-xpol/visdata) then
	uvlist vis=$wd/$file-xpol recnum=0 options=stat select=-auto > $wd/temp.log
	grep "CHAN" $wd/temp.log | tr -d "CHAN" > $wd/temp.xlist1
	sed 's/:/ /g' $wd/temp.log | awk '{if ($1" "$2 == "Data values") date=$4; else if ($7 == "XX" || $7 == "XY") printf "%s%.6f ABC%2.0d ABC%2.0d %s\n",date,($2/24+$3/1440+$4/86400),$5*1,$6,$7}' | sed -e 's/ABC /0/g' -e 's/ABC//g' > $wd/temp.xlist2
	echo "X-pol scan complete..."
    else
	echo "No X-pol data found..."
    endif

    if (-e $wd/$file-ypol/visdata) then
	uvlist vis=$wd/$file-ypol recnum=0 options=stat select=-auto > $wd/temp.log
	grep "CHAN" $wd/temp.log | tr -d "CHAN" >> $wd/temp.xlist1
	sed 's/:/ /g' $wd/temp.log | awk '{if ($1" "$2 == "Data values") date=$4; else if ($7 == "YX" || $7 == "YY") printf "%s%.6f ABC%2.0d ABC%2.0d %s\n",date,($2/24+$3/1440+$4/86400),$5*1,$6,$7}' | sed -e 's/ABC /0/g' -e 's/ABC//g' >> $wd/temp.xlist2
	echo "Y-pol scan complete..."
    else
	echo "No Y-pol data found..."
    endif

    #Check to see if metadata parameters (number of unique tags) match. If not, rerun metadata collection WITHOUT shortcut (process all data)
    if (`awk '{print $1}' $wd/temp.xlist2 | sort -u | wc -l` != `wc -l $wd/$file.obstimes | awk '{print $1}'`) then
	echo "Initial obstimes detection failed, moving to brute force method..."
	uvlist vis=$file options=list recnum=0 | sed '1,9d' | awk '{if ($1*1 > 0 && $3 != last) {printf "%s %3.2f %3.2f\n",$3,(540-$12)%360,$13*1; last=$3}}' | awk '{print $2,$3}' > $wd/$file.obstimes #Get Az/El information
	uvlist vis=$file recnum=0 options=var,full | sed -e '/Header/b' -e '/source  :/b' -e '/sfreq   :/b' -e '/sdf     :/b' -e '/dec     :/b' -e '/ra      :/b' -e '/freq    :/b' -e d | uniq | awk '{if ($1 == "Header") printf "\n%s %s\n",$1,$4; else printf "%s ",$0}' | sed '1d' | awk '{if ($1 == "Header") system("julian options=quiet date="$2); else print $0}' | grep '.' | sed 's/ : /   /g' > $wd/details
	set idx = 1
	set lim = `wc -l $wd/details | awk '{print $1}'`
	rm -f $wd/moredetails
	while ($idx <= $lim)
	    set vars = (`sed -n {$idx}p $wd/details` "dummy")
	    if ("$idx$#vars" == 12) then	
		set time = `echo $vars[1] | awk '{printf "%5.6f\n",$1-2400000.5}'`
	    else if ("$#vars$idx" == "2$lim") then
		echo $time $pvars >> $wd/moredetails
		set time = `echo $vars[1] | awk '{printf "%5.6f\n",$1-2400000.5}'`
		echo $time $pvars >> $wd/moredetails
	    else if ($#vars == 2) then
		echo $time $pvars >> $wd/moredetails
		set time = `echo $vars[1] | awk '{printf "%5.6f\n",$1-2400000.5}'`
	    endif
	    while ($#vars > 2)
		if ($vars[1] == "sdf") then
		    set sdf = $vars[2]
		    shift vars; shift vars
		else if ($vars[1] == "sfreq") then
		    set sfreq = $vars[2]
		    shift vars; shift vars
		else if ($vars[1] == "source") then
		    set source = `echo $vars[2] | sed 's/://'`
		    shift vars; shift vars
		else if ($vars[1] == "ra") then
		    set ra = $vars[2]
		    shift vars; shift vars
		else if ($vars[1] == "dec") then 
		    set dec = $vars[2]
		    shift vars; shift vars
		else if ($vars[1] == "freq") then
		    set freq = $vars[2]
		    shift vars; shift vars
		else
		    shift vars
		endif
	    end
	    if ($idx == 1) then
	    else if ($idx == 2) then
		set pvars = ($sdf $sfreq $freq $source $ra $dec)
	    else if ("$sdf $sfreq $freq $source $ra $dec" != "$pvars") then
		set pvars = ($sdf $sfreq $freq $source $ra $dec)
	    endif
	    @ idx++
	end
	cat $wd/moredetails | uniq > $wd/emoredetails
	
	perl -e ' $separator="\t"; ($file1, $file2) = @ARGV; open (F1, $file1) or die; open (F2, $file2) or die; while (<F1>) { if (eof(F2)) { warn "WARNING: File $file2 ended early\n"; last } $line2 = <F2>; s/\r?\n//; print "$_$separator$line2" } if (! eof(F2)) { warn "WARNING: File $file1 ended early\n"; } warn "Metadata scanning complete...\n" ' $wd/emoredetails $wd/$file.obstimes | sort -nk1 > $wd/meta.full
    endif
    #End check/repeat processing, metadata integrity now confirmed
    set odates = (`awk '{if ($1 != last) {last = $1; print $1}}' $wd/temp.xlist2 | sed 's/0\./  /g' | awk '{print $1}' | uniq`)

    echo -n 'sed ' > $wd/julday.source
    #Substitute dates for Julian dates in uvlist data
    foreach odate (`echo $odates`)
	echo -n "-e 's/"`julian date=$odate | grep 'Modified' | awk '{print $1"0/"int($6)"/g"}'`"' " >> $wd/julday.source
    end

    echo "$wd/temp.xlist2" >> $wd/julday.source
    source $wd/julday.source > $wd/temp.xlist3
    cp $wd/$file.obstimes $wd/obstimes
    awk '{print $2"-"$3"-"$4}' $wd/temp.xlist2 | sort -u | tr '-' ' ' > $wd/baselist
    perl -e ' $separator="\t"; ($file1, $file2) = @ARGV; open (F1, $file1) or die; open (F2, $file2) or die; while (<F1>) { if (eof(F2)) { warn "WARNING: File $file2 ended early\n"; last } $line2 = <F2>; s/\r?\n//; print "$_$separator$line2" } if (! eof(F2)) { warn "WARNING: File $file1 ended early\n"; } warn "Scanning complete. Building count spectra...\n" ' $wd/temp.xlist3 $wd/temp.xlist1 | sort -nk1 > $wd/temp.full
    
    #Build source files for spectra processing. antspec performs counts baseline-by-baseline, storing each spectra in a unique array. antreset resets all arrays back to their "0" value
    awk '{print "set "$3$1$2" = ($chan)"}' $wd/baselist > $wd/antreset.source
    awk '{print "set mc"$3$1$2" = 0"}' $wd/baselist >> $wd/antreset.source
    source $wd/antreset.source
    
    awk '{print "echo "$1*1" "$2*1" "$3" $times[1] $pos[3] $pos[1] $pos[2] $mlist[2] $mlist[3] $mlist[4] $mlist[5] $mlist[6] $mlist[7] $mc"$3$1$2" $"$3$1$2}' $wd/baselist > $wd/antspec.source

    set finaltime = `tail -n 1 $wd/meta.full | awk '{print $1}'`
    set idx = 1
    #Below is the code that performs the loop operation for each time cycle
################################################################
    while (`wc -l $wd/meta.full | awk '{print $1}'` != 0)
	set times = (`head -n 1 $wd/meta.full | awk '{printf "%5.6f %5.6f\n",$1,($1+(inttime/1440))}' inttime=$inttime`)
	set mlist = (`awk '{if ($1 > time) next; else print $0}' time=$times[1] $wd/meta.full | head -n 1`)
	awk '{if ($1 > end) next; else print $0}' end=$times[2] $wd/temp.full > $wd/temp.raw
	set mcount = `wc -l $wd/temp.raw | awk '{print $1}'`
	set pos = (`awk '{if (($1-start) > (inttime/1440)) next; else print $1,$8,$9}' inttime=$inttime start=$times[1] $wd/meta.full | awk '{SUM1 += 1; SUM2 += $2; SUM3 += $3; if (FTIME < $1) FTIME = $1} END {print SUM2/SUM1, SUM3/SUM1, FTIME}'`)

	awk '{print "@ mc"$4$2$3"++ "$4$2$3"["$5"]++ "$4$2$3"["$6"]++ "$4$2$3"["$7"]++ "$4$2$3"["$8"]++ "$4$2$3"["$9"]++ "$4$2$3"["$10"]++ "$4$2$3"["$11"]++ "$4$2$3"["$12"]++ "$4$2$3"["$13"]++ "$4$2$3"["$14"]++ "$4$2$3"["$15"]++ "$4$2$3"["$16"]++ "}' $wd/temp.raw| sed 's/ ......\[]++//g' > $wd/temp.source

	source $wd/temp.source > /dev/null
	source $wd/antspec.source >> $wd/$file.specdata
	source $wd/antreset.source > /dev/null

	awk '{if (($1-start) > (inttime/1440)) print $0}' start=$times[1] inttime=$inttime $wd/meta.full > $wd/meta.full2
	if (`wc -l $wd/meta.full2 | awk '{print $1}'` != 0) then
	    echo "Moving on to next time cycle... "
	    echo $pos[3] $finaltime | awk '{printf "%s%2.0d%s%2.0d%s%2.0d%s%2.0d%s%2.0d%s%2.0d \n","Current cycle end time - ",int($1*24)%24,":",int(($1*1440)%60),":",int(($1*86400)%60),"   Final time - ",int($2*24)%24,":",int(($2*1440)%60),":",int(($2*86400)%60)}' |  sed 's/: /:0/g' | sed 's/ :/0:/g'
	endif
	mv $wd/meta.full2 $wd/meta.full
	sed '1,'$mcount'd' $wd/temp.full > $wd/temp.full2 # Cull out any data that has been processed. Slows down shorter operation, but speeds up longer processing operations.
	mv $wd/temp.full2 $wd/temp.full
    end
###############################################################

    mv $wd/$file.specdata $file/specdata    
    echo "$file scanning complete! "`wc -l $file/specdata | awk '{print $1}'`" spectra built." # File processed, move on to the next one
end

set times = (`date +%s.%N | awk '{print int(($1-date1)/60),int(($1-date1)%60)}' date1=$date1`)
echo "Scanning process took $times[1] minute(s) $times[2] second(s)."

rm -r $wd

finish:

exit 0

fail:
rm -rf $wd
echo "Houston, we have a problem..."
exit 1
