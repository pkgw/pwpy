#! /usr/bin/env python
# -*- python -*-

"""= gpmergepols - merge gains tables for multi-pol data
& pkgw
: calibration
+
 The tasks SELFCAL and MSELFCAL only operate on data of a single 
 polarization at a time. GPMERGEPOLS will take separate 
 single-feed two gains solutions, such as those created by
 running SELFCAL on data split into XX and YY pols, and
 merge them together into one table that can be applied to
 multiple-polarization datasets.

 GPMERGEPOLS is fairly strict in ensuring that its inputs have 
 gains tables for the same number of antennas, the same times, and
 so on.

@ vis
 Two input datasets. The first should contain a solution for the 
 X or L feeds only and the second should contain a solution for the
 Y or R feeds only.

@ out
 The name of an output dataset. The created dataset will contain the
 gain information but no visibility data. The gains in this set can
 by copied to visibility datasets with GPCOPY.

@ ttol
 The tolerance for differing gain solution timestamps in the datasets,
 measured in seconds. If SELFCAL is run separately on the XX and YY
 pols in a dataset, the gain solution timestamps will vary slightly
 between the two gains solutions. Default is 1 second, which should
 be strict but not overly so.

@ options
 Options are specified separated by commas. Minimum-match is used.

 'replace' - The output dataset already exists, and its gains will
   be replaced with the merged gains table.
--
"""

import sys, miriad
import numpy as N
from mirtask import keys, readgains
from mirtask.util import printBannerSvn

SVNID = '$Id$'


class FormatError (StandardError):
    pass


DEFAULT_TTOL = 1.0 / 86400

def merge (name1, ds1, name2, ds2, outset, banner, ttol):
    # Read in gains, check consistency
    int1 = ds1.getHeaderDouble ('interval', 0)
    gr1 = readgains.GainsReader (ds1)
    gr1.prep ()

    int2 = ds1.getHeaderDouble ('interval', 0)
    gr2 = readgains.GainsReader (ds2)
    gr2.prep ()

    for (gr, name) in ((gr1, name1), (gr2, name2)):
        if gr.nfeeds != 1:
            raise FormatError ('Dataset %s has gains for %d feeds; expected 1' %
                               (name, gr.nfeeds))

        if gr.ntau != 0:
            raise FormatError ('Delay terms are not supported in dataset %s' %
                               (name, ))

    def checksame (v1, v2, msg):
        if v1 == v2:
            return

        raise FormatError ('%s: %d and %d' % (msg, v1, v2))

    checksame (gr1.nants, gr2.nants, 'Disagreeing number of antennas')
    checksame (gr1.nsols, gr2.nsols, 'Disagreeing number of gain solutions')
    checksame (int1, int2, 'Disagreeing solution durations')

    nants = gr1.nants

    # Create and populate the new gains dataset
    outset.openHistory ()
    outset.writeHistory (banner)
    outset.logInvocation ('GPMERGEPOLS')

    outset.writeHeaderInt ('nsols', gr1.nsols)
    outset.writeHeaderInt ('nfeeds', 2)
    outset.writeHeaderInt ('ntau', 0)
    outset.writeHeaderInt ('ngains', nants * 2)
    outset.writeHeaderDouble ('interval', int1)

    gout = outset.getItem ('gains', 'w')
    gbuf = N.empty (nants * 2, dtype=N.complex64)
    gen1 = gr1.readSeq ()
    gen2 = gr2.readSeq ()
    offset = 8

    while True:
        try:
            done1 = False
            t1, g1 = gen1.next ()
        except StopIteration:
            done1 = True

        try:
            done2 = False
            t2, g2 = gen2.next ()
        except StopIteration:
            done2 = True

        if done1 or done2:
            if not (done1 and done2):
                raise FormatError ('Unequal number of gains solutions')
            break

        if abs (t1 - t2) > ttol:
            raise FormatError ('Disagreeing timestamps %f and %f (%.1f s, tol %.1f s)' %
                               (t1, t2, (t1 - t2) * 86400, ttol * 86400))

        gbuf[0::2] = g1
        gbuf[1::2] = g2

        gout.writeDoubles (t1, offset, 1)
        offset += 8
        gout.writeComplex (gbuf, offset, 2 * nants)
        offset += 8 * 2 * nants

    del gout
    outset.closeHistory ()


def task (argv):
    banner = printBannerSvn ('gpmergepols', 'merge gains table for multi-pol data',
                             SVNID)

    # Args
    keys.init (argv)
    keys.keyword ('vis', 'f', ' ', 2)
    keys.keyword ('out', 'f', ' ')
    keys.keyword ('ttol', 'd', DEFAULT_TTOL * 86400)
    keys.option ('replace')
    opts = keys.process ()

    if len (opts.vis) != 2:
        print >>sys.stderr, 'Error: must specify two input vis or gains files'
        return 1

    if opts.out == ' ':
        print >>sys.stderr, 'Error: must specify an output dataset'
        return 1

    ttol = opts.ttol / 86400

    # Run it
    ds1 = miriad.Data (opts.vis[0]).open ('rw')
    ds2 = miriad.Data (opts.vis[1]).open ('rw')

    if opts.replace:
        outset = miriad.Data (opts.out).open ('rw')
    else:
        outset = miriad.Data (opts.out).open ('c')
        ds1.copyHeader (outset, 'history')

    try:
        merge (opts.vis[0], ds1, opts.vis[1], ds2, outset, banner, ttol)
    except FormatError, e:
        print >>sys.stderr, 'Error:', e.args[0]
        return 1

    outset.close ()
    ds1.close ()
    ds2.close ()

    # All done
    return 0


if __name__ == '__main__':
    sys.exit (task (sys.argv))
