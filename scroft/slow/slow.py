#!/usr/bin/env python
# Source Locator and Outburst Watcher
# Produces a PDF with postage stamps of ATA sources from multiple epochs which match NVSS sources
#
# Steve Croft 2008/08/19
# Rewritten in Perl 2009/07/06
# Modified to use SQL 2010 May
# Rewritten in Python 2011 June
# Requires MIRIAD, Java (must be installed by user and in path), sqlite3
# Python (modules astropysics,)
# You can test that these are installed as follows:
# miriad -h
# java -version
# sqlite3 -version
# python -V
#
# Also requires Skyview Java script (installed locally by INSTALL script)
# plus cfitsio, NVSSlist and NVSS catalog (installed locally by INSTALL script)
# plus a whole slew of Perl and Python scripts (supplied as part of install):
# getnvss.py
# slowcat.pl
# matchcolnl.pl
# setierrcirc.pl
# setisortmax.pl
# setinvss.pl
# addjid.pl
# atanvssseticm.pl
# setipdf.pl
# setipngsql.pl
#
#
# NB - SLOW may delete files in the working directory; create a new directory and copy the input maps there before running
# NB - the presence of additional sfind files, mosaics, etc. in the working directory may cause SLOW not to run as expected
#      although generally a restart from a previous run of SLOW is possible (but may not produce the expected results).
#      The default switches should allow SLOW to run in a directory containing nothing but input ATA mosaics.
#
# TO DO - option to reject sources that are less than n sigma from sfind catalogs - configurable sfind options?
# TO DO - allow an input catalog other than NVSS - can currently fudge this by giving nvsscat=0 and providing an input catalog called NVSS.txt
# TO DO - Generate SQL database in slowcat.pl instead of setisql.pl - flag sources in bad regions using SQL

from sys import exit
import os
import argparse
from re import match
import shutil
from operator import itemgetter

parser = argparse.ArgumentParser(description='Source Locater and Outburst Watcher (SLOW)')
parser.add_argument('images',help='input images - must be MIRIAD format with filenames starting with mos and ending with .cm',nargs="+")
parser.add_argument('--notimesort',help='don\'t sort input images into time order based on headers',action="store_true",default=False)
parser.add_argument('--nonvsscat',help='don\'t get NVSS catalog',action="store_true",default=False)
parser.add_argument('--nogencat',help='don\'t generate SFIND culled catalogs',action="store_true",default=False)
parser.add_argument('--oldslowcat',help='use old slowcat gain method (1 or 0)',action="store_true",default=False)
parser.add_argument('--oldsfind',help='use old sfind',action="store_true",default=False)
parser.add_argument('--nopsfsize',help='don\'t use psfsize option in sfind',action="store_true",default=False)
parser.add_argument('--matchrad',help='match radius',type=float,default=75.0)
parser.add_argument('--fmin',help='NVSS minimum flux',type=float,default=0.0)
# *** for testing purposes, can set fmin to be high, either here or on command line, so that NVSS catalog
# *** is smaller and script runs more quickly
parser.add_argument('--nomkfits',help='don\'t make 2D FITS images of input files',action="store_true",default=False)
parser.add_argument('--noseti',help='don\'t run Steve\'s Excellent Transient Identifier',action="store_true",default=False)
parser.add_argument('--sort',help='output sort method',default="sortmaxata")
parser.add_argument('--coadd',help='make coadd image',action="store_true",default=False)
parser.add_argument('--swarp',help='use SWARP to make coadd image',action="store_true",default=False)
parser.add_argument('--nonvsspost',help='don\'t get NVSS postage stamps',action="store_true",default=False)
#parser.add_argument('-m','--nvssmir',help='generate MIRIAD versions of NVSS postage stamps?',default=1)
parser.add_argument('--noeppost',help='don\'t generate FITS postage stamps from input files',action="store_true",default=False)
parser.add_argument('--norejbl',help='don\'t reject sources where more than 200 pixels are blanked?',action="store_true",default=False)
parser.add_argument('--nofluxgr',help='don\'t generate flux graphs?',action="store_true",default=False)
#parser.add_argument('--postps',help='don\'t generate postscript postage stamps?',action="store_false",default=True)
parser.add_argument('--nocomball',help='don\'t combine graphs and postage stamps into a single PDF?',action="store_true",default=False)
#parser.add_argument('--html',help='don\'t generate HTML file?',action="store_false",default=True)
args = parser.parse_args()

# ********** MAKE FITS FILES FIRST, THEN TEST FOR BLANKS AT CATALOG CREATION
# AND MATCHING; COMBINE SLOWCAT.PY AND SETISQL.PL

imn = 0
allimr = []
allim = []
allimreg = []
allroot = []
allimf = []
eps = {}

if(not args.oldslowcat and not args.coadd):
    if (not os.path.exists("coadd.gain")):
        exit("Must supply mosaic gain images, e.g., coadd.gain, for catalog-based gain correction, or use oldslowcat")

for arg in args.images:
    m = match(r'(\S+).cm',arg)
    if m:
		imroot = m.group(1)
		allimr.append(imroot)
		imn += 1
                if(not args.oldslowcat):
                   if (not os.path.exists(imroot+".gain")):
                       exit("Must supply mosaic gain images, e.g., "+imroot+".gain, for catalog-based gain correction, or use oldslowcat")


print "Input images are "+' '.join(allimr)
	
if(not args.notimesort):
	for im in allimr:
		pjd = os.popen("gethd in="+im+".cm/obstime").read()
		eps[im] = pjd.rstrip()
#	allimrs = sorted(eps.iteritems(), key=lambda (k,v):v)
	allimrsa = sorted(eps.iteritems(), key=lambda (k,v):(v,k))
	allimrs = map(itemgetter(0),allimrsa)
	print "\nImages sorted in time order are "+' '.join(allimrs)
else:
	allimrs = allimr

print "\n"
#print allimrs

for imr in allimrs:
# if your images aren't all registered to the same reference, you may want to regrid if you want slow to generate a coadd
#	inimreg = imr+".regrid"
# but we'll assume here that they are:
	inimreg = imr+".cm"
	inim = imr+".cm"
        inimf = imr+".fits"
        allimf.append(inimf)
	allim.append(inim)
	allimreg.append(inimreg)

allims = ' '.join(allim)
allimregs = ','.join(allimreg)
allimroots = ' '.join(allimrs)
allimfs = ' '.join(allimf)

try:
	os.remove("coadd.fits")
except OSError:
	pass


if (args.coadd and imn > 1):
	print "\n*** Creating the coadd image ***\n\n"
    
	shutil.rmtree("coadd.cm",ignore_errors=True)
	shutil.rmtree("coadd_tmp????.fits",ignore_errors=True)
	if (args.swarp):
        ## SWARP method
        #   # copy the SWarp config file
		shutil.copytree("/o/scroft/h/scripts/slow/default.swarp",".")
		os.system("swarp "+allims)
		os.system("fits in=coadd.fits out=coadd.cm op=xyin")
	else:
		os.system("linmos in="+allimregs+" out=coadd.cm options=taper")
else:
	if (not os.path.exists("coadd.cm")):
		exit("Coadd file coadd.cm does not exist -- either set slow.py to create this automatically, or provide it\n\n")
	else:
		print "Using provided coadd image, coadd.cm\n"

os.system("fits in=coadd.cm out=coadd.fits op=xyout")

if (not args.nonvsscat):
	print "\n*** Getting NVSS catalog ***\n\n"
	os.system("/o/scroft/h/scripts/slow/getnvss.py coadd.fits -f "+str(args.fmin))
	try:
		os.remove("NVSS.txt")
	except OSError:
		pass
	print "and renaming it NVSS.txt."
	os.rename("coadd.fits.nvss.txt","NVSS.txt")
	if (not os.path.exists("NVSS.txt")):
		exit("NVSS catalog creation failed")

if (not args.nogencat):
	psopt = "psfsize"
	nsopt = ""
	if (not args.oldsfind):
		nsopt = "newsfind"
        if (not args.nopsfsize):
		psopt = ""
        print "\n*** Generating catalogs from ATA data ***\n\n"
    #   # run Source Locator and Outburst Watcher perl script (runs sfind, determines mosaic gains, preserves sources in good regions of the image)
        if (args.oldslowcat):
            os.system("/o/scroft/h/scripts/slow/slowcat_oldgain.py coadd.cm "+allims+" "+nsopt+" "+psopt)
        else:
            os.system("/o/scroft/h/scripts/slow/slowcat.py coadd.cm "+allims+" "+nsopt+" "+psopt)

if (not args.nomkfits):
	for imroot in allimrs:
            print "Making "+imroot+".fits from "+imroot+".cm"
            os.system("fits in="+imroot+".cm out="+imroot+".fits op=xyout")

if (not args.noseti):
	try:
		os.remove("slow.db")
	except OSError:
		pass
   	print "\n*** Matching catalogs across epochs ***\n\n"
    #   # call Steve's Excellent Transient Identifier (matches sfind catalogs) - now using a circular match
#	os.system("/o/scroft/h/scripts/slow/setisql.pl coadd.cm "+allims+" mrad="+str(args.matchrad))
	os.system("/o/scroft/h/scripts/slow/setisql.pl coadd.cm "+allims+" mrad="+str(args.matchrad))
    #    system("/o/scroft/h/scripts/slow/setiquery.pl $sort > seti.txt");

#cwd = `pwd`
#chomp(cwd);
#$dir = "$cwd/nvss";

if (not args.nonvsspost):
	print "\n*** Downloading NVSS postage stamp images ***\n\n"
	#   # this is where we'll put the NVSS postage stamps
	shutil.rmtree("nvss",ignore_errors=True)
	os.mkdir("nvss")
	# generate the NVSS postage stamps
	os.system("/o/scroft/h/scripts/slow/setinvss.pl")
	
# ********** DO REGISTRATION OTF IN SETIPOSTAGE.PY
# LIKE g = ap.FITSFigure("blah.fits")
# g.recenter(ra_decimal,dec_decimal,width=1.0)
# g.show_grayscale()
# SHOULD WE JUST DOWNLOAD A BIG NVSS IMAGE TOO?

#   # here's the list of NVSS postage stamps
#@nvsscutf = <$dir/J*.fits>;
#if ($nvssmir) {
#    print "\n*** Making MIRIAD versions of NVSS postage stamp images ***\n\n";
#    foreach $nvss (@nvsscutf) {
#	print "$nvss\n";
#	($nvsscm = $nvss) =~ s/.fits/.cm/;
#	system("rm -rf $nvsscm");
#	system("fits in=$nvss out=$nvsscm op=xyin");
#    }
#}

#@nvsscut = <$dir/J*.cm>;

if (not args.noeppost):
	print "\n*** Making postage stamps for each epoch and for coadd image ***\n\n"
	os.system("/o/scroft/h/scripts/slow/setipostage.py coadd.fits "+allimfs)


#if (not args.norejbl):
# only keep sources with mostly good pixels in every epoch
#    print "\n*** Rejecting sources near map edges and in bad regions ***\n\n";
#    system("/o/scroft/h/scripts/slow/setirejbl.pl");

#system("/o/scroft/h/scripts/slow/setiquery.pl $sort > seti.txt");

if (not args.nofluxgr):
	print "\n*** Making graphs of flux vs. epoch ***\n\n"
	shutil.rmtree("seti",ignore_errors=True)
	os.mkdir("seti")
    # create the panels with the graphs of flux vs. epoch
	os.system("/o/scroft/h/scripts/slow/slowqig.py")

#if (postps):
#    print "\n*** Assembling postage stamp images into postscript files ***\n\n"
#    system("rm -rf ps")
#    mkdir "ps", 0744
#    unlink("atanvssall.wip");
   # create the WIP scripts


#   # run the WIP master script (using the NULL device as default)
#    system("wip -d /NULL atanvssall.wip");

if (not args.nocomball):
	print "\n*** Assembling postage stamps and flux graphs into PDF file ***\n\n"
	os.system("/o/scroft/h/scripts/slow/setipdfsql.pl $sort")

#if (html):
#    system("rm -rf setipng")
#    system("rm -rf cutpng")
#    mkdir "setipng", 0744
#    mkdir "cutpng", 0744
#    print "\n*** Making PNG versions of postage stamps and flux graphs, and assembling into HTML file ***\n\n"
#    system("/o/scroft/h/scripts/slow/setipngsql.pl $sort")

