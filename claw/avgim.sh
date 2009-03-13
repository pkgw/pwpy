#! /bin/bash
#
# Usage: avgim.sh
#
# Output files are
#
#
#

# set -e -x   # for debugging

visroot='fxc-j0332-0.1s'
suffix='tst'
halflist='aa'

for ((i=0; i<=7; i++))
    do
    expmp=''
    expbm=''
    nhalves=0
    # average bm and mp across pols and halves (split for 256 line limit of miriad)
    for half in $halflist
	do
	expmp='+<'${visroot}-xx-${suffix}'-bin'${i}${half}'.mp>+<'${visroot}-yy-${suffix}'-bin'${i}${half}'.mp>'${expmp}
	expbm='+<'${visroot}-xx-${suffix}'-bin'${i}${half}'.bm>+<'${visroot}-yy-${suffix}'-bin'${i}${half}'.bm>'${expbm}
	nhalves=`echo ${nhalves}+2 | bc`
    done
    # need to use cut to remove superfluous + symbol
    expmp=`echo $expmp | cut -c2-`
    expbm=`echo $expbm | cut -c2-`
    expmp='('${expmp}')/'${nhalves}
    expbm='('${expbm}')/'${nhalves}

    maths exp=${expmp} out=${visroot}'-i-'${suffix}'-bin'${i}$'.mp'
    maths exp=${expbm} out=${visroot}'-i-'${suffix}'-bin'${i}$'.bm'
done

# cat together along third axis
imcat in=${visroot}'-i-'${suffix}'-bin?.mp' out=${visroot}'-icube-'${suffix}'.mp' options=relax
imcat in=${visroot}'-i-'${suffix}'-bin?.bm' out=${visroot}'-icube-'${suffix}'.bm' options=relax

# arithmetic on mp
avmaths in=${visroot}'-icube-'${suffix}'.mp' out=${visroot}'-icube-'${suffix}'-sub.mp' options=subtract

echo
echo '***Mean-subtracted image stats***'
imstat in=${visroot}'-icube-'${suffix}'-sub.mp'

# clean map (lightly) and restore
clean map=${visroot}'-icube-'${suffix}'-sub.mp' beam=${visroot}'-icube-'${suffix}'.bm' out=${visroot}'-icube-'${suffix}'-sub.cl' niters=100
restor map=${visroot}'-icube-'${suffix}'-sub.mp' beam=${visroot}'-icube-'${suffix}'.bm' model=${visroot}'-icube-'${suffix}'-sub.cl' out=${visroot}'-icube-'${suffix}'-sub.rm'

echo
echo '***Restored image stats***'
imstat in=${visroot}'-icube-'${suffix}'-sub.rm'

# other analysis
#
# fit the source!
#imfit in=fxc-j0332-0.1s-icube-sub.rm region='boxes(30,30,50,50)(2,2)' object=gaussian
#
# redo cube without chan 2
#avmaths in=fxc-j0332-0.1s-icube.mp out=fxc-j0332-0.1s-icube-subno2.mp options=subtract region='image(1,1),image(3,8)'
#
#clean map=fxc-j0332-0.1s-icube-subno2.mp beam=fxc-j0332-0.1s-icube.bm out=fxc-j0332-0.1s-icube-subno2.cl niters=100
#restor map=fxc-j0332-0.1s-icube-subno2.mp beam=fxc-j0332-0.1s-icube.bm model=fxc-j0332-0.1s-icube-subno2.cl out=fxc-j0332-0.1s-icube-subno2.rm
