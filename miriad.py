# Wrapper for invoking MIRIAD scripts

import sys, os, re, math
from os.path import join
from subprocess import *

home = '/linux-apps4/miriad3'
hosttype = 'linux'
_bindir = join (home, 'bin', hosttype)

# Here is the awesome part where we set up a million environment
# variables. I have no idea how many of these are actually necessary.
# mir.help needs a bunch of them, but it's a script; the actual
# executables don't seem to need any.

childenv = {}
childenv['MIR'] = home
childenv['MIRHOST'] = hosttype
childenv['AIPSTV'] = 'XASIN'
childenv['MIRBIN'] = _bindir
childenv['MIRCAT'] = join (home, 'cat')
childenv['MIRDEF'] = '.'
childenv['MIRDOC'] = join (home, 'doc')
childenv['MIRLIB'] = join (home, 'lib', hosttype)
childenv['MIRNEWS'] = join (home, 'news')
childenv['MIRPAGER'] = 'doc'
childenv['MIRSRC'] = join (home, 'src')
childenv['MIRPROG'] = join (home, 'src', 'prog')
childenv['MIRSUBS'] = join (home, 'src', 'subs')
childenv['MIRPDOC'] = join (home, 'doc', 'prog')
childenv['MIRSDOC'] = join (home, 'doc', 'subs')
childenv['PGPLOT_DIR'] = childenv['MIRLIB']

for (k, v) in childenv.iteritems ():
    os.environ[k] = v

# Need this to find pgxwin_server if using PGPlot.
os.environ['PATH'] += ':' + childenv['MIRBIN']

ldlp = os.environ.get ('LD_LIBRARY_PATH')
if ldlp:
    os.environ['LD_LIBRARY_PATH'] = ldlp + ':' + childenv['MIRLIB']
else:
    os.environ['LD_LIBRARY_PATH'] = childenv['MIRLIB']

# The MIRIAD task running framework

class TaskBase (object):
    """Generic MIRIAD task launcher class. The parameters to commands
    are taken from fields in the object; those with names contained in
    self._params are added to the command line in the style
    '[member name]=[member value]'. The field self._name is the name of
    the MIRIAD task to be run.

    If an element in self._params ends with an underscore, the key name
    associated with that element has the underscore stripped off. This
    allows parameters corresponding to Python keywords to be passed to
    MIRIAD programs (eg, _params = ['in_']).

    IDEA/FIXME/TODO: if an element in _params begins with *, ensure that
    it is not None before running the task.
    """
    
    _name = None
    _params = None

    def __init__ (self, **kwargs):
        self.setArgs (**kwargs)

    def setArgs (self, **kwargs):
        for (key, val) in kwargs.iteritems ():
            setattr (self, key, val)
            
    def launch (self, **kwargs):
        cmd = [join (_bindir, self._name)]
        params = self._params or []
        
        for name in params:
            if name[-1] == '_': key = name[:-1]
            else: key = name
            
            val = getattr (self, name)
            if val: cmd.append ("%s=%s" % (key, val))

        self.cmdline = ' '.join (cmd)
        self.proc = Popen (cmd, stdout=PIPE, stderr=PIPE, shell=False, **kwargs)

    def checkFail (self, stderr=None):
        if not stderr: stderr = self.proc.stderr
        if isinstance (stderr, basestring):
            stderr = stderr.splitlines ()
            
        if self.proc.returncode:
            print 'Ran: %s' % self.cmdline
            print 'Task "%s" failed with exit code %d! It printed:' % (self._name, self.proc.returncode)
            for x in stderr: print '\t', x.strip ()
            raise CalledProcessError (self.proc.returncode, self._name)

    def run (self, **kwargs):
        self.launch (**kwargs)
        self.proc.wait ()
        self.checkFail ()

    def snarf (self, send=None, **kwargs):
        self.launch (**kwargs)
        (stdout, stderr) = self.proc.communicate (send)
        self.checkFail (stderr)
        return (stdout.splitlines (), stderr.splitlines ())

    def what (self):
        """Print some useful information about the last process that
        was invoked. This is useful if a command doesn't work for some
        nonobvious reason."""
        
        print 'Ran: %s' % self.cmdline
        print 'Task "%s", return code %d' % (self._name, self.proc.returncode)
        print 'Standard output:'
        for x in self.proc.stdout: print '\t', x.strip ()
        print 'Standard error:'
        for x in self.proc.stderr: print '\t', x.strip ()

class TaskCgDisp (TaskBase):
    # XXX FIXME: incomplete set of keywords
    _name = 'cgdisp'
    _params = ['device', 'in_', 'type', 'region', 'xybin', 'chan',
               'slev', 'levs1', 'levs2', 'levs3', 'cols1', 'range',
               'vecfac', 'boxfac']

    device = '/xs'
    in_ = None
    type = None
    region = None
    xybin = None
    chan = None
    slev = None
    levs1 = None
    levs2 = None
    levs3 = None
    cols1 = None
    range = None
    vecfac = None
    boxfac = None

class TaskUVList (TaskBase):
    # XXX FIXME: incomplete set of keywords
    _name = 'uvlist'
    _params = ['recnum', 'vis', 'options']

    recnum = 1000
    vis = None
    options = 'variables'

class TaskUVPlot (TaskBase):
    # XXX FIXME: incomplete set of keywords
    _name = 'uvplt'
    _params = ['vis', 'device', 'axis', 'size', 'select']

    vis = None
    device = '/xs'
    axis = 'uu,vv'
    size = 2
    select = None

class TaskInvert (TaskBase):
    # XXX FIXME: incomplete set of keywords
    _name = 'invert'
    _params = ['vis', 'map', 'beam', 'select', 'stokes', 'options',
               'robust', 'cell', 'fwhm', 'imsize']

    vis = None
    map = None
    beam = None
    select = None
    stokes = 'ii'
    options = 'mfs,systemp,double'
    robust = None
    cell = None
    fwhm = None
    imsize = None

class TaskClean (TaskBase):
    # XXX FIXME: incomplete set of keywords
    _name = 'clean'
    _params = ['map', 'beam', 'out', 'niters', 'region']

    map = None
    beam = None
    out = None
    niters = 100
    region = None

class TaskRestore (TaskBase):
    # XXX FIXME: incomplete set of keywords
    _name = 'restor'
    _params = ['map', 'beam', 'model', 'out']

    map = None
    beam = None
    model = None
    out = None

class TaskImStat (TaskBase):
    _name = 'imstat'
    _params = ['in_', 'region', 'options', 'plot', 'cutoff',
               'beam', 'axes', 'device', 'log']

    in_ = None
    beam = None
    region = None
    options = None
    plot = None
    cutoff = None
    axes = None
    device = None
    log = None
    
class TaskImHead (TaskBase):
    _name = 'imhead'
    _params = ['in_', 'key', 'log']

    in_ = None
    key = None
    log = None

    def snarfOne (self, key):
        self.key = key
        (stdout, stderr) = self.snarf ()
        
        if len(stdout) != 1:
            raise Exception ('Unexpected output from IMHEAD: %s' % \
                             stdout + '\nStderr: ' + stderr)

        return stdout[0].strip ()

class TaskIMom (TaskBase):
    _name = 'imom'
    _params = ['in_', 'options', 'region', 'min', 'max', 'log']

    in_ = None
    options = None
    region = None
    min = None
    max = None
    log = None
        
# These functions operate on single images, using several of
# the tasks defined above.

def getImageDimensions (image, **kwargs):
    imh = TaskImHead (in_=image, **kwargs)

    naxis = int (imh.snarfOne ('naxis'))
    res = []
    
    for i in range (1, naxis + 1):
        res.append (int (imh.snarfOne ('naxis%d' % i)))
    
    return res

def getImageStats (image, **kwargs):
    # FIXME: noheader option seems a little dangerous, if we
    # ever use this for multifreq data.
    ims = TaskImStat (in_=image, options='noheader', **kwargs)
    (stdout, stderr) = ims.snarf ()
        
    if len(stdout) != 2:
        raise Exception ('Unexpected output from IMSTAT: %s' % \
                         stdout + '\nStderr: ' + stderr)

    # ' Total                  Sum      Mean      rms     Maximum   Minimum    Npoints'
    #  0123456789012345678901234567890123456789012345678901234567890123456789012345678'
    #  0         1         2         3         4         5         6         7        '
    #                       ^         ^         ^         ^         ^         ^ 
        
    sum = float (stdout[1][21:31])
    mean = float (stdout[1][31:41])
    rms = float (stdout[1][41:51])
    max = float (stdout[1][51:61])
    min = float (stdout[1][61:71])
    npts = int (stdout[1][71:])
    
    return (sum, mean, rms, max, min, npts)

def getImageMoment (image, **kwargs):
    imom = TaskIMom (in_=image, **kwargs)
    (stdout, stderr) = imom.snarf ()

    # 'Plane:    1   Centroid:  9.00143E+01  9.00160E+01 pixels'
    # 'Plane:    1     Spread:  5.14889E+01  5.15338E+01 pixels'
    #  012345678901234567890123456789012345678901234567890123456
    #  0         1         2         3         4         5      
    #                          ^            ^

    ctr1 = ctr2 = spr1 = spr2 = -1

    for line in stdout:
        if 'Centroid:' in line:
            ctr1 = int (float (line[24:37]))
            ctr2 = int (float (line[37:49]))
        elif 'Spread:' in line:
            spr1 = int (float (line[24:37]))
            spr2 = int (float (line[37:49]))

    if min (ctr1, ctr2, spr1, spr2) < 0:
        raise Exception ('Incomplete output from IMOM task?' + imom.what (stderr=stderr))

    return (ctr1, ctr2, spr1, spr2)

def getImageBeamSize (image, **kwargs):
    imh = TaskImHead (in_=image, **kwargs)

    bmaj = float (imh.snarfOne ('bmaj')) # in radians
    bmin = float (imh.snarfOne ('bmin')) # in radians
    
    return (bmaj, bmin)
