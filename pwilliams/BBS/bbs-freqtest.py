#! /usr/bin/python
#
# Broadband spectra observing script, going by frequency
# From bbs.py

import atactl, ataprobe
from atactl import *
import os, time, sys

# Some parameters that are unlikely to be tweaked.

me = 'bbsft'
obsDur = 60 # seconds

# Load config file and check that it sets our
# vital parameters

sys.path = ['.'] + sys.path
from bbsftcfg import *
cfgFile = sys.modules['bbsftcfg'].__file__
del sys.path[0]

if len (sciSources) < 1:
    print >>sys.stderr, '"sciSources" not set in config file', cfgFile
    sys.exit (1)

if len (obsFreqs) < 1:
    print >>sys.stderr, '"obsFreqs" not set in config file', cfgFile
    sys.exit (1)
    
# Settings from the commandline

if len (sys.argv) != 4:
    print >>sys.stderr, 'Usage: %s [debug|real] instrument stopHour' % sys.argv[0]
    print >>sys.stderr, 'E.g.: %s debug default 3.0' % sys.argv[0]
    sys.exit (1)

if sys.argv[1] == 'real':
    reallyDoIt = True
elif sys.argv[1] == 'debug':
    reallyDoIt = False
else:
    print >>sys.stderr, 'First argument must be "debug" or "real"; got', sys.argv[1]
    sys.exit (1)

instr = sys.argv[2]
if instr == 'default': instr = None

stopHour = float (sys.argv[3])

# Define state structure

class BBSState (State):
    vars = ['ifreq', 'isci']

    def init (self):
        self.ifreq = self.isci = 0

    def map (self):
        self.freq = obsFreqs[self.ifreq]
        self.src = sciSources[self.isci]

    def inc (self):
        self.ifreq += 1

        if self.ifreq == len (obsFreqs):
            self.ifreq = 0

            self.isci += 1
            if self.isci == len (sciSources):
                self.isci = 0
        
# OK, let's go!

initScript (reallyDoIt, me + '.log')
stopTime, durHours = calcStopTime (stopHour)
S = BBSState ()

# Initial setup

h = ataprobe.Hookup (instr)
initAntennas (h.ants ())
setIntegTime ()
fringeKill ()

def roundFocus (s):
    return s - (s % 1000)

atactl.roundFocusSetting = roundFocus

def attenKey (src, freq):
    return freq - (freq % 1000)

atactl.makeAttenKey = attenKey

# Stuff

def mainLoop ():
    while not isTimeUp (stopTime, True):
        log ('State: %s %d' % (S.src, S.freq))
        
        # Now our main obs

        if not isSourceUp (S.src, obsDur):
            log ('Would observe %s, but not up; skipping' % S.src)
        else:
            observe (me, h, 'obs', S.src, S.freq, obsDur)
        
        if isTimeUp (stopTime, False): break
        S.next ()

retcode = 1

try:
    try:
        log ('Locking server and beginning observing script.')
        lockServer ('lo' + h.lo)
        mainLoop ()
        log ('Script ended normally (time up)')
        showAccounting ()
        retcode = 0
    except Exception, e:
        logAbort (e)
finally:
    for src in sciSources:
        try: os.unlink (src + '.nsephem')
        except: pass
        try: os.unlink (src + '.msephem')
        except: pass

sys.exit (retcode)
