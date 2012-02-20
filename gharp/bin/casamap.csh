#!/bin/tcsh 

set wdir=ssa-fitmap

set f1=4200
set f2=""
#set slist = (3c84)
set slist = "3c119 3c147 3c48 casa 3c138 3c395 3c84"
set slist=$1
set clist=$2
set sc=$3

set pwd = `pwd`    # should be /data/user1b/rick/SSA
set set root = mosfx; set bw=-100

set log = cmap.log
echo " "  | tee -ia $log
echo "`date` - casamap begins for $wdir" | tee -ia $log

goto map

# Flagging loop
rfi:
cd $pwd/$wdir
foreach freq ($f1)
 set cor=a; if ($freq == $f2) set cor=c
 foreach sou (`echo $slist`)
  set vis = $root{$cor}-$sou-$freq$bw
  flag-4200-450-550 $vis
  #this is bad news --- newrfisweep.csh vis=$vis options=autoedge scans=4 subint=999
 end  # loop over sou
end   # loop over freq

# Loop that generates maps
map:
cd $pwd/$wdir
foreach freq ($f1)
 set cor=a 
 set cal = $root{$cor}-$clist-$freq$bw
 foreach sou  (`echo $slist`) 
   # Break the visibility file into x and y pols
   set vis = $root{$cor}-$sou-$freq$bw
   rm -r $vis-xx $vis-yy
   uvcat vis=$vis select=pol"(xx)" out=$vis-xx
   uvcat vis=$vis select=pol"(yy)" out=$vis-yy
	# Generate a beam for the standard observation 
	# and show CasA image using this cal
	cd /exports/user1/gerry/0817/ssa/4200 
	$sc 7 >> /dev/null
	rm -r *.cm
	cd $pwd/$wdir
   # Calibrate the new file with the same calibrations used for CasA above
   gpcopy vis=../ssa/4200/casa-4200-xx out=$vis-xx
   gpcopy vis=../ssa/4200/casa-4200-yy out=$vis-yy
   rm -r junk.xx junk.yy
   uvcat vis=$vis-xx out=junk.xx 
   uvcat vis=$vis-yy out=junk.yy
   rm -r $vis-xx-cald $vis-yy-cald
   uvaver vis=junk.xx out=$vis-xx-cald line=chan,1,750,100
   uvaver vis=junk.yy out=$vis-yy-cald line=chan,1,750,100

   # Generate image of vis with appropriate filenames to match fitmaps.csh
   set mapname="$sou-$freq-$clist-maps"
   rm -r $mapname
   mkdir $mapname
   cd $mapname
   ../pretty-picture ../$vis-xx-cald,../$vis-yy-cald $sou-$freq-$cal "niters=700"
 end  # loop over sou
end  # loop over clist

fit:
cd $pwd/$wdir
$pwd/fitmaps.csh
echo " "
echo "`date` - fitmap ends for $wdir" | tee -ia $log

exit 0
