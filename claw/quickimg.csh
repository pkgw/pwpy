#! /bin/tcsh -f
#
# quick and dirty image, clean, restore, then fit
# claw, 9may09

set in=$argv[1]
set outroot=${in}

foreach stokes (i q u v)
    # first clean up
    rm -rf ${outroot}-${stokes}.*

    #image
    invert vis=${in} options=mfs map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm sup=0 stokes=${stokes} imsize=215,80
    clean map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm out=${outroot}-${stokes}.cl niters=1000
    restor map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm out=${outroot}-${stokes}.rm model=${outroot}-${stokes}.cl
end
