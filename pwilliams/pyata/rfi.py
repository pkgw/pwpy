#! /usr/bin/env python

import numpy as N
import mirtask, mirtask.util, mirtask.keys, mirtask.uvdat
import sys

totals = {}
tcounts = {}
accums = {}
acounts = {}
cutoff = 10000
specdata = {}

def accum (cfreq, amps):
    if cfreq not in accums:
        accums[cfreq] = amps.copy ()
        acounts[cfreq] = 1
        acount = 1
    else:
        accums[cfreq] += amps
        acounts[cfreq] += 1
        acount = acounts[cfreq]

    if acount < cutoff: return

    accumed = accums[cfreq]
    del accums[cfreq], acounts[cfreq]
    
    if cfreq not in totals:
        totals[cfreq] = accumed
        tcounts[cfreq] = 1
    else:
        totals[cfreq] += accumed
        tcounts[cfreq] += 1

def getspecdata (inp, cfreq):
    start = inp.getVarDouble ('sfreq', 1)[0]
    delta = inp.getVarDouble ('sdf', 1)[0]
    
    specdata[cfreq] = (start, delta)
    
def dofile (fn):
    bits = fn.split ('-')
    cfreq = int (bits[3])
    if bits[4] == 'e':
        print 'Skipping bad E slice file:', fn
        return
    print fn
    
    mirtask.keys.init (['visindex', 'vis=' + fn])
    mirtask.uvdat.init ('wb3')
    inp = mirtask.uvdat.singleInputSet ()

    needsd = cfreq not in specdata:
    
    for (preamble, data, flags, nread) in mirtask.uvdat.readData ():
        if needsd:
            getspecdata (inp, cfreq)
            needsd = False
        accum (cfreq, N.abs (data[0:nread]))

    inp.close ()

def doneFreq (cfreq, f, smooth=3):
    start, delta = specdata[cfreq]

    if cfreq in totals:
        tot = totals[cfreq]
        tc = tcounts[cfreq]
    else:
        tot = N.zeros (1024)
        tc = 0

    if cfreq in accums:
        tot += accums[cfreq] / cutoff
        tc += acounts[cfreq] / cutoff

    tot /= tc
    
    aLeft = N.convolve (tot[128:512], N.ones (smooth)/smooth, 'same')
    fLeft = (start + delta * N.linspace (128, 511, 384)) * 1000
    aRight = N.convolve (tot[513:897], N.ones (smooth)/smooth, 'same')
    fRight = (start + delta * N.linspace (513, 896, 384)) * 1000
    
    for i in xrange (0, 384):
        print >>f, '%lg %lg' % (fLeft[i], aLeft[i])
    for i in xrange (0, 384):
        print >>f, '%lg %lg' % (fRight[i], aRight[i])

for infn in sys.argv[1:]:
    dofile (infn)

allfreqs = set ()
for cf in totals.iterkeys (): allfreqs.add (cf)
for cf in accums.iterkeys (): allfreqs.add (cf)
allfreqs = sorted (allfreqs)

f = file ('rfi.txt', 'w')
for cf in allfreqs:
    doneFreq (cf, f)
f.close ()
