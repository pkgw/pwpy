#! /usr/bin/env python2.5
"""= ataglue.py - Merge together two ATA half-datasets, accounting for single-item errors.
& pkgw
: Tools
+

 The ATAGLUE task merges together two 512-channel ATA FX64
 half-datasets, writing a single 1024-channel output dataset
 containing the combined data.

 This task performs a similar function to the task UVGLUE, but that
 task fails with ATA data since sometimes the two half-datasets start
 at different clock ticks due to the way in which the ATA FX64
 correlator is currently run. One can get records in which the
 timestamps look like this:

   H1 H2
   -----
   T0 T1
   T1 T2
   T2 T3
   T3 T4

 In this case, ATAGLUE will write out records that look like:

   T0   Last 512 channels flagged
   T1
   T2
   T3
   T4   First 512 channels flagged

 ATAGLUE will print information about the out-of-sync records that
 it encounters.

 The timestamps on the two datasets are derived from the system clocks
 of the two X hosts that the data catcher software runs on. These clocks
 are normally synchronized to the HCRO NTP server and should agree to
 within a few milliseconds. However, the clocks can occasionally get
 out of sync -- typically this happens after a power incident. In that
 case, timestamps on the two datasets that should agree (T1 on H1 and T1
 on H2, e.g.) will differ nontrivially. The "tol" keyword lets you specify
 the timestamp disagreement tolerance: timestamps differing by less than
 TOL are considered identical. The default value is 0.1 ms. (See
 the documentation for the keyword below.) You can increase this value
 if ATAGLUE fails to process your datasets. When ATAGLUE performs a
 "catchup", it prints the difference between the two timestamps. If
 this number is any smaller than your integration time (typically 7.5
 s), you probably need to increase "tol". Note, however, that the
 integration windows of the two halves are out of phase in this
 situation. It is up to you to decide whether it is appropriate to
 glue together your datasets with a large value of "tol".
 
 ATAGLUE is fairly strict about its inputs and tries to ensure that
 it will never create bad datasets. Running ATAGLUE on raw ATA data
 should always work if it is valid to do so; running it on somewhat-
 processed data is not advised.

 FIXME: The left and right halves of glued ATA datasets have
 slightly-different UVW coordinates. These coordinates should be
 relative to the sky frequency and hence should agree between the two
 datasets. This may indicate a bug in the current datacatcher. The
 coordinates from the half-1 dataset are used in the merged dataset.
 
@ vis
 Should specify exactly two input sets, with the first being the
 lower-frequency set (fx64a-SRC-FREQ_1) and the second being the
 higher-frequency one (fx64a-SRC-FREQ_2).

@ out
 The name of the glued dataset to create.

@ tol
 A floating-point number, giving the tolerance to which two timestamps
 must agree to be considered identical, as measured in
 seconds. Defaults to 0.1 ms. You may wish to set this to a higher
 value if the system clocks on the two X hosts were not sufficiently
 synchronized. See the discussion above.
 
@ options

 Task enrichment options. Minimum match of names is used.
 
 'flagdc'  Flag the DC channel in all output records.
 
 'badc1'   Flag channels 513 - 769 of antpols 1X, 16X, 19X, 23X,
           and 37X. In some array hookups, these were the antpols
           and channels that were affected by bad C board hardware.
           If these corrupted channels are not flagged, their very
           high amplitudes can corrupt the rest of the (good) data in
           their associated records due to quantization in the Miriad
           data format. You should check that the above-named records
           are in fact affected by bad-C-board data before using this
           flag. (The C board was fixed on May 1, 2008.)

--
"""

import sys, numpy as N
from miriad import *
from mirtask import keys, util

# Some constants

specVars = ['ischan', 'nschan', 'nspect', 'restfreq',
            'sdf', 'sfreq']
AF_NEITHER, AF_LEFT, AF_RIGHT, AF_BOTH = range (0, 4)
badCAnts = set ((1, 16, 19, 23, 37))

SVNID = '$Id$'

# Keyword handling

banner = util.printBannerSvn ('ataglue', 'glue together two 512-channel ATA datasets', SVNID)

keys.keyword ('out', 'f', ' ')
keys.keyword ('vis', 'f', None, 2)
keys.keyword ('tol', 'd', 1e-4)
keys.option ('badc1', 'flagdc')
opts = keys.process ()

if opts.out == ' ':
    print >>sys.stderr, 'Error: must give output filename.'
    sys.exit (1)

if len (opts.vis) != 2:
    print >>sys.stderr, 'Error: must give exactly two input datasets'
    sys.exit (1)

if opts.badc1:
    print '**** MASKING BAD-C DATA! Read the documentation before using this option! ****'

if opts.flagdc:
    print 'Automatically flagging and zeroing DC channel.'

TOL = opts.tol / 86400.
print 'Timestamp tolerance: %g s' % opts.tol

# Setup.

dOut = VisData (opts.out).open ('c')
dOut.setPreambleType ('uvw', 'time', 'baseline')

in1 = VisData (opts.vis[0]).open ('rw')
in1.setPreambleType ('uvw', 'time', 'baseline')
in2 = VisData (opts.vis[1]).open ('rw')
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
    pol = src.getVarInt ('pol')
    dOut.writeVarInt ('pol', pol)
    dOut.writeVarInt ('npol', src.getVarInt ('npol'))
    dOut.writeVarInt ('nspect', 1)
    dOut.writeVarInt ('nschan', 1024)        
    dOut.writeVarInt ('ischan', 1)
    dOut.writeVarDouble ('sfreq', sfreq)
    dOut.writeVarDouble ('sdf', sdf)
    dOut.writeVarDouble ('restfreq', restfreq)

    if opts.flagdc:
        mFlags[512] = 0
        mData[512] = 0.0

    if opts.badc1 and pol == util.POL_XX:
        bl = util.decodeBaseline (pream[4])
        if bl[0] in badCAnts or bl[1] in badCAnts:
            mFlags[512:768] = 0
            mData[512:768] = 0
    
    dOut.write (pream, mData, mFlags, 1024)

def aligned (first, t1, t2):
    while abs (t1 - t2) < TOL:
        # No important variables changed?
        if not first and sanity1.updated () and getConfig (in1) != config1:
            print >>sys.stderr, 'Error: correlator configuration changed in input 1!'
            sys.exit (1)
                
        if not first and sanity2.updated () and getConfig (in2) != config2:
            print >>sys.stderr, 'Error: correlator configuration changed in input 2!'
            sys.exit (1)

        # Preambles agree?
        if abs (pream1[3] - pream2[3]) > TOL or pream1[4] != pream2[4]:
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
    
    while abs (t - ta) < TOL:
        # No important variables changed?
        if not first and sanitya.updated () and getConfig (ahead) != configa:
            print >>sys.stderr, 'Error: correlator configuration changed in ahead input!'
            sys.exit (1)
                
        if leftIsAhead: mFlags[512:].fill (0)
        else: mFlags[:512].fill (0)

        #if expectFinish: print 'Writing half-record'
        writes[akey] += 1
        write (ahead, preama)

        if leftIsAhead:
            na = ahead.lowlevelRead (preama, mData[:512], mFlags[:512], 512)
        else:
            na = ahead.lowlevelRead (preama, mData[512:], mFlags[512:], 512)

        #if expectFinish: print 'Read half-record, got', na
        
        if na == 0:
            if expectFinish:
                print 'Expected to finish and did'
                return True
            print >>sys.stderr, 'Error: Unexpected EOF in ahead dataset'
            sys.exit (1)
        elif na != 512:
            print >>sys.stderr, 'Error: Read error from ahead dataset. (%d)' % na
            sys.exit (1)
        else:
            reads[akey] += 1

        t = preama[3]
        #if expectFinish: print 'New time', util.jdToFull (t), '; reference', util.jdToFull (ta)

    if expectFinish:
        print >>sys.stderr, 'Error: should have finished but time changed instead!'
        sys.exit (1)
    
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
    print '%s %s:' % (util.jdToFull (t1), util.jdToFull (t2)),
    
    if abs (t1 - t2) < TOL:
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
            catchup (False, True, first, 0, pream2[3])
            break
        elif finishState == AF_RIGHT:
            # Will exit if the left dataset doesn't finish
            nLeft += 1
            print 'Right finished, catching up left'
            catchup (True, True, first, pream1[3], 0)
            break
    elif t1 < t2:
        print 'need to catch up left: T1 %f, T2 %f' % (t1, t2)
        print 'Timestamps differ by %g seconds' % ((t2 - t1) * 86400)
        nLeft += 1
        catchup (True, False, first, t1, t2)
    else:
        print 'need to catch up right: T1 %f, T2 %f' % (t1, t2)
        print 'Timestamps differ by %g seconds' % ((t1 - t2) * 86400)
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
