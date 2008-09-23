#! /usr/bin/python
#
# Broadband spectra observing script, going by frequency

import sys, atactl, ataprobe
from atactl import *

SVNID = '$Id$'
me = 'bbsf'

# Observing script state. A bit cumbersome, but this lets us
# resume the script if we're canceled in the middle of an
# observation. The logic here controls ALL of the observations
# except for the script initialization.

class BBSState (State):
    vars = ['ifreq', 'isrc']

    def __init__ (self, freqs, sources, hookup, obsDur):
        self.freqs = freqs
        self.sources = sources
        self.hookup = hookup
        self.obsDur = obsDur
        self.ifreq = self.isrc = 0

    def next (self):
        self.ifreq += 1

        if self.ifreq == len (self.freqs):
            self.ifreq = 0

            self.isrc += 1
            if self.isrc == len (self.sources):
                self.isrc = 0
    
    def iteration (self, stopTime):
        src = self.sources[self.isrc]
        freq = self.freqs[self.ifreq]

        log ('State: %s %d' % (src, freq))
        
        if not isSourceUp (src, self.obsDur):
            log ('Would observe %s, but not up; skipping' % src)
        else:
            observe (self.hookup, me, src, freq, self.obsDur)

# Default values.

obsDur = 60 # seconds

# Load config file and check that it sets our
# vital parameters

sys.path = ['.'] + sys.path
from config import *
cfgFile = sys.modules['config'].__file__
del sys.path[0]

if len (sources) < 1:
    print >>sys.stderr, '"sources" not set in config file', cfgFile
    sys.exit (1)

if len (freqs) < 1:
    print >>sys.stderr, '"freqs" not set in config file', cfgFile
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

# Tweak the focus-setting and attemplifier-setting
# logic: use the same settings for all sky frequencies
# in the same GHz range. This saves time since
# setting attemplifiers and especially focusing are
# slow operations.

def roundFocus (s):
    if s % 1000 == 0: return s
    return s - (s % 1000) + 1000

atactl.roundFocusSetting = roundFocus

def attenKey (src, freq):
    return freq - (freq % 1000)

atactl.makeAttenKey = attenKey
        
# That was all prep. Now let's go!

initScript (reallyDoIt, me + '.log')
log (SVNID)
stopTime, durHours = calcStopTime (stopHour)
h = ataprobe.Hookup (instr)
state = BBSState (freqs, sources, h, obsDur)

# Initial hardware setup. setIntegTime takes a while
# but only happens once per invocation.

lockServer ('lo' + h.lo)
initAntennas (h.ants ())
setIntegTime ()
fringeKill ()

# Enter main loop and run until done.

state.runAndExit (stopTime)
