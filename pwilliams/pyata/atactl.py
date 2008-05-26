"""HACKY Routines for controlling the ATA.

This works by executing the various ata* commands, which
is obviously highly suboptimal. But I want to be able to
write my observing scripts in a scripting language, not
Java. And I want to use a scripting language that can do
math (ie not shell) and that doesn't make me want to kill
myself (Perl). Python doesn't have a phenomenal infrastructure
for executing subprocesses, but it's good enough.

Jython would have been kind of nice to do all this in, but
it seems to be a dead project. Jruby has been recommended and
should be looked into.
"""

import subprocess, sys, os, time, atexit

noopMode = True
logFile = None
_bindir = '/opt/atasys/ata/run/'
_startTime = None

def initScript (doAnything, logname):
    global logFile, noopMode, _startTime

    noopMode = not doAnything

    if doAnything:
        print '>>> This script is actually going to run! You have 5 seconds to cancel <<<'
        try:
            time.sleep (5)
        except:
            print 'Canceled!'
            sys.exit (0)
        
        logFile = file (logname, 'a')

    _startTime = time.time ()

    if doAnything: mode = 'for-real'
    else: mode = 'debug'
    
    log ('Initialized script in %s mode' % mode)

def log (text):
    utc = time.gmtime ()
    stamp = time.strftime ('%Y-%m-%dT%H:%M:%SZ', utc)
    
    if logFile is not None:
        print >>logFile, '%s: %s' % (stamp, text)
    print '%s: %s' % (stamp, text)

def logAbort (exc):
    log ('Exception raised!')
    log ('Error: ' + str (exc))
    log ('Aborting after %f hours elapsed' % ((time.time () - _startTime) / 3600.0))

_accountInfo = {}

def account (desc, duration):
    if desc not in _accountInfo:
        _accountInfo[desc] = (1, duration)
    else:
        (n, time) = _accountInfo[desc]
        _accountInfo[desc] = (n + 1, time + duration)

def showAccounting ():
    import time
    totalTime = time.time () - _startTime
    accounted = 0.0

    if totalTime > 3600.:
        dur = '%.1f hours' % (totalTime / 3600.)
    elif totalTime > 60.:
        dur = '%.1f minutes' % (totalTime / 60.)
    else:
        dur = '%.1f seconds' % totalTime
    
    log ('Script finished; %s elapsed' % dur)
    log ('Summary of time spent (all in seconds):')
    
    info = _accountInfo.items ()
    info.sort (key = lambda x: x[1][1], reverse=True)

    for (desc, (n, time)) in info:
        accounted += time
        pct = 100.0 * time / totalTime 
        log ('  %4.1f%% : %8.1f (%4d * %8.2f) : %s' % (pct, time, n, time / n, desc))

    unacct = totalTime - accounted
    pct = 100.0 * unacct / totalTime
    log ('  %4.1f%% : %8.1f                   : unaccounted for' % (pct, unacct))

def runCommand (*args):
    if noopMode:
        log ('WOULD execute: %s' % (' '.join (args))) 
        return
    
    log ('executing: %s' % (' '.join (args))) 

    proc = subprocess.Popen (args, shell=False, close_fds=True,
                             stdin=file (os.devnull, 'r'),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for line in proc.stdout:
        line = line.strip ()
        log ('output: %s' % line)
    for line in proc.stderr:
        line = line.strip ()
        log ('stderr output: %s' % line)
    proc.wait ()

    if proc.returncode != 0:
        log ('process returned error code %d!' % proc.returncode)
        raise Exception ("Command failed")

# Script state save/restore in case the script gets interrupted
# and restarted

_stateFile = 'obs-state.txt'
class State (object):
    """Must define: field vars; methods init, map, inc."""
    
    vars = None
    
    def __init__ (self):
        self.init ()
        
        if os.path.exists (_stateFile) and not noopMode:
            log ('Loading script state from ' + _stateFile)
            self._load ()
        else:
            log ('Using blank script state.')
            
        self.map ()
    
    def next (self):
        self.inc ()
        self.map ()

        if noopMode: return
        
        f = file (_stateFile, 'w')
        
        for name in self.vars:
            val = getattr (self, name)
            print >>f, '%s %d' % (name, val)
    
    def _load (self):
        f = file (_stateFile, 'r')

        for l in f:
            name, val = l.strip ().split ()
            setattr (self, name, int (val))
            
# Locking servers

_lockInfo = set ()
_lockKey = None

def _releaseLocks ():
    for server in _lockInfo:
        runCommand ('/bin/sh', _bindir + 'ataunlockserver', server, _lockKey)

atexit.register (_releaseLocks)

def setLockKey (key):
    global _lockKey

    if _lockKey is not None: raise Exception ('Can only set lock key once!')
    _lockKey = key

_acctLock = 'locking and unlocking servers'

def lockServer (server):
    if server in _lockInfo: raise Exception ('Trying to re-lock server %s' % server)

    tStart = time.time ()
    runCommand ('/bin/sh', _bindir + 'atalockserver', server, _lockKey)
    _lockInfo.add (server)
    account (_acctLock, time.time () - tStart)

def unlockServer (server):
    if server not in _lockInfo: raise Exception ('Trying to unlock un-held server %s' % server)

    tStart = time.time ()
    runCommand ('/bin/sh', _bindir + 'ataunlockserver', server, _lockKey)
    _lockInfo.remove (server)
    account (_acctLock, time.time () - tStart)

# Misc

def isSourceUp (source, integTime, padTime=300):
    if noopMode:
        # FIXME: keep track of a synthetic LAST and guess based on RA
        # for a real simulation of observations.
        log ('[Skipping isSourceUp check, assuming yes]')
        return True

    from ataprobe import check
    (isUp, az, el, risesIn, setsIn) = check (source)

    if not isUp: return False

    # Sets too soon?
    if setsIn * 3600 < integTime + padTime: return False
    
    return True

def initAntennas (ants):
    antlist = ','.join (ants)
    log ('Initializing hardware for antennas: %s' % ', '.join (ants))
    tStart = time.time ()
    runCommand ('/bin/sh', _bindir + 'atasetpams', antlist)
    runCommand ('/bin/sh', _bindir + 'atalnaon', antlist)
    account ('initializing PAMs and LNAs', time.time () - tStart)

_acctPAM = 'setting PAM values'

def setAllPAMsToDefaults ():
    log ('Setting all PAMs to their defaults')
    tStart = time.time ()
    runCommand ('/bin/sh', _bindir + 'atasetpams', 'all')
    account (_acctPAM, time.time () - tStart)

def setPAM (ants, xval, yval):
    log ('Setting PAMs to [%.1f, %.1f] for antennas: %s' % (xval, yval, ', '.join (ants)))
    tStart = time.time ()
    runCommand ('/bin/sh', _bindir + 'atasetpams', ','.join (ants), str (xval), str (yval))
    account (_acctPAM, time.time () - tStart)
    
def setSkyFreq (lo, freqInMhz):
    log ('Setting sky frequency to %d MHz' % freqInMhz)
    unlockServer ('lo' + lo)
    tStart = time.time ()
    runCommand ('/bin/sh', _bindir + 'atasetskyfreq', str (lo), str (freqInMhz))
    account ('setting the sky frequency', time.time () - tStart)
    lockServer ('lo' + lo)

#_controlFiles = ['hookup8x1.dat', 'genswitch']
_controlFiles = ['hookup8x1.dat']

def initControlFiles ():
    homedir = os.environ['HOME']
    gendir = os.path.join (homedir, 'bin')
    
    for f in _controlFiles:
        if os.path.exists (f): continue

        print 'copy here', f
        log ('Copying over generic control file %s' % f)
        generic = os.path.join (gendir, f)
        runCommand ('cp', generic, f)

    log ('Reading in settings from control files')
    
    #f = file ('genswitch', 'r')
    #switches = f.read ().strip ()
    #f.close ()
    switches = 'unused'
    
    f = file ('hookup8x1.dat', 'r')
    corrAnts = {}
    corrPols = {}
    corrLOs = {}
    
    for l in f:
        l = l.strip ()
        if l[0] == '#': continue

        # split on both commas and whitespace.
        
        pieces = []
        spaces = [x for x in l.split () if x != '']
        
        for bit in spaces:
            pieces += [x for x in bit.split (',') if x != '']

        linetype = pieces[8]
        if linetype[0:3] != 'fx8': raise Exception ('format change?: "%s"' % linetype)
        corrid = linetype[3]

        if linetype[5:] == 'ant':
            corrAnts[corrid] = pieces[0:8] 
        elif linetype[5:] == 'pols':
            corrPols[corrid] = pieces[0:8] 
        elif linetype[5:] == 'LO':
            corrLOs[corrid] = pieces[0:8] 

    usedAnts = {}
    corrExact = {}
    allAnts = set ()

    for corr in 'abcdefgh':
        ants = corrAnts[corr]
        pols = corrPols[corr]
        los = corrLOs[corr]
        
        s = set (ants)
        if 'nc' in s: s.remove ('nc')
        usedAnts[corr] = s

        allAnts = allAnts.union (s)

        ex =','.join (['%s%s%s1' % tup for tup in zip (ants, pols, los)])
        corrExact[corr] = ex

    return switches, allAnts #, usedAnts, corrExact

def calcStopTime (stopHour):
    """Calculate the Unix time at which we should stop, if we were told
    to stop at the given (potentially fractional) hour of local time.

    Returns: (stopTime, durHours), where stopTime is the Unix time at
    which we stop, and durHours is the planned duration of the
    observation in hours.
    """
    
    from math import floor
    
    start = time.localtime (_startTime)
    stop = list (start)
    if stopHour < start[3]: # go on to next day?
        stop[2] += 1 # it's ok to have impossible days like sep 31

    stop[3] = int (floor (stopHour))
    stop[4] = int ((stopHour - stop[3]) * 60)
    stopTime = time.mktime (tuple (stop))

    assert (stopTime > _startTime)
    durHours = (stopTime - _startTime) / 3600.0
    log ('Observation planned to last %.1f hours' % durHours)
    return stopTime, durHours

_doneOne = False

def isTimeUp (stopTime, outermost):
    global _doneOne
    
    if noopMode and outermost:
        if _doneOne:
            log ('[Exiting in outermost time-up check because we\'re noop]')
            return True
        _doneOne = True
        return False

    return time.time () >= stopTime

# Ephemerides

def makeCatalogEphemOwned (owner, src, duration, outfile):
    cmd = "atacatalogephem --owner '%s' '%s' now +%fhours >%s" % \
          (owner, src, duration, outfile)

    if noopMode:
        log ('WOULD execute: %s' % cmd)
        log ('Creating outfile so cleanup code can be exercised')
        print >>file (outfile, 'w'), 'Fake ephemeris file.'
        return 'ra,dec'
    
    tStart = time.time ()
    log ('executing: %s' % cmd) 

    proc = subprocess.Popen (cmd, shell=True, close_fds=True,
                             stdin=file (os.devnull, 'r'),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for line in proc.stdout:
        line = line.strip ()
        log ('output: %s' % line)
    for line in proc.stderr:
        line = line.strip ()
        log ('stderr output: %s' % line)
    proc.wait ()

    if proc.returncode != 0:
        log ('process returned error code %d!' % proc.returncode)
        try:
            os.unlink (outfile)
        except:
            pass
        raise Exception ("Command failed")

    # Wrap ephem to avoid hitting limits.
    runCommand ('/bin/sh', _bindir + 'atawrapephem', outfile)

    # Extract the RA and Dec for passing to the FX64 dumper
    cmd = "atalistcatalog -l --owner '%s' --source '%s'" % (owner, src)
    log ('executing: %s' % cmd) 

    proc = subprocess.Popen (cmd, shell=True, close_fds=True,
                             stdin=file (os.devnull, 'r'),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = proc.communicate ()

    if proc.returncode != 0:
        log ('process returned error code %d!' % proc.returncode)
        try:
            os.unlink (outfile)
        except:
            pass
        raise Exception ("Command failed")

    a = stdout.split ()
    if len (a) != 5:
        raise Exception ("Unexpected output from atalistephem: " + stdout)
    radec = a[3] + ',' + a[4]

    account ('generating ephemerides', time.time () - tStart)
    return radec

def makeCatalogEphem (src, duration, outfile):
    """Create an ephemeris file for the specified source in the ATA catalog.

    The source is looked for under the 'bima' and 'pta' owners in the catalog.
    Duration is measured in hours. The ephemeris is written to the file
    outfile.
    """
    
    for owner in ['bima', 'pta', 'pkgw']:
        try:
            radec = makeCatalogEphemOwned (owner, src, duration, outfile)
            log ('Found catalog ephemeris for source "%s" under owner "%s"' % (src, owner))
            log ('  Saved data for next %f hours into %s' % (duration, outfile))
            return radec
        except:
            pass

    raise Exception ("Can't find source %s owned by anyone in the official catalog!" % src)

_ephemTable = {}
_radecTable = {}

def ensureEphem (src, f, obsDur):
    now = time.time ()
    expiry = _ephemTable.get (src)
    
    if expiry is not None and now + obsDur + 180 < expiry:
            return _radecTable[src]

    radec = makeCatalogEphem (src, 1.1, f)
    _ephemTable[src] = now + 3600
    _radecTable[src] = radec
    return radec

def trackEphemWait (ants, file):
    log ('Tracking antennas: %s' % ', '.join (ants))
    log (' ... to ephemeris in file: %s' % file)
    tStart = time.time ()
    # Sort the list of antennas to put 3f,3g,3h next to each other. This gets them
    # moving at the same time and hopefully reduces the likelihood of the collision
    # server getting angry at us.
    runCommand ('/bin/sh', _bindir + 'atatrackephem', '-w', ','.join (sorted (ants)), file)
    account ('tracking to sources', time.time () - tStart)

# Launching the FX64

integTime = 7.5
import math

def launchFX64 (src, freq, radec, duration, outbase):
    tStart = time.time ()
    ndumps = int (math.ceil (duration / integTime))
    
    log ('Launching FX64 obs: %s at %s MHz' % (src, freq))
    log ('      Output files: %s_{1,2}' % outbase)
    log ('  Embedding coords: ' + radec)
    log ('          Duration: %f (%d dumps)' % (duration, ndumps))

    args = ['/bin/sh', '/home/pkwill/obs/fx64.sh', src, str(freq), radec,
            str(ndumps), outbase]
    
    if noopMode:
        log ('WOULD execute: %s' % (' '.join (args))) 
    else:
        log ('executing: %s' % (' '.join (args))) 

        proc = subprocess.Popen (args, shell=False, close_fds=True,
                                 stdin=file (os.devnull, 'r'),
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        for l in proc.stdout:
            log ('FX64: ' + l[:-1])

        if proc.wait ():
            log ('FX64 returned nonzero! %d' % proc.returncode)
            raise Exception ('FX64 invocation failed.')
    
    account ('integrating for %d seconds' % duration, time.time () - tStart)
