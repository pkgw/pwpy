#!/usr/bin/env python
# extracts matched sources from slow.db sqlite3 database
# (matching each epoch to master mosaic catalog)
# determines best fit, and updates database with fit parameters
# corresponding to each epoch for sources detected in that epoch
# creates PDF files with matched sources and fit
# outputs file "setipp.out" with fit parameters per epoch
# requires ransac.py

#import argparse
import sys
import sqlite3
import numpy as np
import matplotlib
matplotlib.use('PDF')
import matplotlib.pyplot as plt
from scipy.optimize import leastsq
import ransac

dbfile = "slow.db"
dbh = sqlite3.connect(dbfile)
dbc = dbh.cursor()

# 
try:
	ccol = """ALTER TABLE master ADD COLUMN slope"""
	dbc.execute(ccol)
except:
	pass
try:
	ccol = """ALTER TABLE master ADD COLUMN icpt"""
	dbc.execute(ccol)
except:
	pass

epnq = """SELECT DISTINCT epname FROM master ORDER BY epjd"""
#epnq = """SELECT DISTINCT epname FROM master where (epname == 'ATA115')"""
dbc.execute(epnq)

epnames = dbc.fetchall()
#mastepname = "ATA47"
mastepname = "ATA_Coadd"
print "** Running with "+mastepname+" as master epoch"

# find which frequencies are present in the catalog
freqq = """SELECT DISTINCT freq FROM master"""
dbc.execute(freqq)
freqs = dbc.fetchall()


fig = plt.figure()

fitparfile = "setipp.out"
fitpars = open(fitparfile,"w")

# loop over frequencies
for freqn in freqs:
	freq = freqn[0]
	print "Starting "+str(freq)+" MHz"
	# loop over epochs
	for epname in epnames:
		pt = fig.add_subplot(1,1,1)
		epn = epname[0]
		print "\nStarting epoch "+epn
		# select the epoch name, mjid, flux, error, and frequency for all sources in this epoch which are matched in the master epoch
		souq = """SELECT m1.epname, m1.mjid, m1.fi, m1.rb, m1.freq, m2.epname, m2.mjid, m2.fi, m2.rb, m2.freq FROM master AS m1, master AS m2 WHERE (m1.epname == '"""+mastepname+"""' AND m2.epname == '"""+epn+"""' AND m1.mjid == m2.mjid AND m1.freq == m2.freq)"""
		dbc.execute(souq)
		sources = dbc.fetchall()
		# put source details into a numpy array
		sourcen = np.asanyarray(sources)
		# master flux densities
		maf = np.asfarray(sourcen[:,2])
		# master flux density uncertainties
		mafe = np.asfarray(sourcen[:,3])
		# flux densities at this epoch
		epf = np.asfarray(sourcen[:,7])
		# uncertainties at this epoch
		epfe = np.asfarray(sourcen[:,8])
		# array of matched master and single-epoch flux densities - use if we want to fit straight line with intercept 0
		#randat = np.asfarray([sourcen[:,2],sourcen[:,7]]).transpose()
		# array of matched master and single-epoch flux densities - use if we want to fit intercept
		randat = np.asfarray([sourcen[:,2],sourcen[:,7],np.ones(len(epf))]).transpose()
		#print randat
		# unweighted linear least squares fit
		mafavg = maf.mean()
		slopeu = (epf*(maf-mafavg)).sum()/(maf*(maf-mafavg)).sum()
		yintu = epf.mean()-slopeu*mafavg
		fitu = str(slopeu)+' '+str(yintu)
		print "Unweighted least squares: "+fitu
		# RANSAC unweighted linear least squares fit - intercept 0
		#lsmod = ransac.LinearLeastSquaresModel([0],[1])
		# RANSAC unweighted linear least squares fit - fit intercept
		lsmod = ransac.LinearLeastSquaresModel([0,2],[1])
		# pick 20% of the sources at each iteration
		nsource = maf.size
		nmin = 0.2 * nsource
		# unless that's fewer than 3
		if nmin < 3:
			nmin = 3
		# 70% of the sources should be close to the fit for acceptance
		nclose = 0.7 * nsource
		# unless that's more than the total number of sources minus 4
		if nclose > nsource - 4:
			nclose = nsource - 4
		# number of iterations
		niter = 1000
		# fit tolerance
		toler = 8000
		print "Using "+str(nmin)+" sources per iteration, "+str(niter)+" iterations, "+str(nclose)+" sources for good fit"
		# perform the fit
		#ransac_fit, ransac_data = ransac.ransac(randat,lsmod,nmin,niter,toler,nclose,return_all=True)
		ransac_fit = ransac.ransac(randat,lsmod,nmin,niter,toler,nclose)
		#print ransac_fit
		sloper = ransac_fit[0,0]
		yintr = ransac_fit[1,0]
		fitr = str(sloper)+' '+str(yintr)
		print "RANSAC: "+fitr
		# weighted linear least squares
		# http://physics.nyu.edu/pine/pymanual/graphics/graphics.html
		fitfunc = lambda p, x: p[0] + p[1] * x
		errfunc = lambda p, x, y, err: (y - fitfunc(p, x)) / err
		pinit = [1.0, 1.0]
		out = leastsq(errfunc, pinit, args=(maf, epf, epfe), full_output=1)
		pfinal = out[0]
		covar = out[1]
		slopew = pfinal[1]
		yintw = pfinal[0]
		fitw = str(slopew)+' '+str(yintw)
		print "Weighted least squares: "+fitw
		fitpars.write(epn+' '+str(freq)+' '+fitu+' '+fitw+' '+fitr+"\n")
		#	fitpars.write(str(slope)+' '+str(yint)+' '+str(slopew)+' '+str(yintw))
		# plot the measured points and their uncertainties
		pt.errorbar(maf,epf,xerr=mafe,yerr=epfe,linestyle='None')
		# plot the weighted linear least squares fit
		mafs = np.sort(maf)
		pt.plot(mafs,slopew*mafs+yintw,'r--')
#		pt.plot(maf,slope*maf+yint,'g')
		# plot the ransac fit
		pt.plot(mafs,sloper*mafs+yintr,'k-')
		plt.xlabel('Master Flux Density (mJy)')
		plt.ylabel(epn+' Flux Density (mJy)')
		# label plot with fit parameters
#		pt.set_title(fitw+' '+fitr)
		# update the database with weighted lsq values
		#fitpdb = """UPDATE master SET slope="""+str(slopew)+""", icpt="""+str(yintw)+""" WHERE (epname =='"""+epn+"""' AND freq =="""+str(freq)+""")"""
		# update the database with RANSAC values
		fitpdb = """UPDATE master SET slope="""+str(sloper)+""", icpt="""+str(yintr)+""" WHERE (epname =='"""+epn+"""' AND freq =="""+str(freq)+""")"""
#		print fitpdb
		dbc.execute(fitpdb)
		# http://www.scipy.org/Cookbook/FittingData
		#	pt.plot(xdata, powerlaw(xdata, amp, index))
		#	fig.show()
		oname = epn+"_"+str(freq)+"_fit.pdf"
		plt.savefig(oname)
		plt.clf()
#	print sources
dbh.commit()	
dbh.close()
fitpars.close()
