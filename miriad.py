# Wrapper for invoking MIRIAD scripts
#
# 'mirhelp uvflag' has good help on the 'select' and
# 'line' parameters.

import sys, os, re, math
import os.path
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

class DefaultedTaskType (type):
    # YES! I get to write a metaclass! This looks at the
    # _params and _options members and fills in default values
    # in the class dictionary for any parameters or options
    # not already specified. So if there is a 'foo' parameter,
    # it creates an entry in the class dictionary of 'foo = None'.
    # This allows TaskBase to just getattr() any class parameter,
    # and makes tab-completing easy.
    #
    # We also guess the task name if _name is not set. Cute.
    
    def __init__ (cls, name, bases, dict):
        type.__init__ (cls, name, bases, dict)
        
        # TaskBase doesn't get any special treatment
        if name == 'TaskBase': return 
        
        if '_name' not in dict:
            if name.startswith ('Task'):
                setattr (cls, '_name', name[4:].lower ())
            else:
                raise Exception ('Task class must define a _name member')

        for p in dict.get ('_params') or []:
            if p in dict: continue

            setattr (cls, p, None)

        for o in dict.get ('_options') or []:
            if o in dict: continue
            
            setattr (cls, o, False)

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

    __metaclass__ = DefaultedTaskType
    
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

        # Now go. Set stdin to /dev/null so that the program can't
        # block waiting for user input.
        
        self.cmdline = ' '.join (cmd)
        self.proc = Popen (cmd, stdin=file (os.devnull, 'r'),
                           stdout=PIPE, stderr=PIPE, shell=False, **kwargs)

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
    _params = ['device', 'in_', 'type', 'region', 'xybin', 'chan',
               'slev', 'levs1', 'levs2', 'levs3', 'cols1', 'range',
               'vecfac', 'boxfac', 'nxy', 'labtyp', 'beamtyp',
               '3format', 'lines', 'break', 'csize', 'scale', 'olay']

    _options = ['abut', 'beamAB', 'blacklab', 'conlabel', 'fiddle',
                'full', 'gaps', 'grid', 'mirror', 'nodistort',
                'noepoch', 'noerase', 'nofirst', 'corner', 'relax',
                'rot90', 'signs', 'single', 'solneg1', 'solneg2',
                'solneg3', 'trlab', 'unequal', 'wedge', '3pixel',
                '3value']
    
    device = '/xs'

class TaskUVList (TaskBase):
    _params = ['vis', 'select', 'line', 'scale', 'recnum', 'log']
    _options = ['brief', 'data', 'average', 'allan', 'history',
                'flux', 'full', 'list', 'variables', 'stat',
                'birds', 'spectra']
    
    recnum = 1000
    variables = True

class TaskUVPlot (TaskBase):
    # XXX FIXME: there is a 'log' option, but that would conflict
    # with the 'log' parameter.
    
    _name = 'uvplt'
    _params = ['vis', 'line', 'device', 'axis', 'size', 'select',
               'stokes', 'xrange', 'yrange', 'average', 'hann',
               'inc', 'nxy', 'log', 'comment']
    _options = ['nocal', 'nopol', 'nopass', 'nofqav', 'nobase',
                '2pass', 'scalar', 'avall', 'unwrap', 'rms',
                'mrms', 'noerr', 'all', 'flagged', 'nanosec',
                'days', 'hours', 'seconds', 'xind', 'yind',
                'equal', 'zero', 'symbols', 'nocolour', 'dots',
                'source', 'inter']
                
    device = '/xs'
    axis = 'uu,vv'
    size = 2

class TaskInvert (TaskBase):
    _params = ['vis', 'map', 'beam', 'select', 'stokes',
               'robust', 'cell', 'fwhm', 'imsize', 'offset',
               'sup', 'line', 'ref', 'mode', 'slop']
    _options = ['nocal', 'nopol', 'nopass', 'double', 'systemp',
                'mfs', 'sdb', 'mosaic', 'imaginary', 'amplitude',
                'phase']
    
    stokes = 'ii'

    double = True
    systemp = True
    mfs = True

class TaskClean (TaskBase):
    _params = ['map', 'beam', 'out', 'niters', 'region',
               'gain', 'cutoff', 'phat', 'minpatch',
               'speed', 'mode', 'clip']
    _options = ['negstop', 'positive', 'asym', 'pad']
    
    niters = 100

class TaskRestore (TaskBase):
    _name = 'restor'
    _params = ['map', 'beam', 'model', 'out', 'mode', 'fwhm',
               'pa']

class TaskImStat (TaskBase):
    _params = ['in_', 'region', 'plot', 'cutoff',
               'beam', 'axes', 'device', 'log']
    _options = ['tb', 'hanning', 'boxcar', 'deriv', 'noheader',
                'nolist', 'eformat', 'guaranteespaces', 'xmin',
                'xmax', 'ymin', 'ymax', 'title', 'style']

class TaskImHead (TaskBase):
    _params = ['in_', 'key', 'log']

    def snarfOne (self, key):
        self.key = key
        (stdout, stderr) = self.snarf ()
        
        if len(stdout) != 1:
            raise Exception ('Unexpected output from IMHEAD: %s' % \
                             stdout + '\nStderr: ' + stderr)

        return stdout[0].strip ()

class TaskIMom (TaskBase):
    _params = ['in_', 'region', 'min', 'max', 'log']
    _options = ['skew', 'clipmean', 'clip1sigma']
    
class TaskImFit (TaskBase):
    _params = ['in_', 'region', 'clip', 'object', 'spar',
               'fix', 'out']
    _options = ['residual']
    
class TaskUVAver (TaskBase):
    _params = ['vis', 'select', 'line', 'ref', 'stokes',
               'interval', 'out']
    _options = ['nocal', 'nopass', 'nopol', 'relax',
                'vector', 'scalar', 'scavec']

class TaskGPCopy (TaskBase):
    _params = ['vis', 'out', 'mode']
    _options = ['nopol', 'nocal', 'nopass']

class TaskMSelfCal (TaskBase):
    _params = ['vis', 'select', 'model', 'clip', 'interval',
               'minants', 'refant', 'flux', 'offset', 'line',
               'out']
    _options = ['amplitude', 'phase', 'smooth', 'polarized',
                'mfs', 'relax', 'apriori', 'noscale', 'mosaic',
                'verbose']

class TaskPutHead (TaskBase):
    _name = 'puthd'
    _params = ['in_', 'value', 'type']

class TaskGPPlot (TaskBase):
    _name = 'gpplt'
    _params = ['vis', 'device', 'log', 'yaxis', 'nxy',
               'select', 'yrange']
    _options = ['gains', 'xygains', 'xbyygain',
                'polarization', 'delays', 'speccor',
                'bandpass', 'dots', 'dtime', 'wrap']

    device = '/xs'

class TaskPrintHead (TaskBase):
    _name = 'prthd'
    _params = ['in_', 'log']
    _options = ['brief', 'full']

    full = True

class TaskClosure (TaskBase):
    _params = ['vis', 'select', 'line', 'stokes', 'device',
               'nxy', 'yrange', 'interval']
    _options = ['amplitude', 'quad', 'avall', 'notriple', 'rms',
                'nocal', 'nopol', 'nopass']

    device = '/xs'

class TaskUVFlag (TaskBase):
    _params = ['vis', 'select', 'line', 'edge', 'flagval', 'log' ]
    _options = ['noapply', 'none', 'brief', 'indicative', 'full',
                'noquery', 'hms', 'decimal']

class TaskUVSpec (TaskBase):
    _params = ['vis', 'select', 'line', 'stokes', 'interval', 'hann',
               'offset', 'axis', 'yrange', 'device', 'nxy', 'log']
    _options = ['nocal', 'nopass', 'nopol', 'ampscalar', 'rms',
                'nobase', 'avall', 'dots', 'flagged', 'all']

    device= '/xs'

# These functions operate on single images or single visibilities,
# using several of the tasks defined above.

def getVisRestfreq (vis, **kwargs):
    """Returns the rest frequency of the specified visibility file
    in gigahertz. The data is obtained from the output of the miriad
    prthd task."""
    
    # FIXME: probably breaks with multifreq data! No example
    # files!

    ph = TaskPrintHead (in_=vis, full=True, **kwargs)
    (stdout, stderr) = ph.snarf ()

    sawHead = False
    
    # '  Spectrum  Channels  Freq(chan=1)  Increment  Restfreq     '
    # '      1          1       5.00020     0.011719   5.00000 GHz '
    #  012345678901234567890123456789012345678901234567890123456789'
    #  0         1         2         3         4         5         '
    #                      ^             ^          ^         ^    '

    for line in stdout:
        if 'Restfreq' in line:
            sawHead = True
        elif sawHead:
            if line[56:59] != 'GHz':
                raise Exception ('Restfreq not in GHz???: %s' % line)
            s = line[45:55].strip ()
            return float (s)

    raise Exception ('Unexpected output from prthd task: %s' % stdout)

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

def fitImageGaussian (image, **kwargs):
    imf = TaskImFit (in_=image, **kwargs)
    imf.object = 'gaussian'
    
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
