#!/usr/bin/env python
"""
Script to read FITS images of Stokes Q, U with 2 bands (as in VLA 6cm GC survey).
Functions can be used to measure RM for a region.
"""

import pylab as p
import numpy as n
import pyfits

def read(q1n, q2n, u1n, u2n):
    """Takes four strings as names of fits files.
    Returns tuple of four 2d arrays of pixel values.
    """

    q1 = pyfits.open(q1n, 'readonly')
    q2 = pyfits.open(q2n, 'readonly')
    u1 = pyfits.open(u1n, 'readonly')
    u2 = pyfits.open(u2n, 'readonly')

    return (q1[0].data)[0][0], (q2[0].data)[0][0], (u1[0].data)[0][0], (u2[0].data)[0][0]

def angle(q, u):
    """Takes q, u array and returns angle array
    """

    p = n.array(q, dtype='complex')
    p.imag = u

    return n.angle(p)/2.

def diffangle(a1, a2):
    """Takes two angles, returns difference within +-pi/2 range.
    Note:  does not return 2d array (yet?).
    """

    da = a1 - a2
    for i in range(len(da)):
        for j in range(len(da[0])):
            if da[i,j] > n.pi/2:
                da[i,j] = da[i,j] - n.pi
            elif da[i,j] < -n.pi/2:
                da[i,j] = da[i,j] + n.pi

    return da

def trim(arr1,arr2,arr3,arr4):
    """Trim four 2d arrays to good common range
    """

    good1 = n.where((arr1 > -9999999) & (arr1 < 9999999))
    good2 = n.where((arr2 > -9999999) & (arr2 < 9999999))
    good3 = n.where((arr3 > -9999999) & (arr3 < 9999999))
    good4 = n.where((arr4 > -9999999) & (arr4 < 9999999))

    maxminx = max(good1[0].min(), good2[0].min(), good3[0].min(), good4[0].min())
    minmaxx = min(good1[0].max(), good2[0].max(), good3[0].max(), good4[0].max())
    maxminy = max(good1[1].min(), good2[1].min(), good3[1].min(), good4[1].min())
    minmaxy = min(good1[1].max(), good2[1].max(), good3[1].max(), good4[1].max())

    arr12 = arr1[maxminx:minmaxx, maxminy:minmaxy]
    arr22 = arr2[maxminx:minmaxx, maxminy:minmaxy]
    arr32 = arr3[maxminx:minmaxx, maxminy:minmaxy]
    arr42 = arr4[maxminx:minmaxx, maxminy:minmaxy]

    return arr12, arr22, arr32, arr42


def meanmap(da, tilesize=30):
    """Takes full-res map and returns smoothed map via a mean.
    """

    damean = n.zeros((len(da)/tilesize, len(da[0])/tilesize))

    for i in range(len(damean)):
        for j in range(len(damean[0])):
            damean[i,j] = n.mean(da[i*tilesize:(i+1)*tilesize, j*tilesize:(j+1)*tilesize])

    return damean

def medianmap(da, tilesize=30):
    """Takes full-res map and returns smoothed map via a mean.
    """

    damed = n.zeros((len(da)/tilesize, len(da[0])/tilesize))

    for i in range(len(damed)):
        for j in range(len(damed[0])):
            damed[i,j] = n.median(da[i*tilesize:(i+1)*tilesize, j*tilesize:(j+1)*tilesize])

    return damed

def hist(da, nbins=70):
    """Makes a single histogram of any 2d array given.
    Returns best-fit Lorentzian parameters.
    """

    import scipy.optimize as opt

    hist,edges = n.histogram(da,bins=nbins)
    hist = hist/((180/70.) * 25)
    centers = [(edges[i:i+2]).mean() for i in range(len(edges)-1)]

    lorentzian = lambda a,b,c,d,x: a + b**2 / (c**2 + (x - d)**2)
    fitfunc = lambda p, x:  lorentzian(p[0], p[1], p[2], p[3], x)
    errfunc = lambda p, x, y: y - fitfunc(p, x)

    # attempt one, using two channels
    p0 = [100., 10000., 10., 0.]

    p1, success = opt.leastsq(errfunc, p0[:], args = (centers, hist))
    if success:
        print 'First attempt...'
        print 'Chi^2, Results: ', n.sum(errfunc(p1, centers, hist)), p1
        p0 = p1

    p.errorbar(centers, hist, yerr=n.sqrt(hist), fmt=None)
    p.plot(centers, fitfunc(p1, centers), '--')
    p.xlabel('Delta Theta (deg)')
    p.ylabel('Number of beams')

    return centers,hist
