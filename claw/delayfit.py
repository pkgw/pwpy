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
from matplotlib.font_manager import fontManager, FontProperties

# This has us get our input file from the vis= keyword
# with support for select=, line=, stokes=,
# options=nocal,nopass,nopol

keys.doUvdat ('dsl3', True)
opts = keys.process ()

# initialize
nchan = 64
chans = n.arange(10,50)
nbl = 36
sfreq = 0.77  # freq for first channel in GHz
sdf = 0.104/nchan   # dfreq per channel in GHz
baseline_order = n.array([ 257, 258, 514, 261, 517, 1285, 262, 518, 1286, 1542, 259, 515, 773, 774, 771, 516, 1029, 1030, 772, 1028, 1287, 1543, 775, 1031, 1799, 1544, 776, 1032, 1800, 2056, 260, 263, 264, 519, 520, 1288])   # second iteration of bl nums
#baseline_order = n.array([257, 258, 514, 259, 515, 771, 260, 516, 772, 1028, 261, 517, 773, 1029, 1285, 518, 774, 1030, 1286, 1542, 775, 1031, 1287, 1543, 1799, 1032, 1288, 1544, 1800, 2056, 262, 263, 264, 519, 520, 776])   # wrong first guess?
delay = n.array([0.,0.,0.,0.,0.,0.,0.,0.])  # first guess at delays in ns
#delay = n.array([0.,0.,-20.,-20.,0.,0.,20.,20.])  # first guess at delays in noise source data (tfl8)
font= FontProperties(size='x-small');

# create phase and rotation functions to rotate visibilities
delayphase = lambda delay1,delay2:  (2 * n.pi * (sfreq+n.arange(nchan)*sdf) * (delay1 - delay2))  # calc delay phase for delay time diff
ddelay = lambda phaseperch:  phaseperch / (360. * sdf)     # calc delay time diff for given phase change per channel (e.g., from fit)
rot = lambda ph: [n.complex(n.cos([ph[i]]), -n.sin([ph[i]])) for i in range(nchan)]  # function to phase rotate a spectrum

#print [divmod(x,256) for x in baseline_order]

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
def display(phases,fig=1,showbl=[-1]):
    print ''
    print 'Plotting phases...'
    for a1 in range(1,9):
        for a2 in range(a1,9):
            if (showbl == [-1]):
                blindex = n.where(baseline_order == a1*256 + a2)[0][0]
                p.figure(fig)
                p.subplot(6,6,blindex+1)
                p.plot(phases[blindex,chans],'.',label=str(bl[blindex]))
                p.axis([0,len(chans),-180,180])
                p.legend(prop=font)
            else:
                if ((a1 in showbl) | (a2 in showbl)):
                    blindex = n.where(baseline_order == a1*256 + a2)[0][0]
                    p.figure(blindex)
                    p.plot(phases[blindex,chans])
                    p.title(str(bl[blindex]))
    p.show()

# need to avoid phase wraps during fitting
def unwrap(phase):
    print ''
    shift = n.zeros(len(phase))
    for i in range(len(phase)-2):
        dph0 = (phase + shift)[i+1] - (phase + shift)[i]
        dph1 = (phase + shift)[i+2] - (phase + shift)[i+1]
#        print 'dph0,dph1:  ',dph0,dph1
        if abs((phase + shift)[i] + 2*dph0 - (phase + shift)[i+2]) >= 180.:
            print 'Unwrapping phase at chan ',i+2
            shift[i+2:] = shift[i+2:] + n.sign(dph0) * 360.

#    print 'Spectrum of phase shifts:  ', shift
    return phase + shift

# fit phases
def fitdelay(phase):
    print ''
    p0 = [0.,0.]
    phase = unwrap(phase[chans])
    fitfunc = lambda p, x:  p[0] + p[1]*x
    errfunc = lambda p, x, y: fitfunc(p, x) - y
    p1, success = opt.leastsq(errfunc, p0[:], args = (chans, phase))
    if success: 
        print 'Fit ok!', p1
#        p.plot(chans, phase[chans])
#        p.plot(chans, fitfunc(p1, chans))
#        p.plot(chans, errfunc(p1, chans, phase[chans]))
#        p.show()
        return p1
    else:
        print 'Fit not ok!'
        exit (1)

# adjust phases for current
def adjustphases(da,delay):
    da2 = da.copy()
    for a1 in range(1,9):
        for a2 in range(a1,9):
            blindex = n.where(baseline_order == a1*256 + a2)[0][0]
#            print 'delay', delay
#            print 'delayphase(a1,a2)', delayphase(delay[a1-1],delay[a2-1])
#            print 'rot(delayphase(a1,a2))', rot(delayphase(delay[a1-1],delay[a2-1]))
#            da2[blindex] = da[blindex] * rot(delayphase(delay[a1-1],delay[a2-1]))
            if (a1 == a2):
                da2[blindex] = da[blindex]  # **why not cut this?**
            else:
#                if blindex in conj:
#                    da2[blindex] = n.conj(da[blindex]) * rot(delayphase(delay[a1-1],delay[a2-1]))
#                else:
                da2[blindex] = da[blindex] * rot(delayphase(delay[a1-1],delay[a2-1]))

    return n.angle(da2,deg=True)    # original phase values

# analysis
phases = adjustphases(da,delay)    #  initial phases (observed values for delays=0)
display(phases,fig=1)

for a1 in range(1,2):             # loop to adjust delays
    for a2 in range(a1+1,9):
        blindex = n.where(baseline_order == a1*256 + a2)[0][0]
        p1 = fitdelay(phases[blindex])
        print 'Need to adjust ',a1,a2,' by ',ddelay(p1[1]), 'ns'
        delay[a2-1] = delay[a2-1] - ddelay(p1[1])

print 'delay: ', delay
phases = adjustphases(da,delay)
display(phases,fig=2)

sys.exit (0)
