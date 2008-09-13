#! /bin/bash
#
# Invert, clean, restore, fit point source, all in one go.

. common.sh

srcs=`./index-list.py mf.list src "$@"`
freqs=`./index-list.py mf.list freq "$@"`
flux=""

for src in $srcs ; do
    for freq in $freqs ; do
	vises=$(./comma.py $(./filter-list.py mf.list src=$src freq=$freq "$@"))

	echo $vises ...

	mp=mp-$src-$freq
	bm=bm-$src-$freq
	cl=cl-$src-$freq
	rm=rm-$src-$freq
	rs=rs-$src-$freq

	rm -rf $mp $bm $cl $rm $rs
	cmd invert vis=$vises map=$mp beam=$bm options=double,mfs sup=0
	cmd clean map=$mp beam=$bm out=$cl niters=5000
	cmd restor map=$mp beam=$bm model=$cl out=$rm

	# Imfit. We want to preserve the output so things get
	# messier

	imfit region='arcsec,box(-500,-500,500,500)' object=point \
	    options=resid in=$rm out=$rs >$rm/ws-imfit
	cat $rm/ws-imfit >>wank.log
	pk=`grep 'Peak' $rm/ws-imfit`
	model=`cat calfluxes.tab |grep "^$src $freq" |cut -d' ' -f 3`
	flux="$flux
$src $freq:
$pk
  Model: $model
"
    done
done

echo "$flux"
