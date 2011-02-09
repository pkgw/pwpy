"""Routines for extracting information about the ATA. Would be nice
if we could bridge directly to the Java APIs -- for a discussion of
that, see atactl.py.
"""

SVNID = '$Id$'

runLogger = None

# Some utilities for constructing commandlines. These are actually
# not used much in this module, but come into play a lot in atactl.py

_bindir = '/hcro/atasys/ata/run/'
_rubydir = '/home/obs/ruby/bin/'
_obsbindir = '/home/obs/bin/'
_sysrubydir = '/hcro/opt/bin/'

def ataArgs (command, *rest):
    a = ['/bin/sh', _bindir + command]
    for x in rest: a.append (str (x))
    return a


def obsArgs (command, *rest):
    a = ['/bin/tcsh', _obsbindir + command]
    for x in rest: a.append (str (x))
    return a


def obsRubyArgs (command, *rest):
    a = ['/usr/bin/env', 'ruby', _rubydir + command]
    for x in rest: a.append (str (x))
    return a


def sysRubyArgs (command, *rest):
    a = ['/usr/bin/env', 'ruby', _sysrubydir + command]
    for x in rest: a.append (str (x))
    return a


# Getting information by parsing program output.

class SlurpError (EnvironmentError):
    """An error raised if a program whose output was desired
    exited with an error code or produced unexpected output."""

    def __init__ (self, args, code, stdout, stderr, subexc):
        args = list (args)
        code = int (code)
        # We used to use some semantics of EnvironmentError.__init__()
        # that were inconsistent between Python 2.5 and later versions.
        # The following should be robust.
        super (SlurpError, self).__init__ (0, 'temp')
        self.args = (args, code, stdout, stderr, subexc)

    def __str__ (self):
        args, code, stdout, stderr, subexc = self.args
        if subexc is None:
            substr = '[none]'
        else:
            substr = '%s: %s' % (subexc.__class__.__name__, subexc)
        return """Couldn't parse output of command: %s
Exit code: %d
Standard out: %s
Standard error: %s
Subexception: %s""" % (' '.join (args), code,
                       stdout or '[none]',
                       stderr or '[none]',
                       substr)


def _slurp (args, checkCode=True):
    """Return the output of a cmd, which is executed in a shell.

    If checkCode is True, an exception is raised if the exit code of
    the program is nonzero. If the exit code is zero, an array of lines
    representing the program's stdout is returned.

    If checkCode is False, a tuple of (retcode, stdout, stderr) is
    returned. Retcode is the process's return code, stdout is its stdout
    split by lines, and stderr is its stderr split by lines."""
    
    import subprocess, os

    if runLogger is not None:
        runLogger (args)
    
    proc = subprocess.Popen (args, shell=False, stdin=file (os.devnull, 'r'),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, close_fds=True)
    (stdout, stderr) = proc.communicate (None)

    if checkCode:
        if proc.returncode != 0:
            raise SlurpError (args, proc.returncode, stdout, stderr,
                              EnvironmentError ('Nonzero exit code'))
        return stdout.splitlines ()
    else:
        return proc.returncode, stdout.splitlines (), stderr.splitlines ()


def getLAST ():
    """Return the local apparent sidereal time, according to the ATA
    system."""

    args = ataArgs ('atamainsystime', '--csv', '-s')
    lines = _slurp (args)

    try:
        assert len (lines) == 1
        return float (lines[0].split (',')[1])
    except StandardError, e:
        raise SlurpError (args, 0, lines, None, e)


def _checkGeneric (code, stdout):
    import re
    
    isUp = code == 0
    
    re_azel = re.compile ('Az, El = \\(([-+0-9.]+), ([-+0-9.]+)\\)')
    gr_azel = re_azel.match (stdout[2]).groups ()
    az = float (gr_azel[0])
    el = float (gr_azel[1])

    # Check for circumpolar
    if 'always above' in stdout[3]:
        return (True, az, el, 0., 24.0)

    if 'always below' in stdout[3]:
        return (False, az, el, 24.0, 0)

    re_lst = re.compile ('.*\\(LST ([0-9]+):([0-9]+):([0-9.]+)\\)')

    def getlst (line):
        gr = re_lst.match (line).groups ()
        hr, min, sec = int (gr[0]), int (gr[1]), float (gr[2])
        return 1.0 * hr + min / 60.0 + sec / 3600.0

    curlst = getlst (stdout[2])
    riselst = getlst (stdout[3])
    setlst = getlst (stdout[4])

    risesIn = riselst - curlst
    if risesIn < 0: risesIn += 24.0

    setsIn = setlst - curlst
    if setsIn < 0: setsIn += 24.0

    return (isUp, az, el, risesIn, setsIn)


def check (source):
    """Return information about the current sky position of the specified source.

    Returns: (isUp, az, el, risesIn, setsIn) where the tuple elements are:
    
    isUp    - True if the source is currently up
    az      - Current azimuth of the source
    el      - Current elevation of the source
    risesIn - Number of hours until the source next rises above 18 deg
    setsIn  - Number of hours until the source next sets below 18 deg
    """

    args = ataArgs ('atacheck', source)
    (code, stdout, stderr) = _slurp (args, False)

    # Get rid of warning about ambiguous catalog entries to make
    # our assumptions simpler. Can get a message about 'another entry'
    # or 'other entries'.
    if 'other entr' in stdout[0]: del stdout[0]
    if stdout[0].startswith ('AntUtil:'): del stdout[0]
    
    try:
        assert len (stdout) == 6 or len (stdout) == 5
        return _checkGeneric (code, stdout)
    except StandardError, e:
        raise SlurpError (args, code, stdout, stderr, e)


def checkRADec (raHours, decDeg):
    """Return information about the current sky position of the specified
    RA/Dec coordinates.

    Returns: (isUp, az, el, risesIn, setsIn) where the tuple elements are:
    
    isUp    - True if the source is currently up
    az      - Current azimuth of the source
    el      - Current elevation of the source
    risesIn - Number of hours until the source next rises above 18 deg
    setsIn  - Number of hours until the source next sets below 18 deg
    """

    args = ataArgs ('atacheck', '--radec', '%.6f,%.6f' % (raHours, decDeg))
    (code, stdout, stderr) = _slurp (args, False)

    try:
        assert len (stdout) == 5 or len (stdout) == 6
        return _checkGeneric (code, stdout)
    except StandardError, e:
        raise SlurpError (args, code, stdout, stderr, e)


def getPAMDefaults (ants):
    """Return the default PAM settings for the specified antennas.

    Returns a list of the same length as ants containing tuples of
    (XPamDefault, YPamDefault).
    """

    args = ataArgs ('atasetpams', ','.join (ants))
    lines = _slurp (args)

    def parse (line):
        a = line.split ()
        return (float (a[1]), float (a[2]))

    try:
        assert len (lines) == len (ants)
        return [parse (l) for l in lines]
    except StandardError, e:
        raise SlurpError (args, 0, lines, None, e)


# Integration time

def getIntegTime (hookup):
    """Returns the integration time for the specified hookup object,
    measured in seconds."""
    
    args = obsArgs ('getintfx.csh', hookup.instr)
    lines = _slurp (args)
    try:
        return float (lines[0])
    except StandardError, e:
        raise SlurpError (args, 0, lines, None, e)


# Bandwidth

_bandwidthValues = [100, 52, 26, 13, 7, 3]

def getBandwidth (hookup, board='i1'):
    """Returns the *approximate* bandwidth, an integer."""

    fullboard = '%s.fx%c' % (board, hookup.instr.split (':')[0][-1])
    args = obsRubyArgs ('ibob', fullboard, 'regread', 'bwsel')
    lines = _slurp (args)
    try:
        val = int (lines[0].split ()[0], 16) # string is in hex
    except StandardError, e:
        raise SlurpError (args, 0, lines, None, e)

    mode0 = val & 0xF

    if mode0 < 0 or mode0 > 5:
        raise Exception ('Unexpected bandwidth code %d (from %s)' % \
                         (mode0, lines[0]))

    check = mode0 | (mode0 << 4) | (mode0 << 8) | (mode0 << 12)
    if val & 0xFFFF != check:
        raise Exception ('Unhandled non-uniform bandwidth config (from %s)' % \
                         lines[0])

    return _bandwidthValues[mode0]

def computeExactBandwidth (approx):
    # Copy of decision tree in bw.csh

    if approx >= 79:
        n = 0
    elif approx >= 39:
        n = 1
    elif approx >= 20:
        n = 2
    elif approx >= 10:
        n = 3
    elif approx >= 5:
        n = 4
    else:
        n = 5

    return 104.8576 / 2**n


# Focus stuff

def getFocusSettings (ants):
    """Return the current focus settings for the specified antennas.

    Returns a dictionary mapping antenna name (as seen in ants) to
    estimated focus frequency in MHz. Antennas with uncalibrated
    focus settings are not present in the dictionary."""

    args = ataArgs ('atagetfocus', ','.join (ants))
    lines = _slurp (args)
    res = {}

    try:
        for l in lines:
            l = l.strip ()
            if len (l) == 0: continue

            a = l.split ()

            try:
                freq = float (a[1])
            except ValueError:
                # there's an error message for this ant
                continue

            ant = a[0]

            # Handle the fact that we may refer to an ant as '3f'
            # but getfocus will print out 'ant3f' as the name.

            if ant in ants:
                res[ant] = freq
            elif ant[3:] in ants:
                res[ant[3:]] = freq
            else:
                raise Exception ('Unexpected antname in atagetfocus output: ' + ant)
    except StandardError, e:
        raise SlurpError (args, 0, lines, None, e)

    return res

def logFocusSettings (ants, destname):
    from subprocess import call
    
    call ('atagetfocus %s >%s 2>&1' % (','.join (sorted (ants)), destname),
          shell=True)

# Array hookup data

_defaultInstrument = 'fx64c:fxa'


def _parseHookup (instr):
    tab = {}
    ants = set ()
    los = set ()
        
    args = obsRubyArgs ('fxconf.rb', 'hookup_tab', instr)
    lines = _slurp (args)

    try:
        for l in lines:
            if len (l) == 0 or l[0] == ':':
                # "grayed out" and not used
                continue

            a = l.split ()

            num = int (a[3])
            conn = a[5]
            antinfo = a[7]
            mirinfo = a[9]
            walsh = int (a[12])
        
            ibob = conn.split (':')[0]
            inp = int (conn[-1:])
            
            antpol = antinfo[0:3]
            lo = antinfo[3]

            # "Analog" LO output number -- doesn't
            # do much of anything right now, I believe.
            outp = int (antinfo[4])

            mirnum = int (mirinfo[:-1])
        
            tab[antpol] = (ibob, inp, lo, outp, walsh, num, mirnum)
            ants.add (antpol[0:2])
            los.add (lo)
    except StandardError, e:
        raise SlurpError (args, 0, lines, None, e)

    return tab, ants, los


class Hookup (object):
    def __init__ (self, instr=None):
        if instr is None: instr = _defaultInstrument

        self.instr = instr
        self.lo = self.tab = self.sants = None
        
    def load (self):
        tab, ants, los = _parseHookup (self.instr)
        
        assert len (ants) > 0, 'No ants! Using an empty subarray?'
        assert len (los) == 1

        self.tab = tab
        self.sants = sorted (ants)
        self.lo = list (los)[0]

    def ants (self): return self.sants

    def antpols (self): return sorted (self.tab.iterkeys ())

    def apIbobs (self):
        l = []
        
        for (ap, info) in self.tab.iteritems ():
            l.append ((ap, (info[0], info[1])))

        # This sorts by ADC input first. This is important,
        # since it makes looping through this list talk to an
        # four times with long breaks in between, instead of
        # one long time. The latter mode seems to be too much
        # for the ibobs, causing them to sometimes fail to
        # respond to commands.
        
        l.sort (key = lambda t: str (t[1][1]) + t[1][0])
        return l

    def ibobInps (self):
        # Same sorting as above.
        return sorted (((t[0], t[1]) for t in self.tab.itervalues ()),
                       key = lambda t: str (t[1]) + t[0])


_defaultMultiInstrs = ['fx64a:fxa', 'fx64c:fxa']

class MultiHookup (object):
    def __init__ (self, instrs=None):
        if instrs is None: instrs = _defaultMultiInstrs

        self.hookups = hs = {}

        for instr in instrs:
            hs[instr] = Hookup (instr)


    def load (self):
        for h in self.hookups.itervalues ():
            h.load ()


    def los (self):
        s = set ()
        for h in self.hookups.itervalues ():
            s.update ((h.lo, ))
        return sorted (s)


    def ants (self):
        s = set ()
        for h in self.hookups.itervalues ():
            s.update (h.ants ())
        return sorted (s)

    def antpols (self):
        s = set ()
        for h in self.hookups.itervalues ():
            s.update (h.antpols ())
        return sorted (s)

    def ibobInps (self):
        s = set ()
        for h in self.hookups.itervalues ():
            s.update ((t[1] for t in h.apIbobs ()))
        return sorted (s, key = lambda t: str (t[1]) + t[0])
