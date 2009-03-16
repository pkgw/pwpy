#! /bin/bash
#
# Usage: avgim.sh
#
# Output files are
#
#
#
##################
# default params?
#imroot='j0332-0.1s'
#suffix='tst'
#phasebins=16
##################
imroot="$1"
suffix="$2"
phasebins="$3"

set -e -x   # for debugging
file='time-'${suffix}

nsplit=`ls ${file}-bin0a? | wc | gawk '{printf "%d \n", $0}' | head -n 1`
if [ $nsplit -eq 1 ]
then
    halflist='aa'
elif [ $nsplit -eq 2 ]
then
    halflist='aa ab'
elif [ $nsplit -eq 3 ]
then
    halflist='aa ab ac'
elif [ $nsplit -eq 4 ]
then
    halflist='aa ab ac ad'
else
    print 'Not getting split files higher than ad!'
    halflist='aa ab ac ad'
fi

echo
echo '***Starting averaging of images across pols (and any split for miriad line limit)***'
echo

for ((i=0; i<=${phasebins}-1; i++))
    do
    expmp=''
    expbm=''
    nhalves=0
    # average bm and mp across pols and halves (split for 256 line limit of miriad)
    for half in $halflist
	do
	expmp='+<'${imroot}-xx-${suffix}'-bin'${i}${half}'.mp>+<'${imroot}-yy-${suffix}'-bin'${i}${half}'.mp>'${expmp}
	expbm='+<'${imroot}-xx-${suffix}'-bin'${i}${half}'.bm>+<'${imroot}-yy-${suffix}'-bin'${i}${half}'.bm>'${expbm}
	nhalves=`echo ${nhalves}+2 | bc`
    done
    # need to use cut to remove superfluous + symbol
    expmp=`echo $expmp | cut -c2-`
    expbm=`echo $expbm | cut -c2-`

    # normalize by number of images
    expmp='('${expmp}')/'${nhalves}
    expbm='('${expbm}')/'${nhalves}

    maths exp=${expmp} out=${imroot}'-i-'${suffix}'-bin'${i}$'.mp'
    maths exp=${expbm} out=${imroot}'-i-'${suffix}'-bin'${i}$'.bm'
done

# cat together along third axis
imcat in=${imroot}'-i-'${suffix}'-bin*.mp' out=${imroot}'-icube-'${suffix}'.mp' options=relax
imcat in=${imroot}'-i-'${suffix}'-bin*.bm' out=${imroot}'-icube-'${suffix}'.bm' options=relax

# arithmetic on mp
avmaths in=${imroot}'-icube-'${suffix}'.mp' out=${imroot}'-icube-'${suffix}'-sub.mp' options=subtract

echo
echo '***Mean-subtracted image stats***'
imstat in=${imroot}'-icube-'${suffix}'-sub.mp'

# clean map (lightly) and restore
clean map=${imroot}'-icube-'${suffix}'-sub.mp' beam=${imroot}'-icube-'${suffix}'.bm' out=${imroot}'-icube-'${suffix}'-sub.cl' niters=100
restor map=${imroot}'-icube-'${suffix}'-sub.mp' beam=${imroot}'-icube-'${suffix}'.bm' model=${imroot}'-icube-'${suffix}'-sub.cl' out=${imroot}'-icube-'${suffix}'-sub.rm'

echo
echo '***Restored image stats***'
imstat in=${imroot}'-icube-'${suffix}'-sub.rm'

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
