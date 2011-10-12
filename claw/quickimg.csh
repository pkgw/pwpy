#! /bin/tcsh -f
#
# quick and dirty image, clean, restore
# claw, 9may09

set in=$argv[1]
set outroot=$in:r
set cleanreg='-30,-30,30,30'
set ims=150
set cs=60

# first clean up
set stokes=i
rm -rf ${outroot}-${stokes}.*
#image stokes i
invert vis=${in} options=mfs,double map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm cell=${cs} imsize=${ims},${ims} stokes=$stokes
clean map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm out=${outroot}-${stokes}.cl region='relpixel,boxes('${cleanreg}')'
restor map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm out=${outroot}-${stokes}.rm model=${outroot}-${stokes}.cl

# skip the rest...
#exit 0

# proceed to other stokes
foreach stokes (q u v)
    # first clean up
    rm -rf ${outroot}-${stokes}.*

    #image
    invert vis=${in} options=mfs map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm stokes=${stokes} robust=0 imsize=${ims},${ims} cell=$cs
    clean map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm out=${outroot}-${stokes}.cl niters=200 region='relpixel,boxes('${cleanreg}')'
    restor map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm out=${outroot}-${stokes}.rm model=${outroot}-${stokes}.cl
end
