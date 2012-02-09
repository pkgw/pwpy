#!/usr/bin/env python

import sys
import os
import shutil
import numpy as np
import scipy as sp
import pyfits
import pywcs
import re
import astropysics as ap
import astropysics.coords as ac
import argparse
import math

parser = argparse.ArgumentParser(description='Get NVSS catalog over area at least as large as input image.')
parser.add_argument('image',help='input image')
parser.add_argument('-f','--fmin',help='minimum NVSS flux density to include',default=1)
parser.add_argument('-p','--usepk',help='use peak instead of integrated flux density',action='store_true')
parser.add_argument('-r','--radius',help='radius from center of image to search (overrides automatically determined value')
parser.add_argument('-n','--nvss',help='NVSSlist directory (see ftp://nvss.cv.nrao.edu/pub/nvss/CATALOG/README)',default="/Volumes/grumpy/scroft/NVSS/")
args = parser.parse_args()

nvssdir = args.nvss
usepeak = 1
fmax = "1.0E10"

if not args.usepk:
    print "Using integrated (deconvolved) values"
    usepeak = 0

inim = args.image 


nvssex = nvssdir+"NVSSlist"
nvsscfg = nvssdir+"NVSSlist.cfg"
tfile = "/tmp/nvssin.tmp"
nfile = inim+".NVSS"
ptxt = inim+".nvss.txt"
olay = inim+".olay"

shutil.copy(nvsscfg,".")

radius = args.radius

hdulist = pyfits.open(inim)
wcs = pywcs.WCS(hdulist[0].header,naxis=['longitude','latitude'])
footprint = wcs.calcFootprint()
# image centroid
imcen = (footprint[0]+footprint[1]+footprint[2]+footprint[3])/4
# distance of the four corners from the centroid
if not args.radius:
    for ft in footprint:
        r = (ft - imcen)
        rd = math.sqrt(r[0]**2 + r[1]**2)
        if rd > radius:
            radius = rd
# allow a small buffer region
    radius *= 1.1

# convert to arcsec
radius=radius*3600.0

# hms, dms tuples
#ra = ac.AngularCoordinate(imcen[0]).hms
#dec = ac.AngularCoordinate(imcen[1]).dms
# hms, dms strings
ra = ac.AngularCoordinate(imcen[0]).getHmsStr(secform='%05.2f', sep=' ')
dec = ac.AngularCoordinate(imcen[1]).getDmsStr(secform='%05.2f', sep=' ', sign=False)

print "Image centroid is",imcen
print "Search radius is",radius,"arcsec"
#print ra, dec

# Create input file for NVSSlist
sc = open(tfile, "w")
# Comments are NVSSlist prompts
# Enter any output file name [terminal] {CR}
sc.write(nfile+"\n")
# Enter any input field list file name [ask] {CR}
sc.write("\n")
# Enter equinox code 1=B1900 2=B1950 3=J2000 [3] {3}
sc.write("3\n")
# Enter 0=Deconvolved 1=Fitted 2=Raw values [0] {0}
sc.write(str(usepeak)+"\n")
# Enter minimum, maximum flux density (mJy) [0,1.0E10] {$fmin,$fmax}
sc.write(str(args.fmin)+","+str(fmax)+"\n")
# Enter minimum percent pol. flux density [0] {0}
sc.write("0\n")
# Enter object name [none} {CR}
sc.write("\n")
# Enter central RA (hh mm ss.ss) {$rahr $ramn $rasc}
sc.write(ra+"\n")
# Enter central Dec (sdd mm ss.s) {$dedg $demn $desc}
sc.write(dec+"\n")
# Search radius, verification radius in arcsec [15,0] {$rad,0}
sc.write(str(radius)+",0\n")
# Search box halfwidth in hr,deg [12,180]
sc.write("\n")
# Max, min abs gal latitude in deg [0,90]
sc.write("\n")
sc.close()

try:
    os.remove(nfile)
except OSError:
    pass

print "Querying NVSS catalog ..."
os.system(nvssex+" < "+tfile+" >& /dev/null")
os.remove(tfile)
print "Done. Writing output catalog",ptxt,"..." 

nf = open(nfile,"r")
pt = open(ptxt,"w")

for line in nf:
    m = re.match(r'(\d+)\s+(\d+)\s+(\d+\.\d\d)\s+([+-])(\d+)\s+(\d+)\s+(\d+\.\d)......\s*(\d+\.\d)',line)
    if m:
        rah = m.group(1)
        ram = m.group(2)
        ras = m.group(3)
        raa = rah+"h"+ram+"m"+ras+"s"
        sign = m.group(4)
        ded = m.group(5)
        dem = m.group(6)
        des = m.group(7)
        flux = float(m.group(8))
# flux errors are on the next line
        line2 = nf.next()
        field = line2.split()
        fluxe = float(field[3])
        dea = sign+ded+"d"+dem+"m"+des+"s"
        rafp = ac.AngularCoordinate(raa).h
        defp = ac.AngularCoordinate(dea).d
        lout =  "%9.5f %9.5f %9.1f %4.1f\n" % (rafp, defp, flux, fluxe)
        pt.write(lout)

nf.close()
pt.close()

print "Done."
