#!/usr/tcsh
#
# claw, 23jul09
# Script to apply frequency dependent leakages.
# Assumes output from 'split-cal-leak.csh' script.
# Assumes target file has gain and bandpass calibration.

# User parameters
set cal=mosfxa-3C286-CAL-4860  # original file of leakage calibrated data
set apply=mosfxa-gal01503-4860  # apply leakages to this file
set chans=100  # channels per frequency chunk.  
set refant=1

# loop over frequency chunks
foreach piece (1 2 3 4 5 6 7 8)
#foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32)

    # define first channel number of frequency chunk
    set startfreq = `echo '100 + '${chans}' * ('${piece}'-1)' | bc`

    # reorder data to keep pol data in order expected by other tools.  also split in frequency
    uvaver vis=${apply} out=${apply}.uvaver${piece} line=ch,${chans},${startfreq} interval=0.001 options=nocal,nopass,nopol

    # now do cal steps.  mfcal for bandpass, gpcal for gains and leakages
    gpcopy vis=${cal}${piece} out=${apply} options=nocal,nopass

end
