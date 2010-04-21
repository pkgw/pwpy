#!/bin/csh -f

set invis=$1
set vis=$2
set tvok=$3

rm -rf $vis.mp $vis.bm $vis.cl $vis.cm $vis.rs
#invert vis=$invis map=$vis.mp beam=$vis.bm cell=15 imsize=1024 options=mfs,double robust=5 select="pol(xx,yy)" 
invert vis=$invis map=$vis.mp beam=$vis.bm cell=15 imsize=1024 options=mfs,double  stokes=ii sup=0
clean map=$vis.mp beam=$vis.bm out=$vis.cl niters=3000
restor map=$vis.mp beam=$vis.bm model=$vis.cl out=$vis.cm 
rm -rf $vis.cmf
restor map=$vis.mp beam=$vis.bm model=$vis.cl out=$vis.cmf fwhm=100,100

if ($tvok == "y") then

  cgdisp in=$vis.cmf device=/xs labtyp=hms

endif
