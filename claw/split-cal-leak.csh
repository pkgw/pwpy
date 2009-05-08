#!/usr/tcsh

set src=c138
set visroot=mosfxc-3${src}.uvaver.uvcal
foreach piece (2 3 4 5 6 7 8)

uvaver vis=${visroot} out=${visroot}${piece} line=ch,100,${piece}00
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
