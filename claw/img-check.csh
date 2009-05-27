#!/bin/tcsh
#
# quick and dirty image, clean, restore, then fit
# claw, 9may09

set in=hexc-3c138-p0-2000.uvaver7
set outroot=3c138-p0-2000.uvaver7

invert vis=hexc-3c138-p0-2000.uvaver7 options=mfs map=${outroot}.mp beam=${outroot}.bm sup=0 #line=ch,25,100
clean map=${outroot}.mp beam=${outroot}.bm out=${outroot}.cl niters=300
restor map=${outroot}.mp beam=${outroot}.bm out=${outroot}.rm model=${outroot}.cl
imfit in=${outroot}.rm object=gaussian out=${outroot}.rm.resid options=residual
cgdisp in=${outroot}.rm.resid device=1/xs range=0,0,log,-2
