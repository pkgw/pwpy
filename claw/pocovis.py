#! /usr/bin/env python

"""= pocovis.py - a skeleton task
& claw
: Unknown
+
 Script to load and visualize poco data
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

# initialize'
file = 'poco_crab_candpulse.mir'
sys.argv.append('vis='+file)
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
autos = []
noautos = []
for a1 in range(1,9):             # loop to adjust delays
    for a2 in range(a1,9):
        blindex = n.where(baseline_order == a1*256 + a2)[0][0]
        if a1 == a2:
            autos.append(blindex)
        else:
            noautos.append(blindex)

def load():
# read in data and create arrays
    keys.doUvdat ('dsl3', True)
    opts = keys.process ()

    i = 0
    initsize=50000
    da = n.zeros((initsize,nchan),dtype='complex64')
    fl = n.zeros((initsize,nchan),dtype='complex64')
    ti = n.zeros((initsize),dtype='complex64')
    for inp, preamble, data, flags, nread in uvdat.readAll ():

   # Reduce these arrays to the correct size
        data = data[0:nread]
        flags = flags[0:nread]

    # Decode the preamble
#        u, v, w = preamble[0:3]
        time = preamble[3]
#        baseline = util.decodeBaseline (preamble[4])

#    pol = uvdat.getPol ()
    
        if i < initsize:
            ti[i] = time
            da[i] = data
            fl[i] = flags
        else:
            da = n.concatenate((da,[data]))
            ti = n.concatenate((ti,[time]))
            fl = n.concatenate((fl,[flags]))
#            bl = n.concatenate((bl,[baseline]))
        i = i+1

    if i <= initsize:
        da = da[0:i]
        fl = fl[0:i]
        ti = ti[0:i]

    da = da.reshape(i/nbl,nbl,nchan)
    fl = fl.reshape(i/nbl,nbl,nchan)
    ti = ti[::nbl]
    return ti,da,fl

# End of loop.

def debug(da):
    for a1 in range(1,2):             # loop to adjust delays
        for a2 in range(a1,9):
            blindex = n.where(baseline_order == a1*256 + a2)[0][0]
            print 'For int 0, a1,a2,blindex,baseline:', a1, a2, blindex, a1*256 + a2
            print da[0,blindex]


def vis(da,chans=chans):
#reorganize into dimensions of integration, baseline, channel
    print 'Original data type and shape: ', type(da), ', ', da.shape

    abs = n.abs(da[:,noautos][:,:,chans].mean(axis=1))

    p.figure(1)
    day0 = int(time[0])
    ax = p.imshow(abs, aspect='auto')
#    ax = p.imshow(abs, aspect='auto', extent=(0,max(chans),max(time-day0),min(time-day0)))

#    p.axis([-0.5,len(chans)+0.5,100,0])
    p.colorbar(ax)

#def dedisperse(da):
    

# default stuff
time,data,flags = load()
data2 = data*flags
vis(data2)
