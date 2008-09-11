#! /usr/bin/python
#
# Broadband spectra observing script, going by frequency
# From bbs.py

from atactl import *
import os, time, sys, socket

# Some parameters that are unlikely to be tweaked.

me = 'bbsft'
obsDur = 60 # seconds
calFreq = 1430 # MHz
calPeriod = 1200 # how many seconds between attempts to cal

# Load config file and check that it sets our
# vital parameters

sys.path = ['.'] + sys.path
from bbsftcfg import *
cfgFile = sys.modules['bbsftcfg'].__file__
del sys.path[0]

if len (calSources) < 2:
    print >>sys.stderr, '"calSources" not set in config file', cfgFile
    sys.exit (1)

if len (sciSources) < 2:
    print >>sys.stderr, '"sciSources" not set in config file', cfgFile
    sys.exit (1)

if len (obsFreqs) < 1:
    print >>sys.stderr, '"obsFreqs" not set in config file', cfgFile
    sys.exit (1)
    
# Settings from the commandline

if len (sys.argv) != 3:
    print >>sys.stderr, 'Usage: %s [debug|real] stopHour' % sys.argv[0]
    print >>sys.stderr, 'E.g.: %s debug 3.0' % sys.argv[0]
    sys.exit (1)

if sys.argv[1] == 'real':
    reallyDoIt = True
elif sys.argv[1] == 'debug':
    reallyDoIt = False
else:
    print >>sys.stderr, 'First argument must be "debug" or "real"; got', sys.argv[1]
    sys.exit (1)
    
stopHour = float (sys.argv[2])

# Define state structure

class BBSState (State):
    vars = ['ifreq', 'isci', 'ical', 'lastCal', 'onCal']

    def init (self):
        self.ifreq = self.isci = self.ical = self.lastCal = 0
        self.onCal = True

    def map (self):
        self.freq = obsFreqs[self.ifreq]

        if self.onCal:
            self.src = calSources[self.ical]
        else:
            self.src = sciSources[self.isci]
        
        self.doCal = (time.time () - self.lastCal) > calPeriod

    def inc (self):
        # self.lastCal must be updated in the script loop.
        
        self.ifreq += 1

        if self.ifreq == len (obsFreqs):
            self.ifreq = 0

            if self.onCal:
                self.ical += 1
                if self.ical == len (calSources):
                    self.ical = 0
            else:
                self.isci += 1
                if self.isci == len (sciSources):
                    self.isci = 0
                    
            self.onCal = not self.onCal
        
# OK, let's go!

initScript (reallyDoIt, me + '.log')
stopTime, durHours = calcStopTime (stopHour)
S = BBSState ()

# Initial setup

initAntennas (allAnts)
setIntegTime ()
fringeKill ()

# Stuff

def mainLoop ():
    while not isTimeUp (stopTime, True):
        log ('State: %s %d %s %d' % (S.src, S.freq, S.doCal, S.lastCal))
        
        if S.doCal and S.onCal and S.ical == 0: # cal when we can avoid two consecutive slews
            if not isSourceUp (calSources[0]):
                log ('Would cal on %s, but not up; skipping.' % calSources[0])
            else:
                observe ('cal', calSources[0], calFreq, obsDur)
                S.lastCal = int (time.time ())

        if isTimeUp (stopTime, False): break

        # Now our main obs

        if not isSourceUp (S.src):
            log ('Would observe %s, but not up; skipping' % S.src)
        else:
            observe ('obs', S.src, S.freq, obsDur)
        
        if isTimeUp (stopTime, False): break
        S.next ()

retcode = 1

try:
    try:
        log ('Locking server and beginning observing script.')
        lockServer ('lo' + LO)
        mainLoop ()
        log ('Script ended normally (time up)')
        showAccounting ()
        retcode = 0
    except Exception, e:
        logAbort (e)
finally:
    for src in calSources:
        try: os.unlink (src + '.ephem')
        except: pass
    for src in sciSources:
        try: os.unlink (src + '.ephem')
        except: pass

sys.exit (retcode)
