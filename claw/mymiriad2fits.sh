#!/bin/bash


NITER=2
TMP1=`mktemp -u ./atadata.XXXX`

for y in $@ ;
  do x=`dirname $y`\/`basename $y`
  echo "Processing $x"

  uvaver vis="$x" interval=0.000000001 options=nocal,nopass,nopol out=$TMP1 || exit
  
  if [[ $x =~ 3[Cc]286 ]] ; then
    echo "Correcting coordinates for 3C286"
    puthd in=$TMP1/ra value=13:31:08.2879,hms
    puthd in=$TMP1/dec value=30:30:32.958,dms
    puthd in=$TMP1/obsra value=13:31:08.2879,hms
    puthd in=$TMP1/obsdec value=30:30:32.958,dms
  fi

  uvaver vis=$TMP1 stokes=xx,yy,xy,yx interval=0.333333333 select="-auto" options=nocal,nopass,nopol out="$x".pol || exit
  rm -rf $TMP1
  fits in="$x".pol op=uvout out="$x".pol.fits
done
