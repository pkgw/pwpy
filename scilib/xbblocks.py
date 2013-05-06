# Copyright 2013 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""
xbblocks - extended Bayesian Blocks

Bayesian Blocks analysis for the "time tagged" case described by Scargle+ 2013.
Inspired by the bayesian_blocks implementation by Jake Vanderplas in the AstroML
package, but that turned out to have some limitations.

We have iterative determination of the best number of blocks (using an ad-hoc
routine described in Scargle+ 2013) and bootstrap-based determination of
uncertainties on the block heights (ditto).
"""

import numpy as np

__all__ = ['nlogn binbblock ttbblock bsttbblock']

## quickutil: holder
#- snippet: holder.py (2012 Sep 29)
#- SHA1: bc9ad74474ffc74f18a12675f7422f0c5963df59
class Holder (object):
    def __init__ (self, **kwargs):
        self.set (**kwargs)

    def __str__ (self):
        d = self.__dict__
        s = sorted (d.iterkeys ())
        return '{' + ', '.join ('%s=%s' % (k, d[k]) for k in s) + '}'

    def __repr__ (self):
        d = self.__dict__
        s = sorted (d.iterkeys ())
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join ('%s=%r' % (k, d[k]) for k in s))

    def set (self, **kwargs):
        self.__dict__.update (kwargs)
        return self

    def get (self, name, defval=None):
        return self.__dict__.get (name, defval)

    def setone (self, name, value):
        self.__dict__[name] = value
        return self

    def has (self, name):
        return name in self.__dict__

    def copy (self):
        new = self.__class__ ()
        new.__dict__ = dict (self.__dict__)
        return new
## end


def nlogn (n, dt):
    # I really feel like there must be a cleverer way to do this
    # scalar-or-vector possible-bad-value masking.

    if np.isscalar (n):
        if n == 0:
            return 0.
        return n * (np.log (n) - np.log (dt))

    n = np.asarray (n)
    mask = (n == 0)
    r = n * (np.log (np.where (mask, 1, n)) - np.log (dt))
    return np.where (mask, 0, r)


def binbblock (widths, counts, p0=0.05):
    widths = np.asarray (widths)
    counts = np.asarray (counts)
    ncells = widths.size
    origp0 = p0

    if np.any (widths <= 0):
        raise ValueError ('bin widths must be positive')
    if widths.size != counts.size:
        raise ValueError ('widths and counts must have same size')
    if p0 < 0 or p0 >= 1.:
        raise ValueError ('p0 must lie within [0, 1)')

    vedges = np.cumsum (np.concatenate (([0], widths))) # size: ncells + 1
    block_remainders = vedges[-1] - vedges # size: nedges = ncells + 1
    ccounts = np.cumsum (np.concatenate (([0], counts)))
    count_remainders = ccounts[-1] - ccounts

    prev_blockstarts = None
    best = np.zeros (ncells, dtype=np.float)
    last = np.zeros (ncells, dtype=np.int)

    for _ in xrange (10):
        # Pluggable num-change-points prior-weight expression:
        ncp_prior = 4 - np.log (p0 / (0.0136 * ncells**0.478))

        for r in xrange (ncells):
            tk = block_remainders[:r+1] - block_remainders[r+1]
            nk = count_remainders[:r+1] - count_remainders[r+1]

            # Pluggable fitness expression:
            try:
                fit_vec = nlogn (nk, tk)
            except:
                print 'q', nk, tk
                print 'r', widths, counts
                raise

            # This incrementally penalizes partitions with more blocks:
            tmp = fit_vec - ncp_prior
            tmp[1:] += best[:r]

            imax = np.argmax (tmp)
            last[r] = imax
            best[r] = tmp[imax]

        # different semantics than Scargle impl: our blockstarts is similar to
        # their changepoints, but we always finish with blockstarts[0] = 0.

        work = np.zeros (ncells, dtype=int)
        workidx = 0
        ind = last[-1]

        while True:
            work[workidx] = ind
            workidx += 1
            if ind == 0:
                break
            ind = last[ind - 1]

        blockstarts = work[:workidx][::-1]

        if prev_blockstarts is not None:
            if (blockstarts.size == prev_blockstarts.size and
                (blockstarts == prev_blockstarts).all ()):
                break # converged

        if blockstarts.size == 1:
            break # can't shrink any farther

        # Recommended ad-hoc iteration to favor fewer blocks above and beyond
        # the value of p0:
        p0 = 1. - (1. - p0)**(1. / (blockstarts.size - 1))
        prev_blockstarts = blockstarts

    assert blockstarts[0] == 0
    nblocks = blockstarts.size

    info = Holder ()
    info.ncells = ncells
    info.nblocks = nblocks
    info.origp0 = origp0
    info.finalp0 = p0
    info.blockstarts = blockstarts
    info.counts = np.empty (nblocks, dtype=np.int)
    info.widths = np.empty (nblocks)

    for iblk in xrange (nblocks):
        cellstart = blockstarts[iblk]
        if iblk == nblocks - 1:
            cellend = ncells - 1
        else:
            cellend = blockstarts[iblk+1] - 1

        info.widths[iblk] = widths[cellstart:cellend+1].sum ()
        info.counts[iblk] = counts[cellstart:cellend+1].sum ()

    info.rates = info.counts / info.widths
    return info


def ttbblock (tstart, tstop, times, p0=0.05):
    times = np.asarray (times)
    dt = times[1:] - times[:-1]

    if np.any (dt < 0):
        raise ValueError ('times must be ordered')
    if times.min () < tstart:
        raise ValueError ('no times may be smaller than tstart')
    if times.max () > tstop:
        raise ValueError ('no times may be larger than tstop')
    if p0 < 0 or p0 >= 1.:
        raise ValueError ('p0 must lie within [0, 1)')

    utimes, uidxs = np.unique (times, return_index=True)
    nunique = utimes.size

    counts = np.empty (nunique)
    counts[:-1] = uidxs[1:] - uidxs[:-1]
    counts[-1] = times.size - uidxs[-1]
    #assert counts.sum () == times.size

    midpoints = 0.5 * (utimes[1:] + utimes[:-1]) # size: nunique - 1
    edges = np.concatenate (([tstart], midpoints, [tstop])) # size: nunique + 1
    widths = edges[1:] - edges[:-1] # size: nunique
    #assert widths.sum () == tstop - tstart

    info = binbblock (widths, counts, p0=p0)
    info.ledges = edges[info.blockstarts]
    info.redges = np.concatenate ((edges[info.blockstarts[1:]], [tstop]))
    info.midpoints = 0.5 * (info.ledges + info.redges)
    return info


def bsttbblock (times, tstart, tstop, p0=0.05, nbootstrap=512):
    np.seterr ('raise')
    times = np.asarray (times)
    nevents = times.size
    if nevents < 1:
        raise ValueError ('must be given at least 1 event')

    info = ttbblock (tstart, tstop, times, p0)

    # Now bootstrap resample to assess uncertainties on the bin heights. This
    # is the approach recommended by Scargle+.

    bsrsums = np.zeros (info.nblocks)
    bsrsumsqs = np.zeros (info.nblocks)

    for _ in xrange (nbootstrap):
        bstimes = times[np.random.randint (0, times.size, times.size)]
        bstimes.sort ()
        bsinfo = ttbblock (tstart, tstop, bstimes, p0)
        blocknums = np.minimum (np.searchsorted (bsinfo.redges, info.midpoints),
                                bsinfo.nblocks - 1)
        samprates = bsinfo.rates[blocknums]
        bsrsums += samprates
        bsrsumsqs += samprates**2

    bsrmeans = bsrsums / nbootstrap
    mask = bsrsumsqs / nbootstrap <= bsrmeans**2
    bsrstds = np.sqrt (np.where (mask, 0, bsrsumsqs / nbootstrap - bsrmeans**2))
    info.bsrates = bsrmeans
    info.bsrstds = bsrstds
    return info
