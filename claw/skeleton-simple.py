#! /usr/bin/env python

"""Skeleton code to read in a UV data file."""

import miriad, mirtask, mirtask.util

vis = miriad.VisData ('yourfilenamehere')

# If the argument to readLowlevel is True, flags will be written
# while iterating through the file. False is what you will want
# most of the time (unless you are editing the file's flags.)
#
# You can pass traditional Miriad UV keywords to readLowlevel as
# keyword arguments:
#
# vis.readLowlevel (False, select='-auto', nopol=True, line='chan,1,1')
#
# etc.

for inp, preamble, data, flags, nread in vis.readLowlevel (False):
    
    # Reduce these arrays to the correct size
    data = data[0:nread]
    flags = flags[0:nread]

    # Decode the preamble
    u, v, w = preamble[0:3]
    time = preamble[3]
    baseline = mirtask.util.decodeBaseline (preamble[4])

    pol = inp.getVarInt ('pol')
    
    # inp is a handle representing the current input file.
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
