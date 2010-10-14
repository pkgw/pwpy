#! /usr/bin/env python

# TODO: theoretical uncerts on amplitude quad closures.

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

 'relative'  Sort values according to the ratio of the computed
             value to the theoretical value. Useful for
             identifying baselines/antpols with non-thermal noise
             properties (i.e., bad hardware).

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
from mirtask.util import fmtBP
from numutils import *
import sys

SVNID = '$Id$'
SECOND = 1.0 / 3600. / 24.

p2p = lambda ap1, ap2: util.aps2bp ((ap1, ap2))


def _format (aps):
    if isinstance (aps, int): aps = (aps, )
    return '-'.join (util.fmtAP (x) for x in aps)


def _flagAnd (flags1, flags2, *rest):
    # Avoid allocation of many temporary arrays here.
    isect = N.logical_and (flags1, flags2)

    for f in rest:
        N.logical_and (isect, f, isect)

    return isect


def _flushOneInteg3 (integData, accData, ap1, ap2, ap3):
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
    v = (v12 + v13 + v23) * n**3 * t
    
    accKey = (ap1, ap2, ap3)
    if accKey not in accData:
        accData[accKey] = (t, c, v)
    else:
        (t0, c0, v0) = accData[accKey]
        accData[accKey] = (t + t0, c + c0, v + v0)


def _flushOneInteg4 (integData, accData, ap1, ap2, ap3, ap4):
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

    # FIXME: in closure.for, the variance is the sum of the variances
    # over flux**2, where flux = (|d12| + |d34| + |d14| + |d23|) / 4,
    # but need to think through whether this is by channel or what.

    v = (v12 + v13 + v24 + v34) * t
    
    accKey = (ap1, ap2, ap3, ap4)
    if accKey not in accData:
        accData[accKey] = (t, c, v)
    else:
        (t0, c0, v0) = accData[accKey]
        accData[accKey] = (t + t0, c + c0, v + v0)


def _flushOneAcc3 (accData, allData, ap1, ap2, ap3):
    key = (ap1, ap2, ap3)
    tup = accData.get (key)
    if tup is None:
        return

    (time, c, v) = tup

    # note! not dividing by time since that doesn't affect phase.
    # Does affect amp though.
    ph = 180/N.pi * N.arctan2 (c.imag, c.real)
    amp = N.abs (c) / time
    thy = 180/N.pi * N.sqrt (v / time) / (amp ** (1./3))

    allData.accum (key, (ph, thy))
    #allData.accum (key, (time, ph, v / time))


def _flushOneAcc4 (accData, allData, ap1, ap2, ap3, ap4):
    key = (ap1, ap2, ap3, ap4)
    tup = accData.get (key)
    if tup is None:
        return

    (time, c, v) = tup
    amp = N.abs (c) / time
    thy = N.sqrt (v) / time
    
    allData.accum (key, (amp, thy))


class ClosureComputer (object):
    def __init__ (self, rmshist, relative):
        self.rmshist = rmshist
        self.relative = relative
        
        self.integData = {}
        self.accData = {}
        self.allData = AccDict (lambda: ArrayGrower (2), lambda o, v: o.addLine (v))
        self.seenaps = {}
        self.seenpols = set ()

    def integrate (self, bp, data, flags, var, inttime):
        for ap in util.bp2aps (bp):
            fpol = util.apFPol (ap)
            self.seenpols.add (fpol)

            if fpol in self.seenaps:
                self.seenaps[fpol].add (ap)
            else:
                self.seenaps[fpol] = set ((ap, ))

        self.integData[bp] = (data, flags, var, inttime)


    def pDataSummary (self):
        print '  Read %d %s closure %s.' % (len (self.allData), self.item, self.datum)


    def computeStats (self):
        if self.rmshist:
            self.allrms = VectorGrower ()

        self.process ()


    def valHist (self):
        import omega
        rms = self.allrms.finish ()
        n = int (N.ceil (N.log2 (rms.size) + 1))
        p = omega.quickHist (rms, n, keyText=self.datum)
        p.setLabels ('%s closure' % self.item, 'Number of %s' % self.datum)
        return p


    def bpHist (self):
        import omega
        n = int (N.ceil (N.log2 (len (self.bpData)) + 1))
        values = [t[1] for t in self.bpData]
        p = omega.quickHist (values, n, keyText='Basepols')
        p.setLabels ('%s closure' % self.item, 'Number of basepols')
        return p

    def _printGeneric (self, data, capname, haveStats, n, best):
        if n == 0 or len (data) == 0: return
        
        if best:
            adj = 'best'
            subset = data[0:n]
        else:
            adj = 'worst'
            subset = data[-n:]
        
        print
        print '%s with %s %s closure values:' % (capname, adj, self.item)
        
        if haveStats:
            if self.relative:
                err = 'Th.Uncert.'
            else:
                err = 'StdDev'
                
            print '%15s  %14s (%10s, %5s) %14s' % (capname[:-1], self.manystat,
                                                   err, self.ndatum,
                                                   self.manystat + '/T.U.')
            
            for ident, val, std, num in subset:
                print '%15s: %14g (%10g, %5d) %14g' % (_format (ident), val,
                                                       std, num, val / std)
        else:
            print '%15s  %14s %14s %14s' % (capname[:-1],
                                            self.onestat,
                                            'Th. Uncert.',
                                            self.onestat + '/ThUn')

            for ident, val, thy in subset:
                print '%15s: %14g %14g %14g' % (_format (ident), val, thy,
                                                val / thy)


    def pQuantities (self, n, best):
        self._printGeneric (self.qtyData, self.capdatum, False, n, best)


    def pBasepols (self, n, best):
        self._printGeneric (self.bpData, 'Basepols', True, n, best)
        

    def pAntpols (self, n, best):
        self._printGeneric (self.apData, 'Antpols', True, n, best)
    

class TripleComputer (ClosureComputer):
    item = 'phase'
    datum = 'triples'
    capdatum = 'Triples'
    ndatum ='nTrip'
    onestat = 'RMS'
    manystat = 'Mean(RMS)'
    
    
    def flushInteg (self):
        id, ac = self.integData, self.accData
        
        for pol in self.seenpols:
            aps = sorted (self.seenaps[pol])
        
            for i in xrange (0, len (aps)):
                ap3 = aps[i]
                for j in xrange (0, i):
                    ap2 = aps[j]
                    for k in xrange (0, j):
                        ap1 = aps[k]

                        _flushOneInteg3 (id, ac, ap1, ap2, ap3)

        self.integData = {}

    
    def flushAcc (self):
        acc, all = self.accData, self.allData
        
        for pol in self.seenpols:
            aps = sorted (self.seenaps[pol])

            for i in xrange (0, len (aps)):
                ap3 = aps[i]
                for j in xrange (0, i):
                    ap2 = aps[j]
                    for k in xrange (0, j):
                        ap1 = aps[k]

                        _flushOneAcc3 (acc, all, ap1, ap2, ap3)
                        
        self.accData = {}
        self.seenpols = set ()
        self.seenaps = {}


    def process (self):
        if self.relative:
            bpStats = AccDict (WeightAccumulator, lambda sa, t: sa.add (*t))
            bpacc = bpStats.accum
            apStats = AccDict (WeightAccumulator, lambda sa, t: sa.add (*t))
            apacc = apStats.accum
        else:
            bpStats = AccDict (StatsAccumulator, lambda sa, rms: sa.add (rms))
            bpacc = bpStats.accum
            apStats = AccDict (StatsAccumulator, lambda sa, rms: sa.add (rms))
            apacc = apStats.accum

        def c ():
            for (key, ag) in self.allData.iteritems ():
                phs, thys = ag.finish ().T
                (ap1, ap2, ap3) = key
                rms = N.sqrt (N.mean (phs**2))
                thy = N.sqrt (N.mean (thys**2))

                if thy == 0.:
                    thy = -1
                
                if self.rmshist:
                    self.allrms.add (rms)

                if self.relative:
                    q = (rms, thy**-2)
                else:
                    q = rms
                    
                bpacc ((ap1, ap2), q)
                bpacc ((ap1, ap3), q)
                bpacc ((ap2, ap3), q)
                apacc (ap1, q)
                apacc (ap2, q)
                apacc (ap3, q)

                yield key, rms, thy

        if self.relative:
            key = lambda t: t[1] / t[2]
            tval = lambda t: (t[0], t[1].wtavg (), t[1].std (),
                              t[1].num ())
        else:
            key = lambda t: t[1]
            tval = lambda t: (t[0], t[1].mean (), t[1].std (),
                              t[1].num ())
            
        self.qtyData = sorted (c (), key=key)

        g = (tval (t) for t in bpStats.iteritems ())
        self.bpData = sorted (g, key=key)
        
        g = (tval (t) for t in apStats.iteritems ())
        self.apData = sorted (g, key=key)

    
class QuadComputer (ClosureComputer):
    item = 'amplitude'
    datum = 'quads'
    capdatum = 'Quads'
    ndatum = 'nQuad'
    onestat = 'log(RMS)'
    manystat = 'RMS(log(RMS))'
    
    def flushInteg (self):
        id, ac = self.integData, self.accData

        for pol in self.seenpols:
            aps = sorted (self.seenaps[pol])

            for i in xrange (0, len (aps)):
                ap4 = aps[i]
                for j in xrange (0, i):
                    ap3 = aps[j]
                    for k in xrange (0, j):
                        ap2 = aps[k]
                        for l in xrange (0, k):
                            ap1 = aps[l]

                            _flushOneInteg4 (id, ac, ap1, ap2, ap3, ap4)

        self.integData = {}


    def flushAcc (self):
        acc, all = self.accData, self.allData

        for pol in self.seenpols:
            aps = sorted (self.seenaps[pol])
        
            for i in xrange (0, len (aps)):
                ap4 = aps[i]
                for j in xrange (0, i):
                    ap3 = aps[j]
                    for k in xrange (0, j):
                        ap2 = aps[k]
                        for l in xrange (0, k):
                            ap1 = aps[l]

                            _flushOneAcc4 (acc, all, ap1, ap2, ap3, ap4)

        self.accData = {}
        self.seenpols = set ()
        self.seenaps = {}


    def process (self):
        seenQuads = set ()

        bpStats = AccDict (StatsAccumulator, lambda sa, rms: sa.add (rms))
        bpacc = bpStats.accum
        
        apStats = AccDict (StatsAccumulator, lambda sa, rms: sa.add (rms))
        apacc = apStats.accum

        def c ():
            for (key, ag) in self.allData.iteritems ():
                amps, thy = ag.finish ().T
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
        
                lrms = N.log (N.mean (amps**2)) / 2 # log of the rms

                if self.rmshist:
                    self.allrms.add (lrms)

                bpacc ((ap1, ap2), lrms)
                bpacc ((ap1, ap3), lrms)
                bpacc ((ap2, ap4), lrms)
                bpacc ((ap3, ap4), lrms)
                apacc (ap1, lrms)
                apacc (ap2, lrms)
                apacc (ap3, lrms)
                apacc (ap4, lrms)

                yield key, lrms

        self.qtyData = sorted (c (), key=lambda t: abs (t[1]))
        
        g = ((t[0], t[1].rms (), t[1].std (), t[1].num ()) for t in bpStats.iteritems ())
        self.bpData = sorted (g, key=lambda t: abs (t[1]))
        
        g = ((t[0], t[1].rms (), t[1].std (), t[1].num ()) for t in apStats.iteritems ())
        self.apData = sorted (g, key=lambda t: abs (t[1]))

        
class ClosureProcessor (object):
    def __init__ (self, interval, ccs, uvdPlot):
        self.interval = interval
        self.uvdPlot = uvdPlot

        self.ccs = ccs
        
        if uvdPlot:
            self.uvdists = AccDict (StatsAccumulator, lambda sa, v: sa.add (v))
        
    def _read (self, gen):
        ccs = self.ccs
        first = True
        interval = self.interval
        
        # Try to avoid doing tests and member lookups
        # inside the inner loop. Probably totally
        # unneccessary ...

        integs = [x.integrate for x in ccs]
        fis = [x.flushInteg for x in ccs]
        fas = [x.flushAcc for x in ccs]
        
        # Go!
        
        for inp, preamble, data, flags in gen:
            data = data.copy ()
            flags = flags.copy ()

            time = preamble[3]
            bp = util.mir2bp (inp, preamble)
    
            var = uvdat.getVariance ()
            inttime = inp.getVarFloat ('inttime')
    
            # Some first checks.
    
            if not util.bpIsInten (bp): continue
            if not flags.any (): continue
    
            if first:
                time0 = int (time - 0.5) + 0.5
                tmin = time - time0
                tmax = tmin
                tprev = tmin
                first = False

            t = time - time0

            if abs (t - tprev) > SECOND:
                for fi in fis: fi ()
                tprev = t

            if (t - tmin) > interval or (tmax - t) > interval:
                for fa in fas: fa ()
                tmin = tmax = t

            # Store info for this vis
    
            tmin = min (tmin, t)
            tmax = max (tmax, t)
            for integ in integs: integ (bp, data, flags, var, inttime)

            if self.uvdPlot:
                self.uvdists.accum (util.bp2aps (bp),
                                    N.sqrt ((preamble[0:3]**2).sum ()))

        # Clean up last interval
        
        for fi in fis: fi ()
        for fa in fas: fa ()

    def readUVDat (self):
        self._read (uvdat.read ())

    def readVis (self, vis):
        self._read (vis.readLowlevel ('w3', False))
    
    def plotUVDs (self):
        import omega
        from bisect import bisect
        
        d = ArrayGrower (2)
        bpd = self.ccs[0].bpData
        idxs = xrange (0, len (bpd))
        
        for bp, uvdsa in self.uvdists.iteritems ():
            uvd = uvdsa.mean () * 0.001

            # FIXME: slooooooow
            for i in idxs:
                if bpd[i][0] == bp:
                    break
            else:
                continue
            
            val = bpd[i][1]
            d.add (uvd, val)

        d = d.finish ()

        p = omega.quickXY (d[:,0], d[:,1], 'Closure values', lines=False)
        p.setLabels ('UV Distance (kilolambda)', '%s closure' % self.ccs[0].item)
        return p

# Task functionality

def task (args):
    banner = util.printBannerSvn ('closanal', 'attempt to identify bad baselines based on '
                                  'closure quantities', SVNID)

    ks = keys.KeySpec ()
    ks.keyword ('interval', 'd', 10.)
    ks.keyword ('nclos', 'i', 10)
    ks.keyword ('nbl', 'i', 10)
    ks.keyword ('nant', 'i', 10)
    ks.option ('rmshist', 'best', 'uvdplot', 'blhist', 'amplitude', 'relative')
    ks.uvdat ('dsl3xw', True)
    args = ks.process (args)

    # Verify arguments
    
    interval = args.interval / 60. / 24.
    if interval < 0:
        print >>sys.stderr, 'Error: averaging interval must be nonnegative'
        return 1

    # Summarize parameters

    if args.amplitude:
        cc = QuadComputer (args.rmshist, args.relative)
    else:
        cc = TripleComputer (args.rmshist, args.relative)
        
    print 'Configuration:'
    print '  Averaging interval: %g minutes' % (args.interval)
    print '  Calculating %s closure %s' % (cc.item, cc.datum)

    if args.relative:
        print '  Using relative (x/sigma_x) ranking'
    else:
        print '  Using absolute ranking'
        
    # Read the info

    cp = ClosureProcessor (interval, [cc], args.uvdplot)
        
    print 'Reading data ...',
    cp.readUVDat ()
    print 'done.'
    cc.pDataSummary ()

    # Compute and print out the statistics

    cc.computeStats ()

    cc.pQuantities (args.nclos, args.best)
    cc.pBasepols (args.nbl, args.best)
    cc.pAntpols (args.nant, args.best)

    # Misc queries

    if args.uvdplot:
        print
        print 'Showing baseline closure errors as function of UV distance ...'
        cp.plotUVDs ().show ()

    if args.rmshist:
        print
        print 'Showing histogram of closure quantities ...'
        cc.valHist ().show ()

    if args.blhist:
        print
        print 'Showing histogram of baseline closure values ...'
        cc.bpHist ().show ()

    # All done!
    
    return 0

# Standalone task execution

if __name__ == '__main__':
    sys.exit (task (sys.argv[1:]))
