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

#set -e -x   # for debugging
file='time-'${suffix}

nsplit=`ls ${file}-bin0a? | wc | gawk '{printf "%d \n", $0}' | head -n 1`
if [ $nsplit -eq 1 ]
then
    splitlist='aa'
elif [ $nsplit -eq 2 ]
then
    splitlist='aa ab'
elif [ $nsplit -eq 3 ]
then
    splitlist='aa ab ac'
elif [ $nsplit -eq 4 ]
then
    splitlist='aa ab ac ad'
elif [ $nsplit -eq 5 ]
then
    splitlist='aa ab ac ad ae'
elif [ $nsplit -eq 6 ]
then
    splitlist='aa ab ac ad ae af'
elif [ $nsplit -eq 7 ]
then
    splitlist='aa ab ac ad ae af ag'
elif [ $nsplit -eq 8 ]
then
    splitlist='aa ab ac ad ae af ag ah'
elif [ $nsplit -eq 9 ]
then
    splitlist='aa ab ac ad ae af ag ah ai'
elif [ $nsplit -eq 10 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj'
elif [ $nsplit -eq 11 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak'
elif [ $nsplit -eq 12 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al'
elif [ $nsplit -eq 13 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am'
elif [ $nsplit -eq 14 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an'
elif [ $nsplit -eq 15 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao'
elif [ $nsplit -eq 16 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao ap'
elif [ $nsplit -eq 17 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao ap aq'
elif [ $nsplit -eq 18 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao ap aq ar'
elif [ $nsplit -eq 19 ]
then
    splitlist='aa ab ac ad ae af ag ah ai aj ak al am an ao ap aq ar as'
elif [ $nsplit -eq 20 ]
then
    splitlist='aa ab ac ad ae af ah ai aj ak al am an ao ap aq ar as'
else
    echo 'Not getting split files higher than at!'
    splitlist='aa ab ac ad ae af ah ai aj ak al am an ao ap aq ar as at'
fi

echo
echo '***Starting averaging of images across pols (and any split for miriad line limit)***'
echo

for ((i=0; i<=${phasebins}-1; i++))
    do
    expmpxx=''
    expbmxx=''
    expmpyy=''
    expbmyy=''
    nsplit=0
    # average bm and mp across pols and splits (split for 256 line limit of miriad)
    for split in $splitlist
      do
      # generate short-named symbolic links for files
      ln -s ${imroot}-xx-${suffix}'-bin'${i}${split}'.mp' ${i}${split}xm
      ln -s ${imroot}-xx-${suffix}'-bin'${i}${split}'.bm' ${i}${split}xb
      ln -s ${imroot}-yy-${suffix}'-bin'${i}${split}'.mp' ${i}${split}ym
      ln -s ${imroot}-yy-${suffix}'-bin'${i}${split}'.bm' ${i}${split}yb

      expmpxx='+<'${i}${split}'xm>'${expmpxx}
      expbmxx='+<'${i}${split}'xb>'${expbmxx}
      expmpyy='+<'${i}${split}'ym>'${expmpyy}
      expbmyy='+<'${i}${split}'yb>'${expbmyy}
      nsplit=`echo ${nsplit}+1 | bc`

# original for less than 256 chars
#	expmpxx='+<'${imroot}-xx-${suffix}'-bin'${i}${split}'.mp>'${expmpxx}
#	expbmxx='+<'${imroot}-xx-${suffix}'-bin'${i}${split}'.bm>'${expbmxx}
#	expmpyy='+<'${imroot}-yy-${suffix}'-bin'${i}${split}'.mp>'${expmpyy}
#	expbmyy='+<'${imroot}-yy-${suffix}'-bin'${i}${split}'.bm>'${expbmyy}
#	nsplit=`echo ${nsplit}+1 | bc`
# original for only a few split files
#	expmp='+<'${imroot}-xx-${suffix}'-bin'${i}${split}'.mp>+<'${imroot}-yy-${suffix}'-bin'${i}${split}'.mp>'${expmp}
#	expbm='+<'${imroot}-xx-${suffix}'-bin'${i}${split}'.bm>+<'${imroot}-yy-${suffix}'-bin'${i}${split}'.bm>'${expbm}
#	nsplit=`echo ${nsplit}+2 | bc`
    done
    # need to use cut to remove superfluous + symbol
    expmpxx=`echo $expmpxx | cut -c2-`
    expbmxx=`echo $expbmxx | cut -c2-`
    expmpyy=`echo $expmpyy | cut -c2-`
    expbmyy=`echo $expbmyy | cut -c2-`

    # normalize by number of images
    expmpxx='('${expmpxx}')/'${nsplit}
    expbmxx='('${expbmxx}')/'${nsplit}
    expmpyy='('${expmpyy}')/'${nsplit}
    expbmyy='('${expbmyy}')/'${nsplit}

# original...
#    maths exp=${expmp} out=${imroot}'-i-'${suffix}'-bin'${i}$'.mp'
#    maths exp=${expbm} out=${imroot}'-i-'${suffix}'-bin'${i}$'.bm'
    maths exp=${expmpxx} out=${imroot}'-ixx-'${suffix}'-bin'${i}$'.mp'
    maths exp=${expbmxx} out=${imroot}'-ixx-'${suffix}'-bin'${i}$'.bm'
    maths exp=${expmpyy} out=${imroot}'-iyy-'${suffix}'-bin'${i}$'.mp'
    maths exp=${expbmyy} out=${imroot}'-iyy-'${suffix}'-bin'${i}$'.bm'
    maths exp='(<'${imroot}'-ixx-'${suffix}'-bin'${i}$'.mp>+<'${imroot}'-iyy-'${suffix}'-bin'${i}$'.mp>)/2' out=${imroot}'-i-'${suffix}'-bin'${i}$'.mp'
    maths exp='(<'${imroot}'-ixx-'${suffix}'-bin'${i}$'.bm>+<'${imroot}'-iyy-'${suffix}'-bin'${i}$'.bm>)/2' out=${imroot}'-i-'${suffix}'-bin'${i}$'.bm'
    # clean up temp files
    rm -rf ${imroot}'-ixx-'${suffix}'-bin'${i}$'.mp'
    rm -rf ${imroot}'-ixx-'${suffix}'-bin'${i}$'.bm'
    rm -rf ${imroot}'-iyy-'${suffix}'-bin'${i}$'.mp'
    rm -rf ${imroot}'-iyy-'${suffix}'-bin'${i}$'.bm'

    for split in $splitlist
    do
      rm ${i}${split}xm
      rm ${i}${split}xb
      rm ${i}${split}ym
      rm ${i}${split}yb
    done
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
clean map=${imroot}'-icube-'${suffix}'-sub.mp' beam=${imroot}'-icube-'${suffix}'.bm' out=${imroot}'-icube-'${suffix}'-sub.cl' niters=100 region='relpixel,boxes(-10,-10,10,10)' gain=0.03
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
