#!/usr/bin/tcsh
# claw, 23jul09
#
# Script to apply frequency dependent leakages.
# Assumes output from 'split-cal-leak.csh' script.
# Assumes target file has gain and bandpass calibration.

# User parameters
set chans=50  # channels per frequency chunk.  
set combine=0
#set leakcal=''  # if leakages are calibrated externally
#set leakcal='../nvss-rm2/try5-1800/mosfxc-3c286-1800-100-flagged2'  # if leakages are calibrated externally
#set antsel=select=ant'('1,4,5,6,7,8,10,11,12,13,14,33,37')('1,4,5,6,7,8,10,11,12,13,14,33,37')' # smaller leak in polcal2.uvaver.high
#set antsel=select=ant'('16,17,25,26,27,29,30,31,32,34,35,36,37,40,41')('16,17,25,26,27,29,30,31,32,34,35,36,37,40,41')'
#set antsel='select=-ant(5,8,16,26,42)'  # removes 1000 day2,3 large leaks
#set antsel='select=-ant(5,6,10,11,42)'  # removes 1800 day2,3 large leaks
#set antsel='select=-ant(5,42)'  # removes 2010 day2 large leaks
#set antsel='select=-ant(6)'  # removes 1430 day1 large leak
set antsel=select=ant'('1,4,8,11,12,16,25,33,36,37,41')('1,4,8,11,12,16,25,33,36,37,41')'  # good polcal list
#set antsel=''
#set refant=16

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
uvaver vis=${apply} out=tmp-${apply}-tmp interval=0.001 options=nopol,nocal,nopass $antsel

# loop over frequency chunks
#foreach piece (1 2 3 4 5 6 7 8)
foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)
#foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52  53  54  55  56  57  58  59  60  61  62  63  64 65  66  67  68  69  70  71  72  73  74  75  76  77 78  79  80  81  82  83  84  85  86  87  88  89  90 91  92  93  94  95  96  97  98  99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160)

  if (-e ${cal}-${piece}) then

    # define first channel number of frequency chunk
    set startchan = `echo '100 + '${chans}' * ('${piece}'-1)' | bc`

    # reorder data to keep pol data in order expected by other tools.  also split in frequency
    uvaver vis=tmp-${apply}-tmp out=${apply}-${piece} line=ch,${chans},${startchan},1,1 interval=0.001 options=nopol,nocal,nopass

    # copy 3c286 cal to source.  apply extended cal if it exists.
    if $combine == 1 then
# if using secondary flux calibrator, no need to apply cal with uvaver
#	gpcopy vis=${cal}-${piece} out=${apply}-${piece} #options=nocal,nopass
#	uvcat vis=${apply}-${piece} out=tmp-${piece}
#	rm -rf ${apply}-${piece}
#	cp -r tmp-${piece} ${apply}-${piece}
#	rm -rf tmp-${piece}
#	gpcopy vis=${cal}join-${piece} out=${apply}-${piece} #options=nocal,nopass
	gpcopy vis=${cal}-${piece} out=${apply}-${piece} #options=nocal,nopass
    else
	gpcopy vis=${cal}-${piece} out=${apply}-${piece} #options=nocal,nopass
# fitting 1331 as 3c286
#	set xyphases = `grep GPCAL ${cal}-${piece}/history | grep Xyphase | tail -n 7 | cut -c 25- | gawk '{printf("%s,%s,%s,%s,%s,%s,%s,",$1,$2,$3,$4,$5,$6,$7)}'`
#	gpcal vis=${apply}-${piece} refant=${refant} options=xyref,nopol interval=999 tol=0.00001 xyphase=$xyphases
#
#	if ${leakcal} != '' then
#	    echo 'apply leakage from '${leakcal}
#	    gpcopy vis=${leakcal}-${piece} out=${apply}-${piece} options=nocal,nopass
#	endif
    endif
  endif

end

rm -rf tmp-${apply}-tmp
