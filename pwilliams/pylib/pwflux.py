#! /usr/bin/env python
# -*- python -*-

"""= pwflux - assess point-source fluxes from UV data
& pkgw
: uv-analysis
+
 PWFLUX is performs the same function as the standard MIRIAD task
 UVFLUX: it computes fluxes in UV data, assuming the visibilities
 correspond to a single point source. PWFLUX differs from UVFLUX
 in the following ways:

 - UVFLUX computes flux values for all of the selected UV data;
   PWFLUX will divide the selected UV data into time intervals,
   in the usual way, and compute fluxes for each interval.
 - When computing fluxes, PWFLUX weights the contribution of each
   visibility by its variance. UVFLUX adds them up with equal weight.
 - PWFLUX can write its output in a tabular format, while UVFLUX
   cannot.
 - PWFLUX cannot handle more than one source per UV dataset, while
   UVFLUX can.
 - PWFLUX can only handle data with a single spectral window and
   no wide channels.

 PWFLUX accepts the following keyword arguments:

< vis
 PWFLUX allows multiple input visibility datasets.

@ interval
 The time interval into which the data are grouped for flux
 computation, in minutes. This is essentially an averaging
 interval. The default is 1.

@ offset
 The positional offset of the point source from phase center, in
 arcsec. The default is 0,0. The offset is measured such that north
 and east are positive, and the offset is measured on the sky (i.e.,
 the RA offset is divided by cos(dec) when computing the equatorial
 coordinates of the point source).

@ select
 The standard UV-data selection keyword. For more help, see 
 "mirhelp select".

@ line
 The standard channel selection keyword. For more help, see 
 "mirhelp line".

@ stokes
 The standard Stokes/polarization parameter selection keyword.
 For more help, see "mirhelp stokes".

@ textapp
 Flux information is appended to the specified textual file in a
 tabular format. FIXME specify it.
--

FIXME: assuming a single source per UV data file!
FIXME: assuming nspect=1 nwide=0, fixed corr. cfg, etc.
FIXME: compute weighted center times / time bounds via inttime, etc
"""

import sys, numpy as N, miriad
from mirtask import keys, uvdat, util

SVNID = '$Id$'
__all__ = ['Fluxer']


# Actual task implementation

D_REAL = 0
D_IMAG = 1
D_VAR = 2
D_AMP2 = 3
D_TOTWT = 4
I_COUNT = 0

class Fluxer (object):
    def __init__ (self, interval, offset):
        self.interval = interval
        self.offset = offset
        self.doOffset = (offset**2).sum () > 0
        self.flushfunc = None


    def onFlush (self, func):
        self.flushfunc = func
        return self


    lmn = None
    phscale = None

    def prepOffset (self, inp, nchan):
        # Copied from mmm/hex/hex-lib-calcgainerr

        ra0 = inp.getVarDouble ('ra')
        dec0 = inp.getVarDouble ('dec')
        ra = ra0 + self.offset[0] / N.cos (dec0)
        dec = dec0 + self.offset[1]

        l = N.sin (ra - ra0) * N.cos (dec)
        m = N.sin (dec) * N.cos (dec0) - N.cos (ra - ra0) * N.cos (dec) * N.sin (dec0)
        n = N.sin (dec) * N.sin (dec0) + N.cos (ra - ra0) * N.cos (dec) * N.cos (dec0)
        n -= 1 # makes the work below easier
        self.lmn = N.asarray ([l, m, n])

        # FIXME: assuming nspect=1, nwide=0
        sdf = inp.getVarDouble ('sdf')
        sfreq = inp.getVarDouble ('sfreq')
        self.phscale = 1 + N.arange (nchan) * sdf / sfreq


    def process (self):
        byPol = {}
        tMin = tMax = None

        for inp, preamble, data, flags in uvdat.read ():
            if not flags.any ():
                continue

            pol = uvdat.getPol ()
            variance = uvdat.getVariance ()
            t = preamble[3]

            # Separation into intervals -- time to flush?

            if tMin is None:
                tMin = tMax = t
            elif t - tMin > self.interval or tMax - t > self.interval:
                self.flush (tMin, tMax, byPol)
                byPol = {}
                tMin = tMax = t
            else:
                tMin = min (tMin, t)
                tMax = max (tMax, t)

            # Accumulation

            if self.doOffset:
                if self.lmn is None:
                    self.prepOffset (inp, data.size)
                ph0 = (0-2j) * N.pi * N.dot (self.lmn, preamble[0:3])
                data *= N.exp (ph0 * self.phscale)

            if pol in byPol:
                ddata, idata = byPol[pol]
            else:
                ddata = N.zeros (5, dtype=N.double)
                idata = N.zeros (1, dtype=N.int)
                byPol[pol] = ddata, idata

            w = N.where (flags)[0]
            ngood = w.size
            data = data[w]

            wt = 1 / variance

            ddata[D_REAL] += data.real.sum () * wt
            ddata[D_IMAG] += data.imag.sum () * wt
            ddata[D_VAR] += variance * ngood
            ddata[D_AMP2] += (data.real**2 + data.imag**2).sum ()
            ddata[D_TOTWT] += wt * ngood
            idata[I_COUNT] += ngood

        if tMin is not None:
            self.flush (tMin, tMax, byPol)
            byPol = {}


    def flush (self, tMin, tMax, byPol):
        if self.flushfunc is None:
            return

        poldata = {}

        for pol, (ddata, idata) in byPol.iteritems ():
            mreal = ddata[D_REAL] / ddata[D_TOTWT]
            mimag = ddata[D_IMAG] / ddata[D_TOTWT]
            u = 1. / N.sqrt (ddata[D_TOTWT])
            amp = N.sqrt (mreal**2 + mimag**2)
            # if real and imag have same uncert, uncert on amp is
            # that same value, if mreal, mimag >> u.
            ph = N.arctan2 (mimag, mreal)
            uph = N.abs (mimag / mreal) / (1 + (mimag / mreal)**2)
            phdeg = ph * 180 / N.pi
            uphdeg = uph * 180 / N.pi

            poldata[pol] = (mreal, mimag, amp, u, phdeg, uphdeg, idata[I_COUNT])

        self.flushfunc (tMin, tMax, poldata)


class TabularAppender (object):
    def __init__ (self, f):
        assert f is not None
        self.f = f


    def append (self, tMin, tMax, poldata):
        tCenter = 0.5 * (tMin + tMax)
        dur = tMax - tMin

        treal = 0.0
        tweight = 0.0

        for pol, data in poldata.iteritems ():
            mreal, mimag, amp, u, phdeg, uphdeg, count = data

            wt = u ** -2
            treal += mreal * wt
            tweight += wt

        real = treal / tweight
        uncert = 1 / N.sqrt (tweight)

        print >>self.f, '%.8f\t%.8f\t%.8f\t%.8f' % (tCenter, dur, real, uncert)
            

    def appendAndPrint (self, tmin, tmax, poldata):
        flushPrint (tmin, tmax, poldata)
        self.append (tmin, tmax, poldata)


# Task

def flushPrint (tMin, tMax, poldata):
    print 'Start/end times:', util.jdToFull (tMin), ';', util.jdToFull (tMax)
    print 'Duration:', (tMax - tMin) * 24 * 60, 'min'

    pols = sorted (poldata.iterkeys (), key=lambda p: abs (p))

    for pol in pols:
        pname = util.polarizationName (pol)

        mreal, mimag, amp, uamp, phdeg, uphdeg, count = poldata[pol]

        print '%s: real %f, imag %f, amp %f (+- %f), ph %f deg (+- %f) (%d items)' % \
            (pname, mreal, mimag, amp, uamp, phdeg, uphdeg, count)


def task (args=None):
    banner = util.printBannerSvn ('pwflux', 'calculate flux from UV data', SVNID)

    ks = keys.KeySpec ()
    ks.keyword ('interval', 'd', 1)
    ks.mkeyword ('offset', 'd', 2)
    ks.keyword ('textapp', 'f', ' ')
    ks.uvdat ('dsl3w', True)
    opts = ks.process (args)

    interval = opts.interval / (24. * 60.)

    if interval <= 0:
        print >>sys.stderr, 'Error: averaging interval must be positive, not', opts.interval
        return 1

    if len (opts.offset) == 0:
        offset = N.zeros (2)
    elif len (opts.offset) == 2:
        offset = N.asarray (opts.offset) / 206265.
    else:
        print >>sys.stderr, ('Error: zero or two values must be specified for source offset;'
                             ' got'), opts.offset
        return 1
    
    f = Fluxer (interval, offset)

    if opts.textapp == ' ':
        f.onFlush (flushPrint)
    else:
        appobj = TabularAppender (file (opts.textapp, 'a'))
        f.onFlush (appobj.appendAndPrint )

    f.process ()
    return 0


# Go

if __name__ == '__main__':
    sys.exit (task ())
