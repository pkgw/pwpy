#!/bin/bash

rm -rf .tmpcatfile
TEMP=`getopt -o hr:n: --long help,refant:,nchan: -n 'atapolcal.sh' -- "$@"`
if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around `$TEMP': they are essential!
eval set -- "$TEMP"

refant=1;
nchan=103; # or 8
startch=100;
endch=923
while true ; do
	case "$1" in
		-h|--help) echo "atacalpol.sh [-r refant] [-n channels] [-h] datafile ..." ; shift ; exit ;;
		-r|--refant) refant=$2 ; shift 2 ;;
		-n|--nchan) nchan=$2 ; shift 2 ;;
		--) shift ; break ;;
		*) echo "Internal error!" ; exit 1 ;;
	esac
done

files=$@;
TMPDIR=/dev/shm
echo "Reference antenna: $refant"
echo "Using slices of $nchan channels"
echo "Will process: $files"


for file in $files;
  do for i in `seq $startch $nchan $endch` ;
    do uvaver vis=$file out="$TMPDIR"/"$file"-"$i" line=ch,1,$i,$nchan interval=0.000001 options=nocal,nopass,nopol
    echo '**************************'
    echo "  Calibrating $file-$i"
    echo '**************************'
    mfcal vis=$TMPDIR/$file-$i refant=$refant interval=10 tol=0.00005
    gpcal vis=$TMPDIR/$file-$i refant=$refant options=xyref,polref interval=2880
    # or loop through gpcal/mfcal to iterate to gain and leakage solution?
    echo $TMPDIR/$file-$i >> .tmpcatfile
  done
  # merge cals into original data
  uvcat vis=@.tmpcatfile out=$file-join
  rm -rf `cat .tmpcatfile`
done
