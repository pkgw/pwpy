#! /usr/bin/env python

"""= skeleton.py - a skeleton task
& pkgw
: Unknown
+
 This file is a skeleton for a Miriad task that reads in UV data.
--
"""

import sys
import mirtask
from mirtask import uvdat, keys, util

# This has us get our input file from the vis= keyword
# with support for select=, line=, stokes=,
# options=nocal,nopass,nopol

keys.doUvdat ('dsl3', True)
opts = keys.process ()

for inp, preamble, data, flags, nread in uvdat.readAll ():
    # Reduce these arrays to the correct size
    data = data[0:nread]
    flags = flags[0:nread]

    # Decode the preamble
    u, v, w = preamble[0:3]
    time = preamble[3]
    baseline = util.decodeBaseline (preamble[4])

    pol = uvdat.getPol ()
    
    # inp is a handle representing the current input file
    # (this can change if you run this with vis=foo,bar)
    # You can access UV variables and other things via inp.

    # data is a Numpy array of 'nread' complex numbers giving
    # the complex visibilities

    # flags is a Numpy array of 'nread' integers giving flag
    # status: 0 if flagged out, 1 if unflagged

    # u, v, w are the coordinates of this spectrum measured
    # in nanoseconds
    
    # time is a julian date

    # baseline is a tuple of two integers giving the baseline
    # of this visibility

    # pol is the FITS-encoded polarization value; mnemonics
    # are stored in util.POL_XX, util.POL_YY, etc.

    print 'Do something here!'

# End of loop.
sys.exit (0)
