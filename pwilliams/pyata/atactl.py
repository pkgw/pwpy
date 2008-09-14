"""Routines for controlling the ATA.

This module provides a framework for writing ATA observing
scripts. Some of the nice higher-level features that it provides are:

 - Comprehensive logging of all actions
 - Accounting of how observing time is spent
 - Saving of script state and resuming in-place if the script
   crashes or is killed.

It also implements the usual elements of an observing script:

 - Stopping at a given cutoff time
 - Checking for source visibility
 - Generating ephemeris files
 - Setting the sky frequency
 - Steering antennas
 - Taking data
 - Controlling antenna focus
 - Controlling the fringe rotation
 - Controlling the attemplifiers

In most cases, these all come together in one function:

   observe (hookup, outBase, src, freq, integTimeSeconds)

where the arguments are

           hookup - A structure holding information about the 
                    correlator
          outBase - A prefix for the names of the data files 
                    that will be generated
              src - The name of the source to observe
             freq - The observing frequency in MHz
 integTimeSeconds - The integration time in seconds

observe() will set the focus, steer the antennas (generating an
ephemeris if necessary), tune the LOs (if necessary), set the
attemplifiers (if necessary), start the fringe rotator, run the
datacatcher, and stop the fringe rotaor.

This module controls and interrogates that ATA by executing the ata*
commands, which isn't ideal, since the ATA can be controlled natively
in Java. But it's nice to be able to write scripts in a scripting
language. Two options to pursue are:

 - Ruby, which has an active JRuby project to bridge Ruby and Java
 - Groovy, a scripting language that targets the JVM.
"""

import subprocess, sys, os, time, atexit

SVNID = '$Id$'

noopMode = True
logFile = None
_bindir = '/opt/atasys/ata/run/'
_rubydir = '/home/obs/ruby/bin/'
_obsbindir = '/home/obs/bin/'
_startTime = None

def initScript (doAnything, logname):
    global logFile, noopMode, _startTime
    import ataprobe
    
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
    log (ataprobe.SVNID)
    log (SVNID)
    
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

import ataprobe

def _logProbeCommand (cmd):
    log ('running (probe): ' + cmd)
    
ataprobe.runLogger = _logProbeCommand

# Time accounting.

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

def _getLockKey ():
    from socket import gethostname
    from os import getpid, getuid
    from os.path import basename
    from sys import argv
    from pwd import getpwuid

    script = basename (argv[0])
    user = getpwuid (os.getuid ())[0]
    
    return '-'.join (['%s@%s' % (user, gethostname ()), script, 'pid%d' % getpid ()])

_lockKey = _getLockKey ()

def _releaseLocks ():
    for server in _lockInfo:
        runCommand ('/bin/sh', _bindir + 'ataunlockserver', server, _lockKey)

atexit.register (_releaseLocks)

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
    log ('@@ Initializing PAMs and LNAs for antennas: %s' % ','.join (ants))
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
    log ('Setting PAMs to [%.1f, %.1f] for antennas: %s' % (xval, yval, ','.join (ants)))
    tStart = time.time ()
    runCommand ('/bin/sh', _bindir + 'atasetpams', ','.join (ants), str (xval), str (yval))
    account (_acctPAM, time.time () - tStart)
    
def setSkyFreq (lo, freqInMhz):
    log ('@@ Setting sky frequency to %d MHz' % freqInMhz)
    unlockServer ('lo' + lo)
    tStart = time.time ()
    runCommand ('/bin/sh', _bindir + 'atasetskyfreq', str (lo), str (freqInMhz))
    account ('setting the sky frequency', time.time () - tStart)
    lockServer ('lo' + lo)

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

def _makeCatalogEphemOwned (owner, src, durHours, start, outfile, args):
    cmd = "atacatalogephem --owner '%s' '%s' %s +%fhours %s >%s" % \
          (owner, src, start, durHours, args, outfile)

    if noopMode:
        log ('WOULD execute: %s' % cmd)
        log ('Creating outfile so cleanup code can be exercised')
        print >>file (outfile, 'w'), 'Fake ephemeris file.'
        return 'ra,dec'
    
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

def makeCatalogEphemsOwned (owner, src, durHours, outbase):
    tStart = time.time ()

    _makeCatalogEphemOwned (owner, src, durHours, 'now', outbase +
                            '.nsephem', '')
    t = time.gmtime ()
    stUTC = time.strftime ('%Y-%m-%dT%H:%M:00.000Z', time.gmtime ())
    _makeCatalogEphemOwned (owner, src, durHours, stUTC,
                            outbase + '.msephem',
                            '--utcms --interval 10')
    
    # Extract the RA and Dec for passing to the FX64 dumper
    cmd = "atalistcatalog -l --owner '%s' --source '%s'" % (owner, src)
    log ('executing: %s' % cmd) 

    proc = subprocess.Popen (cmd, shell=True, close_fds=True,
                             stdin=file (os.devnull, 'r'),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = proc.communicate ()

    if proc.returncode != 0:
        log ('process returned error code %d!' % proc.returncode)
        raise Exception ("Command failed")

    a = stdout.split ()
    if len (a) != 5:
        raise Exception ("Unexpected output from atalistephem: " + stdout)
    radec = a[3] + ',' + a[4]

    account ('generating ephemerides', time.time () - tStart)
    return radec

def makeCatalogEphem (src, durHours, outbase):
    """Create an ephemeris file for the specified source in the ATA catalog.

    The source is looked for under the 'bima' and 'pta' owners in the catalog.
    Duration is measured in hours. The ephemeris is written to files named
    outbase.{ns,ms}ephem.
    """
    
    for owner in ['bima', 'pta', 'pkgw']:
        try:
            radec = makeCatalogEphemsOwned (owner, src, durHours, outbase)
            log ('Found catalog ephemeris for source "%s" under owner "%s"' % (src, owner))
            log ('  Saved data for next %f hours into %s.*ephem' % (durHours, outbase))
            return radec
        except:
            pass

    raise Exception ("Can't find source %s owned by anyone in the official catalog!" % src)

_ephemTable = {}
_radecTable = {}

def ensureEphem (src, ebase, obsDurSeconds):
    now = time.time ()
    expiry = _ephemTable.get (src)
    
    if expiry is not None and now + obsDurSeconds + 180 < expiry:
            return _radecTable[src]

    radec = makeCatalogEphem (src, 1.1, ebase)
    _ephemTable[src] = now + 3600
    _radecTable[src] = radec
    return radec

def trackEphem (ants, ebase, wait):
    f = ebase + '.nsephem'
    log ('@@ Tracking antennas: %s' % ','.join (ants))
    log (' ... to ephemeris in file: %s' % f)
    tStart = time.time ()
    # Sort the list of antennas to put 3f,3g,3h next to each other. This gets them
    # moving at the same time and hopefully reduces the likelihood of the collision
    # server getting angry at us.
    args = ['/bin/sh', _bindir + 'atatrackephem']
    if wait: args.append ('-w')
    args += [','.join (sorted (ants)), f]
    runCommand (*args)
    account ('tracking to sources', time.time () - tStart)

# Launching the data catcher

defaultIntegTime = 10.0 # in s
_integTime = None
import math

def setIntegTime (itime=None):
    global _integTime
    
    if itime is None: itime = defaultIntegTime

    tStart = time.time ()
    runCommand ('/bin/csh', _obsbindir + 'setint64.csh', str (itime))
    _integTime = itime
    account ('setting integration time', time.time () - tStart)

def launchCatcher (hookup, src, freq, radec, durationSeconds, outbase, ebase):
    assert _integTime is not None
    
    tStart = time.time ()
    ndumps = int (math.ceil (durationSeconds / _integTime))
    nsephem = ebase + '.nsephem'
    
    log ('@@ Launching data catcher: %s at %s MHz on %s' % (src, freq, hookup.instr))
    log ('        atafx output base: %s' % outbase)
    log ('         Embedding coords: ' + radec)
    log ('   Ephemeris file (in ns): ' + nsephem)
    log ('                 Duration: %f s (%d dumps)' % (durationSeconds, ndumps))

    mydir = os.path.dirname (__file__)
    script = os.path.join (mydir, 'fxlaunch.sh')
    args = ['/bin/sh', script, src, str(freq), radec, str (ndumps),
            outbase, ','.join (hookup.antpols ()), hookup.lo, nsephem,
            str (durationSeconds)]
    
    if noopMode:
        log ('WOULD execute: %s' % (' '.join (args))) 
    else:
        log ('executing: %s' % (' '.join (args))) 

        proc = subprocess.Popen (args, shell=False, close_fds=True,
                                 stdin=file (os.devnull, 'r'),
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        for l in proc.stdout:
            log ('Catcher: ' + l[:-1])

        if proc.wait ():
            log ('Catcher returned nonzero! %d' % proc.returncode)
            raise Exception ('Catcher invocation failed.')
    
    account ('integrating for %d seconds' % durationSeconds, time.time () - tStart)

# Focus control

def _setFocus (ants, settingInMHz, calMode):
    antstr = ','.join (sorted (ants))
    log ('@@ Setting focus of %f for antennas: %s' % (settingInMHz, antstr))

    args = ['/bin/sh', _bindir + 'atasetfocus', antstr, str (settingInMHz)]
    if calMode: args.append ('--cal')
    runCommand (*args)

_curFocus = None

def roundFocusSetting (settingInMHz):
    return settingInMHz

_focusWaitInterval = 15
_focusWaitTimeout = 90.

# how close to we have to be to the commanded focus 
# frequency (fractionally) to be considered on-focus?
_focusTol = 0.008

def _waitForFocus (ants):
    from ataprobe import getFocusSettings
    allThere = False
    tStart = time.time ()
    log ('Waiting for antennas to reach focus %f' % _curFocus)

    tol = _focusTol * _curFocus

    while time.time () - tStart < _focusWaitTimeout:
        notThere = set ()
        unknown = set ()
        settings = getFocusSettings (ants)
        log (str (settings))
            
        for ant in ants:
            if not ant.startswith ('ant'): ant = 'ant' + ant
                
            if ant not in settings:
                unknown.add (ant)
                continue

            val = settings[ant]

            if abs (val - _curFocus) > tol:
                notThere.add (ant)

        if len (notThere) + len (unknown) == 0:
            return
        elif len (notThere) + len (unknown) < 3:
            log ('Only a few antennas unfocused, not waiting. Hope for the best!')
            return
        
        time.sleep (_focusWaitInterval)
        ants = notThere.union (unknown)

    if len (notThere) > 0:
        log ('!!!! Antennas are slow to focus: ' + ','.join (notThere))
    if len (unknown) > 0:
        log ('!!!! Antennas don\'t have focus info: ' + ','.join (unknown))
    
def setFocus (ants, settingInMHz, wait=True):
    """Set the focus setting of the specified antennas to the
    specified value. If already at the given value, do
    nothing. Calibrates focus settings upon first invocation and if
    moving from higher frequency to lower frequency (!!! -- apparently
    the focus gets wacky if one moves back and forth. Recommended to
    focus in one direction only). Calls roundFocusSetting() to tweak
    the given focus setting; this can be used to make the focus not be
    adjusted very often."""
    
    # FIXME: assumes that we're always setting the focus of the same suite
    # of antennas ...
    global _curFocus

    # don't both pausing if simulating.
    if noopMode: wait = False
    
    tStart = time.time ()
    log ('Setting input focus %f for: %s' % (settingInMHz,
                                             ','.join (sorted (ants))))
    
    s = roundFocusSetting (settingInMHz)

    if s < 1000:
        log ('Clamping focus value from %f to %f', s, 1000)
        s = 1000
    if s > 9000:
        log ('Clamping focus value from %f to %f', s, 9000)
        s = 9000
        
    log ('Focus value %f mapped to %f' % (settingInMHz, s))
    
    if _curFocus is None or _curFocus > s:
        _setFocus (ants, s, True)
        _curFocus = s
        if wait:
            log ('Pausing 60s for focus cal to proceed.')
            time.sleep (60)
    elif _curFocus != s:
        _setFocus (ants, s, False)
        _curFocus = s
    else:
        # already at desired focus setting
        wait = False

    if wait: _waitForFocus (ants)
    
    account ('focusing antennas', time.time () - tStart)

def waitForFocus (ants):
    tStart = time.time ()
    log ('Waiting for antennas to focus ...')
    _waitForFocus (ants)
    account ('focusing antennas', time.time () - tStart)

# Attemplifier control

_fakeAtten = \
'setatten.rb iXX.fxX inX 99.9 0 ;: Got 99.9 RMS, wanted 99.9 +/- 9.9 ;'
_acctAttemp = 'controlling attemplifiers'

def autoAttenAll (hookup, rms=13.0):
    from ataprobe import _slurp
    
    tStart = time.time ()
    log ('@@ Auto-attening all antpols')
    settings = {}
    
    for (antpol, (ibob, inp)) in hookup.apIbobs ():
        cmd = 'autoatten.rb %s in%d %f 0' % (ibob, inp, rms)

        if noopMode:
            log ('WOULD slurp: ' + cmd)
            out = _fakeAtten
        else:
            out = _slurp (cmd)
            assert len (out) == 1
            out = out[0]

        log (out)
        if 'too low' in out: flag = 'low'
        elif 'too high' in out: flag = 'high'
        else: flag = 'ok'
        
        setting = float (out.split ()[3])
        settings[(ibob, inp)] = (setting, flag)

    account (_acctAttemp, time.time () - tStart)
    return settings

def setAttens (settings):
    tStart = time.time ()

    log ('@@ Restoring saved attemplifier settings')
    
    for ((ibob, inp), (db, flag)) in settings.iteritems ():
        if flag != 'ok':
            log ('!! Warning: flag = %s ; what to do ?' % flag)
        
        runCommand ('/usr/bin/env', 'ruby', _rubydir + 'setatten.rb', ibob,
                    'in%d' % inp, str (db), '0')

    account (_acctAttemp, time.time () - tStart)

def makeAttenKey (src, freq): return freq

_attenSettings = {}
_curAttenKey = None

def setupAttens (src, freq, hookup):
    global _curAttenKey
    
    k = makeAttenKey (src, freq)

    s = _attenSettings.get (k)
    log ('Retrieving or auto-getting attemplifier ' + \
         'settings for key ' + str (k))

    if _curAttenKey is not None and _curAttenKey == k:
        log ('Already at right settings.')
        return
    
    if s is not None:
        setAttens (s)
    else:
        s = autoAttenAll (hookup)
        _attenSettings[k] = s

    _curAttenKey = k

# Fringe rotation control

_acctFringe = 'controlling fringe rotation'

def fringeKill ():
    tStart = time.time ()
    runCommand ('/bin/csh', _obsbindir + 'frot.csh', 'ign_gr',
                'ign_eph', 'ign_freq', os.getcwd (), 'kill')
    account (_acctFringe, time.time () - tStart)

atexit.register (fringeKill)

def fringeStart (hookup, ebase, freq):
    tStart = time.time ()
    msephem = ebase + '.msephem'
    log ('@@ Starting fringe rotation server')
    group = hookup.instr.split (':')[1]
    runCommand ('/bin/csh', _obsbindir + 'frot.csh', group,
                msephem, str (freq), os.getcwd (), 'start')
    # Pause to not confuse the ibobs by talking to them too much
    # -- copied from mosfx.sh 9/11/2008
    time.sleep (10)
    account (_acctFringe, time.time () - tStart)
    
def fringeStop (hookup):
    tStart = time.time ()
    log ('@@ Stopping fringe rotation')
    group = hookup.instr.split (':')[1]
    runCommand ('/bin/csh', _obsbindir + 'frot.csh', group,
                'ign_eph', 'ign_freq', os.getcwd (), 'stop')
    # Pause to not confuse the ibobs by talking to them too much
    # -- copied from mosfx.sh 9/11/2008
    time.sleep (5)
    account (_acctFringe, time.time () - tStart)

# Generic observing function

_lastFreq = 0
_lastSrc = None
_lastSrcExpire = 0

def observe (hookup, outBase, src, freq, integTimeSeconds):
    global _lastFreq, _lastSrc, _lastSrcExpire

    assert _integTime is not None # save time in this case

    # Start the ants focusing. Don't wait for them, so that
    # we can do other stuff while they're moving around.
    setFocus (hookup.ants (), freq, False)

    f = src + '.ephem'
    radec = ensureEphem (src, src, integTimeSeconds)
    now = time.time ()
    
    # Start tracking. Same rationale as above.
    if _lastSrc != src or now >= _lastSrcExpire:
        trackEphem (hookup.ants (), src, False)
        _lastSrc = src
        _lastSrcExpire = now + 2000 # ensureephem actually gives us 1.1 hours
        needTrackWait = True
    else: needTrackWait = False

    if _lastFreq != freq:
        setSkyFreq (hookup.lo, freq)
        _lastFreq = freq

    setupAttens (src, freq, hookup)

    # Start this last to not tickle the ibobs too much before --
    # auto-attening can fail with this going, I think.
    fringeStart (hookup, src, freq)

    try:
        # Wait to finish tracking. This reissues the trackephem command,
        # but we're already on the way so I don't think it will slow
        # things down much.
        if needTrackWait:
            trackEphem (hookup.ants (), src, True)

        # Wait for the ants to reach their focus if they haven't
        # already.
        waitForFocus (hookup.ants ())

        log ('@@ Beginning observations (%s, %s, %d MHz)' % (outBase, src, freq))
        launchCatcher (hookup, src, freq, radec, integTimeSeconds, outBase, src)
    finally:
        # Make sure to always kill the frotter.
        fringeStop (hookup)
