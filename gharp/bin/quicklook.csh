#!/usr/bin/tcsh

if ($#argv < 1) then
  echo "must enter source (e.g. 3c274)"
  exit 0
endif

set source $1

rm *.ephem
fxconf.rb sagive none fxa 1a 1b 1c 1d 1e 1f 1g 1h 1k 2a 2b 2c 2e 2f 2g 2j 2k 2m 3d 3e 3f 3g 3h 3j 3l 4j 4k 5b 5c 5e 5g;
mosfx.csh 1045 100 fx64a:fxa 10 none 1800 $source 60 -0 test r
