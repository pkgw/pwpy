#!/usr/tcsh

set src=c138
set visroot=mosfxc-3${src}.uvaver.uvcal
set chans=25
foreach piece (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32)
set startfreq = `echo '100 + '${chans}' * ('${piece}'-1)' | bc`

uvaver vis=${visroot} out=${visroot}${piece} line=ch,${chans},${startfreq}
puthd in=${visroot}${piece}/evector value=1.570796
uvredo vis=${visroot}${piece} out=${visroot}${piece}.uvredo options=chi
mfcal vis=${visroot}${piece}.uvredo refant=1
gpcal vis=${visroot}${piece}.uvredo refant=1 options=xyref
gpplt vis=${visroot}${piece}.uvredo options=polarization yaxis=amp log=3${src}-leak${piece}.amp.txt
gpplt vis=${visroot}${piece}.uvredo options=polarization yaxis=phase log=3${src}-leak${piece}.phase.txt

# rationalize leakage files
tail -n15 3${src}-leak${piece}.amp.txt > tmp
cut -c1-28 tmp > tmp2
cut -c29-56 tmp >> tmp2
cut -c57- tmp >> tmp2
mv tmp2 3${src}-leak${piece}.amp.txt
rm -f tmp

tail -n15 3${src}-leak${piece}.phase.txt > tmp
cut -c1-28 tmp > tmp2
cut -c29-56 tmp >> tmp2
cut -c57- tmp >> tmp2
mv tmp2 3${src}-leak${piece}.phase.txt
rm -f tmp
end
