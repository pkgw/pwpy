#! /usr/bin/env python
# Copyright 2012 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

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

import numpy as np
from mirtask import keys, util, uvdat
import sys

IDENT = '$Id$'
SECOND = 1.0 / 3600. / 24.

## quickutil: accdict arraygrower vectorgrower statsacc weightacc
#- snippet: accdict.py
#- date: 2012 Feb 27
#- SHA1: 8864021336ff2d87be433823cc9cca04657862ae
class AccDict (dict):
    """An accumulating dictionary.

create = lambda: <new accumulator object>
accum = lambda a, v: <accumulate v into accumulator a>

e.g.: create = list, accum = lambda l, v: l.append (v)
"""

    __slots__ = '_create _accum'.split ()

    def __init__ (self, create, accum):
        self._create = create
        self._accum = accum

    def accum (self, key, val):
        entry = self.get (key)
        if entry is None:
            self[key] = entry = self._create ()

        self._accum (entry, val)
        return self
#- snippet: arraygrower.py
#- date: 2012 Feb 27
#- SHA1: 8ae43ac24e7ea0fb6ee2cc1047cab1588433a7ec
class ArrayGrower (object):
    __slots__ = 'dtype ncols chunkSize _nextIdx _arr'.split ()

    def __init__ (self, ncols, dtype=None, chunkSize=128):
        if dtype is None:
            import numpy as np
            dtype = np.float

        self.dtype = dtype
        self.ncols = ncols
        self.chunkSize = chunkSize
        self.clear ()


    def clear (self):
        self._nextIdx = 0
        self._arr = None
        return self


    def __len__ (self):
        return self._nextIdx


    def addLine (self, line):
        from numpy import asarray, ndarray

        line = asarray (line, dtype=self.dtype)
        if line.size != self.ncols:
            raise ValueError ('line is wrong size')

        if self._arr is None:
            self._arr = ndarray ((self.chunkSize, self.ncols),
                                 dtype=self.dtype)
        elif self._arr.shape[0] <= self._nextIdx:
            self._arr.resize ((self._arr.shape[0] + self.chunkSize,
                               self.ncols))

        self._arr[self._nextIdx] = line
        self._nextIdx += 1
        return self


    def add (self, *args):
        self.addLine (args)
        return self


    def finish (self):
        if self._arr is None:
            from numpy import ndarray
            ret = ndarray ((0, self.ncols), dtype=self.dtype)
        else:
            self._arr.resize ((self._nextIdx, self.ncols))
            ret = self._arr

        self.clear ()
        return ret
#- snippet: vectorgrower.py
#- date: 2012 Feb 27
#- SHA1: 87dc19e32d84ade4a740dc856d9692fa9be186f7
class VectorGrower (object):
    __slots__ = 'dtype chunkSize _nextIdx _vec'.split ()

    def __init__ (self, dtype=None, chunkSize=128):
        if dtype is None:
            import numpy
            dtype = numpy.float

        self.dtype = dtype
        self.chunkSize = chunkSize
        self.clear ()


    def clear (self):
        self._nextIdx = 0
        self._vec = None
        return self


    def __len__ (self):
        return self._nextIdx


    def add (self, val):
        if self._vec is None:
            from numpy import ndarray
            self._vec = ndarray ((self.chunkSize, ), dtype=self.dtype)
        elif self._vec.size <= self._nextIdx:
            self._vec.resize ((self._vec.size + self.chunkSize, ))

        self._vec[self._nextIdx] = val
        self._nextIdx += 1
        return self


    def finish (self):
        if self._vec is None:
            from numpy import ndarray
            ret = ndarray ((0, ), dtype=self.dtype)
        else:
            self._vec.resize ((self._nextIdx, ))
            ret = self._vec

        self.clear ()
        return ret
#- snippet: statsacc.py
#- date: 2012 Feb 27
#- SHA1: 37d74dcad853c14a76e2fb627c8f9063d19e9d0c
class StatsAccumulator (object):
    # FIXME: I worry about loss of precision when n gets very large:
    # we'll be adding a tiny number to a large number.  We could
    # periodically rebalance or something. I'll think about it more if
    # it's ever actually a problem.

    __slots__ = 'xtot xsqtot n _shape'.split ()

    def __init__ (self, shape=None):
        self._shape = shape
        self.clear ()

    def clear (self):
        if self._shape is None:
            self.xtot = 0.
            self.xsqtot = 0.
        else:
            from numpy import zeros
            self.xtot = zeros (self.shape)
            self.xsqtot = zeros (self.shape)

        self.n = 0
        return self

    def add (self, x):
        if self._shape is not None:
            from numpy import asarray
            x = asarray (x)
            if x.shape != self._shape:
                raise ValueError ('x has wrong shape')

        self.xtot += x
        self.xsqtot += x**2
        self.n += 1
        return self

    def num (self):
        return self.n

    def mean (self):
        return self.xtot / self.n

    def rms (self):
        if self._shape is None:
            from math import sqrt
        else:
            from numpy import sqrt
        return sqrt (self.xsqtot / self.n)

    def std (self):
        if self._shape is None:
            from math import sqrt
        else:
            from numpy import sqrt
        return sqrt (self.var ())

    def var (self):
        return self.xsqtot/self.n - (self.xtot/self.n)**2
#- snippet: weightacc.py
#- date: 2012 Feb 27
#- SHA1: 47853621ac1518fe8529d3233df4a9124ecb4f1a
class WeightAccumulator (object):
    """Standard statistical weighting is wt_i = sigma_i**-2. We don't
need the 'n' variable to do any stats, but it can be nice to have that
information."""

    __slots__ = 'xwtot wtot n _shape'.split ()

    def __init__ (self, shape=None):
        self._shape = shape
        self.clear ()

    def clear (self):
        if self._shape is None:
            self.xwtot = 0.
            self.wtot = 0.
        else:
            from numpy import zeros
            self.xwtot = zeros (self._shape)
            self.wtot = zeros (self._shape)

        self.n = 0
        return self

    def add (self, x, wt):
        self.xwtot += x * wt
        self.wtot += wt
        self.n += 1
        return self

    def num (self):
        return self.n

    def wtavg (self, nullval):
        if self._shape is None:
            if self.wtot == 0:
                return nullval
            return self.xwtot / self.wtot

        # Vectorized case. Trickier.
        zerowt = (self.wtot == 0)
        if not zerowt.any ():
            return self.xwtot / self.wtot

        from numpy import putmask
        weff = self.wtot.copy ()
        putmask (weff, zerowt, 1)
        result = self.xwtot / weff
        putmask (result, zerowt, nullval)
        return result

    def var (self):
        """Assumes wt_i = sigma_i**-2"""
        return 1. / self.wtot

    def std (self):
        """Uncertainty of the mean (i.e., scales as ~1/sqrt(n_vals))"""
        if self._shape is None:
            from math import sqrt
        else:
            from numpy import sqrt
        return sqrt (self.var ())
## end

p2p = lambda ap1, ap2: util.bpToPBP32 ((ap1, ap2))


def _format (aps):
    if isinstance (aps, int): aps = (aps, )
    return '-'.join (util.fmtAP (x) for x in aps)


def _flagAnd (flags1, flags2, *rest):
    # Avoid allocation of many temporary arrays here.
    isect = np.logical_and (flags1, flags2)

    for f in rest:
        np.logical_and (isect, f, isect)

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

    w = np.where (_flagAnd (f12, f13, f23))
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
    w = np.where (_flagAnd (f12, f13, f24, f34, d13 != 0, d24 != 0))
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
    ph = 180/np.pi * np.arctan2 (c.imag, c.real)
    amp = np.abs (c) / time
    thy = 180/np.pi * np.sqrt (v / time) / (amp ** (1./3))

    allData.accum (key, (ph, thy))
    #allData.accum (key, (time, ph, v / time))


def _flushOneAcc4 (accData, allData, ap1, ap2, ap3, ap4):
    key = (ap1, ap2, ap3, ap4)
    tup = accData.get (key)
    if tup is None:
        return

    (time, c, v) = tup
    amp = np.abs (c) / time
    thy = np.sqrt (v) / time

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

    def integrate (self, pbp, data, flags, var, inttime):
        for ap in util.pbp32ToBP (pbp):
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
        n = int (np.ceil (np.log2 (rms.size) + 1))
        p = omega.quickHist (rms, n, keyText=self.datum)
        p.setLabels ('%s closure' % self.item, 'Number of %s' % self.datum)
        return p


    def bpHist (self):
        import omega
        n = int (np.ceil (np.log2 (len (self.bpData)) + 1))
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
                rms = np.sqrt (np.mean (phs**2))
                thy = np.sqrt (np.mean (thys**2))

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
            tval = lambda t: (t[0], t[1].wtavg (0), t[1].std (),
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

                lrms = np.log (np.mean (amps**2)) / 2 # log of the rms

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

                yield key, lrms, 0.

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
            bp = util.mir2pbp32 (inp, preamble)

            var = inp.getVariance ()
            inttime = inp.getVarFloat ('inttime')

            # Some first checks.

            if not util.pbp32IsInten (bp): continue
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
                self.uvdists.accum (util.pbp32ToBP (bp),
                                    np.sqrt ((preamble[0:3]**2).sum ()))

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
    banner = util.printBannerGit ('closanal', 'attempt to identify bad baselines based on '
                                  'closure quantities', IDENT)

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
