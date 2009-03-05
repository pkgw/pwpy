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

def ataArgs (command, *rest):
    a = ['/bin/sh', _bindir + command]
    for x in rest: a.append (str (x))
    return a


def obsArgs (command, *rest):
    a = ['/bin/csh', _obsbindir + command]
    for x in rest: a.append (str (x))
    return a


def obsRubyArgs (command, *rest):
    a = ['/usr/bin/env', 'ruby', _rubydir + command]
    for x in rest: a.append (str (x))
    return a


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
            raise Exception ("Command '%s' failed: %s" % (cmd, stderr))
        return stdout.splitlines ()
    else:
        return proc.returncode, stdout.splitlines (), stderr.splitlines ()

def getLAST ():
    """Return the local apparent sidereal time, according to the ATA
    system."""

    lines = _slurp (ataArgs ('atamainsystime', '--csv', '-s'))
    if len (lines) != 1: raise Exception ('Expected only one line from atamainsystime')
    return float (lines[0].split (',')[1])

def check (source):
    """Return information about the current sky position of the specified source.

    Returns: (isUp, az, el, risesIn, setsIn) where the tuple elements are:
    
    isUp    - True if the source is currently up
    az      - Current azimuth of the source
    el      - Current elevation of the source
    risesIn - Number of hours until the source next rises above 18 deg
    setsIn  - Number of hours until the source next sets below 18 deg
    """

    import re
    
    (code, stdout, stderr) = _slurp (ataArgs ('atacheck', source), False)

    # Get rid of warning about ambiguous catalog entries to make
    # our assumptions simpler.
    if 'another entry' in stdout[0]: del stdout[0]

    if len (stdout) != 7 and len (stdout) != 6:
        raise Exception ('Error checking source "%s" -- probably not in the catalog.' % source)

    isUp = code == 0
    
    re_azel = re.compile ('Az, El = \\(([-+0-9.]+), ([-+0-9.]+)\\)')
    gr_azel = re_azel.match (stdout[3]).groups ()
    az = float (gr_azel[0])
    el = float (gr_azel[1])

    # Check for circumpolar
    if 'always above' in stdout[4]:
        return (True, az, el, 0., 24.0)
    
    re_lst = re.compile ('.*\\(LST ([0-9]+):([0-9]+):([0-9.]+)\\)')

    def getlst (line):
        gr = re_lst.match (line).groups ()
        hr, min, sec = int (gr[0]), int (gr[1]), float (gr[2])
        return 1.0 * hr + min / 60.0 + sec / 3600.0

    curlst = getlst (stdout[3])
    riselst = getlst (stdout[4])
    setlst = getlst (stdout[5])

    risesIn = riselst - curlst
    if risesIn < 0: risesIn += 24.0

    setsIn = setlst - curlst
    if setsIn < 0: setsIn += 24.0

    return (isUp, az, el, risesIn, setsIn)

def getPAMDefaults (ants):
    """Return the default PAM settings for the specified antennas.

    Returns a list of the same length as ants containing tuples of
    (XPamDefault, YPamDefault).
    """

    lines = _slurp (ataArgs ('atasetpams', ','.join (ants)))

    if len (lines) != len (ants):
        raise Exception ('Unexpected output from atasetpams!')

    def parse (line):
        a = line.split ()
        return (float (a[1]), float (a[2]))

    return [parse (l) for l in lines]


# Integration time

def getIntegTime (hookup):
    """Returns the integration time for the specified hookup object,
    measured in seconds."""
    
    lines = _slurp (obsArgs ('getintfx.csh', hookup.instr))
    integ = float (lines[0])
    return integ


# Focus stuff

def getFocusSettings (ants):
    """Return the current focus settings for the specified antennas.

    Returns a dictionary mapping antenna name (as seen in ants) to
    estimated focus frequency in MHz. Antennas with uncalibrated
    focus settings are not present in the dictionary."""

    lines = _slurp (ataArgs ('atagetfocus', ','.join (ants)))

    res = {}

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

    return res

def logFocusSettings (ants, destname):
    from subprocess import call
    
    call ('atagetfocus %s >%s 2>&1' % (','.join (sorted (ants)), destname),
          shell=True)

# Array hookup data

_defaultInstrument = 'fx64c:fxa'

class Hookup (object):
    def __init__ (self, instr=None):
        if instr is None: instr = _defaultInstrument

        self.instr = instr
        self.lo = self.tab = self.sants = None
        
    def load (self):
        lines = _slurp (obsRubyArgs ('fxconf.rb', 'hookup_tab', self.instr))

        tab = {}
        ants = set ()
        los = set ()
        
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

        self.tab = tab
        self.sants = sorted (ants)
        assert len (los) == 1
        self.lo = lo

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
