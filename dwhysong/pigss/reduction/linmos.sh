#!/bin/bash

corrs=(a c)
freqs=(3040 3140)
pfxs="$1"

rm -f linmos_0.list linmos_1.list
corrlist="0 1"

for c in $corrlist ; do
  corr=${corrs[$c]};
  freq=${freqs[$c]};
  echo $corr, $freq
  for pfx in $pfxs ; do
    ls -d mosfx"$corr"-"$pfx"-*-"$freq".cmf  >> linmos_"$c".list
  done
  cat linmos_"$c".list
done



rm -rf $pfx_?.linmos $pfx.linmos
linmos in=\@linmos_0.list options=taper out="$pfx"_0.linmos
linmos in=\@linmos_1.list options=taper out="$pfx"_1.linmos
rm -rf $pfx.linmos
cat linmos_0.list linmos_1.list > linmos.list
linmos in=\@linmos.list options=taper out="$pfx".linmos
