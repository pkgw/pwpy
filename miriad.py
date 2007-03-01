# Wrapper for invoking MIRIAD scripts
#
# 'mirhelp uvflag' has good help on the 'select' and
# 'line' parameters.

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
    _options = None
    
    def __init__ (self, **kwargs):
        self.setArgs (**kwargs)

    def setArgs (self, **kwargs):
        for (key, val) in kwargs.iteritems ():
            setattr (self, key, val)
            
    def launch (self, **kwargs):
        cmd = [join (_bindir, self._name)]
        options = []

        # Options
        
        for opt in self._options or []:
            val = getattr (self, opt)

            if val is None: continue
            
            if isinstance (val, bool):
                if val: options.append (opt)
            else:
                options.append (opt)

                if not hasattr (val, '__iter__'):
                    options.append (str (val))
                else:
                    for x in val:
                        options.append (str (x))

        if len (options) > 0:
            cmd.append ('options=%s' % (','.join (options)))

        # Parameters
        
        for name in self._params or []:
            if name[-1] == '_': key = name[:-1]
            else: key = name
            
            val = getattr (self, name)
            if val: cmd.append ("%s=%s" % (key, val))

        # Now go.
        
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
    _name = 'uvlist'
    _params = ['vis', 'select', 'line', 'scale', 'recnum', 'log']
    _options = ['brief', 'data', 'average', 'allan', 'history',
                'flux', 'full', 'list', 'variables', 'stat',
                'birds', 'spectra']
    
    vis = None
    select = None
    line = None
    scale = None
    recnum = 1000
    log = None

    brief = False
    data = False
    average = False
    allan = False
    history = False
    flux = False
    full = False
    list = False
    variables = True
    stat = False
    birds = False
    spectra = False

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
    _params = ['vis', 'map', 'beam', 'select', 'stokes',
               'robust', 'cell', 'fwhm', 'imsize']
    _options = ['nocal', 'nopol', 'nopass', 'double', 'systemp',
                'mfs', 'sdb', 'mosaic', 'imaginary', 'amplitude',
                'phase']
    
    vis = None
    map = None
    beam = None
    select = None
    stokes = 'ii'
    robust = None
    cell = None
    fwhm = None
    imsize = None

    nocal = False
    nopol = False
    nopass = False
    double = True
    systemp = True
    mfs = True
    sdb = False
    mosaic = False
    imaginary = False
    amplitude = False
    phase = False

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
    _params = ['in_', 'region', 'plot', 'cutoff',
               'beam', 'axes', 'device', 'log']
    _options = ['tb', 'hanning', 'boxcar', 'deriv', 'noheader',
                'nolist', 'eformat', 'guaranteespaces', 'xmin',
                'xmax', 'ymin', 'ymax', 'title', 'style']
               
    in_ = None
    beam = None
    region = None
    plot = None
    cutoff = None
    axes = None
    device = None
    log = None

    tb = False
    hanning = None
    boxcar = None
    deriv = None
    noheader = False
    nolist = False
    eformat = False
    guaranteespaces = False
    xmin = None
    xmax = None
    ymin = None
    ymax = None
    title = None
    style = None
    
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
    _params = ['in_', 'region', 'min', 'max', 'log']
    _options = ['skew', 'clipmean', 'clip1sigma']
    
    in_ = None
    options = None
    region = None
    min = None
    max = None
    log = None

    skew = False
    clipmean = False
    clip1sigma = False
    
class TaskImFit (TaskBase):
    _name = 'imfit'
    _params = ['in_', 'region', 'clip', 'object', 'spar',
               'fix', 'out']
    _options = ['residual']
    
    in_ = None
    region = None
    clip = None
    object = None
    spar = None
    fix = None
    out = None
    options = None

    residual = False
    
class TaskUVAver (TaskBase):
    _name = 'uvaver'
    _params = ['vis', 'select', 'line', 'ref', 'stokes',
               'interval', 'out']
    _options = ['nocal', 'nopass', 'nopol', 'relax',
                'vector', 'scalar', 'scavec']
    
    vis = None
    select = None
    line = None
    ref = None
    stokes = None
    interval = None
    options = None
    out = None

    nocal = False
    nopass = False
    nopol = False
    relax = False
    vector = False
    scalar = False
    scavec = False

class TaskGPCopy (TaskBase):
    _name = 'gpcopy'
    _params = ['vis', 'out', 'mode']
    _options = ['nopol', 'nocal', 'nopass']

    vis = None
    out = None
    mode = None

    nopol = False
    nocal = False
    nopass = False

class TaskMSelfCal (TaskBase):
    _name = 'mselfcal'
    _params = ['vis', 'select', 'model', 'clip', 'interval',
               'minants', 'refant', 'flux', 'offset', 'line',
               'out']
    _options = ['amplitude', 'phase', 'smooth', 'polarized',
                'mfs', 'relax', 'apriori', 'noscale', 'mosaic',
                'verbose']

    vis = None
    select = None
    model = None
    clip = None
    interval = None
    minants = None
    refant = None
    flux = None
    offset = None
    line = None
    out = None

    amplitude = False
    phase = False
    smooth = False
    polarized = False
    mfs = False
    relax = False
    apriori = False
    noscale = False
    mosaic = False
    verbose = False

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
    ims = TaskImStat (in_=image, noheader=True, **kwargs)
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

def fitImagePoint (image, **kwargs):
    imf = TaskImFit (in_=image, **kwargs)
    imf.object = 'point'
    
    (stdout, stderr) = imf.snarf ()

    rms = max = None
    
    for line in stdout:
        if 'RMS residual' in line:
            a = line.split (' ')
            rms = float (a[3])
        elif 'Peak value:' in line:
            # '  Peak value:                 6.9948E-04 +/-  0.0000'
            #  012345678901234567890123456789012345678901234567890123456
            #  0         1         2         3         4         5      
            max = float (line[30:40])

    if not rms or not max:
        raise Exception ('Didn\'t get all info from imfit routine!')

    return (max, rms)

# Simple object representing a MIRIAD data set of some kind or another.
# gb.py has VisData and ImageData subclasses, etc.

class MiriadData (object):
    def __init__ (self, basedata):
        self.base = basedata

    def __str__ (self):
        return self.base

    def __repr__ (self):
        return '<MIRIAD data, base "%s">' % self.base

    @property
    def exists (self):
        """True if the data specified by this class actually exists.
        (If False, the data corresponding to this object will probably
        be created by the execution of a command.)"""
        return os.path.exists (self.base)

    def checkExists (self):
        if self.exists: return

        raise Exception ('Data set %s does not exist' % self.base)
    
    def delete (self):
        # Silently not doing anything seems appropriate here.
        if not self.exists: return
        
        for e in os.listdir (self.base):
            os.remove (join (self.base, e))
        os.rmdir (self.base)

    def makeVariant (self, kind, name):
        if not issubclass (kind, MiriadData): raise Exception ('blarg')

        return kind (self.base + '.' + name)
    
