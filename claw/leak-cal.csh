#!/usr/bin/tcsh
# claw, 19jun09
#
# Script to calibrate ATA data with frequency dependent gains and leakages.
# Also outputs leakages for plotting by 'plotleak-realimag.py', in mmm code repository.
# Assumes the data is flagged.  Best to flag aggressively and remove any suspect antpols.

# User parameters
set visroot=$1
set chans=50  # channels per frequency chunk.  
set refant=1
set combine=0  # combine cal with other sources (hardcoded)?
set leaks=0   # output leakage text files?
#set antsel=select=ant'('1,8,33,37')('1,8,33,37')' # smaller leak in polcal2.uvaver.high
set antsel=''
set cal2='mosfxa-NVSSJ052109+163822-1430-100'
set cal3='mosfxa-NVSSJ084124+705341-1430-100'

# put data in time, stokes order
rm -rf tmp-${visroot}-tmp
uvaver vis=${visroot} out=tmp-${visroot}-tmp interval=0.001 options=nocal,nopass,nopol
if $combine == 1 then
    rm -rf tmp-${cal2}-tmp
    uvaver vis=${cal2} out=tmp-${cal2}-tmp interval=0.001 options=nocal,nopass,nopol
    rm -rf tmp-${cal3}-tmp
    uvaver vis=${cal3} out=tmp-${cal3}-tmp interval=0.001 options=nocal,nopass,nopol
endif

# loop over frequency chunks
#foreach piece (1 2 3 4 5 6 7 8)
foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)
#foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40)

    # define first channel number of frequency chunk
    set startchan = `echo '100 + '${chans}' * ('${piece}'-1)' | bc`

    # reorder data to keep pol data in order expected by other tools.  also split in frequency
    uvaver vis=tmp-${visroot}-tmp out=${visroot}-${piece} line=ch,${chans},${startchan},1,1 interval=0.001 options=nocal,nopass,nopol

    # these are a few obsolete steps
    #puthd in=${visroot}${piece}/evector value=1.570796
    #uvredo vis=${visroot}${piece} out=${visroot}${piece}.uvredo options=chi
    #rm -rf ${visroot}${piece};  mv ${visroot}${piece}.uvredo ${visroot}${piece}

    # now do cal steps.  mfcal for bandpass, gpcal for gains and leakages
    mfcal vis=${visroot}-${piece} refant=${refant} interval=10 tol=0.00005 $antsel
    gpcal vis=${visroot}-${piece} refant=${refant} options=xyref,polref interval=10 $antsel # options=xyref,polref critical!
    gpcal vis=${visroot}-${piece} refant=${refant} options=xyref,polref interval=10 tol=0.00001 $antsel

    if ${combine} == 1 then
	# apply main calibrator to others, selfcal others, then merge to single calibration file
	# secondary cal
	uvaver vis=tmp-${cal2}-tmp out=${cal2}-${piece} line=ch,${chans},${startchan},1,1 interval=0.001 options=nocal,nopass,nopol
	gpcopy vis=${visroot}-${piece} out=${cal2}-${piece}
	uvcat vis=${cal2}-${piece} out=tmp-${piece}
	rm -rf ${cal2}-${piece}
	mv tmp-${piece} ${cal2}-${piece}
	selfcal vis=${cal2}-${piece} refant=${refant} interval=999 select='-auto'

	# tertiary cal
	uvaver vis=tmp-${cal3}-tmp out=${cal3}-${piece} line=ch,${chans},${startchan},1,1 interval=0.001 options=nocal,nopass,nopol
	gpcopy vis=${visroot}-${piece} out=${cal3}-${piece}
	uvcat vis=${cal3}-${piece} out=tmp-${piece}
	rm -rf ${cal3}-${piece}
	mv tmp-${piece} ${cal3}-${piece}
	selfcal vis=${cal3}-${piece} refant=${refant} interval=999 select='-auto'

	# merge cals into new file
	uvcat vis=${visroot}-${piece} out=${visroot}join-${piece}
	selfcal vis=${visroot}join-${piece} refant=${refant} interval=999 select='-auto'
	gpcopy mode=merge vis=${cal2}-${piece} out=${visroot}join-${piece}
	gpcopy mode=merge vis=${cal3}-${piece} out=${visroot}join-${piece}

    endif

    if $leaks == 1 then
	# now output the leakages for visualization later
	gpplt vis=${visroot}-${piece} options=polarization yaxis=amp log=${visroot}-leakamp${piece}.txt
	gpplt vis=${visroot}-${piece} options=polarization yaxis=phase log=${visroot}-leakphase${piece}.txt

	# rationalize leakage files for easy plotting by python script
	tail -n15 ${visroot}-leakamp${piece}.txt > tmp
	cut -c1-28 tmp > tmp2
	cut -c29-56 tmp >> tmp2
	cut -c57- tmp >> tmp2
	mv tmp2 ${visroot}-leakamp${piece}.txt
	rm -f tmp

	tail -n15 ${visroot}-leakphase${piece}.txt > tmp
	cut -c1-28 tmp > tmp2
	cut -c29-56 tmp >> tmp2
	cut -c57- tmp >> tmp2
	mv tmp2 ${visroot}-leakphase${piece}.txt
	rm -f tmp
   endif

end

# clean up
rm -rf tmp-${visroot}-tmp
rm -rf tmp-${cal2}-tmp
rm -rf tmp-${cal3}-tmp

