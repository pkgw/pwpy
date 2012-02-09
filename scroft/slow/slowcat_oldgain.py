#!/usr/bin/env python

# Runs sfind on a mosaic image, determines mosaic gains, discards sources
# from sfind.log in regions with gain lower than some cutoff
# Works with multiple epochs, preserving only sources that are within the 
# detection region in all epochs

# Modified from original teeth-grindingly slow Perl version
# Steve Croft 2/18/11

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

# gains above this value are "good"
gaincut = 0.7

# SFIND optiosn
sfopt2 = "xrms=5 rmsbox=107 options=auto,pbcorr,old"

if "newsfind" in sys.argv:
    sfopt2 = "xrms=5 rmsbox=25 options=auto,pbcorr"

if "psfsize" in sys.argv:
    sfopt2 = "xrms=5 rmsbox=107 options=auto,pbcorr,old,psfsize"

if "newsfind" and "psfsize" in sys.argv:
    sfopt2 = "xrms=5 rmsbox=25 options=auto,pbcorr,psfsize"

print "SFIND options",sfopt2

try:
    os.remove("allim.gain.fits")
except OSError:
    pass

txnames = []
slnames = []
finames = []
ganames = []
rgnames = []
grnames = []

nfiles = 0

shutil.rmtree("tmp.gain",ignore_errors=True)
shutil.rmtree("tmp2.gain",ignore_errors=True)
shutil.rmtree("allim.gain",ignore_errors=True)


for ar in sys.argv[1:]:
    inf = re.match(r'(.+).cm',ar)
    if inf:
        nfiles += 1
        froot = inf.group(1)
#        print froot
        txnames.append ('sfind.'+froot+".orig")
        slnames.append ('sfind.'+froot+".slow")
        finames.append (ar)
        ganames.append (froot+".gain")
        rgnames.append (froot+".regrid")
        grnames.append (froot+".grg")

for infile,gafile,rgfile,grfile,txfile in zip(finames,ganames,rgnames,grnames,txnames):
#    print infile,gafile,rgfile,grfile
    shutil.rmtree(gafile,ignore_errors=True)
    shutil.rmtree(rgfile,ignore_errors=True)
    shutil.rmtree(grfile,ignore_errors=True)

    print "\nCreating gain image",gafile
    mosopt = "in="+infile+" gain="+gafile
    os.system("mossen "+mosopt)
    print "Regridding input image",infile,"->",rgfile
    regopt = "in="+infile+" tin="+finames[0]+" out="+rgfile+" axes=1,2"
    os.system("regrid "+regopt)
    print "Regridding gain image",gafile,"->",grfile
    regopt = "in="+gafile+" tin="+ganames[0]+" out="+grfile+" axes=1,2"
    os.system("regrid "+regopt)

    print "Running sfind on",infile
    try:
        os.remove("sfind.log")
    except OSError:
        pass
    sfopt = "in="+infile+" "+sfopt2
    os.system("sfind "+sfopt)
    os.rename("sfind.log",txfile)
    print "Output SFIND file is",txfile

# better to write all these as FITS files, read them in as arrays, and multiply them all together

if nfiles == 1:
    shutil.copytree(gafile,"allim.gain")
if nfiles == 2:    
    os.system("maths exp=\'(<"+grnames[0]+">*<"+grnames[1]+">)\' out=allim.gain")
if nfiles > 2:
    print "maths exp=\'(<"+grnames[0]+">*<"+grnames[1]+">)\' out=tmp.gain"
    os.system("maths exp=\'(<"+grnames[0]+">*<"+grnames[1]+">)\' out=tmp.gain")
    fnum = 0
    for gfile in grnames:
#        print gfile
        if fnum > 0 and fnum < nfiles - 1:
            print "maths exp=\'(<tmp.gain>*<"+grnames[fnum+1]+">)\' out=tmp2.gain"
            os.system("maths exp=\'(<tmp.gain>*<"+grnames[fnum+1]+">)\' out=tmp2.gain")
            shutil.rmtree("tmp.gain",ignore_errors=True)
            os.rename("tmp2.gain","tmp.gain")
        fnum += 1
    os.rename("tmp.gain","allim.gain")

os.system("fits in=allim.gain out=allim.gain.fits op=xyout")

# open gain image
hdulist = pyfits.open('allim.gain.fits')
# data is 4-D (including freq and stokes)
gain4 = hdulist[0].data
# just read RA and Dec from the header
wcs = pywcs.WCS(hdulist[0].header,naxis=['longitude','latitude'])
# just save RA and Dec info from the 4-D data
gain = np.array(gain4[0,0])

# size of gain image
gx = gain.shape[0]
gy = gain.shape[1]

if "nonvss" in sys.argv:
    print "Skipping NVSS cull"
else:
    txnames.append('NVSS.txt')
    slnames.append('NVSS.slow')

for txfile, slfile in zip(txnames, slnames):
    print txfile,"->",slfile

    tx = open(txfile, "r")
    slow = file(slfile, "w")

    for line in tx:        
        if not re.match(r'^#',line):
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
                    val = gain[x.astype(int),y.astype(int)]
#                    print ra,dec,val
                    if (val > gaincut):
                        slow.write(line)
                
    slow.close()
    tx.close()
#print(val)


