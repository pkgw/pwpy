# Copyright 2013 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""
xbblocks - extended Bayesian Blocks

Builds on the bayesian_blocks implementation by Jake Vanderplas in the AstroML
package (which has been borrowed into pwpy since it can stand alone).

We add iterative determination of the best number of blocks (using an ad-hoc
routine described in Scargle+ 2012) and bootstrap-based determination of
uncertainties on the block heights (ditto).
"""

import numpy as np
from bayesian_blocks import bayesian_blocks

__all__ = ['blockalyze']

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


def blockalyze (times, p0=0.05, nbootstrap=512):
    times = np.asarray (times)
    nevents = times.size
    if nevents < 2:
        raise ValueError ('must be given at least 2 events')

    # Use the iteration scheme described in Scargle+ 2012, section 2.7, to
    # adjust the p0 parameter to converge on a believable number of blocks.

    origp0 = p0
    prevnblocks = -1

    for _ in xrange (20):
        edges = bayesian_blocks (times, fitness='events', p0=p0)
        nblocks = edges.size - 1
        assert nblocks > 0

        if nblocks == prevnblocks:
            # Iteration converged. We *could* repeat the bootstrap analysis
            # below: the different value of p0 will give us different results,
            # above and beyond the variance associated with the random
            # bootstrap sampling. My (not-well-informed) intuition is that
            # it's more proper to use the values derived from the looser p0
            # value.
            break

        ledges = edges[:-1]
        redges = edges[1:]
        widths = redges - ledges

        # We must be careful about inequality-inclusiveness here to not
        # lose either the first or last event.
        counts = np.empty (nblocks)
        counts[0] = np.count_nonzero (times <= redges[0])
        for i in xrange (1, counts.size):
            counts[i] = np.count_nonzero ((times > ledges[i]) & (times <= redges[i]))
        assert counts.sum () == nevents

        rates = counts / widths
        midpoints = 0.5 * (ledges + redges)

        # Now bootstrap resample to figure out uncertainties on the bin heights. I
        # would have thought that the Bayesian analysis would get uncertainties
        # automagically, but this is the approach recommended by Scargle+.

        bs_rsums = np.zeros (nblocks)
        bs_rsumsqs = np.zeros (nblocks)

        for _ in xrange (nbootstrap):
            # Perform the bootstrap sample:
            bs_times = times[np.random.randint (0, times.size, times.size)]

            # Compute rates for this particular instance:
            bs_edges = bayesian_blocks (bs_times, fitness='events', p0=p0)
            bs_nblocks = bs_edges.size - 1

            bs_ledges = bs_edges[:-1]
            bs_redges = bs_edges[1:]
            bs_widths = bs_redges - bs_ledges

            bs_counts = np.empty (bs_nblocks)
            bs_counts[0] = np.count_nonzero (bs_times <= bs_redges[0])
            for i in xrange (1, bs_counts.size):
                bs_counts[i] = np.count_nonzero ((bs_times > bs_ledges[i]) &
                                                 (bs_times <= bs_redges[i]))

            bs_rates = bs_counts / bs_widths

            # Sample the bootstrap rates at the midpoints of the optimal blocks:
            bs_blocknums = np.minimum (np.searchsorted (bs_redges, midpoints),
                                       bs_nblocks - 1)
            optrates = bs_rates[bs_blocknums]
            bs_rsums += optrates
            bs_rsumsqs += optrates**2

        bsmeans = bs_rsums / nbootstrap
        bsstds = np.sqrt (bs_rsumsqs / nbootstrap - bsmeans**2)

        # Prepare for the next iteration. If only one block, no point in
        # rerunning.

        if nblocks == 1:
            break

        prevnblocks = nblocks
        p0 = 1 - (1 - p0)**(1. / nblocks)
    else:
        raise RuntimeError ('iterative nblock-finding algorithm didn\'t converge')

    rv = Holder ()
    rv.origp0 = origp0
    rv.finalp0 = p0
    rv.nevents = nevents
    rv.nblocks = nblocks
    rv.edges = edges
    rv.midpoints = midpoints
    rv.widths = widths
    rv.optcounts = counts
    rv.optrates = rates
    rv.bsrates = bsmeans
    rv.bsstds = bsstds
    return rv
