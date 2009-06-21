#! /usr/bin/python
"""bbsf - Broadband spectra observing script, going by frequency.

Usage: bbsf.py MODE INSTR1,INSTR2,... STOPHOUR

MODE is the mode to run the script in: "debug" or "real". No
other values are accepted. If "debug", the script does not actually
issue any array-control commands. If "real", the script does
use the array.

INSTR1,INSTR2... is a list of correlator instruments to use.

STOPHOUR is the hour to stop observing, a floating-point number
between 0 and 24.0. The script stops when the local time passes
the specified hour.

This script is mostly high-level logic defining the sequence of
observations used. All of the magic that actually controls the array
is in the "atactl" Python module, in mmm/pwilliams/pyata/atactl.py.
"""

import sys, atactl, ataprobe
from atactl import *

SVNID = '$Id$'
me = 'bbsf'

# Observing script state. A bit cumbersome, but this lets us
# resume the script if we're canceled in the middle of an
# observation. The logic here controls ALL of the observations
# except for the script initialization.

class BBSState (State):
    vars = ['ifreq', 'isrc', 'ilist']

    def __init__ (self, freqLists, sources, mhookup, obsDurs, dfObsDur):
        self.freqLists = freqLists
        self.sources = sources
        self.mhookup = mhookup
        self.obsDurs = obsDurs
        self.dfObsDur = dfObsDur
        self.ifreq = self.isrc = self.ilist = 0

        atactl.roundFocusSetting = self.roundFocus
        atactl.makeAttenKey = self.attenKey

    def next (self):
        self.ifreq += 1

        if self.ifreq < len (self.freqLists[self.ilist]): return

        self.ifreq = 0
        self.isrc += 1

        if self.isrc < len (self.sources): return

        self.isrc = 0
        self.ilist += 1

        if self.ilist < len (self.freqLists): return

        self.ilist = 0
    
    def iteration (self, stopTime):
        src = self.sources[self.isrc]
        freq = self.freqLists[self.ilist][self.ifreq]

        log ('State: %s %d' % (src, freq))
        
        if src in self.obsDurs:
            dur = self.obsDurs[src]
        else:
            dur = self.dfObsDur

        if not isSourceUp (src, dur):
            log ('Would observe %s, but not up; skipping' % src)
        else:
            observe2 (self.mhookup, me, src, freq, dur)

    # Tweak the focus-setting and attemplifier-setting
    # logic: use the same settings for all sky frequencies
    # in the same GHz range. This saves time since
    # setting attemplifiers and especially focusing are
    # slow operations.
            
    def roundFocus (self, s):
        maxFreq = 0

        for f in self.freqLists[self.ilist]:
            maxFreq = max (maxFreq, f)

        return maxFreq

    def attenKey (self, src, freq):
        return self.ilist
        
# Default values.

defaultObsDur = 60 # seconds
obsDurs = {}

# Load config file and check that it sets our
# vital parameters

sys.path = ['.'] + sys.path
from config import *
cfgFile = sys.modules['config'].__file__
del sys.path[0]

if len (sources) < 1:
    print >>sys.stderr, '"sources" not set in config file', cfgFile
    sys.exit (1)

if len (freqLists) < 1:
    print >>sys.stderr, '"freqLists" not set in config file', cfgFile
    sys.exit (1)

# Check that we have a UUID file before we do anything.

def checkUUID ():
    from os.path import exists

    if exists ('bbs.uuid'): return

    print >>sys.stderr, 'Error: no such file "bbs.uuid" in current directory.'
    sys.exit (1)

checkUUID ()

# Settings from the commandline

if len (sys.argv) != 4:
    print >>sys.stderr, 'Usage: %s [debug|real] instrs stopHour' % sys.argv[0]
    print >>sys.stderr, 'E.g.: %s debug fx64a:fxa,fx64c:fxa 3.0' % sys.argv[0]
    sys.exit (1)

reallyDoIt = parseMode (sys.argv[1])
mh = ataprobe.MultiHookup (sys.argv[2].split (','))
stopHour = float (sys.argv[3])

# That was all prep. Now let's go!

initScript (reallyDoIt, me + '.log')
log (SVNID)
stopTime, durHours = calcStopTime (stopHour)
mh.load ()
state = BBSState (freqLists, sources, mh, obsDurs, defaultObsDur)

# Initial hardware setup.

for h in mh.hookups.itervalues ():
    lockServer ('lo' + h.lo)
    initAntennas (h.ants ())
    checkIntegTime (h)
    fringeKill (h)

# Enter main loop and run until done.

state.runAndExit (stopTime)
