#!/bin/tcsh
#
# quick and dirty image, clean, restore, then fit
# claw, 9may09

set in=mosfxc-3c138.uvaver.uvcal1.uvredo
set outroot=3c138.1

invert vis=${in} options=mfs map=${outroot}.mp beam=${outroot}.bm sup=0
clean map=${outroot}.mp beam=${outroot}.bm out=${outroot}.cl niters=300
restor map=${outroot}.mp beam=${outroot}.bm out=${outroot}.rm model=${outroot}.cl
imfit in=${outroot}.rm object=gaussian
cgdisp in=${outroot}.rm device=1/xs
