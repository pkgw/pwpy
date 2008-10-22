#! /usr/bin/env python

# TODO: 'closure' can compute theoretical RMS closure values. Should
# find out how they do that.

"""= closanal.py - Attempt to identify bad baselines based on closure quantities
& pkgw
: uv Analysis
+

 CLOSANAL is a utility for identifying which antennas and/or baselines
 are bad in a given dataset based on closure quantities. It can
 compute phase triple closures or amplitude quad closures from the
 data and shows RMS values for each baseline and antenna from the
 closures for each closure quantity that they contribute to. The worst
 triple/quad, baseline, and antenna closure values are then printed.

 If phase triple closures are computed, the reported quantities are
 the closure value in degrees. If amplitude quad closures are
 computed, the reported quantities are the natural logarithm of the
 dimensionles amplitude closure value. This means that a "perfect"
 closure value for a point source in both cases is zero, and that
 raw amplitude closures of K and 1/K have the same value but opposite
 signs.

 Besides the RMS closure value for each baseline and antenna, the
 standard deviation of those values ("StdDev") and the number of
 closure quantities used in the computation ("nTrip" or "nQuad") are
 also printed.
 
< vis

@ interval
 UV data time-averaging interval in minutes. It's recommended that
 this be set to a few minutes to damp out noise. Default is 10. An
 extremely small number such as 0.01 will result in no averaging.

@ nclos
 The number of closure quantities to print. Default is 10.

@ nbl
 The number of RMS baseline closure values to print. Default is 10.

@ nant
 The number of antenna closure values to print. Default is 10.

@ options
 Multiple options can be specified, separated by commas, and
 minimum-match is used.

 'amplitude' Compute amplitude quad closures. The default is to
             compute phase triple closures.

 'best'    Print out the best closure values rather than the worst.

 'blhist'  Plot a histogram of the average closure values for each
           baseline. Requires the Python module 'omega'.

 'rmshist' Plot a histogram of the computed closure values. Requires
           the Python module 'omega'.

 'uvdplot' Plot a scatter diagram of RMS baseline closure versus
           average baseline UV distance. Requires the Python module
           'omega'

 'nocal'   Do not apply antenna gain corrections. This task should
           yield identical results with this enabled or disabled --
           that's the whole point of looking at closures!

 'nopol'   Do not apply polarization leakage corrections.

 'nopass'  Do not apply bandpass shape corrections.

< select

< line

< stokes

--
"""

import numpy as N
from mirtask import keys, util, uvdat
from mirtask.util import fmtPBP
from numutils import *
import sys

SVNID = '$Id$'
banner = util.printBannerSvn ('closanal', 'attempt to identify bad baselines based on ' +
                              'closure quantities', SVNID)

SECOND = 1.0 / 3600. / 24.

keys.keyword ('interval', 'd', 10.)
keys.keyword ('nclos', 'i', 10)
keys.keyword ('nbl', 'i', 10)
keys.keyword ('nant', 'i', 10)
keys.option ('rmshist', 'best', 'uvdplot', 'blhist', 'amplitude')
keys.doUvdat ('dsl3xw', True)

integData = {}
accData = {}

#def cr (): return GrowingArray (N.double, 3)
#allData = AccDict (cr, lambda ga, tup: ga.add (*tup))
allData = AccDict (GrowingVector, lambda o, v: o.add (v))

seenaps = {}
seenpols = set ()

p2p = lambda ap1, ap2: util.paps2pbp ((ap1, ap2))

def format (*aps):
    return '-'.join (util.fmtPAP (x) for x in aps)

def _flagAnd (flags1, flags2, *rest):
    # Avoid allocation of many temporary arrays here.
    isect = N.logical_and (flags1, flags2)

    for f in rest:
        N.logical_and (isect, f, isect)

    return isect

def flushInteg3 ():
    global integData

    for pol in seenpols:
        aps = sorted (seenaps[pol])
        
        for i in xrange (0, len (aps)):
            ap3 = aps[i]
            for j in xrange (0, i):
                ap2 = aps[j]
                for k in xrange (0, j):
                    ap1 = aps[k]

                    flushOneInteg3 (ap1, ap2, ap3)
    integData = {}

def flushOneInteg3 (ap1, ap2, ap3):
    tup12 = integData.get (p2p (ap1, ap2))
    tup13 = integData.get (p2p (ap1, ap3))
    tup23 = integData.get (p2p (ap2, ap3))

    if tup12 is None or tup13 is None or tup23 is None:
        return

    (d12, f12, v12, t12) =  tup12
    (d13, f13, v13, t13) =  tup13
    (d23, f23, v23, t23) =  tup23

    assert t12 == t13 and t12 == t23
    
    w = N.where (_flagAnd (f12, f13, f23))
    n = len (w[0])

    if n == 0: return
    
    t = n * t12
    c = (d12[w].sum () * d23[w].sum () * d13[w].sum ().conj ()) * t
    v = (v12 + v13 + v23) * t
    
    accKey = (ap1, ap2, ap3)
    if accKey not in accData:
        accData[accKey] = (t, c, v)
    else:
        (t0, c0, v0) = accData[accKey]
        accData[accKey] = (t + t0, c + c0, v + v0)
    
def flushInteg4 ():
    global integData

    for pol in seenpols:
        aps = sorted (seenaps[pol])

        for i in xrange (0, len (aps)):
            ap4 = aps[i]
            for j in xrange (0, i):
                ap3 = aps[j]
                for k in xrange (0, j):
                    ap2 = aps[k]
                    for l in xrange (0, k):
                        ap1 = aps[l]

                        flushOneInteg4 (ap1, ap2, ap3, ap4)
    integData = {}

def flushOneInteg4 (ap1, ap2, ap3, ap4):
    tup12 = integData.get (p2p (ap1, ap2))
    tup13 = integData.get (p2p (ap1, ap3))
    tup24 = integData.get (p2p (ap2, ap4))
    tup34 = integData.get (p2p (ap3, ap4))

    if tup12 is None or tup13 is None or tup24 is None or tup34 is None:
        return

    (d12, f12, v12, t12) =  tup12
    (d13, f13, v13, t13) =  tup13
    (d24, f24, v24, t24) =  tup24
    (d34, f34, v34, t34) =  tup34

    assert t12 == t13 and t12 == t24 and t12 == t34

    # Avoid div-by-zero
    w = N.where (_flagAnd (f12, f13, f24, f34, d13 != 0, d24 != 0))
    n = len (w[0])

    if n == 0: return
    
    t = n * t12
    c = (d12[w].sum () * d34[w].sum () / d13[w].sum () / d24[w].sum ().conj ()) * t
    v = (v12 + v13 + v24 + v34) * t

    accKey = (ap1, ap2, ap3, ap4)
    if accKey not in accData:
        accData[accKey] = (t, c, v)
    else:
        (t0, c0, v0) = accData[accKey]
        accData[accKey] = (t + t0, c + c0, v + v0)

def flushAcc3 ():
    global accData

    for pol in seenpols:
        aps = sorted (seenaps[pol])

        for i in xrange (0, len (aps)):
            ap3 = aps[i]
            for j in xrange (0, i):
                ap2 = aps[j]
                for k in xrange (0, j):
                    ap1 = aps[k]

                    flushOneAcc3 (ap1, ap2, ap3)
    accData = {}

def flushOneAcc3 (ap1, ap2, ap3):
    key = (ap1, ap2, ap3)
    tup = accData.get (key)
    if tup is None:
        return

    (time, c, v) = tup

    # note! not dividing by time since that doesn't affect phase.
    # Does affect amp though.
    ph = 180/N.pi * N.arctan2 (c.imag, c.real)

    allData.accum (key, ph)
    #allData.accum (key, (time, ph, v / time))

def flushAcc4 ():
    global accData

    for pol in seenpols:
        aps = sorted (seenaps[pol])
        
        for i in xrange (0, len (aps)):
            ap4 = aps[i]
            for j in xrange (0, i):
                ap3 = aps[j]
                for k in xrange (0, j):
                    ap2 = aps[k]
                    for l in xrange (0, k):
                        ap1 = aps[l]

                        flushOneAcc4 (ap1, ap2, ap3, ap4)
    accData = {}

def flushOneAcc4 (ap1, ap2, ap3, ap4):
    key = (ap1, ap2, ap3, ap4)
    tup = accData.get (key)
    if tup is None:
        return

    (time, c, v) = tup
    amp = N.abs (c) / time
    allData.accum (key, amp)

args = keys.process ()

interval = args.interval / 60. / 24.
print 'Averaging interval: %g minutes' % (args.interval)

if args.amplitude:
    flushInteg = flushInteg4
    flushAcc = flushAcc4
    item = 'amplitude'
    datum = 'quads'
    capdatum = 'Quads'
    ndatum = 'nQuad'
else:
    flushInteg = flushInteg3
    flushAcc = flushAcc3
    item = 'phase'
    datum = 'triples'
    capdatum = 'Triples'
    ndatum ='nTrip'

print 'Calculating %s closure %s' % (item, datum)

if args.uvdplot:
    uvdists = AccDict (StatsAccumulator, lambda sa, v: sa.add (v))

# Let's go.

first = True
print 'Reading data ...'

for (inp, preamble, data, flags, nread) in uvdat.readAll ():
    data = data[0:nread].copy ()
    flags = flags[0:nread].copy ()

    time = preamble[3]
    bp = util.mir2pbp (inp, preamble)
    
    var = uvdat.getVariance ()
    inttime = inp.getVarFloat ('inttime')
    
    # Some first checks.
    
    if not util.pbpIsInten (bp): continue
    if not flags.any (): continue
    
    for ap in util.pbp2paps (bp):
        fpol = util.papFPol (ap)
        seenpols.add (fpol)

        if fpol in seenaps:
            seenaps[fpol].add (ap)
        else:
            seenaps[fpol] = set ((ap, ))

    if first:
        time0 = int (time - 0.5) + 0.5
        tmin = time - time0
        tmax = tmin
        tprev = tmin
        first = False

    t = time - time0

    if abs (t - tprev) > SECOND:
        flushInteg ()
        tprev = t

    if (t - tmin) > interval or (tmax - t) > interval:
        flushAcc ()
        tmin = tmax = t

    # Store info for this vis
    
    tmin = min (tmin, t)
    tmax = max (tmax, t)
    integData[bp] = (data, flags, var, inttime)

    if args.uvdplot:
        uvdists.accum (bp, N.sqrt ((preamble[0:3]**2).sum ()))

flushInteg ()
flushAcc ()

print ' ... done. Read %d %s closure %s.' % (len (allData), item, datum)

# OK, now do our fancy analysis.

bpStats = AccDict (StatsAccumulator, lambda sa, rms: sa.add (rms))
apStats = AccDict (StatsAccumulator, lambda sa, rms: sa.add (rms))

if args.rmshist:
    allrms = GrowingVector ()

def processTriples ():
    for (key, gv) in allData.iteritems ():
        gv.doneAdding ()    
        (ap1, ap2, ap3) = key
        phs = gv.arr
        rms = N.sqrt (N.mean (phs**2))

        if args.rmshist:
            allrms.add (rms)

        bpStats.accum (p2p (ap1, ap2), rms)
        bpStats.accum (p2p (ap1, ap3), rms)
        bpStats.accum (p2p (ap2, ap3), rms)
        apStats.accum (ap1, rms)
        apStats.accum (ap2, rms)
        apStats.accum (ap3, rms)

        yield (ap1, ap2, ap3), rms

def processQuads ():
    seenQuads = set ()
    
    for (key, gv) in allData.iteritems ():
        gv.doneAdding ()    
        (ap1, ap2, ap3, ap4) = key

        # Cf. Pearson & Readhead 1984 ARAA 22 97:
        # if we know the closure of k-l-m-n and k-l-n-m,
        # then k-n-m-l adds no information
        # here, 1=k, 2=n, 3=m, 4=l, so we need to check for
        # 1-4-3-2 and 1-4-2-3
        
        if (ap1, ap4, ap3, ap2) in seenQuads and \
           (ap1, ap2, ap2, ap3) in seenQuads:
            continue

        seenQuads.add (key)

        # This quad is not redundant.
        
        amps = gv.arr
        lrms = N.log (N.mean (amps**2)) / 2 # log of the rms

        if args.rmshist:
            allrms.add (lrms)

        bpStats.accum (p2p (ap1, ap2), lrms)
        bpStats.accum (p2p (ap1, ap3), lrms)
        bpStats.accum (p2p (ap2, ap4), lrms)
        bpStats.accum (p2p (ap3, ap4), lrms)
        apStats.accum (ap1, lrms)
        apStats.accum (ap2, lrms)
        apStats.accum (ap3, lrms)
        apStats.accum (ap4, lrms)

        yield (ap1, ap2, ap3, ap4), lrms

if args.amplitude:
    process = processQuads
    key = lambda x: abs (x[1])
    collkey = lambda x: x[1].rms ()
    statkey = lambda sa: sa.rms ()
    stat = 'RMS'
else:
    process = processTriples
    key = lambda x: x[1]
    collkey = lambda x: x[1].mean ()
    statkey = lambda sa: sa.mean ()
    stat = 'Mean'

worstCls = sorted (process (), key=key, reverse=not args.best)
worstCls = worstCls[0:args.nclos]

worstBps = sorted ((x for x in bpStats.iteritems ()),
                   key=collkey, reverse=not args.best)
worstBps = worstBps[0:args.nbl]

worstAps = sorted ((x for x in apStats.iteritems ()),
                    key=collkey, reverse=not args.best)
worstAps = worstAps[0:args.nant]

if args.best: adj = 'best'
else: adj = 'worst'

if len (worstCls) > 0:
    print
    print '%s with %s %s closure values:' % (capdatum, adj, item)
    for ident, rms in worstCls:
        print '%14s: %10g' % (format (*ident), rms)
    
if len (worstBps) > 0:
    print
    print 'Baselines with %s %s closure values:' % (adj, item)
    print '%14s  %10s (%10s, %5s)' % ('Baseline', stat, 'StdDev', ndatum)
    for bp, sa in worstBps:
        print '%14s: %10g (%10g, %5d)' % (fmtPBP (bp), statkey (sa), sa.std (), sa.num ())

if len (worstAps) > 0:
    print
    print 'Antpols with %s %s closure values:' % (adj, item)
    print '%14s  %10s (%10s, %5s)' % ('Antpol', stat, 'StdDev', ndatum)
    for ap, sa in worstAps:
        print '%14s: %10g (%10g, %5d)' % (format (ap), statkey (sa), sa.std (), sa.num ())

if args.rmshist:
    print
    print 'Showing histogram of RMS values ...'
    import omega
    allrms.doneAdding ()
    n = int (N.ceil (N.log2 (len (allrms)) + 1))
    omega.quickHist (allrms.arr, n).showBlocking ()

if args.blhist:
    print
    print 'Showing histogram of baseline closure values ...'
    import omega
    n = int (N.ceil (N.log2 (len (bpStats)) + 1))
    values = [x.mean () for x in bpStats.itervalues ()]
    omega.quickHist (values, n).showBlocking ()

if args.uvdplot:
    print
    print 'Showing baseline closure errors as function of UV distance ...'
    import omega
    n = len (uvdists)
    uvds = N.ndarray (n)
    rmss = N.ndarray (n)

    i = 0
    for bp, uvdsa in uvdists.iteritems ():
        uvds[i] = uvdsa.mean ()
        rmss[i] = bpStats[bp].mean ()
        i += 1

    uvds *= 0.001 # express in kilolambda.
    omega.quickXY (uvds, rmss, lines=False).showBlocking ()

sys.exit (0)
