
#
# quick and dirty image, clean, restore, then fit
# claw, 9may09

set in=$argv[1]
set outroot=${in}

# clean up
rm -rf ${in}*.*

#image
foreach stokes (i q u v)
    invert vis=${in} options=mfs map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm sup=0 stokes=${stokes} #line=ch,25,100
    clean map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm out=${outroot}-${stokes}.cl niters=300
    restor map=${outroot}-${stokes}.mp beam=${outroot}-${stokes}.bm out=${outroot}-${stokes}.rm model=${outroot}-${stokes}.cl
end
