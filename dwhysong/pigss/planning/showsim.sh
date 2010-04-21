#!/bin/bash

MAPARGS='';
DIR='sim'

rm -f unobs unobs2 obs new *.reg *jpg
cat pigss_ngalcap.catalog.list | ./ata2rad.pl | sort -n > unobs2

#for i in `seq 0 40` ;
for i in 3 ;
	do if [ -f $DIR/targets."$i" ] ;
	  then rm ds9.reg
	  grep -f $DIR/targets."$i" pigss_ngalcap.catalog.list | ./ata2rad.pl > new
	  grep -f $DIR/possible."$i" pigss_ngalcap.catalog.list | ./ata2rad.pl > pos
	  ./map.pl $MAPARGS -c green -r new -o ds9.reg
	  ./map.pl $MAPARGS -c red -r pos -o ds9.reg
	  if [ -f obs ]; then ./map.pl $MAPARGS -c yellow -r obs -o ds9.reg; fi
	  cat new pos obs > all
	  cat all unobs2 | sort -n | uniq -u > unobs
	  ./map.pl $MAPARGS -c blue -r unobs -o ds9.reg
	  ds9 -geometry 2000x1000 -cmap BB -log -fits nvss.fits -zoom 0.7 -regions load ds9.reg -saveimage jpeg $DIR/sim-"$i".jpg -exit
	  cat new >> obs
	  #/sbin/getkey
	fi
done
