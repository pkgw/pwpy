#!/usr/bin/tcsh
# claw, 19jun09
#
# Script to calibrate ATA data with frequency dependent gains and leakages.
# This is a wrapper script that splits the data in frequency and runs mfcal and gpcal.
# It also outputs leakages for plotting by the python script 'plotleak-realimag.py'.
# It is best to flag aggressively and remove any suspect antenna polarizations.
# If parallacic angle coverage is poor, the calibration model can be simplified to improve reliability.

## User parameters
set visroot=$1   # input file name
set log=${1}.log  # output log file
set chans=50  # channels per frequency chunk;  each is calibrated independently
set combine=0  # optionally can combine gain (not leakage) cal with other files to extend in time
set leakcal='../../polcal/oct2010/mosfxc-3c286.uvaver.uvredo'  # optionally can apply leakages from other files;  sometimes useful for helping the fit converge  **may fail when filename is long?**
#set leakcal=''  # optionally can apply leakages from other files;  sometimes useful for helping the fit converge
set leaks=1   # optionally can output leakage text files

#set antsel=''
set antsel=select=ant'('1,4,8,11,12,16,25,33,36,37,41')('1,4,8,11,12,16,25,33,36,37,41')'  # original list used for polcal memo
#set antsel=select=ant'('1,4,5,6,8,11,19,29,33,36,41')('1,4,5,6,8,11,19,29,33,36,41')'  # second list used for polcal memo, same diff
#set antsel=select=ant'('1,4,5,6,7,8,10,11,12,13,14,33,37')('1,4,5,6,7,8,10,11,12,13,14,33,37')' # smaller leak in polcal2.uvaver.high
#set antsel='select=-ant(5,6,10,11,42)'  # removes 1800 day2,3 large leaks
#set antsel='select=-ant(5,8,16,26,42)'  # removes 1000 day2,3 large leaks
#set antsel='select=-ant(5,16,42)'  # removes 2010 day1,2 large leaks
#set antsel='select=-ant(6)'  # removes 1430 day1 large leak

## Parsing the inputs
# set refant, if you like, defaults to number 1, which is often good
if $#argv == 2 then
    set refant=$2
else
    set refant=1
endif

# if using secondary gain (not leakage) calibrator, if you need to extende gain in time
if $#argv == 3 then
    set refant=$2
    set cal2=$3
#    set cal3=$4
else
#    set cal2='mosfxa-NVSSJ133108+303032-1430-100'
    set cal2='mosfxc-3c138-2010-100'
#    set cal3='mosfxc-NVSSJ084124+705341-2010-100'
endif

## Start processing
# First, put data in (time, stokes) order required by gpcal.  Skip this is tmp file exists...
if ( -e tmp-${visroot}-tmp ) then
    goto tmpexists
else
    uvaver vis=${visroot} out=tmp-${visroot}-tmp interval=0.001 options=nocal,nopass,nopol | tee -ia $log

if $combine == 1 then
    uvaver vis=${cal2} out=tmp-${cal2}-tmp interval=0.001 options=nocal,nopass,nopol | tee -ia $log
#    rm -rf tmp-${cal3}-tmp
#    uvaver vis=${cal3} out=tmp-${cal3}-tmp interval=0.001 options=nocal,nopass,nopol
endif

tmpexists:

# Loop over frequency chunks, split data and calibrate each chunk.
#foreach piece (1 2 3 4 5 6 7 8)
foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)
#foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52  53  54  55  56  57  58  59  60  61  62  63  64 65  66  67  68  69  70  71  72  73  74  75  76  77 78  79  80  81  82  83  84  85  86  87  88  89  90 91  92  93  94  95  96  97  98  99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160)

    # Check that there is data in this chunk.  If not, skip it.
    if (${leakcal} != '') then
      if (! -e ${leakcal}-${piece}) then
	echo 'Skipping channel '${piece} | tee -ia $log
	continue
      endif
    endif
    echo 'Starting channel ' $piece | tee -ia $log

    # Define first channel number of frequency chunk
    set startchan = `echo '100 + '${chans}' * ('${piece}'-1)' | bc`

    # Reorder data to keep pol data in order expected by other tools.  also split in frequency
    uvaver vis=tmp-${visroot}-tmp out=${visroot}-${piece} line=ch,${chans},${startchan},1,1 interval=0.001 options=nocal,nopass,nopol $antsel | tee -ia $log

    # Do calibration:  mfcal for bandpass, gpcal for gains and leakages.
    # If calibrating only with this file, run it alone...
    if ${leakcal} == '' then
	echo 'Running gpcal...' | tee -ia $log
	mfcal vis=${visroot}-${piece} refant=${refant} interval=60 tol=0.00001 | tee -ia $log
	gpcal vis=${visroot}-${piece} refant=${refant} options=xyref,polref interval=999 | tee -ia $log # op | tee -ia $logtions=xyref,polref critical!
	gpcal vis=${visroot}-${piece} refant=${refant} options=xyref,polref interval=60 tol=0.000001 | tee -ia $log
#	gpcal vis=${visroot}-${piece} refant=${refant} options=xyref,polref interval=60 tol=0.000001 flux=8.493,0.590,-0.256,0.000 | tee -ia $log   # test for 3c138
#	gpcal vis=${visroot}-${piece} refant=${refant} options=xyref,polref interval=60 tol=0.000001 flux=14.572,0.550,1.280,0.000 | tee -ia $log   # test for 3c286

    # If calibrating with help from another file, copy leaks over first...
    else
	echo 'Copying leakage calbration from '${leakcal} | tee -ia $log
	mfcal vis=${visroot}-${piece} refant=${refant} interval=60 tol=0.00001 | tee -ia $log
#	cp ${leakcal}-${piece}/leakage ${visroot}-${piece}/
	gpcopy vis=${leakcal}-${piece} out=${visroot}-${piece} options=nopass,nocal | tee -ia $log # this works for 1800 xfer  **OR NOT?!**  long filename problem?!
	set xyphases = `grep GPCAL ${leakcal}-${piece}/history | grep Xyphase | tail -n 7 | cut -c 25- | gawk '{printf("%s,%s,%s,%s,%s,%s,%s,",$1,$2,$3,$4,$5,$6,$7)}'`
	echo $xyphases | tee -ia $log
#	gpcal vis=${visroot}-${piece} refant=${refant} options=nopol,xyref interval=90 tol=0.00001 xyphase=$xyphases # this works for 1800 xfer
	gpcal vis=${visroot}-${piece} refant=${refant} options=nopol,noxy interval=60 tol=0.000001 xyphase=$xyphases | tee -ia $log
# or loop through gpcal/mfcal to iterate to gain and leakage solution?

# other, old method using gpscal method.  some bad problem here.  not solving xyphase?
#	uvcat vis=${visroot}-${piece} out=tmp-${visroot}-${piece}
#	rm -rf ${visroot}-${piece}
#	mv tmp-${visroot}-${piece} ${visroot}-${piece}
#	rm -f tmp.flux
#	gpcal vis=${visroot}-${piece} refant=${refant} options=noxy,nopol interval=999 | grep 'Using IQUV' | cut -c 14-48 | sed 's/ //g' > tmp.flux
#	echo 'Using IQUV used by gpcal:'
#	cat tmp.flux
#	gpscal vis=${visroot}-${piece} flux=`cat tmp.flux` refant=$refant interval=90 options=amplitude,xyref,noscale
#	rm -f tmp.flux
    endif

    # If extending gain calibration in time, apply first gain and leakage solutions, then calibration secondary cal.
    if ${combine} == 1 then
	# apply main calibrator to others, selfcal others, then merge to single calibration file
	# secondary cal
	uvaver vis=tmp-${cal2}-tmp out=${cal2}-${piece} line=ch,${chans},${startchan},1,1 interval=0.001 options=nocal,nopass,nopol $antsel | tee -ia $log
# if doing selfcal, need to apply gains first...
#	gpcopy vis=${visroot}-${piece} out=${cal2}-${piece}
#	uvcat vis=${cal2}-${piece} out=tmp-${piece}
#	rm -rf ${cal2}-${piece}
#	mv tmp-${piece} ${cal2}-${piece}
#	selfcal vis=${cal2}-${piece} refant=${refant} interval=60  # can do phase selfcal.  not all that important
# if doing secondary flux cal, just run mfcal then copy leaks xyphase on top of that
	mfcal vis=${cal2}-${piece} refant=${refant} interval=30 tol=0.00001 | tee -ia $log  # start with bandpass
	gpcopy vis=${visroot}-${piece} out=${cal2}-${piece} options=nopass | tee -ia $log  # copy leaks, gains on top
	gpcal vis=${cal2}-${piece} refant=${refant} interval=30 tol=0.00001 options=nopol,noxy | tee -ia $log # resolve the gains with fixed xyphase

	# tertiary cal
#	uvaver vis=tmp-${cal3}-tmp out=${cal3}-${piece} line=ch,${chans},${startchan},1,1 interval=0.001 options=nocal,nopass,nopol
#	gpcopy vis=${visroot}-${piece} out=${cal3}-${piece}
#	uvcat vis=${cal3}-${piece} out=tmp-${piece}
#	rm -rf ${cal3}-${piece}
#	mv tmp-${piece} ${cal3}-${piece}
#	selfcal vis=${cal3}-${piece} refant=${refant} interval=999

	# merge cals into new file
#       uvaver ... join
#	selfcal vis=${visroot}join-${piece} refant=${refant} interval=60
#	gpcopy mode=merge vis=${cal3}-${piece} out=${visroot}join-${piece}
# alternatively
#	cp -r ${visroot}-${piece} ${visroot}join-${piece}

	# Finally merge the two gain solutions into a single file.  This file can be applied to target fields later.
	gpcopy mode=merge vis=${cal2}-${piece} out=${visroot}-${piece} options=nopass,nopol | tee -ia $log
    endif

    # One can optionally print out the leakage values to a text file for plotting with a python script.
    if $leaks == 1 then
	# now output the leakages for visualization later
	gpplt vis=${visroot}-${piece} options=polarization yaxis=amp log=${visroot}-leakamp${piece}.txt | tee -ia $log
	gpplt vis=${visroot}-${piece} options=polarization yaxis=phase log=${visroot}-leakphase${piece}.txt | tee -ia $log

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

# Clean up
rm -rf tmp-${visroot}-tmp | tee -ia $log
rm -rf tmp-${cal2}-tmp | tee -ia $log
#rm -rf tmp-${cal3}-tmp
if ${combine} == 1 then
    rm -rf ${cal2}-* | tee -ia $log
#    rm -rf ${cal3}-*
endif
