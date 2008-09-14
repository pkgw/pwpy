#! /bin/bash
#
# Invert, clean, restore, fit point source, all in one go.

. common.sh

srcs=`./index-list.py sc.list src "$@"`
freqs=`./index-list.py sc.list freq "$@"`
epochs=`./index-list.py sc.list epoch "$@"`
flux=""

for src in $srcs ; do
    for freq in $freqs ; do
	for epoch in $epochs ; do
	    vises=$(./comma.py $(./filter-list.py sc.list \
		src=$src freq=$freq epoch=$epoch "$@"))

	    [ x"$vises" = x ] && continue
	
	    echo $vises ...

	    mp=mp-$src-$freq-$epoch
	    bm=bm-$src-$freq-$epoch
	    cl=cl-$src-$freq-$epoch
	    rm=rm-$src-$freq-$epoch
	    rs=rs-$src-$freq-$epoch

	    rm -rf $mp $bm $cl $rm $rs
	    cmd invert vis=$vises map=$mp beam=$bm options=double,mfs sup=0
	    cmd clean map=$mp beam=$bm out=$cl niters=5000
	    cmd restor map=$mp beam=$bm model=$cl out=$rm

	    echo $src >$rm/ws-src
	    echo $freq >$rm/ws-freq
	    echo $epoch >$rm/ws-epoch

	    # Imfit. We want to preserve the output so things get
	    # messier
	    
	    imfit region='arcsec,box(-500,-500,500,500)' object=point \
		options=resid in=$rm out=$rs >$rm/ws-imfit
	    cat $rm/ws-imfit >>wank.log
	    pk=`grep 'Peak' $rm/ws-imfit`
	    model=`cat calfluxes.tab |grep "^$src $freq" |cut -d' ' -f 3`
	    flux="$flux
$src $freq $epoch:
$pk
  Model: $model
"
	done
    done
done

echo "$flux"
