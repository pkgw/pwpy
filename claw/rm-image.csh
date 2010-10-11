#! /usr/bin/tcsh
# Written by bgaensler, modified by claw 25sep09
#
# Script to make multi-channel images from calibrated uv data
# Scaled cell, fwhm to appropriate values for ata
# Assumes files already split in freq and leakage calibrations tables present.  Each freq chunk has multiple chans, though.

# parameters
if $#argv == 0 then
  set source = hexa-3c286-hp0-1430  # default
else
  set source = $argv[1]  # or first argument
endif
set freq = 1430
set diam = 20
set imsize = 1024
set nchan = 16
set boxlo = `echo $imsize'/2 - 60' | bc`
set boxhi = `echo $imsize'/2 + 60' | bc`
#set imgparams = "robust=0 cell=10 select=-shadow($diam),ti(09SEP19:18:00:00,09SEP20:15:00:00),ti(09NOV27:16:00:00,09NOV27:23:59:00),ti(09DEC04:17:30:00,09DEC04:23:59:00)" # fwhm=440,150"  # cuts bad cal in day 1,2,3
set imgparams = "robust=0 cell=10 select=-shadow($diam)"
set restorparams = ''   # fwhm=440,150 pa=74 # for 1230 (m87)
#set restorparams = 'fwhm=440,150 pa=74'  # for 1230 (m87)
set visall = `ls -df $source-? $source-?? $source-??? | awk '{printf("%s,",$1)}' ; echo`

#  clean up
\rm -fr $source.?{cln,map,cmp}
\rm -fr $source.?{cln,map,cmp}.imsub
\rm -fr $source.beam
\rm -fr $source-?.?{cln,map,cmp}
\rm -fr $source-?.?{cln,map,cmp}.imsub
\rm -fr $source-?.beam
\rm -fr $source-??.?{cln,map,cmp}
\rm -fr $source-??.?{cln,map,cmp}.imsub
\rm -fr $source-??.beam
\rm -fr $source-???.?{cln,map,cmp}
\rm -fr $source-???.?{cln,map,cmp}.imsub
\rm -fr $source-???.beam
\rm -f t???vs
\rm -f t????vs
\rm -f t?????vs

set regcommand = region=abspix,box'('$boxlo,$boxlo,$boxhi,$boxhi')'  # sfind not working?!

# need to check that bins have data.  also need short file names for invert
set n = 1
set rand = `date | cut -c 18-19`
foreach f (`ls -df ${source}-? ${source}-?? ${source}-???`)
    set records = `uvindex vis=$f | grep 'Total number of records' | awk '{printf("%d\n",$6)}'`
    if ( $records > 0 ) then
	ln -s $f t${rand}${n}vs
    else
	echo 'No records in '$f'. Skipping.'
    endif
    @ n = ($n + 1)
end

#   Make one map
invert vis=t${rand}\*vs map=$source.imap,$source.qmap,$source.umap,$source.vmap beam=$source.beam imsize=$imsize \
stokes=i,q,u,v options=mfs,double $imgparams
set rms = `gethd in=$source.imap/rms`
set icut = `echo "4.5*$rms" | bc -l`
clean map=$source.imap beam=$source.beam out=$source.icmp niters=500 cutoff=$icut $regcommand | tail -2
clean map=$source.qmap beam=$source.beam out=$source.qcmp niters=300 cutoff=$icut $regcommand | tail -2
clean map=$source.umap beam=$source.beam out=$source.ucmp niters=300 cutoff=$icut $regcommand | tail -2
restor model=$source.icmp beam=$source.beam map=$source.imap out=$source.icln $restorparams | tail -2
restor model=$source.qcmp beam=$source.beam map=$source.qmap out=$source.qcln $restorparams | tail -2
restor model=$source.ucmp beam=$source.beam map=$source.umap out=$source.ucln $restorparams | tail -2
imsub in=$source.icln out=$source.icln.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"
imsub in=$source.qcln out=$source.qcln.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"
imsub in=$source.ucln out=$source.ucln.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"
\rm -fr $source.[iqu]cmp
\rm -fr $source.beam
 
impol in=$source.qcln,$source.ucln,$source.icln poli=$source.pcln sigma=1e-9 options=bias sncut=0
imsub in=$source.pcln out=$source.pcln.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"

#goto skipall

goto skipsfind  # sfind not working yet...

#   Find polarised sources in map and make region file

set sig = 9
set icut = `echo $rms $sig | awk '{print $1*$2}'`

# Number of pixels for half-size of box
set b = 5

\rm sfind.log
\rm clean.$source.pcln 
# coordinate conversion problem with sfind?
sfind in=$source.pcln cutoff=$icut xrms=$sig "options=auto" | tail -3 | head -1  # changed to pcln

# How many sources did we detect?
set numsrc = `wc sfind.log | awk '{print $1-4}' `

# Now make a box for each source
set n = 1
while ($n <= $numsrc)
  set ra  = `tail -$numsrc sfind.log | head -$n | tail -1 | cut -c1-12`
  set dec = `tail -$numsrc sfind.log | head -$n | tail -1 | cut -c13-26`
  set x0 = `impos in=$source.pcln coord=''$ra,$dec'' "type=hms,dms" | tail -8 | head -1 |  awk '{print $5}' `
  set y0 = `impos in=$source.pcln coord=''$ra,$dec'' "type=hms,dms" | tail -7 | head -1 | awk '{print $5}' `
  echo $ra $dec $x0 $y0

  set x1 =  `echo "$x0 + $b" | bc -l `
  set x2 =  `echo "$x0 - $b" | bc -l `
  set y1 =  `echo "$x0 + $b" | bc -l `
  set y2 =  `echo "$x0 - $b" | bc -l `

  echo "abspix,box($x2,$y2,$x1,$y1)" >> clean.$source.pcln

   @ n = ($n + 1)
end

# set clean region
if (-f clean.$source.pcln) then
#  cat clean.$source.pcln
#  set regcommand = region=@clean.$source.pcln
else
  set regcommand = ''
endif

skipsfind:

set regcommand = region=abspix,box'('$boxlo,$boxlo,$boxhi,$boxhi')'  # sfind not working?!

#  Make channel maps
set n=1
while ($n <= $nchan)
 echo 'Starting bin '$n' of source '${source}
 if ( -e t${rand}${n}vs ) then
  invert vis=t${rand}${n}vs map=$source-$n.imap,$source-$n.qmap,$source-$n.umap,$source-$n.vmap \
  beam=$source-$n.beam imsize=$imsize $imgparams \
       stokes=i,q,u,v options=double,mfs | tail -2
  set rms = `gethd in=$source-$n.imap/rms`
  set sig = 4.5
  set icut = `echo $rms $sig | awk '{print $1*$2}'`
  clean map=$source-$n.imap beam=$source-$n.beam out=$source-$n.icmp niters=300 $regcommand cutoff=$icut | tail -2
  clean map=$source-$n.qmap beam=$source-$n.beam out=$source-$n.qcmp niters=200 $regcommand cutoff=$icut | tail -2
  clean map=$source-$n.umap beam=$source-$n.beam out=$source-$n.ucmp niters=200 $regcommand cutoff=$icut | tail -2
  restor model=$source-$n.icmp beam=$source-$n.beam map=$source-$n.imap out=$source-$n.icln $restorparams | tail -2
  restor model=$source-$n.qcmp beam=$source-$n.beam map=$source-$n.qmap out=$source-$n.qcln $restorparams | tail -2
  restor model=$source-$n.ucmp beam=$source-$n.beam map=$source-$n.umap out=$source-$n.ucln $restorparams  | tail -2
#  \rm -fr $source.[1-9]*.[qu]{map,cmp}
  \rm -fr $source-$n.beam

  impol in=$source-$n.qcln,$source-$n.ucln,$source-$n.imap poli=$source-$n.pcln sigma=1e-9 options=bias sncut=0
  imsub in=$source-$n.qcln out=$source-$n.qcln.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"
  imsub in=$source-$n.ucln out=$source-$n.ucln.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"
#  \rm -r $source-$n.[qu]cln
  imsub in=$source-$n.pcln out=$source-$n.pcln.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"
  imsub in=$source-$n.vmap out=$source-$n.vmap.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"
 endif
 @ n = ($n + 1)
end

skipall:

# clean up working visibility files
\rm -f t???vs
\rm -f t????vs
\rm -f t?????vs
 
