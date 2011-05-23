#!/usr/bin/env python
"""
Quick script for plotting and fitting distributions of PoCo pulses.
claw, 7apr11
"""

import asciidata
import pylab as p
import numpy as n
import scipy.optimize as opt

#filename = 'crab_fixdm_ph/poco_crab_fitsp.txt'
filename = 'data/poco_b0329_173027_fitsp.txt'
ignore = 2  # ignore bins up to this one (exclusive).
mode='flux'

f = asciidata.AsciiData(filename)
#amp = n.array(f.columns[3])
#ind = n.array(f.columns[4])
#sig = n.array(f.columns[6])
amp = n.array(f.columns[3])
ind = n.array(f.columns[4])
sig = n.array(f.columns[8])

plaw = lambda a, b, x: a * (x/x[0])**b
freqs = 0.718 + 0.104/64. * n.array([ 3,  4,  5,  6,  7,  8,  9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 37, 38, 40, 44, 45, 46, 47, 48])

meanflux = []
for i in range(len(amp)):
    meanflux.append(plaw(amp[i],ind[i],freqs).mean())

meanflux = n.array(meanflux)
print meanflux

if mode == 'flux':
    plaw = lambda a, b, x: a * (x/100.)**b
    fitfunc = lambda p, x:  plaw(p[0], p[1], x)
    errfunc = lambda p, x, y, rms: ((y - fitfunc(p, x))/rms)**2
    p0 = [1000,-4.5]

    hist = p.hist(meanflux, align='mid',bins=40, label='Observed')
    centers = n.array([(hist[1][i+1] + hist[1][i])/2 for i in range(len(hist[1])-1)])
    errs = 1+(n.sqrt(hist[0] + 0.75))
    p.errorbar(centers,hist[0],yerr=errs,fmt=None,ecolor='b')

    p1,success = opt.leastsq(errfunc, p0[:], args = (centers[ignore:], hist[0][ignore:], errs[ignore:]))

    print 'hist', hist[0],centers
    print 'model', p1
    print 'completeness', hist[0]/fitfunc(p1[:],centers)

    p.plot(centers,fitfunc(p1[:],centers), label='Best fit slope=%.1f' % p1[1])
    p.xlabel('Flux (Jy)')
    p.ylabel('Number of pulses')
    p.legend()
    p.axis([0,780,0,80])
    p.show()

elif mode == 'index':
    gauss = lambda amp, x, x0, sigma: amp * n.exp(-1./(2.*sigma**2)*(x-x0)**2)
    fitfunc = lambda p, x:  gauss(p[0], x, p[1], p[2])
    errfunc = lambda p, x, y, rms: ((y - fitfunc(p, x))/rms)**2
    p0 = [100,0,1]

    hist = p.hist(ind, align='mid',bins=20, label='Observed')
    centers = n.array([(hist[1][i+1] + hist[1][i])/2 for i in range(len(hist[1])-1)])
    errs = 1+(n.sqrt(hist[0] + 0.75))

    p1,success = opt.leastsq(errfunc, p0[:], args = (centers, hist[0], errs))
    print 'model', p1

    p.errorbar(centers,hist[0],yerr=errs,fmt=None,ecolor='b')
    p.plot(centers,fitfunc(p1[:],centers), label='Best fit')
    p.legend()
    p.xlabel('Spectral index')
    p.ylabel('Number of pulses')
    p.show()
