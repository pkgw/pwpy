#!/usr/tcsh

set point=p0
set src=c286
set freq=1430
set visroot=mosfxc-3${src}.uvaver.uvredo
set chans=100
foreach piece (1 2 3 4 5 6 7 8)
#foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32)
set startfreq = `echo '100 + '${chans}' * ('${piece}'-1)' | bc`

uvaver vis=${visroot} out=${visroot}${piece} line=ch,${chans},${startfreq} interval=0.001 options=nocal,nopass,nopol
#puthd in=${visroot}${piece}/evector value=1.570796
#uvredo vis=${visroot}${piece} out=${visroot}${piece}.uvredo options=chi
#rm -rf ${visroot}${piece};  mv ${visroot}${piece}.uvredo ${visroot}${piece}
mfcal vis=${visroot}${piece} refant=1 interval=5
gpcal vis=${visroot}${piece} refant=1 options=xyref interval=5
gpplt vis=${visroot}${piece} options=polarization yaxis=amp log=3${src}-${point}-${freq}-leakamp${piece}.txt
gpplt vis=${visroot}${piece} options=polarization yaxis=phase log=3${src}-${point}-${freq}-leakphase${piece}.txt

# rationalize leakage files
tail -n15 3${src}-${point}-${freq}-leakamp${piece}.txt > tmp
cut -c1-28 tmp > tmp2
cut -c29-56 tmp >> tmp2
cut -c57- tmp >> tmp2
mv tmp2 3${src}-${point}-${freq}-leakamp${piece}.txt
rm -f tmp

tail -n15 3${src}-${point}-${freq}-leakphase${piece}.txt > tmp
cut -c1-28 tmp > tmp2
cut -c29-56 tmp >> tmp2
cut -c57- tmp >> tmp2
mv tmp2 3${src}-${point}-${freq}-leakphase${piece}.txt
rm -f tmp
end
