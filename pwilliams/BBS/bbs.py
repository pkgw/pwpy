#! /usr/bin/python
#
# Broadband spectra observing script.
# Derived from bbs_bysrc.py by way of bbsaas.py

from atactl import *
import os, time, sys, socket

# Some parameters that are unlikely to be tweaked.

me = 'bbs'
# could munge in username: import pwd; uname = pwd.getpwuid (os.getuid ())[0]
lockid = '-'.join ([me, socket.gethostname (), 'pid%d' % os.getpid ()])
integTime = 60 # seconds
calFreq = 1430 # MHz
calPeriod = 1200 # how many seconds between attempts to cal

# Load config file and check that it sets our
# vital parameters

sys.path = ['.'] + sys.path
from bbscfg import *
cfgFile = sys.modules['bbscfg'].__file__
del sys.path[0]

if len (sources) < 2:
    print >>sys.stderr, '"sources" not set in config file', cfgFile
    sys.exit (1)

if len (obsFreqs) < 1:
    print >>sys.stderr, '"obsFreqs" not set in config file', cfgFile
    sys.exit (1)
    
# Settings from the commandline

if len (sys.argv) != 4:
    print >>sys.stderr, 'Usage: %s [debug|real] LO stopHour' % sys.argv[0]
    print >>sys.stderr, 'E.g.: %s debug b 3.0' % sys.argv[0]
    sys.exit (1)

if sys.argv[1] == 'real':
    reallyDoIt = True
elif sys.argv[1] == 'debug':
    reallyDoIt = False
else:
    print >>sys.stderr, 'First argument must be "debug" or "real"; got', sys.argv[1]
    sys.exit (1)
    
LO = sys.argv[2]
stopHour = float (sys.argv[3])

# Define state structure

class BBSState (State):
    vars = ['ifreq', 'isrc', 'lastCal']

    def init (self):
        self.ifreq = self.isrc = self.lastCal = 0

    def map (self):
        self.freq = obsFreqs[self.ifreq]
        self.src = sources[self.isrc]
        self.doCal = (time.time () - self.lastCal) > calPeriod

    def inc (self):
        # self.lastCal must be updated in the script loop.
        self.isrc += 1

        if self.isrc == len (sources):
            self.isrc = 0
            self.ifreq += 1

            if self.ifreq == len (obsFreqs):
                self.ifreq = 0
        
# OK, let's go!

initScript (reallyDoIt, me + '.log')
stopTime, durHours = calcStopTime (stopHour)
S = BBSState ()

# Copy over control files and set up antenna hardware.

#switches, allAnts, usedAnts, corrExact = initControlFiles ()
switches, allAnts = initControlFiles ()
initAntennas (allAnts)

# Stuff

_lastFreq = 0

def observe (kind, src, freq, integTime):
    global _lastFreq
    
    if _lastFreq != freq:
        setSkyFreq (LO, freq)
        _lastFreq = freq

    f = src + '.ephem'
    radec = ensureEphem (src, f, integTime)
    trackEphemWait (allAnts, f)

    log ('Beginning %s observations (%s, %d MHz)' % (kind, src, freq))
    outBase = '-'.join ([me, kind, src, '%04d' % freq])
    launchFX64 (src, freq, radec, integTime, outBase)

def mainLoop ():
    while not isTimeUp (stopTime, True):
        log ('State: %s %d %s %d' % (S.src, S.freq, S.doCal, S.lastCal))
        
        if S.doCal and S.isrc == 0: # cal when we can avoid two consecutive trackephems
            if not isSourceUp (sources[0], integTime):
                log ('Would cal on %s, but not up; skipping.' % sources[0])
            else:
                observe ('cal', sources[0], calFreq, integTime)
                S.lastCal = int (time.time ())

        if isTimeUp (stopTime, False): break

        # Now science obs on all sources.

        if not isSourceUp (S.src, integTime):
            log ('Would observe %s, but not up; skipping' % S.src)
        else:
            observe ('obs', S.src, S.freq, integTime)
        
        if isTimeUp (stopTime, False): break
        S.next ()

retcode = 1

try:
    try:
        log ('Locking server and beginning observing script.')
        setLockKey (lockid)
        lockServer ('lo' + LO)
        mainLoop ()
        log ('Script ended normally (time up)')
        showAccounting ()
        retcode = 0
    except Exception, e:
        logAbort (e)
finally:
    for src in sources:
        try: os.unlink (src + '.ephem')
        except: pass

sys.exit (retcode)
