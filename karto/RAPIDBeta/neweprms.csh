#! /usr/bin/tcsh -f
#
# $Id$
#    exit script cleanly  on interrupt

onintr fail

set vis = $1
set plim = $2
set plim2 = $3
set clim = $4
set clim2 = $5
set stime = $6
set etime = $7

if ("$plim" == "") set plim = 20
if ("$plim2" == "") set plim2 = 0.001
if ("$clim" == "") set clim = 180
if ("$clim2" == "") set clim2 = 0

set wd = `mktemp -d "eprmsXXXX"`

set timerange
if ("$stime" != "") set timerange = "time($stime,$etime),"
#    log phase vs time for given scan and pol for all baselines
uvplt vis=$vis device=/null axis=time,pha options=log,2pass,unwrap log=$wd/xphalog select="window(1),pol(xx),""$timerange""-auto" >& /dev/null 
uvplt vis=$vis device=/null axis=time,pha options=log,2pass,unwrap log=$wd/yphalog select="window(1),pol(yy),""$timerange""-auto" >& /dev/null

if (-e $wd/xphalog) then
sed 1,7d $wd/xphalog | grep 'Baseline' | tr -d '-' | awk '{print ($2*1000)+$3,$2,$3,$5}' | sort -nk1 | awk '{print $2,$3,$4}' > $wd/xbase
sed 1,7d $wd/xphalog | grep -v 'Baseline' > $wd/xpha
endif
if (-e $wd/yphalog) then
sed 1,7d $wd/yphalog | grep 'Baseline' | tr -d '-' | awk '{print ($2*1000)+$3,$2,$3,$5}' | sort -nk1 | awk '{print $2,$3,$4}' > $wd/ybase
sed 1,7d $wd/yphalog | grep -v 'Baseline' > $wd/ypha
endif
 
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
	echo $basestats $baseinfo $pol | awk '{if ($1^2 > clim^2 || $1^2 < clim2^2 || $2 > plim || $2 < plim2) print $3"-"$4}' clim=$clim plim=$plim clim2=$clim2 plim2=$plim2 >> $wd/baselist2
    end
    set antlist = (`sed 's/-/ /g' $wd/baselist2 | awk '{printf "%s\n%s\n",$1,$2}' | sort -n | uniq`)
    while (`wc -w $wd/baselist2 | awk '{print $1}'`)
	set idx = 0
	set nant = 0
	set mcount = 0
	set icount = 0
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
#	set flagcmd = "ant($ant)("`sed 's/-/ /g' $wd/baselist2 | awk '{if ($1 == ant) printf "%s,",$2; else if ($2 == ant) printf "%s,",$1} END {printf "%s\n",")"}' ant=$ant | sed 's/,)/)/g'`",pol($pol$pol)"
	echo $flagcmd
	set antlist[$nant]
	set antlist = (`echo $antlist`)
	sed 's/-/ /g' $wd/baselist2 | awk '{if ($1 != ant && $2 != ant) print $1"-"$2}' ant=$ant > $wd/baselist3
	mv $wd/baselist3 $wd/baselist2
    end
end

fail:

rm -rf $wd

exit 0
