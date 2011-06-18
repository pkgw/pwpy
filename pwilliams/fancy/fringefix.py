#! /usr/bin/env python

"""= fringefix.py - Scale visibility amplitudes to account for fringe rotation
& pkgw
: Calibration
+
 This task applies a fringe-rotation correction to UV data, writing
 the corrected data to a new dataset.

 The correction applied is intended to fix up data taken with an
 interferometer that has a long integration time and does not track
 fringe rotation. Over the course of an integration, the (ideal)
 visibility vector being observed will rotate around the complex plane
 at the fringe rate, reducing the observed amplitude from what it
 should be. The fringe rate is

  -omega_e * u * cos (decl)   [Thompson, Moran, & Swenson, sec 4.4]

 where omega_e is the rotation rate of the Earth in radians per
 second. Computation of the amount of decorrelation indicates that the
 observed amplitude decreases as a sinc (x), where x is the angle (in
 radians) traversed over the integration. Hence, this task multiplies
 the amplitude of each visibility record by

  1 / sinc (-omega_e * u * cos (decl) * inttime)

 Note that this task works on whole records, and not individual
 channels. A more sophisticated approach would be to compute the UVW
 coordinates of each channel and apply the correction on a
 channel-by-channel basis.

 This task should be used with care. It seems to overcorrect ATA-42
 FX64 data. The author believes that it is correct to use this task
 with observations of bright sources at phase center, but is unsure if
 it should also be used for crowded fields or other kinds of data.

< vis
 Multiple input files are supported in FRINGEFIX.PY.

@ out
 The name of the output dataset to create. The corrected data are
 written to this file.

@ maxscale
 A number specifying the maximum allowed correction factor. If the
 correction factor (the 1/sinc (x) quantity given above) is greater
 than maxscale, the record will be elided from the output
 dataset. Default value is 3.

< select

< line

< stokes

@ options
 Multiple options can be specified, separated by commas, and
 minimum-match is used.

 'nocal'   Do not apply antenna gain corrections.

 'nopol'   Do not apply polarization leakage corrections.

 'nopass'  Do not apply bandpass shape corrections.

--
"""

import sys
import miriad, mirtask
import mirtask.lowlevel as ll
from mirtask import uvdat, keys, util
import numpy as N

omega_e = 2. * N.pi / 86400 # Earth rot rate in rads per sec
deg2rad = N.pi / 180.

SVNID = '$Id$'
banner = util.printBannerSvn ('fringefix', 'correct for fringe rate amplitude loss', SVNID)

ks = keys.KeySpec ()
ks.keyword ('out', 'f', ' ')
ks.keyword ('maxscale', 'd', 3.)
ks.uvdat ('dsl3', True)
opts = ks.process ()

if opts.out == ' ':
    print >>sys.stderr, 'Error: must give an output filename'
    sys.exit (1)

# Multifile UV copying algorithm copied from uvcat.for.

dOut = miriad.VisData (opts.out).open ('c')
dOut.setPreambleType ('uvw', 'time', 'baseline')

first = True
curFile = None
saveNPol = 0
polsVaried = False

windowVars = ['ischan', 'nschan', 'nspect', 'restfreq',
              'sdf', 'sfreq', 'systemp', 'xtsys', 'ytsys']
nSeen = 0
nSupp = 0

for dIn, preamble, data, flags in uvdat.read ():
    anyChange = False
    nSeen += 1
    
    if dIn is not curFile:
        # Started reading a new file (or the first file)
        corrType, corrLen, corrUpd = dIn.probeVar ('corr')

        if corrType != 'r' and corrType != 'j' and corrType != 'c':
            raise Exception ('No channels to copy')

        if first:
            # This is NOT a close approximation to uvcat.for
            # We don't use an 'init' var since we assume dochan=True.
            dOut.setCorrelationType (corrType)
        
        dIn.initVarsAsInput (' ') # what does ' ' signify?

        uvt = dIn.makeVarTracker ()
        uvt.track (*windowVars)

        tup = dIn.probeVar ('npol')
        doPol = tup is not None and (tup[0] == 'i')
        nPol = 0
        doneNPol = False
        curFile = dIn
        anyChange = True
        
    if first:
        # If very first file, copy the history entry.
        dIn.copyHeader (dOut, 'history')
        first = False

    if nPol == 0:
        nPol = dIn.getNPol ()
        doneNPol = False

    if uvt.updated ():
        nAnts = dIn.getVarInt ('nants')

        tbl = {}
        
        dIn.probeVar ('nspect')
        nSpec = dIn.getVarInt ('nspect')
        tbl['nspect'] = ('i', nSpec)
        
        for v in ['nschan', 'ischan']:
            dIn.probeVar (v)
            tbl[v] = ('i', dIn.getVarInt (v, nSpec))

        for v in ['sdf', 'sfreq', 'restfreq']:
            dIn.probeVar (v)
            tbl[v] = ('d', dIn.getVarDouble (v, nSpec))

        for v in ['systemp', 'xtsys', 'ytsys', 'xyphase']:
            tup = dIn.probeVar (v)

            if tup is not None and tup[0] == 'r':
                tbl[v] = ('r', dIn.getVarFloat (v, tup[1]))

        for (name, (code, val)) in tbl.iteritems ():
            if code == 'i':
                dOut.writeVarInt (name, val)
            elif code == 'r':
                dOut.writeVarFloat (name, val)
            elif code == 'd':
                dOut.writeVarDouble (name, val)
            else:
                assert (False)

        anyChange = True

    if not flags.any (): continue # skip all-flagged records

    if not doneNPol:
        if nPol != saveNPol:
            dOut.writeVarInt ('npol', nPol)
            polsVaried = saveNPol != 0
            saveNPol = nPol
        doneNPol = True

    dIn.copyLineVars (dOut)

    # Hey! We actually have some data processing to do!

    pol = dIn.getPol ()

    #if i % 5000 == 0:
    #    print 'Orig UVW:', u, v, w
        
    # Calculate fringe rate. From Thompson, Moran, & Swenson sec. 4.4.
    # Need to convert u from nanoseconds to wavelengths.
    
    u = preamble[0] * dIn.getVarDouble ('sfreq', nSpec)
    dec = dIn.getVarDouble ('dec', 1) * deg2rad
    rate = -omega_e * u * N.cos (dec)

    # Apply correction. This is homegrown but I've heard people say that
    # a sinc is what you want. 
    
    inttime = dIn.getVarFirstFloat ('inttime', 10.0)
    corr = N.abs (1. / N.sinc (rate * inttime)) # / N.pi)) # XXX N.pi!!!!!!!!!11!!!

    #uvd = N.sqrt (u**2 + (preamble[1] * dIn.getVarDouble ('sfreq', nSpec))**2) * 1e-3
    #if uvd < 2.0 and uvd > 1.85 and u > 1800:
    #    print 'uvd, bl, corr, a0, u', uvd, mirtask.util.decodeBaseline (preamble[4]), \
    #          corr, abs (data[256]), u
        
    if corr > opts.maxscale:
        nSupp += 1
        continue

    data *= corr
    
    # Write corrected data.

    #if i % 5000 == 0:
    #    #print 'Inttime:', inttime
    #    print 'u', u
    #    print 'Writing UVWTB:', preamble[0], preamble[1], preamble[2], preamble[3], preamble[4]
        
    dOut.writeVarInt ('pol', pol)
    dOut.writeVarFloat ('ffscale', corr)
    dOut.write (preamble, data, flags)
    nPol -= 1

if not polsVaried:
    # wrhdi (dOut, saveNPol)
    pass

print 'Processed %d records' % nSeen
print 'Suppressed %d records (%.2g%%) requiring scale factor > %g' % (nSupp, 100.*nSupp/nSeen, opts.maxscale)

# All done. Write history entry and quit.

dOut.openHistory ()
dOut.writeHistory (banner)
dOut.logInvocation ('FRINGEFIX')
dOut.closeHistory ()
dOut.close ()

sys.exit (0)

