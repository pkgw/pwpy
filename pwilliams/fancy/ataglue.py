#! /usr/bin/env python
"""ataglue - Merge together two ATA half-datasets, accounting for single-item errors."""
# Blah de blah
#
# UVW coordinate handling : the left and right halves have slightly-different UVW
# coordinates. From this I infer that the UVW coordinate refers to the first channel
# in a multichannel dataset, since if referred to the nominal observing
# frequency, it would be the same in both datasets. Hence we should write the
# coordinates from the half-1 preamble as that will still have the first channel
# in the merged dataset. I hope.
#
# UPDATE: I am told that the UVW coordinates should be relative to the sky frequency.
# Need to check on equality etc in datasets
#
# 3c48 2880 is a nice dataset with one epoch where the two halves are aligned.

import sys, numpy as N
from miriad import *
from mirtask import keys, util

# Some constants

specVars = ['ischan', 'nschan', 'nspect', 'restfreq',
            'sdf', 'sfreq']

AF_NEITHER, AF_LEFT, AF_RIGHT, AF_BOTH = range (0, 4)

# Keyword handling

banner = 'ATAGLUE (Python): Glue together two 512-channel ATA datasets'
print banner

keys.keyword ('out', 'f', ' ')
keys.keyword ('vis', 'f', None, 2)
opts = keys.process ()

if opts.out == ' ':
    print >>sys.stderr, 'Error: must give output filename.'
    sys.exit (1)

if len (opts.vis) != 2:
    print >>sys.stderr, 'Error: must give exactly two input datasets'
    sys.exit (1)

# Setup.

dOut = VisData (opts.out).open ('w')
dOut.setPreambleType ('uvw', 'time', 'baseline')

in1 = VisData (opts.vis[0]).open ('r')
in1.setPreambleType ('uvw', 'time', 'baseline')
in2 = VisData (opts.vis[1]).open ('r')
in2.setPreambleType ('uvw', 'time', 'baseline')

in1.copyHeader (dOut, 'history')
dOut.openHistory ()
dOut.writeHistory (banner)
dOut.logInvocation ('ATAGLUE')
dOut.closeHistory ()

in1.initVarsAsInput ('channel')
dOut.initVarsAsOutput (in1, 'channel')

# To check for assumption non-violation
sanity1 = in1.makeVarTracker ()
sanity1.track (*specVars)
sanity2 = in2.makeVarTracker ()
sanity2.track (*specVars)

mData = N.ndarray (1024, dtype=N.complex64)
mFlags = N.ndarray (1024, dtype=N.int32)
pream1 = N.ndarray (5, dtype=N.double)
pream2 = N.ndarray (5, dtype=N.double)

reads = {1: 0, 2: 0} # keyed by half-1 or half-2
writes = {1: 0, 2: 0}

def getConfig (src):
    return (src.getVarInt ('ischan'),
            src.getVarInt ('nschan'),
            src.getVarInt ('nspect'),
            src.getVarDouble ('restfreq'),
            src.getVarDouble ('sdf'),
            src.getVarDouble ('sfreq'))

def write (src, pream):
    src.copyLineVars (dOut)
    dOut.writeVarInt ('pol', src.getVarInt ('pol'))
    dOut.writeVarInt ('npol', src.getVarInt ('npol'))
    dOut.writeVarInt ('nspect', 1)
    dOut.writeVarInt ('nschan', 1024)        
    dOut.writeVarInt ('ischan', 1)
    dOut.writeVarDouble ('sfreq', sfreq)
    dOut.writeVarDouble ('sdf', sdf)
    dOut.writeVarDouble ('restfreq', restfreq)
    dOut.write (pream, mData, mFlags, 1024)

def aligned (first, t1, t2):
    while t1 == t2:
        # No important variables changed?
        if not first and sanity1.updated () and getConfig (in1) != config1:
            print >>sys.stderr, 'Error: correlator configuration changed in input 1!'
            sys.exit (1)
                
        if not first and sanity2.updated () and getConfig (in2) != config2:
            print >>sys.stderr, 'Error: correlator configuration changed in input 2!'
            sys.exit (1)

        # Preambles agree?
        if pream1[3] != pream2[3] or pream1[4] != pream2[4]:
            print >>sys.stderr, 'Error: preamble disagreement! (1)'
            print >>sys.stderr, pream1
            print >>sys.stderr, pream2
            print >>sys.stderr, pream1[3] - pream2[3], pream1[4] - pream2[4]
            sys.exit (1)

        writes[1] += 1
        writes[2] += 1
        write (in1, pream1)
            
        n1 = in1.lowlevelRead (pream1, mData[:512], mFlags[:512], 512)
        n2 = in2.lowlevelRead (pream2, mData[512:], mFlags[512:], 512)

        # Read everything OK? Break if a dataset is done.
        if n1 == 0 and n2 == 0:
            return AF_BOTH
        elif n1 == 0:
            reads[2] += 1
            pream1[3] = 0.
            return AF_LEFT
        elif n2 == 0:
            reads[1] += 1
            pream2[3] = 0.
            return AF_RIGHT
        elif n1 != 512 or n2 != 512:
            print >>sys.stderr, 'Error: unequal amounts read?!? %d %d' % (n1, n2)
            sys.exit (1)
        else:
            reads[1] += 1
            reads[2] += 1
        
        t1 = pream1[3]
        t2 = pream2[3]

    return AF_NEITHER

def catchup (leftIsAhead, expectFinish, first, t1, t2):
    if leftIsAhead:
        ahead = in1
        ta = t1
        sanitya = sanity1
        preama = pream1
        configa = config1
        akey = 1
    else:
        ahead = in2
        ta = t2
        sanitya = sanity2
        preama = pream2
        configa = config2
        akey = 2

    # Scan in the ahead half, write it out half-flagged
    t = ta
    #print 'Catchup starting with', util.jdToFull (t)
    
    while t == ta:
        # No important variables changed?
        if not first and sanitya.updated () and getConfig (ahead) != configa:
            print >>sys.stderr, 'Error: correlator configuration changed in ahead input!'
            sys.exit (1)
                
        if leftIsAhead: mFlags[512:].fill (0)
        else: mFlags[:512].fill (0)

        #print 'Writing half-record'
        writes[akey] += 1
        write (ahead, preama)

        if leftIsAhead:
            na = ahead.lowlevelRead (preama, mData[:512], mFlags[:512], 512)
        else:
            na = ahead.lowlevelRead (preama, mData[512:], mFlags[512:], 512)

        #print 'Read half-record, got', na
        
        if na == 0:
            if expectFinish:
                #print 'Expected to finish and did'
                return True
            print >>sys.stderr, 'Error: Unexpected EOF in ahead dataset'
            sys.exit (1)
        elif na != 512:
            print >>sys.stderr, 'Error: Read error from ahead dataset. (%d)' % na
            sys.exit (1)
        else:
            reads[akey] += 1

        t = preama[3]
        #print 'New time', util.jdToFull (t)

    #print 'Exited because got to new timestamp'
    return False

# Main loop

first = True
nAlign = nLeft = nRight = 0

while True:
    if first:
        n1 = in1.lowlevelRead (pream1, mData[:512], mFlags[:512], 512)
        n2 = in2.lowlevelRead (pream2, mData[512:], mFlags[512:], 512)
        assert n1 == 512
        assert n2 == 512
        reads[1] = reads[2] = 1
        
        corrType, corrLen, corrUpd = in1.probeVar ('corr')
        dOut.setCorrelationType (corrType)

        sfreq = in1.getVarDouble ('sfreq')
        sdf = in1.getVarDouble ('sdf')
        restfreq = in1.getVarDouble ('restfreq')
        
        config1 = getConfig (in1)
        config2 = getConfig (in2)

    t1 = pream1[3]
    t2 = pream2[3]
    print '%s %s: ' % (util.jdToFull (t1), util.jdToFull (t2)),
    
    if t1 == t2:
        #if prevState == PS_1AHEAD:
        # The two sets are aligned for this chunk. Nice!
        print 'aligned'
        nAlign += 1
        finishState = aligned (first, t1, t2)

        if finishState == AF_BOTH:
            break
        elif finishState == AF_LEFT:
            # Will exit if the right dataset doesn't finish
            nRight += 1
            print 'Left finished, catching up right'
            catchup (False, True, first, 0, t2)
            break
        elif finishState == AF_LEFT:
            # Will exit if the left dataset doesn't finish
            nLeft += 1
            print 'Right finished, catching up left'
            catchup (True, True, first, t1, 0)
            break
    elif t1 < t2:
        print 'need to catch up left'
        nLeft += 1
        catchup (True, False, first, t1, t2)
    else:
        print 'need to catch up right'
        nRight += 1
        catchup (False, False, first, t1, t2)
    
    # We now have the first items for the next pair of runs read in,
    # and are ready to start again.
    first = False

dOut.close ()

print 'Had %d aligned runs, %d left catchups, and %d right catchups.' % \
      (nAlign, nLeft, nRight)
print 'Left/right half-reads: %d / %d ' % (reads[1], reads[2])
print 'Left/right half-writes: %d / %d ' % (writes[1], writes[2])

# Check everything.

if nLeft != nRight:
    print >>sys.stderr, 'Error: left and right catchups do not agree'
    sys.exit (1)

if reads[1] != reads[2]:
    print >>sys.stderr, 'Error: left and right reads do not agree'
    sys.exit (1)

if writes[1] != writes[2]:
    print >>sys.stderr, 'Error: left and right writes do not agree'
    sys.exit (1)

if reads[1] != writes[1]:
    print >>sys.stderr, 'Error: left reads and writes do not agree'
    sys.exit (1)

if reads[2] != writes[2]:
    print >>sys.stderr, 'Error: right reads and writes do not agree'
    sys.exit (1)

sys.exit (0)
