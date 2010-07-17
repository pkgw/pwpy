#! /usr/bin/env python

"""= delayfit.py - a skeleton task
& claw
: Unknown
+
 Script to fit delays in a miriad data set.
--
"""

import sys
import mirtask
from mirtask import uvdat, keys, util
import numpy as n
import pylab as p
import scipy.optimize as opt

# This has us get our input file from the vis= keyword
# with support for select=, line=, stokes=,
# options=nocal,nopass,nopol

keys.doUvdat ('dsl3', True)
opts = keys.process ()

# initialize
nchan = 64
nbl = 36
sfreq = 0.7   # freq for first channel in GHz
sdf = 0.1/nchan   # dfreq per channel in GHz
baseline_order = n.array([257, 258, 514, 259, 515, 771, 260, 516, 772, 1028, 261, 517, 773, 1029, 1285, 518, 774, 1030, 1286, 1542, 775, 1031, 1287, 1543, 1799, 1032, 1288, 1544, 1800, 2056, 262, 263, 264, 519, 520, 776])
delay = n.array([0.,0.,0.,0.,0.,0.,0.,0.])  # first guess at delays

# create phase and rotation functions to rotate visibilities
delayphase = lambda delay1,delay2:  2 * n.pi * (sfreq+n.arange(nchan)*sdf) * (delay1 - delay2)   # calc delay phase for delay time diff
## ddelay off?!  units ok?
ddelay = lambda phaseperch:  phaseperch / (2 * n.pi * sdf)     # calc delay time diff for given phase change per channel (e.g., from fit)
rot = lambda ph: [n.complex(n.cos(n.degrees([ph[i]]), -n.sin(n.degrees([ph[i]])))) for i in range(nchan)]

# read in data and create arrays
i = 0
for inp, preamble, data, flags, nread in uvdat.readAll ():
    # Reduce these arrays to the correct size
    data = data[0:nread]
    flags = flags[0:nread]

    # Decode the preamble
    u, v, w = preamble[0:3]
    time = preamble[3]
    baseline = util.decodeBaseline (preamble[4])

    pol = uvdat.getPol ()
    
#    initialize arrays for later manipulation.  gotta be a better way...
    if i == 0:
        bl = n.array([baseline])
        da = n.array([data])
    else:
        bl = n.concatenate((bl,[baseline]))
        da = n.concatenate((da,[data]))
    i = i+1
# End of loop.

# visualize phases
def display(phase):
    for i in range(nbl):
        print 'Baseline: ',bl[i]
        p.figure(1)
        p.subplot(6,6,i+1)
        p.plot(phase[i])
        p.title(str(bl[i]))

    p.show()

# fit phases
def fitdelay(phase):
    p0 = [0.,0.]
    chans = n.arange(nchan)
    fitfunc = lambda p, x:  p[0] + p[1]*x
    errfunc = lambda p, x, y: fitfunc(p, x) - y
    p1, success = opt.leastsq(errfunc, p0[:], args = (chans, phase))
    if success: 
        print 'ok!', p1
#        p.plot(chans, phase)
#        p.plot(chans, fitfunc(p1, chans))
#        p.plot(chans, errfunc(p1, chans, phase))
#        p.show()
        return p1
    else:
        exit (1)

# adjust phases for current
def adjustphases(da,delay):
    for a1 in range(1,9):
        for a2 in range(a1+1,9):
#            print 'delay', delay
#            print 'delayphase(a1,a2)', delayphase(delay[a1-1],delay[a2-1])
            da = da * rot(delayphase(delay[a1-1],delay[a2-1]))
    phase = n.degrees(n.arctan2(da.imag,da.real))    # original phase values
    return phase

# analysis
phase = adjustphases(da,delay)    #  initial phases (observed values for delays=0)
for a1 in range(1,9):             # loop to adjust delays
    for a2 in range(a1+1,9):
        blindex = n.where(baseline_order == a1*256 + a2)[0][0]
        blcode = baseline_order[n.where(baseline_order == a1*256 + a2)][0]
        print 'a1,a2,blindex,blcode:', a1,a2,blindex,blcode

        if ((a1 == 1) & (a2 == 3)):
            p1 = fitdelay(phase[blindex])
            print 'need to adjust ',a1,a2,' by ',ddelay(p1[1])
            delay[0] = delay[0] + ddelay(p1[1])

            print 'delay: ', delay
            display(phase)
            phase = adjustphases(da,delay)
            display(phase)

sys.exit (0)
