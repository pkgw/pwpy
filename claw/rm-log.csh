#! /usr/bin/tcsh   
# Written by bgaensler, modified by claw 25sep09
#
# Script to write log file of Q, U, for polarised sources

set nchan=16
# What source are we processing?

if $#argv == 0 then
  set source = hexa-3c286-hp0-1430  # default
else
  set source = $argv[1]
endif

set id = 1001

set srctot = 1002

set filename = log.qu.$id.x
set b0 = 0
set shortsource = `echo $source | sed '{s/[a-Z-]*//g}' | cut -c-13`
set suffix = ''

echo $id
\rm $filename

# Get peak position
if $#argv == 3 then
  echo 'Using input pixel coords to measure RM'
  set x0 = $argv[2]
  set y0 = $argv[3]
else
  set x0 = `histo in=$source.icln | grep 'Maximum value' | sed s/\(/" "/g | sed s/\,/" "/g | awk '{print $5}'`
  set y0 = `histo in=$source.icln | grep 'Maximum value' | sed s/\(/" "/g | sed s/\,/" "/g | awk '{print $6}'`
endif

set p0 = `histo in=$source.pcln | grep 'Maximum value' | awk '{print $3}'`

set xmin = `echo "$x0-$b0" | bc -l`
set xmax = `echo "$x0+$b0" | bc -l`
set ymin = `echo "$y0-$b0" | bc -l`
set ymax = `echo "$y0+$b0" | bc -l`

# Get RMS
# Theoretical RMS
set rms = `gethd in=$source.vmap/rms`
# Observed RMS
#set rms = `histo in=$source.vmap | grep Rms | cut -c24-38


echo $x0 $y0 $p0 $rms $shortsource
echo $x0 $y0 $p0 $rms $shortsource > $filename
#echo $id $srctot $p0 $rms $shortsource > $filename


#  Make channel maps
set n=1
while ($n <= $nchan)

if (-d $source-$n.ucln${suffix}) then

#     set freq = `uvlist vis=$source-$freqname-$n options=variables,full | grep sfreq | cut -c62-70`  # hack to get freq instead of vlsr.  this may be freq of chan1, so could be off by half chan width
     set freq = `gethd in=$source-$n.ucln${suffix}/crval3`
     set q0 = `imlist in=$source-$n.qcln${suffix} options=stat "region=abspix,box($x0,$y0,$x0,$y0)" | tail -1 | awk '{print $4}' `
     set u0 = `imlist in=$source-$n.ucln${suffix} options=stat "region=abspix,box($x0,$y0,$x0,$y0)" | tail -1 | awk '{print $4}' `

#    set q0 = `histo in=$source-$n.qcln "region=abspix,box($xmin,$ymin,$xmax,$ymax)" | grep Flux | awk '{print $6}' `
#    set u0 = `histo in=$source-$n.ucln "region=abspix,box($xmin,$ymin,$xmax,$ymax)" | grep Flux | awk '{print $6}' `

#     Theoretical RMS
#     set rms = `gethd in=$source-$n.ucln/rms`
#     Observed RMS
      set rms = `histo in=$source-$n.vmap | grep Rms | cut -c24-38`

     echo $freq $q0 $u0 $rms >> $filename
endif

@ n = ($n + 1)
end

sort -nr $filename | grep -v Apr > log.x
\mv log.x $filename


