#! /bin/bash
#
# Create a table of calibrator fluxes from
# my calmodels Python module

. common.sh

srcs=`./index-list.py fx.list src`
freqs=`./index-list.py fx.list freq`

rm -f calfluxes.tab

for src in $srcs ; do
    for freq in $freqs ; do
	echo $src $freq `python -m calmodels $src $freq` >>calfluxes.tab
    done
done

cat calfluxes.tab
