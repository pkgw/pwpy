#! /usr/bin/env python
#
# Build up an index of what was observed when, so we
# know what is the best observation to use as a reference
# for copying calibrations.

cutoff = 5. / 60 / 24 # cutoff to create a new entry - 5 mins

from miriad import VisData
from mirtask.util import jdToFull
from sys import argv, stderr

entries = []

for vname in argv[1:]:
    tSt = 0.
    tPrev = 0.
    
    print >>stderr, '   ', vname
    vis = VisData (vname)
    
    for inp, preamble, data, flags, nread in vis.readLowlevel (False):
        t = preamble[3]

        if abs (tPrev - t) > cutoff:
            if tSt > 0:
                entries.append ((tSt, tPrev, vname))
            tSt = t

        tPrev = t

    if tSt > 0:
        entries.append ((tSt, t, vname))

entries.sort (key = lambda x: x[0])

# Consistency check

prevTEnd = 0

for tSt, tEnd, vname in entries:
    assert tSt > prevTEnd, 'sequencing! %f %f %s' % (tSt, tEnd, vname)
    prevTEnd = tEnd

# Write out

for tSt, tEnd, v in entries: 
    print jdToFull (tSt), jdToFull (tEnd), v
