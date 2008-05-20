#! /usr/bin/env python

"""Fringe Fix -- scale vis amplitudes by a correction factor
to compensate for our lack of fringe rotation."""

# I should write real documentation, but in the meantime ...
#
# This script scales the amplitude of each vis by
#
# 1 / sinc (-omega_e * u * cos (decl) * inttime)
#
# which, ideally, corrects for the loss in amplitude caused
# by the fact that we don't compensate for fringe rotation.
#
# You run this like a normal MIRIAD task:
#
# fringefix.py vis=input out=output maxscale=3 options=nocal,nopass,nopol
#
# "vis" and "out" should be self-explanatory.
#
# "maxscale" sets the maximum scale factor that we are allowed to
# apply: if data in a given vis would have its amplitude scaled by
# more than this number, the vis is flagged instead. (Presumably,
# a vis with a really low amplitude will have a correspondingly low
# SNR, and we don't want them to mess up our results.) The default
# is 7, which is probably too high.
#
# The nocal, nopass, and nopol options are the usual
# calibration-related ones.

import sys
import miriad, mirtask
import mirtask.lowlevel as ll
from mirtask import uvdat, keys
import numpy as N
from cgs import c

omega_e = 2. * N.pi / 86400 # Earth rot rate in rads per sec
deg2rad = N.pi / 180.

banner = 'FRINGEFIX: Correct for fringe rate amplitude loss'
print banner

keys.keyword ('out', 'f', ' ')
keys.keyword ('maxscale', 'd', 7.)
keys.doUvdat ('dsl3', True)
opts = keys.process ()

if opts.out == ' ':
    print >>sys.stderr, 'Error: must give an output filename'
    sys.exit (1)

# Multifile UV copying algorithm copied from uvcat.for.

dOut = miriad.VisData (opts.out).open ('w')
dOut.setPreambleType ('uvw', 'time', 'baseline')

first = True
curFile = None
saveNPol = 0
polsVaried = False

windowVars = ['ischan', 'nschan', 'nspect', 'restfreq',
              'sdf', 'sfreq', 'systemp', 'xtsys', 'ytsys']
nSeen = 0
nSupp = 0

for dIn, preamble, data, flags, nread in uvdat.readAll ():
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
        nPol = uvdat.getNPol ()
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

    data = data[0:nread]
    flags = flags[0:nread]
    pol = uvdat.getPol ()

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
    dOut.write (preamble, data, flags, nread)
        
    # I don't understand what this does ...
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

