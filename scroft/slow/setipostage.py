#!/usr/bin/env python
#
# Plot up ATA / NVSS postage stamps
#
# S. Croft 2008/08/26
# SQL version 2010 May
# Pythonized 2011 June
#
# Usage: setipostage.py images
# images must be in fits format
# must specify coadd.fits first in arg list if present 

from sys import argv
import sqlite3
#import numpy as np
import matplotlib
matplotlib.use('PDF')
#import matplotlib.pyplot as plt
from math import sqrt
from aplpy import FITSFigure
import pyfits
from re import match
from datetime import datetime
import resource
import os
from operator import itemgetter

resource.setrlimit(resource.RLIMIT_NOFILE, (1024,1024))

imn = 0
allimr = []
allimrs = []
obsdates = {}
fitshdus = {}
mjsel = ""
notimesort = 0
eps = {}

if(not notimesort):
        for im in argv[1:]:
                m = match(r'coadd.fits',im)
                if m:
#			allimr.append('coadd')
			allimrs.append('coadd.fits')
                else:
                        m = match(r'(\S+).fits',im)
                        if m:
                              imroot = m.group(1)
                              pjd = os.popen("gethd in="+imroot+".cm/obstime").read()
                              eps[im] = pjd.rstrip()
#       allimrs = sorted(eps.iteritems(), key=lambda (k,v):v)
        allimrsa = sorted(eps.iteritems(), key=lambda (k,v):(v,k))
        allimrs = allimrs + map(itemgetter(0),allimrsa)
        print "\nImages sorted in time order are "+' '.join(allimrs)

for ar in allimrs:
#    print ar
    m = match(r'(\S+).fits',ar)
    if m:
        imroot = m.group(1)
#        print imroot
        allimr.append(imroot)
        imfits = imroot+'.fits'
        hdu = pyfits.open(imfits)
        prihdu = hdu[0]
        fitshdus[imroot] = prihdu
        obsdate = prihdu.header['DATE-OBS']
        obsdates[imroot] = obsdate
#        hdu.close()
        imn += 1
    m = match(r'(J\d\d\d\d\d\d.\d\d\d\d\d\d)',ar)
    if m:
        mjsel = m.group(1)

dbfile = "slow.db"
dbh = sqlite3.connect(dbfile)
dbc = dbh.cursor()

if (mjsel == ""):
    mjids = """SELECT mjid, ra, decl FROM master WHERE mjid <> 'J' GROUP BY mjid"""
else:
    mjids = """SELECT mjid, ra, decl FROM master WHERE mjid in ('"""+mjsel+"""') GROUP BY mjid"""
print mjids
dbc.execute(mjids)
mjo = dbc.fetchall()

#print mjo

eps = """SELECT COUNT (DISTINCT epname) FROM master"""
dbc.execute(eps)
nep = dbc.fetchone()[0]

# number of postage stamps per block
num_per_block = 6
panel_width = 1.0 / num_per_block

for (mj, rac, dec) in mjo:
# start on the first block of postage stamps
#    mj = mji[0]
    print "Starting "+mj+" (image center "+str(rac)+", "+str(dec)+")"
    psblock = 1
    psnum = 1
    epoch = 1
    for inr in allimr:
        if inr == "coadd":
            infile = "coadd.fits"
            epname = "ATA_Coadd"
            bcol = 'blue'
        elif inr== "NVSS":
            infile = "NVSS.fits"
            epname = "NVSS"
            bcol = 'cyan'
        else:
            epname = "ATA"+str(epoch)
            infile = inr+".fits"
            epoch += 1
            bcol = 'green'
        print "Epoch "+epname
        matchj = """SELECT fi, rb FROM master WHERE (mjid == '"""+mj+"""' and epname == '"""+epname+"""')"""
        dbc.execute(matchj)
        nmatch = 0
        fit = 0
        rbst = 0
        for (fi,rb) in dbc.fetchall():
            fit += fi
# sum errors in quadrature
            rbst += rb**2
#            print fi,rb
            nmatch += 1

        rbt = sqrt(rbst);
        print "Block "+str(psblock)+", panel "+str(psnum)
        print "Flux = "+str(fit)+" +/- "+str(rbt)+"; total matches = "+str(nmatch)

        blcx = (psnum - 1) * panel_width

        obsdate = obsdates[inr]
        tits = epname+" "+str(fit)+"+/-"+str(rbt)+" ("+str(nmatch)+")"
#        print "Title: "+tits

        if fit == 0:
            bcol = 'red'

        if (psnum == 1):
            if (psblock > 1):
                gc.save(oname,dpi=75)
                del gc
                fig.clf()
                print "Saved "+oname
            oname = "%s_%03d.pdf" % (mj,psblock)
#            oname = mj+"_"+str(psblock)+".pdf"
            print "New file: "+oname
            fig = matplotlib.pyplot.figure(figsize=(3/panel_width,3))
        gc = FITSFigure(fitshdus[inr],figure=fig,subplot=[blcx,0,panel_width,1])
        gc.set_tick_labels_xformat('hh:mm:ss')
        gc.set_tick_labels_yformat('dd:mm:ss')
        gc.set_tick_labels_font(size='xx-small')
        gc.set_axis_labels_font(size='xx-small')
        try:
            gc.recenter(rac,dec,radius=0.5)
            gc.show_grayscale(invert=True)
        except:
            print str(rac)+", "+str(dec)+" falls outside image for "+infile
        gc.add_label(0.05,0.95,tits,relative=True,size='x-small',horizontalalignment='left')
        gc.add_label(0.05,0.90,obsdate,relative=True,size='x-small',horizontalalignment='left')
        gc.frame.set_color(bcol)
        if (psnum > 1):
            gc.hide_yaxis_label()
            gc.hide_ytick_labels()
        psnum +=1
        if psnum > num_per_block:
            psnum = 1
            psblock += 1

#    fig.show()
# blank remaining panels in this block if necessary
    if psnum < num_per_block:
#        ax2 = fig.add_axes([blcx,0,1-blcx,1],color='white')
        matplotlib.patches.Rectangle((0.99,0),0.01,1,figure=fig,fill=True)
#         matplotlib.patches.Rectangle((blcx,0),1-blcx,1,color='white',figure=fig,fill=True)
    gc.save(oname,dpi=75)
    del gc
    fig.clf()
    print "Saved "+oname

dbh.close()

print "setipostage.py completes at "+ str(datetime.now())

