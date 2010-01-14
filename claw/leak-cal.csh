#!/usr/bin/tcsh
# claw, 19jun09
#
# Script to calibrate ATA data with frequency dependent gains and leakages.
# Also outputs leakages for plotting by 'plotleak-realimag.py', in mmm code repository.
# Assumes the data is flagged.  Best to flag aggressively and remove any suspect antpols.

# User parameters
set visroot=$1
set chans=50  # channels per frequency chunk.  
set combine=1  # combine cal with other sources (hardcoded)?
#set leakcal=''  # if leakages are calibrated externally
set leakcal='../nvss-rm2/try2/mosfxc-3c286-1800-100-flagged'  # if leakages are calibrated externally
set leaks=1   # output leakage text files?
#set antsel=select=ant'('1,4,5,6,7,8,10,11,12,13,14,33,37')('1,4,5,6,7,8,10,11,12,13,14,33,37')' # smaller leak in polcal2.uvaver.high
set antsel=''
# set refant, if you like
if $#argv == 2 then
    set refant=$2
else
    set refant=1
endif
# do second order phase correction with multiple files
if $#argv == 4 then
    set cal2=$3
#    set cal3=$4
else
    set cal2='mosfxc-NVSSJ133108+303032-1800-100-flagged'
#    set cal3='mosfxa-NVSSJ084124+705341-1430-100'
endif

# put data in time, stokes order
if ( -e tmp-${visroot}-tmp ) then
    goto tmpexists
else
    uvaver vis=${visroot} out=tmp-${visroot}-tmp interval=0.001 options=nocal,nopass,nopol

if $combine == 1 then
    uvaver vis=${cal2} out=tmp-${cal2}-tmp interval=0.001 options=nocal,nopass,nopol
#    rm -rf tmp-${cal3}-tmp
#    uvaver vis=${cal3} out=tmp-${cal3}-tmp interval=0.001 options=nocal,nopass,nopol
endif

tmpexists:

# loop over frequency chunks
#foreach piece (1 2 3 4 5 6 7 8)
foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)
#foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52  53  54  55  56  57  58  59  60  61  62  63  64 65  66  67  68  69  70  71  72  73  74  75  76  77 78  79  80  81  82  83  84  85  86  87  88  89  90 91  92  93  94  95  96  97  98  99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160)

    # define first channel number of frequency chunk
    set startchan = `echo '100 + '${chans}' * ('${piece}'-1)' | bc`

    # reorder data to keep pol data in order expected by other tools.  also split in frequency
    uvaver vis=tmp-${visroot}-tmp out=${visroot}-${piece} line=ch,${chans},${startchan},1,1 interval=0.001 options=nocal,nopass,nopol

    # these are a few obsolete steps
    #puthd in=${visroot}${piece}/evector value=1.570796
    #uvredo vis=${visroot}${piece} out=${visroot}${piece}.uvredo options=chi
    #rm -rf ${visroot}${piece};  mv ${visroot}${piece}.uvredo ${visroot}${piece}

    # now do cal steps.  mfcal for bandpass, gpcal for gains and leakages
    if ${leakcal} == '' then
	echo 'Running gpcal...'
	mfcal vis=${visroot}-${piece} refant=${refant} interval=10 tol=0.00005 $antsel select='-auto'
	gpcal vis=${visroot}-${piece} refant=${refant} options=xyref,polref interval=10 $antsel select='-auto' # options=xyref,polref critical!
	gpcal vis=${visroot}-${piece} refant=${refant} options=xyref,polref interval=30 tol=0.00001 $antsel select='-auto'
    else
	echo 'Copying leakage calbration from '${leakcal}
	mfcal vis=${visroot}-${piece} refant=${refant} interval=10 tol=0.00005 $antsel select='-auto'
	gpcopy vis=${leakcal}-${piece} out=${visroot}-${piece} select='-auto'
	set xyphases = `grep GPCAL ${leakcal}-${piece}/history | grep Xyphase | tail -n 7 | cut -c 25- | gawk '{printf("%s,%s,%s,%s,%s,%s,%s,",$1,$2,$3,$4,$5,$6,$7)}'`
	gpcal vis=${visroot}-${piece} refant=${refant} options=nopol,noxy interval=30 tol=0.000001 $antsel xyphase=$xyphases select='-auto'
#	gpcal vis=${visroot}-${piece} refant=${refant} options=nopol,noxy,xyref,polref interval=30 tol=0.00001 $antsel select='-auto'
    endif

    if ${combine} == 1 then
	# apply main calibrator to others, selfcal others, then merge to single calibration file
	# secondary cal
	uvaver vis=tmp-${cal2}-tmp out=${cal2}-${piece} line=ch,${chans},${startchan},1,1 interval=0.001 options=nocal,nopass,nopol
	gpcopy vis=${visroot}-${piece} out=${cal2}-${piece}
	uvcat vis=${cal2}-${piece} out=tmp-${piece}
	rm -rf ${cal2}-${piece}
	mv tmp-${piece} ${cal2}-${piece}
	selfcal vis=${cal2}-${piece} refant=${refant} interval=30 select='-auto'

	# tertiary cal
#	uvaver vis=tmp-${cal3}-tmp out=${cal3}-${piece} line=ch,${chans},${startchan},1,1 interval=0.001 options=nocal,nopass,nopol
#	gpcopy vis=${visroot}-${piece} out=${cal3}-${piece}
#	uvcat vis=${cal3}-${piece} out=tmp-${piece}
#	rm -rf ${cal3}-${piece}
#	mv tmp-${piece} ${cal3}-${piece}
#	selfcal vis=${cal3}-${piece} refant=${refant} interval=999 select='-auto'

	# merge cals into new file
	uvcat vis=${visroot}-${piece} out=${visroot}join-${piece}
	selfcal vis=${visroot}join-${piece} refant=${refant} interval=30 select='-auto'
	gpcopy mode=merge vis=${cal2}-${piece} out=${visroot}join-${piece}
#	gpcopy mode=merge vis=${cal3}-${piece} out=${visroot}join-${piece}

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
#rm -rf tmp-${cal3}-tmp
if ${combine} == 1 then
    rm -rf ${cal2}-*
#    rm -rf ${cal3}-*
endif
