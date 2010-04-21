#!/bin/csh -f

set pfx=$1

set n1=0
if (-e ${pfx}_1.linmos) then
  set n1=`imstat in=${pfx}_1.linmos | gawk '/plane/ && /Frequency/ {getline; print 1.0*$5}'`
endif
echo $n1

set n2=0
if (-e ${pfx}_2.linmos) then
  set n2=`imstat in=${pfx}_2.linmos | gawk '/plane/ && /Frequency/ {getline; print 1.0*$5}'`
endif
echo $n2

rm -rf ${pfx}_avg.linmos
if ( $n1 != 0 && $n2 != 0 ) then
  set wsum=`echo $n1 $n2 | gawk '{print (1/$1^2 + 1/$2^2)}'`
  set w1=`echo $n1 $wsum | gawk '{print 1/$2/$1^2}'`
  set w2=`echo $n2 $wsum | gawk '{print 1/$2/$1^2}'`
  maths exp="<${pfx}_1.linmos>*$w1+<${pfx}_2.linmos>*$w2" out=${pfx}_avg.linmos
else 
  if ( $n1 != 0 ) then
    cp -r ${pfx}_1.linmos ${pfx}_avg.linmos
  endif
  if ( $n2 != 0 ) then
    cp -r ${pfx}_2.linmos ${pfx}_avg.linmos
  endif
endif
set navg=`imstat in=${pfx}_avg.linmos | gawk '/plane/ && /Frequency/ {getline; print 1.0*$5}'`
echo $navg

echo ""
