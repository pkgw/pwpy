#! /bin/tcsh -f
# simple mapping script 			september 06 - jrf
# give one argument to start =  ave, flag, cal, invert, plot, selfcal
#
if ($#argv < 2) then
 echo "Must give a start point (ave, flag, cal, invert, plot or selfcal) and vis filename:"
 exit 0
endif

set start = $1
set vis = $2

set cal=3C380; set sou=$vis; set freq=1628; set pol=xx

set cal=$cal		# specify source and cal filenames
set vis=$sou
set object=$sou.$pol
set fullcal = scan-$cal.ephem-$freq
set fullvis = scan-$vis.ephem-$freq
#
set int=1		# selfcal interval (min)
set scopt=pha		# option = pha or amp (phase+amp)
set sup=0		# natural weighting (high sensitivity - bigger beam)
set line=chan,1,600,200	# extract line - channels to keep from source dataset
set cline = chan,1
set mline = $cline

set refant=1		# choose good antenna for selfcal reference
set imsize=512		# number of cells in image imfit object=point region="relcen,arcsec,box(200,-200,-200,200)" in=3c84.1430.yy.cm

set cell=10		# cell size in arcsec
set map=cm		# plot the cleaned map (source.cm)
set contplt = /xs	
set arc=600		# fov of displayed plot in arcsec
set scint=$int		# selfcal interval 
set clip=0		# clip out negative amplitudes 
set olay = ~/bin/olay	# cross to overlay for center of field

alias hit 'echo Hit return to continue; set yn = $<'
goto $start

ave:		   # uvavr calibrator files to minimize size - keep both pols
if (-e $cal) then
  echo "$cal exists. remake it? [n]"
  if ($< == y) then
   rm -rf $cal
   uvaver vis=$fullcal out=$cal options=nocal interval=.5 line=$line select="pol(xx,yy),-auto"
   echo "--------------------------------------"
   echo created $cal 
  endif
else
   uvaver vis=$fullcal out=$cal options=nocal interval=.5 line=$line select="pol(xx,yy),-auto"
   echo "--------------------------------------"
   echo created $cal 
endif

if (-e $vis) then
  echo "$vis exists. remake it? [n]"
  if ($< == y) then
   rm -rf $vis
   uvaver vis=$fullvis out=$vis options=nocal interval=.5 line=$line select="pol(xx,yy),-auto"
   echo "--------------------------------------"
   echo recreated $vis 
  endif
else
   uvaver vis=$fullvis out=$vis options=nocal interval=.5 line=$line select="pol(xx,yy),-auto"
   echo "--------------------------------------"
   echo created $vis 
endif
goto cal

flag:			# must specify bad data manually
uvflag vis=$cal flagval=f select='ant(6,14,31),pol(xx)'
uvflag vis=$vis flagval=f select='ant(6,14,31),pol(xx)'
uvflag vis=$cal flagval=f select='ant(19,24,28),pol(yy)'
uvflag vis=$vis flagval=f select='ant(19,24,28),pol(yy)'
#exit 0

cal:			# calibrate source data using cal data selfcal gain/phase
mselfcal vis=$cal refant=$refant line=$cline interval=$int options=$scopt minants=3 select="pol($pol)"
puthd in=$cal/interval value=0.1
gpcopy vis=$cal out=$vis mode=copy options=nopol,nopass
gpplt vis=$vis nxy=6,4 device=/xs yaxis=pha yrange=-180,180 options=wrap
echo "show amp? [n]"
if ($< == y) gpplt vis=$vis nxy=4,2 device=/xs yaxis=amp

invert:			# grid and transform visibilities into brightness map
foreach type (map beam clean cm)
   if (-e $object.$type)  rm -r $object.$type
end

invert vis=$vis line=$mline map=$object.map beam=$object.beam cell=$cell \
	imsize=$imsize sup=$sup select="pol($pol)"
clean map=$object.map beam=$object.beam niters=1000 gain=0.1 out=$object.clean 
restor map=$object.map beam=$object.beam model=$object.clean out=$object.cm

fit:
imfit in=$object.cm object=point | tee junk

set offset = (`grep "Offset" junk | awk '{printf "%5.1f %5.1f\n", $4,$5}'`)
set poserr = (`grep "al err" junk | awk '{printf "%5.1f %5.1f\n", $4,$5}'`)
set beamsize = (`grep "Beam Maj" junk | awk '{printf "%5.0f %5.0f\n", $6,$7}'`)

echo " sou  cal  pol beamsize  offset  poserr" | tee -ia junk
echo "$sou $cal $pol $beamsize $offset $poserr" | tee -ia junk

cp $olay olay
#echo box arcsec arcsec "Offset=$offset[1]_$offset[2]_$sou-$cal" yes $offset[1] $offset[2] $poserr[1] $poserr[2] >> olay

mv junk {$sou}-$freq.$cal.$pol.fit

plot:			# display map
cgdisp slev=p,1 in=$object.$map,$object.$map \
   region=relcenter,arcsec,box"($arc,-$arc,-$arc,$arc)" device=$contplt \
   labtyp=arcsec options=mirr,full csize=1,1,1 olay=olay \
   type=contour,pix slev=p,1 levs1=15,30,60,90 \
#   device={$sou}-$freq.$cal.$pol.ps/vcps
 cgdisp slev=p,1 in=$object.$map,$object.$map \
   region=relcenter,arcsec,box"($arc,-$arc,-$arc,$arc)" device=$contplt \
   labtyp=arcsec options=mirr,full csize=1,1,1 olay=olay \
   type=contour,pix slev=p,1 levs1=15,30,60,90 \
   device={$sou}-$freq.$cal.$pol.ps/vcps

echo "sent plot and fit to printer? [n]"
if ($< == y) then
 lp -oraw {$sou}-$freq.$cal.$pol.ps
 lp {$sou}-$freq.$cal.$pol.fit
endif 

exit 0

selfcal:		# selfcal (in the true sense) the imaged data
echo "selfcal? (n)"; set yn = $<
if ($yn == y) then
  echo "Selfcal interval [default=$scint]: "; set ans=$<
  if ($ans != "") set scint = $ans
  echo "amp or pha? [default=$scopt]: "; set cl=$<
  if ($cl != "") set scopt = $cl
  selfcal vis=$vis model=$object.clean interval=$scint refant=$refant \
	minants=3 options=$scopt line=$mline clip=$clip
  gpplt vis=$vis device=/xs yaxis=pha nxy=2,4; echo "show amp? [n]"
  if ($< == y)  gpplt vis=$vis device=/xs nxy=2,4
  goto invert
endif

