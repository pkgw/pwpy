#! /bin/tcsh -f
#
# quick and dirty image, clean, restore
# claw, 9may09

set in=$argv[1]
set outroot=${in}
set cleanreg='-50,-50,50,50'

# first clean up
set stokes=i
rm -rf ${outroot}-${stokes}.*
#image stokes i
invert vis=${in} options=mfs map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm stokes=${stokes} robust=0
clean map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm out=${outroot}-${stokes}.cl niters=400 region='relpixel,boxes('${cleanreg}')'
restor map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm out=${outroot}-${stokes}.rm model=${outroot}-${stokes}.cl

# proceed to other stokes
foreach stokes (q u v)
    # first clean up
    rm -rf ${outroot}-${stokes}.*

    #image
    invert vis=${in} options=mfs map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm stokes=${stokes} robust=-2 imsize=250,100
    clean map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm out=${outroot}-${stokes}.cl niters=200 region='relpixel,boxes('${cleanreg}')'
    restor map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm out=${outroot}-${stokes}.rm model=${outroot}-${stokes}.cl
end
