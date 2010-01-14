#! /usr/bin/env python

"""Skeleton code to read in a UV data file."""

import miriad, mirtask, mirtask.util, pylab, sys
import numpy as N

vis = miriad.VisData ('ata42.snap')

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

u = []
v = []

for inp, preamble, data, flags, nread in vis.readLowlevel (False):
    
    # Reduce these arrays to the correct size
    data = data[0:nread]
    flags = flags[0:nread]

    # Decode the preamble
    uvw = preamble[0:3]
    u.append(uvw[0])
    v.append(uvw[1])

#    time = preamble[3]
#    baseline = mirtask.util.decodeBaseline (preamble[4])

#    pol = inp.getVarInt ('pol')
    
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

#    print 'Do something here!'

u = N.array(u)
v = N.array(v)

uvhist = N.histogram(u**2 + v**2, 50)
pylab.plot(uvhist[1][0:-1],uvhist[0])

gaussian = lambda amp,x,x0,sigma: amp * N.exp(-1./(2.*sigma**2)*(x-x0)**2)  # gaussian SNR distribution for comparison
gau = gaussian(max(uvhist[0]),100*N.arange(uvhist[1][-1]/100),0,10000)

pylab.plot(100*N.arange(uvhist[1][-1]/100), gau)

pylab.show()
