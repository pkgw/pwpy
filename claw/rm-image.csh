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
set diam = 6
set imsize = 256
set boxlo = `echo $imsize'/2 - 10' | bc`
set boxhi = `echo $imsize'/2 + 10' | bc`
set imgparams = "sup=0 cell=20 fwhm=200"

#  Make images
\rm -fr $source.?{cln,map,cmp}
\rm -fr $source.?cln.imsub
\rm -fr $source.beam

#   Make one map
invert vis=$source-1 map=$source.imap,$source.qmap,$source.umap,$source.vmap beam=$source.beam imsize=$imsize \
stokes=i,q,u,v options=mfs,double "select=-shadow($diam)" $imgparams | tail -2
set rms = `gethd in=$source.imap/rms`
set icut = `echo "4.5*$rms" | bc -l`
clean map=$source.imap beam=$source.beam out=$source.icmp niters=1000 cutoff=$icut | tail -2
clean map=$source.qmap beam=$source.beam out=$source.qcmp niters=500 cutoff=$icut | tail -2
clean map=$source.umap beam=$source.beam out=$source.ucmp niters=500 cutoff=$icut | tail -2
restor model=$source.icmp beam=$source.beam map=$source.imap out=$source.icln | tail -2
restor model=$source.qcmp beam=$source.beam map=$source.qmap out=$source.qcln | tail -2
restor model=$source.ucmp beam=$source.beam map=$source.umap out=$source.ucln | tail -2
imsub in=$source.icln out=$source.icln.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"
imsub in=$source.qcln out=$source.qcln.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"
imsub in=$source.ucln out=$source.ucln.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"
\rm -fr $source.[iqu]cmp
\rm -fr $source.beam
 
impol in=$source.qcln,$source.ucln,$source.icln poli=$source.pcln sigma=1e-9 options=bias sncut=0
imsub in=$source.pcln out=$source.pcln.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"

goto skipsfind  # sfind coords bad.  just manually set cleaning to center

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

skipsfind:

# set clean region
if (-f clean.$source.pcln) then
  set regcommand = region=abspix,box'('$boxlo,$boxlo,$boxhi,$boxhi')'  # sfind not working?!
#  cat clean.$source.pcln
#  set regcommand = region=@clean.$source.pcln
else
  set regcommand = ''
endif

#  Make channel maps
\rm -fr $source-*.?{cln,map,cmp}
\rm -fr $source-*.?{cln,map,cmp}.imsub
set n=1
while ($n <= 20)

  invert vis=$source-$n map=$source-$n.imap,$source-$n.qmap,$source-$n.umap,$source-$n.vmap \
  beam=$source-$n.beam imsize=$imsize "select=-shadow($diam)" $imgparams  \
       stokes=i,q,u,v options=double,mfs | tail -2
  set rms = `gethd in=$source-$n.imap/rms`
  set sig = 4.5
  set icut = `echo $rms $sig | awk '{print $1*$2}'`
  clean map=$source-$n.imap beam=$source-$n.beam out=$source-$n.icmp niters=500 $regcommand cutoff=$icut | tail -2
  clean map=$source-$n.qmap beam=$source-$n.beam out=$source-$n.qcmp niters=200 $regcommand cutoff=$icut | tail -2
  clean map=$source-$n.umap beam=$source-$n.beam out=$source-$n.ucmp niters=200 $regcommand cutoff=$icut | tail -2
  restor model=$source-$n.icmp beam=$source-$n.beam map=$source-$n.imap out=$source-$n.icln | tail -2
  restor model=$source-$n.qcmp beam=$source-$n.beam map=$source-$n.qmap out=$source-$n.qcln | tail -2
  restor model=$source-$n.ucmp beam=$source-$n.beam map=$source-$n.umap out=$source-$n.ucln | tail -2
#  \rm -fr $source.[1-9]*.[qu]{map,cmp}
  \rm -fr $source-$n.beam

  impol in=$source-$n.qcln,$source-$n.ucln,$source-$n.imap poli=$source-$n.pcln sigma=1e-9 options=bias sncut=0
  imsub in=$source-$n.qcln out=$source-$n.qcln.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"
  imsub in=$source-$n.ucln out=$source-$n.ucln.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"
#  \rm -r $source-$n.[qu]cln
  imsub in=$source-$n.pcln out=$source-$n.pcln.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"
  imsub in=$source-$n.vmap out=$source-$n.vmap.imsub "region=abspix,box("$boxlo","$boxlo","$boxhi","$boxhi")"
 
  @ n = ($n + 1)
end
