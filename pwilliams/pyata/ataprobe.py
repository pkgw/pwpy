"""Routines for extracting information about the ATA. Should be written
in Jython to use the native Java APIs, but Jython is broken right now.
"""

def _slurp (cmd, checkCode=True):
    """Return the output of a cmd, which is executed in a shell.

    If checkCode is True, an exception is raised if the exit code of
    the program is nonzero. If the exit code is zero, an array of lines
    representing the program's stdout is returned.

    If checkCode is False, a tuple of (retcode, stdout, stderr) is
    returned. Retcode is the process's return code, stdout is its stdout
    split by lines, and stderr is its stderr split by lines."""
    
    import subprocess, os

    proc = subprocess.Popen (str (cmd), shell=True,
                             stdin=file (os.devnull, 'r'), stdout=subprocess.PIPE,
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

    lines = _slurp ('atamainsystime --csv -s')
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
    
    (code, stdout, stderr) = _slurp ('atacheck "%s"' % source, False)

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

    lines = _slurp ('atasetpams "%s"' % ','.join (ants))

    if len (lines) != len (ants):
        raise Exception ('Unexpected output from atasetpams!')

    def parse (line):
        a = line.split ()
        return (float (a[1]), float (a[2]))

    return [parse (l) for l in lines]

def getFocusSettings (ants):
    """Return the current focus settings for the specified antennas.

    Returns a dictionary mapping antenna name (as seen in ants) to
    estimated focus frequency in MHz. Antennas with uncalibrated
    focus settings are not present in the dictionary."""

    lines = _slurp ('atagetfocus "%s"' % ','.join (ants))

    res = {}

    for l in lines:
        a = l.split ()

        if a[0][-1] == ':':
            # Error-message ant. Have seen: uncalibrated; no rim box
            continue
        
        assert len (a) == 2
        freq = float (a[1])
        ant = a[0]

        if ant in ants:
            res[ant] = freq
        elif ant[3:] in ants:
            res[ant[3:]] = freq
        else:
            raise Exception ('Unexpected antname in atagetfocus output: ' + ant)

    return res

