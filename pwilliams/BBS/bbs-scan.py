#! /usr/bin/env python
#
# Run this in the working directory for a broadband spectra
# observation run.
#
# Will scan the data files and collect metadata for entry
# into the observation database. The metadata are printed
# to stdout so we can work if PWD is unwriteable.

import sys, os, os.path
from miriad import VisData

# Version of this script

SVNID = '$Id$'
print 'scannerRev', SVNID.split ()[2]

# Find our position in the archive

def getArchiveDir ():
    cwd = os.getcwd ()
    parts = cwd.split (os.sep)
    for i in xrange (0, len (parts)):
        try:
            num = int (parts[i])
            if num > 2000 and num < 3000:
                return '/'.join (parts[i:])
        except: pass
    assert False, 'Can\'t determine archive directory from PWD!'

archDir = getArchiveDir ()
print 'archdir', archDir

# UUID

def getUUID ():
    return file ('bbs.uuid', 'r').readline ().strip ()

uuid = getUUID ()
print 'uuid', uuid

# Observing script info

def getScriptInfo (archDir):
    if os.path.exists ('bbsft.log'):
        scriptName = 'bbs-freqtest.py'
        log = 'bbsft.log'
        scriptRev = 0
    elif os.path.exists ('bbs.log'):
        scriptName = 'bbs.py'
        log = 'bbs.log'
        scriptRev = 0
    elif os.path.exists ('bbsf.log'):
        scriptName = 'bbsf.py'
        log = 'bbsf.log'
    else:
        assert False, 'Can\'t determine script type from logfile existence!'

    for l in file (log, 'r'):
        a = l.split ()
        if a[1] == '$Id:' and a[2] == scriptName:
            scriptRev = int (a[3])
        elif a[3] == 'fxconf.rb':
            instrument = a[5][1:-1]
            break
        elif a[1] == 'Initializing':
            break

    # Fix up oldest data
    if scriptRev == 0:
        if archDir.startswith ('2008/04'):
            scriptRev = 10
            instrument = 'fx64a:fxa'
        elif archDir == '2008/09/12/williams/bbsft1':
            scriptRev = 125
        elif archDir.startswith ('2008/09/12/williams/bbs-'):
            scriptRev = 129
        elif archDir.startswith ('2008/09/13/williams/bbs-'):
            scriptRev = 136
        elif archDir == '2008/09/14/williams/check-249':
            scriptRev = 136

    assert scriptRev != 0, 'Unable to determine observing script version.'
    
    return scriptName, scriptRev, instrument

scriptName, scriptRev, instrument = getScriptInfo (archDir)

print 'scriptName', scriptName
print 'scriptRev', scriptRev
print 'instrument', instrument

# Scans, catcher type

cutoff = 1. / 60 / 24 # cutoff to create a new entry in single file: 1 min

def getScans (archDir, scriptName, scriptRev):
    scans = []
    catcherType = None
    catcherRev = 0

    if scriptName == 'bbs-freqtest.py':
        if scriptRev < 124:
            catcherType = 'fxmir'
            prefix = 'bbsft'
        else:
            catcherType = 'atafx+fxmir'
            prefix = 'bbsft'
    elif scriptName == 'bbs.py':
        catcherType = 'fxmir'
        prefix = 'bbs'
    elif scriptName == 'bbsf.py':
        catcherType = 'atafx+fxmir'
        prefix = 'bbsf'
    else:
        assert False, 'Unhandled scriptName for catcherType determination.'

    if catcherType == 'atafx' or catcherType == 'atafx+fxmir':
        if archDir.startswith ('2008/09/1'):
            catcherRev = 1273
            
    for v in os.listdir ('.'):
        if not v.startswith (prefix): continue
        if catcherType == 'fxmir' and v.endswith ('_2'): continue
        if not os.path.exists (os.path.join (v, 'visdata')): continue

        if catcherType == 'fxmir' and catcherRev == 0:
            l = file (os.path.join (v, 'history'), 'r').readline ()
            catcherRev = int (l.split ()[4])

        vis = VisData (v)
        tSt = 0.
        tPrev = 0.
        #print '#', v, '...'
        
        for inp, preamble, data, flags, nread in vis.readLowlevel (False):
            t = preamble[3]

            if abs (tPrev - t) > cutoff:
                if tSt > 0:
                    scans.append ((tSt, tPrev, src, freq, v))

                freq = inp.getVarDouble ('freq')
                src = inp.getVarString ('source')
                if src.endswith ('.ephem'):
                    src = src[0:-6]
                elif src.endswith ('.nsephem'):
                    src = src[0:-8]
                # account for when the integration actually started
                inttime = inp.getVarFloat ('inttime')
                tSt = t - inttime / 86400.

            tPrev = t

        if tSt > 0:
            scans.append ((tSt, tPrev, src, freq, v))
            
    assert catcherRev != 0, 'Unable to determine datacatcher revision!'

    scans.sort (key = lambda x: x[0])

    # Consistency check

    prevTEnd = 0

    for tSt, tEnd, src, freq, vis in scans:
        if tSt < prevTEnd:
            #print scans
            assert False, 'sequencing! %f %f %s %4f %s' % (tSt, tEnd, src,
                                                           freq, vis)
        prevTEnd = tEnd

    return catcherType, catcherRev, scans

catcherType, catcherRev, scans = getScans (archDir, scriptName, scriptRev)

print 'catcherType', catcherType
print 'catcherRev', catcherRev
print 'startJD', scans[0][0]
print 'endJD', scans[-1][1]

print 'scans'
for tSt, tEnd, src, freq, v in scans:
    dur = int ((tEnd - tSt) * 86400)
    freq = int (freq * 1000)
    print tSt, dur, src, freq, v
