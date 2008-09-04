#! /usr/bin/env python

"""= closanal.py - Attempt to diagnose bad baselines based on phase triple closures
& pkgw
: uv Analysis
+
 CLOSANAL is a utility for diagnosing which antennas and/or baselines
 are bad in a given dataset. It computes phase triple closures from
 the data and computes RMS values for each baseline and
 antenna from the closures for each triple that they contribute
 to. The worst triple, baseline, and antenna closure values are then
 printed.

 Besides the RMS phase closure value for baselines and antennas, the
 standard deviation of those values ("StdDev") and the number of
 triples used in the computation ("nTrip") are also printed.
 
< vis

@ interval
 UV data time-averaging interval in minutes. It's recommended that
 this be set to a few minutes to damp out noise. Default is 0.01,
 i.e., no averaging.

@ ntrip
 The number of triple closure values to print. Default is 10.

@ nbl
 The number of RMS baseline closure values to print. Default is 10.

@ nant
 The number of antenna closure values to print. Default is 10.

@ options
 Multiple options can be specified, separated by commas, and
 minimum-match is used.

 'best'    Print out the best closure values rather than the worst

 'rmshist' Plot a histogram of the computed closure values. Requires
           the Python module 'omega'.

 'uvdplot' Plot a scatter diagram of RMS baseline phase closure versus
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
from numutils import *
import sys

SVNID = '$Id$'
banner = util.printBannerSvn ('closanal', 'attempt to diagnose bad baselines based on ' +
                              'phase triple closures', SVNID)

SECOND = 1.0 / 3600. / 24.

keys.keyword ('interval', 'd', 0.01)
keys.keyword ('ntrip', 'i', 10)
keys.keyword ('nbl', 'i', 10)
keys.keyword ('nant', 'i', 10)
keys.option ('rmshist', 'best', 'uvdplot')
keys.doUvdat ('dsl3xw', True)

integData = {}
accData = {}

def cr (): return GrowingArray (N.double, 3)
allData = AccDict (cr, lambda ga, tup: ga.add (*tup))

seenants = set ()
seenpols = set ()

def antfmt (pol, ant):
    return '%s-%d' % (util.polarizationName (pol), ant)

def blfmt (pol, ant1, ant2):
    return '%s-%d-%d' % (util.polarizationName (pol), ant1, ant2)

def tripfmt (pol, ant1, ant2, ant3):
    return '%s-%d-%d-%d' % (util.polarizationName (pol), ant1, ant2, ant3)

def flushInteg (time):
    global integData
    ants = sorted (seenants)

    for pol in seenpols:
        for i in xrange (0, len (ants)):
            ant3 = ants[i]
            for j in xrange (0, i):
                ant2 = ants[j]
                for k in xrange (0, j):
                    ant1 = ants[k]

                    flushOneInteg (time, pol, ant1, ant2, ant3)
    integData = {}

def flushOneInteg (time, pol, ant1, ant2, ant3):
    tup12 = integData.get (((ant1, ant2), pol))
    tup13 = integData.get (((ant1, ant3), pol))
    tup23 = integData.get (((ant2, ant3), pol))

    if tup12 is None or tup13 is None or tup23 is None:
        return

    (d12, f12, v12) =  tup12
    (d13, f13, v13) =  tup13
    (d23, f23, v23) =  tup23

    w = N.where (N.logical_and (f12, N.logical_and (f13, f23)))
    n = len (w[0])

    if n == 0: return
    
    c = (d12[w] * d23[w] * d13[w].conj ()).sum ()
    v = n * (v12 + v13 + v23)
    t = n * time
    
    accKey = (pol, ant1, ant2, ant3)
    if accKey not in accData:
        accData[accKey] = (t, n, c, v)
    else:
        (t0, n0, c0, v0) = accData[accKey]
        accData[accKey] = (t + t0, n + n0, c + c0, v + v0)
    
def flushAcc ():
    global accData
    ants = sorted (seenants)

    for pol in seenpols:
        for i in xrange (0, len (ants)):
            ant3 = ants[i]
            for j in xrange (0, i):
                ant2 = ants[j]
                for k in xrange (0, j):
                    ant1 = ants[k]

                    flushOneAcc (pol, ant1, ant2, ant3)
    accData = {}

def flushOneAcc (pol, ant1, ant2, ant3):
    key = (pol, ant1, ant2, ant3)
    tup = accData.get (key)
    if tup is None:
        return

    (time, n, c, v) = tup

    # note! not dividing by n since that doesn't affect phase.
    # Does affect amp though.
    ph = 180/N.pi * N.arctan2 (c.imag, c.real)

    #print pol, ant1, ant2, ant3, time/n, ph
    
    allData.accum (key, (time / n, ph, v / n))

args = keys.process ()

interval = args.interval / 60. / 24.
print 'Averaging interval: %g minutes' % (args.interval)

if args.uvdplot:
    uvdists = AccDict (StatsAccumulator, lambda sa, v: sa.add (v))

# Let's go.

first = True
print 'Reading data ...'

for (inp, preamble, data, flags, nread) in uvdat.readAll ():
    data = data[0:nread].copy ()
    flags = flags[0:nread].copy ()

    time = preamble[3]
    bl = util.decodeBaseline (preamble[4])
    pol = uvdat.getPol ()
    var = uvdat.getVariance ()

    # Some first checks.
    
    if not util.polarizationIsInten (pol): continue
    if not flags.any (): continue
    
    seenpols.add (pol)
    seenants.add (bl[0])
    seenants.add (bl[1])
    
    if first:
        time0 = int (time - 0.5) + 0.5
        tmin = time - time0
        tmax = tmin
        tprev = tmin
        first = False

    t = time - time0

    if abs (t - tprev) > SECOND:
        flushInteg (tprev)
        tprev = t

    if (t - tmin) > interval or (tmax - t) > interval:
        flushAcc ()
        tmin = tmax = t

    # Store info for this vis
    
    tmin = min (tmin, t)
    tmax = max (tmax, t)
    integData[(bl, pol)] = (data, flags, var)

    if args.uvdplot:
        uvdists.accum ((pol, bl[0], bl[1]), N.sqrt ((preamble[0:3]**2).sum ()))

flushInteg (t)
flushAcc ()

print ' ... done. Read %d triples.' % len (allData)

# OK, now do our fancy analysis.

blStats = AccDict (StatsAccumulator, lambda sa, rms: sa.add (rms))
antStats = AccDict (StatsAccumulator, lambda sa, rms: sa.add (rms))

if args.rmshist:
    allrms = GrowingArray (N.double, 1)

def processTriples ():
    for (key, ga) in allData.iteritems ():
        ga.doneAdding ()    
        (pol, ant1, ant2, ant3) = key
        phs = ga.col (1)
        rms = N.sqrt (N.mean (phs**2))

        if args.rmshist:
            allrms.add (rms)

        blStats.accum ((pol, ant1, ant2), rms)
        blStats.accum ((pol, ant1, ant3), rms)
        blStats.accum ((pol, ant2, ant3), rms)
        antStats.accum ((pol, ant1), rms)
        antStats.accum ((pol, ant2), rms)
        antStats.accum ((pol, ant3), rms)

        yield pol, ant1, ant2, ant3, rms

worstTrips = sorted (processTriples (), key=lambda x: x[4], reverse=not args.best)
worstTrips = worstTrips[0:args.ntrip]

worstBls = sorted ((x for x in blStats.iteritems ()),
                   key=lambda x: x[1].mean (), reverse=not args.best)
worstBls = worstBls[0:args.nbl]

worstAnts = sorted ((x for x in antStats.iteritems ()),
                    key=lambda x: x[1].mean (), reverse=not args.best)
worstAnts = worstAnts[0:args.nant]

if args.best: adj = 'best'
else: adj = 'worst'

if len (worstTrips) > 0:
    print
    print 'Triples with %s phase closure values:' % adj
    for pol, ant1, ant2, ant3, rms in worstTrips:
        print '%14s: %10g' % (tripfmt (pol, ant1, ant2, ant3), rms)

if len (worstBls) > 0:
    print
    print 'Baselines with %s phase closure values:' % adj
    print '%14s  %10s (%10s, %5s)' % ('Baseline', 'Mean', 'StdDev', 'nTrip')
    for key, sa in worstBls:
        print '%14s: %10g (%10g, %5d)' % (blfmt (*key), sa.mean (), sa.std (), sa.num ())

if len (worstAnts) > 0:
    print
    print 'Antennas with %s phase closure values:' % adj
    print '%14s  %10s (%10s, %5s)' % ('Antenna', 'Mean', 'StdDev', 'nTrip')
    for key, sa in worstAnts:
        print '%14s: %10g (%10g, %5d)' % (antfmt (*key), sa.mean (), sa.std (), sa.num ())

if args.rmshist:
    print
    print 'Showing histogram of RMS values ...'
    import omega
    allrms.doneAdding ()
    n = int (N.sqrt (len (allrms)))
    omega.quickHist (allrms.col (0), n).showBlocking ()

if args.uvdplot:
    print
    print 'Showing baseline closure errors as function of UV distance ...'
    import omega
    n = len (uvdists)
    uvds = N.ndarray (n)
    rmss = N.ndarray (n)

    i = 0
    for key, uvdsa in uvdists.iteritems ():
        uvds[i] = uvdsa.mean ()
        rmss[i] = blStats[key].mean ()
        i += 1

    uvds *= 0.001 # express in kilolambda.
    omega.quickXY (uvds, rmss, lines=False).showBlocking ()

sys.exit (0)
