#! /usr/bin/env python

"""Skeleton code to read in a UV data file."""

import miriad, mirtask, mirtask.util, pylab, sys
import numpy as N

vis1 = miriad.VisData ('ata42.snap')
vis2 = miriad.VisData ('ata1-32.snap')
#vis3 = miriad.VisData ('ata.top-bottom.cut.snap')
vis3 = miriad.VisData ('ata21-20.merge.cut.snap')

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

u1 = []; v1 = []
u2 = []; v2 = []
u3 = []; v3 = []

for inp, preamble, data, flags, nread in vis1.readLowlevel (False):
    
    # Reduce these arrays to the correct size
    data = data[0:nread]
    flags = flags[0:nread]

    # Decode the preamble
    uvw = preamble[0:3]
    u1.append(uvw[0])
    v1.append(uvw[1])

for inp, preamble, data, flags, nread in vis2.readLowlevel (False):
    
    # Reduce these arrays to the correct size
    data = data[0:nread]
    flags = flags[0:nread]

    # Decode the preamble
    uvw = preamble[0:3]
    u2.append(uvw[0])
    v2.append(uvw[1])

for inp, preamble, data, flags, nread in vis3.readLowlevel (False):
    
    # Reduce these arrays to the correct size
    data = data[0:nread]
    flags = flags[0:nread]

    # Decode the preamble
    uvw = preamble[0:3]
    u3.append(uvw[0])
    v3.append(uvw[1])

u1 = N.array(u1);  v1 = N.array(v1)
u2 = N.array(u2);  v2 = N.array(v2)
u3 = N.array(u3);  v3 = N.array(v3)

print len(u1)
print len(u2)
print len(u3)

# make and plot uv histograms
uvhist1 = N.histogram(N.sqrt(u1**2 + v1**2), 40)
uvhist2 = N.histogram(N.sqrt(u2**2 + v2**2), 40)
uvhist3 = N.histogram(N.sqrt(u3**2 + v3**2), 40)

pylab.plot(uvhist1[1][0:-1],uvhist1[0], label='Full 42')
pylab.plot(uvhist2[1][0:-1],uvhist2[0], label='Minimal 1-32')
pylab.plot(uvhist3[1][0:-1],uvhist3[0], label='Proposed dual correlator')

# make and plot similar gaussians

gaussian = lambda amp,x,x0,sigma: amp * N.exp(-1./(2.*sigma**2)*(x-x0)**2)  # gaussian SNR distribution for comparison
gau1 = gaussian(0.9*max(uvhist1[0]),100*N.arange(uvhist1[1][-1]/100),100,500)
gau2 = gaussian(0.8*max(uvhist2[0]),100*N.arange(uvhist2[1][-1]/100),100,500)

#pylab.plot(100*N.arange(uvhist1[1][-1]/100), gau1)
#pylab.plot(100*N.arange(uvhist2[1][-1]/100), gau2, color='green')
pylab.xlabel('UV Distance (lambda)')
pylab.ylabel('Number of baselines')
pylab.legend()

pylab.show()
