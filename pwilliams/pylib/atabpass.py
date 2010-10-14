# Correct for the ATA digital filter bandpass

"""= atabpass - correct for the ATA digital filter bandpass
& pkgw
: uv Analysis
+
 The ATA has a digital filter with a fixed bandpass in its
 signal processing path. It has a characteristic sinusoidal
 shape across the band. ATABPASS rewrites an input dataset
 (or several input datasets), dividing out the effect of
 this filter to remove the ripple effect.

 Use a task like MFCAL to do a genuine bandpass solution.
 This task merely removes a fixed contribution to the
 bandpass, hopefully making MFCAL's job easier.

< vis
 ATABPASS supports multiple input data sets.

@ out
 The name of the output dataset to create. No default.

< select

< stokes

--
"""

import sys, numpy as N, miriad
from mirtask import keys, util, uvdat
from os.path import dirname, join

SVNID = '$Id$'


def getData ():
    fn = join (dirname (__file__), 'hhaa.dat')
    a = N.loadtxt (fn)
    assert a.size == 512

    # Mirror out the half-bandpass to the full
    # spectrum to make processing easier
    
    biga = N.empty (1024)
    biga[512:] = a

    for i in xrange (0, 512):
        biga[i] = biga[1023-i]

    # Normalize to RMS = 1

    biga /= N.sqrt ((biga**2).mean ())
    
    return biga


def task (args):
    banner = util.printBannerSvn ('atabpass', 'correct for ATA digital filter bandpass', SVNID)

    ks = keys.KeySpec ()
    ks.keyword ('out', 'f', ' ')
    ks.uvdat ('ds3', False)
    opts = ks.process (args)

    if opts.out == ' ':
        print >>sys.stderr, 'Error: must give an output filename'
        sys.exit (1)

    bpass = getData ()
    
    # Multifile UV copying algorithm copied from uvdat.for;
    # implementation copied from fxcal.py
    
    dOut = miriad.VisData (opts.out).open ('c')
    dOut.setPreambleType ('uvw', 'time', 'baseline')

    first = True
    curFile = None
    saveNPol = 0
    polsVaried = False
    
    windowVars = ['ischan', 'nschan', 'nspect', 'restfreq',
                  'sdf', 'sfreq', 'systemp', 'xtsys', 'ytsys']

    for dIn, preamble, data, flags in uvdat.read ():
        anyChange = False
    
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
            dOut.initVarsAsOutput (dIn, ' ')
            
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
            # We're on to a new set of baselines. Get the number
            # of pols in this next set and remind ourselves to
            # update the 'npol' variable if necessary.
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

        pol = uvdat.getPol ()

        if not doneNPol:
            # If necessary, write out a new value for the
            # 'npol' variable. If npol has changed, note
            # that so that we know not to write a
            # dataset-wide npol header variable.
        
            if nPol != saveNPol:
                dOut.writeVarInt ('npol', nPol)
                polsVaried = polsVaried or saveNPol != 0
                saveNPol = nPol
            doneNPol = True

        dIn.copyLineVars (dOut)

        # Hey! We actually have some data processing to do!

        data /= bpass

        # That was fast.
        
        dOut.writeVarInt ('pol', pol)
        dOut.write (preamble, data, flags, flags.size)
        
        # Count down the number of polarizations left for this baseline.
        # When we reach zero, we may reset the npol variable.
        nPol -= 1

    if not polsVaried:
        # Number of pols never varied, so it's valid to write out
        # a single 'npol' in the header of the entire dataset.
        dOut.writeHeaderInt ('npol', saveNPol)

    # All done. Write history entry and quit.

    dOut.openHistory ()
    dOut.writeHistory (banner)
    dOut.logInvocation ('ATABPASS')
    dOut.closeHistory ()
    dOut.close ()
    
    return 0

if __name__ == '__main__':
    sys.exit (task (sys.argv[1:]))
