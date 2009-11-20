#!/usr/bin/tcsh
# claw, 23jul09
#
# Script to apply frequency dependent leakages.
# Assumes output from 'split-cal-leak.csh' script.
# Assumes target file has gain and bandpass calibration.

# User parameters
set refant=1
set chans=50  # channels per frequency chunk.  
set combine=0

if $#argv == 0 then
  set cal=hexa-3c286-hp0-1430  # original file of leakage calibrated data
  set apply=hexa-3c428-hp0-1430  # apply leakages to this file
else
  echo 'Using first argument as root of calibrated data, second argument as uncalibrated target data.'
  set cal = $argv[1]
  set apply = $argv[2]
endif

echo 'Applying calibration to file '${apply}
rm -rf tmp-${apply}-tmp
uvaver vis=${apply} out=tmp-${apply}-tmp interval=0.001 options=nopol,nocal,nopass

# loop over frequency chunks
#foreach piece (1 2 3 4 5 6 7 8)
foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)
#foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20)

    # define first channel number of frequency chunk
    set startchan = `echo '100 + '${chans}' * ('${piece}'-1)' | bc`

    # reorder data to keep pol data in order expected by other tools.  also split in frequency
    uvaver vis=tmp-${apply}-tmp out=${apply}-${piece} line=ch,${chans},${startchan},1,1 interval=0.001 options=nopol,nocal,nopass

    # copy 3c286 cal to source.  apply extended cal if it exists.
    if $combine == 1 then
	gpcopy vis=${cal}-${piece} out=${apply}-${piece} #options=nocal,nopass
	uvcat vis=${apply}-${piece} out=tmp-${piece}
	rm -rf ${apply}-${piece}
	cp -r tmp-${piece} ${apply}-${piece}
	rm -rf tmp-${piece}
	gpcopy vis=${cal}join-${piece} out=${apply}-${piece} #options=nocal,nopass
    else
        gpcopy vis=${cal}-${piece} out=${apply}-${piece} #options=nocal,nopass
    endif

end

rm -rf tmp-${apply}-tmp
