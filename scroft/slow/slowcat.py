#!/usr/bin/env python

# Runs sfind on a mosaic image, determines mosaic gains, discards sources
# from sfind.log in regions with gain lower than some cutoff
# Works with multiple epochs, preserving only sources that are within the 
# detection region in all epochs

# Modified from original teeth-grindingly slow Perl version
# Steve Croft 2/18/11
# Modified to use corresponding gain images, *.gain
# and correct catalog values for the measured gain

import sys
import numpy as np
import scipy as sp
import pyfits
import pywcs
import re
import astropysics as ap
import astropysics.coords as ac
import os
import shutil
import argparse 

parser = argparse.ArgumentParser(description='Source Locater and Outburst Watcher Catalog Generator (SLOWcat)')
parser.add_argument('images',help='input images - must be MIRIAD format with filenames starting with mos and ending with .cm',nargs="+")
parser.add_argument('--newsfind',help='use new sfind',action="store_true",default=False)
parser.add_argument('--psfsize',help='use sfind psfsize option',action="store_true",default=False)
parser.add_argument('--alpha',help='alpha if using new SFIND (see mirhelp sfind)',type=float,default=2)
args = parser.parse_args()

# gains above this value are "good"
gaincut = 0.2

# SFIND optiosn
sfopt2 = "xrms=5 rmsbox=107 options=auto,old"

if (args.newsfind):
# note pbcorr doesn't work properly for linmos - we are now correcting in software
# xrms has no effect in newsfind
    sfopt2 = "rmsbox=50 options=auto alpha="+args.alpha

if (args.psfsize):
    sfopt2 = "xrms=5 rmsbox=107 options=auto,old,psfsize"

if (args.psfsize and args.newsfind):
# xrms has no effect in newsfind
    sfopt2 = "rmsbox=50 options=auto,psfsize alpha="+args.alpha

print "SFIND options",sfopt2

txnames = []
slnames = []
finames = []
ganames = []

nfiles = 0

for ar in sys.argv[1:]:
    inf = re.match(r'(.+).cm',ar)
    if inf:
        nfiles += 1
        froot = inf.group(1)
#        print froot
        txnames.append ('sfind.'+froot+".orig")
        slnames.append ('sfind.'+froot+".slow")
        finames.append (ar)
        gami = froot+".gain"
        gafi = froot+".gain.fits"
        os.system("fits in="+gami+" out="+gafi+" op=xyout")
        ganames.append (gafi)


if "nonvss" in sys.argv:
    print "Skipping NVSS cull"
else:
    txnames.append ('NVSS.txt')
    slnames.append ('NVSS.slow')
    finames.append ('coadd.cm')
    ganames.append ('coadd.fits')

for infile,txfile,slfile,gaim in zip(finames,txnames,slnames,ganames):
    print "Running sfind on",infile
    try:
        os.remove("sfind.log")
    except OSError:
        pass
    sfopt = "in="+infile+" "+sfopt2
    os.system("sfind "+sfopt)
    os.rename("sfind.log",txfile)
    print "Output SFIND file is",txfile

# open gain image
    hdulist = pyfits.open(gaim)
# data is 4-D (including freq and stokes)
    gain4 = hdulist[0].data
# just read RA and Dec from the header
    wcs = pywcs.WCS(hdulist[0].header,naxis=['longitude','latitude'])
# just save RA and Dec info from the 4-D data
    gain = np.array(gain4[0,0])

# size of gain image
    gx = gain.shape[0]
    gy = gain.shape[1]

    print txfile,"->",slfile

    tx = open(txfile, "r")
    slow = file(slfile, "w")

    for line in tx:        
        if (not re.match(r'#',line) and not re.search(r'\*\*\*',line)):
#                print line
                field = line.split()
                ra = ac.AngularCoordinate(field[0]).d
                dec = ac.AngularCoordinate(field[1],sghms=False).d
# NVSS RA is in hours; convert to degrees:
                if re.match('NVSS',txfile):
                    ra *= 15.0
        # array of RA and Dec positions
                skycrd = np.array([[ra,dec]])
#                print skycrd
                
                # convert RAs and Decs to pixel coordinates
                p = wcs.wcs_sky2pix(skycrd,1)
                x = p[0,1]
                y = p[0,0]
                if (y >= 0 and y < gy and x >= 0 and x < gx):
                    gval = gain[x.astype(int),y.astype(int)]
#                    print ra,dec,val
#                    oline = str(gval)+' '+line
                    if re.match('NVSS',txfile):
                        oline = line
                    else: 
                        pf = float(field[4]) / gval
                        pfe = float(field[5]) / gval
                        inf = float(field[6]) / gval
                        rmb = float(field[10]) / gval
                        rmf = float(field[11]) / gval
#                    print '%12s%12s%8s%8s%10.3f%7.3f%10.3f%6s%6s%6s%7.3f%7.3f%6s' % (field[0],field[1],field[2],field[3],pf,pfe,inf,field[7],field[8],field[9],rmb,rmf,field[12])
                        print '%12s%12s %7s %7s %9.3f %6.3f %9.3f %5s %5s %5s %6.3f %6.3f %5s %5.3f' % (field[0],field[1],field[2],field[3],pf,pfe,inf,field[7],field[8],field[9],rmb,rmf,field[12],gval)
                        oline = '%12s%12s %7s %7s %9.3f %6.3f %9.3f %5s %5s %5s %6.3f %7.3f %5s\n' % (field[0],field[1],field[2],field[3],pf,pfe,inf,field[7],field[8],field[9],rmb,rmf,field[12])
                    if (gval > gaincut):
                        slow.write(oline)
                
    slow.close()
    tx.close()
#print(val)


