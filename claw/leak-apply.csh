#!/usr/bin/tcsh
# claw, 23jul09
#
# Script to apply frequency dependent leakages.
# Assumes output from 'split-cal-leak.csh' script.
# Assumes target file has gain and bandpass calibration.

# User parameters
if $#argv == 0 then
  set cal=hexa-3c286-hp0-1430  # original file of leakage calibrated data
  set apply=hexa-3c428-hp0-1430  # apply leakages to this file
else
  echo 'Using first argument as root of calibrated data, second argument as uncalibrated target data.'
  set cal = $argv[1]
  set apply = $argv[2]
endif
set chans=40  # channels per frequency chunk.  
set refant=1

# put data in time, stokes order
rm -rf tmp-${apply}-tmp
uvaver vis=${apply} out=tmp-${apply}-tmp interval=0.001 options=nocal,nopass,nopol

# loop over frequency chunks
foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20)
#foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32)

    # define first channel number of frequency chunk
    set startchan = `echo '100 + '${chans}' * ('${piece}'-1)' | bc`

    # reorder data to keep pol data in order expected by other tools.  also split in frequency
    uvaver vis=tmp-${apply}-tmp out=${apply}-${piece} line=ch,${chans},${startchan} interval=0.001 options=nopol,nocal,nopass

    # now do cal steps.  mfcal for bandpass, gpcal for gains and leakages
    gpcopy vis=${cal}-${piece} out=${apply}-${piece} #options=nocal,nopass

end

# clean up
rm -rf tmp-${apply}-tmp
