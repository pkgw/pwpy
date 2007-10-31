# data structures for the stuff that Geoff Bower (hence
# the gb) is telling me to do

import os, miriad

# Sets of input files that can be passed to a MIRIAD tasks for
# processing.
#
# Compatible classes should implement a getId () method, a
# getCombinedParams () method, and a getSingleParams () method

class SingleVisInput (object):    
    def __init__ (self, visdata, select=None, vid=None):
        self.visdata = visdata
        self.select = select
        self.vid = vid
        
        if not vid and not select:
            self.vid = os.path.split (self.visdata.base)[1]
        else:
            raise Exception ('need to give a nice ID for a single vis input '
                             'with a select argument')

    def getId (self):
        return self.vid

    def getCombinedParams (self):
        return {'vis': self.visdata.base, 'select': self.select}

    def getSingleParams (self):
        yield self.getCombinedParams ()
    
class MultiSourceVisInput (object):    
    def __init__ (self, source, vises, vid=None):
        self.source = source
        self.select = 'source(%s)' % (source, )
        self.vises = vises
        self.vid = vid or source

    def getId (self):
        return self.vid

    def getCombinedParams (self):
        vis = ','.join ((vis.base for vis in self.vises))
        return {'vis': vis, 'select': self.select}

    def getSingleParams (self):
        for vis in self.vises:
            yield {'vis': vis.base, 'select': self.select}

def explodeVisesBySource (vises, setid):
    """Take a list of VisData objects, and generate a set
    of MultiSourceVisInput objects, each of which looks at
    all of the VisData objects with only one of the sources
    select()ed. Basically, this remaps a list of vis files,
    each of which has several sources, into a list of sources,
    each of which has several vis files.

    Yields tuples of (source name, MultiSourceVisInput)"""

    sources = set ()

    for vis in vises:
        sources = sources.union (vis.sources ())

    for source in sources:
        yield (source, MultiSourceVisInput (source, vises, setid + '.' + source))

class VisData (miriad.MiriadData):
    def apply (self, task):
        task.vis = self
        task.run ()
    
    def xShow (self, source=None, **params):
        self.checkExists ()

        uvp = miriad.SmaUVPlot (vis=self.base, **params)
        if source: uvp.select = 'source(%s)' % source
        uvp.run ()

    def xShowPhaseCal (self, select=None, **params):
        self.checkExists ()

        gpp = miriad.TaskGPPlot (vis=self.base,
                                 nxy='4,2', yaxis='phase', yrange='-180,180',
                                 wrap=True)
        gpp.setArgs (**params)
        if select: gpp.select = select
        
        gpp.run ()

    def xShowAmpCal (self, delta=None, select=None, **params):
        self.checkExists ()

        gpp = miriad.TaskGPPlot (vis=self.base,
                                 nxy='4,2', yaxis='amp')
        gpp.setArgs (**params)
        if delta is not None: gpp.yrange = '%.2f,%.2f' % (1. - delta, 1. + delta)
        if select: gpp.select = select
        
        gpp.run ()

    def xClosure (self, **params):
        self.checkExists ()

        tc = miriad.TaskClosure (vis=self.base, nxy='4,2')
        tc.setArgs (**params)

        tc.run ()

    def xFlag (self, select, **params):
        self.checkExists ()

        tf = miriad.TaskUVFlag (vis=self.base, select=select, flagval='f')
        tf.setArgs (**params)

        tf.run ()
        for l in tf.proc.stdout:
            print '\t', l.strip ()

    def xSpectrum (self, **params):
        self.checkExists ()

        ts = miriad.SmaUVSpec (vis=self.base)
        ts.setArgs (**params)
        ts.run ()
        
    def sources (self):
        from re import compile
        
        sources = set ()
        regex = compile ('source +:([^ ]+)')
        
        uvl = miriad.TaskUVList (vis=self)
        uvl.launch ()
        
        for line in uvl.proc.stdout:
            line = line.strip ()
            match = regex.search (line)

            if not match: continue
            if 'vsource' in line: continue

            # Canonicalize source name
            
            src = match.groups()[0]
            if src == '0137+': src = '3c48'
            sources.add (src)

        uvl.proc.wait ()
        uvl.checkFail ()

        return sources

    # VisInput protocol

    def getId (self):
        return os.path.split (self.base)[1]

    def getCombinedParams (self):
        return {'vis': self.base}

    def getSingleParams (self):
        yield self.getCombinedParams ()

    # Utility

    def sourceInput (self, source):
        return SingleVisInput (self, 'select(%s)' % source,
                               self.getId () + '.' + source)
    
class ImageData (miriad.MiriadData):
    def apply (self, task):
        task.in_ = self
        task.run ()
    
    def xShow (self, kind='r', fov=None, **params):
        self.checkExists ()
        max, rms = self.getStats (kind)
        
        cgd = miriad.TaskCgDisp (**params)
        cgd.in_ = '%s,%s' % (self.base, self.base)
        cgd.type = 'contour,pix'
        cgd.labtyp = 'hms'
        cgd.beamtyp = 'b,l'
        cgd.wedge = True
        cgd.csize = '0.6,1'
        cgd.levs1 = '-4,-2,2,4,8,16,32'
        cgd.slev = 'a,%g' % (rms)
        if fov is not None:
            cgd.region = 'relcenter,arcsec,box(%d,%d,%d,%d)' % (fov, -fov, -fov, fov)
        cgd.run ()

    def xBasicShow (self, **params):
        self.checkExists ()
        cgd = miriad.TaskCgDisp (in_=self.base, labtyp='hms', beamtyp='b,l',
                                 **params)
        cgd.run ()

    def getStats (self, kind, **params):
        if kind == 'r': # raw
            (tmp, tmp, rms, max, tmp, tmp) = miriad.getImageStats (self, **params)
        elif kind == 'p': # point
            (max, rms) = miriad.fitImagePoint (self, **params)
        elif kind == 'g': # gaussian
            (max, xx, rms, xx, xx) = miriad.fitImageGaussian (self, **params)
        elif kind == 't': # gaussian total
            (xx, max, rms, xx, xx) = miriad.fitImageGaussian (self, **params)
        else:
            raise Exception ('Unknown stats type ' + kind)
        return max, rms
    
    def xShowFit (self, kind='p', fov=None, **params):
        self.checkExists ()

        model = self.makeVariant ('fitmodel', ImageData)
        if model.exists:
            raise Exception ('Model file %s already exists?' % model)
        
        imf = miriad.TaskImFit (in_=self, out=model, **params)
        if kind == 'p':
            imf.object = 'point'
        elif kind == 'g':
            imf.object = 'gaussian'
        elif kind == 'b':
            imf.object = 'beam'
        else:
            raise Exception ('Unknown fit kind ' + kind)

        imf.run ()
        
        cgd = miriad.TaskCgDisp (**params)
        cgd.in_ = '%s,%s' % (model, self.base)
        cgd.type = 'contour,pix'
        cgd.labtyp = 'hms'
        cgd.beamtyp = 'b,l'
        cgd.wedge = True
        cgd.csize = '0.6,1'
        #cgd.levs1 = '-4,-2,2,4,8,16,32'
        #cgd.slev = 'a,%g' % (rms)
        if fov is not None:
            cgd.region = 'relcenter,arcsec,box(%d,%d,%d,%d)' % (fov, -fov, -fov, fov)
        cgd.run ()
        model.delete ()
    
    def xShowFitResidual (self, kind='p', fov=None, **params):
        self.checkExists ()

        resid = self.makeVariant ('fitresid', ImageData)
        if resid.exists:
            raise Exception ('Resid file %s already exists?' % resid)
        
        imf = miriad.TaskImFit (in_=self, out=resid, residual=True, **params)
        if kind == 'p':
            imf.object = 'point'
        elif kind == 'g':
            imf.object = 'gaussian'
        elif kind == 'b':
            imf.object = 'beam'
        else:
            raise Exception ('Unknown fit kind ' + kind)

        imf.run ()
        
        cgd = miriad.TaskCgDisp (**params)
        cgd.in_ = resid
        cgd.type = 'pix'
        cgd.labtyp = 'hms'
        cgd.beamtyp = 'b,l'
        cgd.wedge = True
        cgd.csize = '0.6,1'
        if fov is not None:
            cgd.region = 'relcenter,arcsec,box(%d,%d,%d,%d)' % (fov, -fov, -fov, fov)
        cgd.run ()
        resid.delete ()
    
    def xStats (self, kind='r', **kwargs):
        from math import pi
        max, rms = self.getStats (kind, **kwargs)
        bmaj, bmin = miriad.getImageBeamSize (self)

        bmaj *= 3600 * 180 / pi
        bmin *= 3600 * 180 / pi
        
        print '      Max: %0.1lf sigma (%lg raw)' % (max / rms, max)
        print '      RMS: %lg raw' % (rms)
        print 'Beam Size: %.1lf arcsec x %.1lf arcsec' % (bmaj, bmin)
    
    def xContour (self, kind='r', **kwargs):
        max, rms = self.getStats (kind)

        tcg = miriad.TaskCgDisp (**kwargs)
        tcg.type = 'contour'
        tcg.in_ = self
        tcg.levs1 = '-2,2,4,8,16,32'
        tcg.slev = 'a,%g' % (rms)
        
        tcg.run ()

    # Example map.csh CGDISP command:
    #
    # cgdisp slev=p,1 in=m87-8000.cm,m87-8000.cm device=/xw
    #        labtyp=hms options=beambl,wedge,3value,mirr,full
    #        csize=0.6,1 olay=/l/pkwill/data/olay
    #        region=relcenter,arcsec,box(700,-700,-700,700)
    #        type=contour,pix slev=p,1 levs1=99


# Storage class implementations. Compatible ones should implement
# a get () method which returns a MiriadData of the appropriate @kind
# with @name somehow uniquifying the dataset within this storage
# system.

class DirStorage (object):
    def __init__ (self, dname):
        self.dname = dname

    def get (self, kind, name):
        if not isinstance (name, tuple): name = (name, )
        return kind (os.path.join (*((self.dname, ) + name)))

def loadDirGeneral (dir='.'):
    specfile = file (os.path.join (dir, 'dataspec.py'), 'r')
    items = {}

    exec specfile in items
    del specfile
    
    return DirStorage (dir), items

class Pipeline (object):
    lastTask = None
    
    def __init__ (self, plid):
        self.plid = plid

    def __repr__ (self):
        return '<%s %s>' % (self.__class__.__name__, self.plid)

    def __str__ (self):
        return self.plid
    
    def run (self, task, **kwargs):
        t = task (**kwargs)
        t.run ()
        self.lastTask = t

def execDir (dir='.', env='env.py'):
    import IPython.ipapi, types
    ipy = IPython.ipapi.get ()
    
    storage = DirStorage (dir)
    envfile = file (os.path.join (dir, env), 'r')
    items = {'storage': storage, 'miriad': miriad}

    exec envfile in items
    del envfile

    def defaultNames ():
        for (k, v) in items.iteritems ():
            if k[0] == '_': continue
            if isinstance (v, types.ModuleType): continue
            yield k

    keyiter = items.get ('__all__') or defaultNames ()

    print
    print 'Import summary of %s in %s:' % (env, dir)
    
    for k in keyiter:
        v = items[k]

        print ' * Imported \'%s\'' % (k, )
        ipy.user_ns[k] = v

_zapIter = None
_zapVar = 'q'

def zapStart (data, var='q'):
    global _zapIter, _zapVar
    _zapIter = iter (data)
    _zapVar = var
    zapNext ()

def zapNext ():
    global _zapIter, _zapVar

    if _zapIter is None:
        print 'Zap: need to zapStart with an iterable'
        return
    
    import IPython.ipapi
    ipy = IPython.ipapi.get ()

    try:
        item = _zapIter.next ()
        print 'Zap: %s = %s' % (_zapVar, item)
        ipy.user_ns[_zapVar] = item
    except StopIteration:
        print 'Zap: done'
        _zapIter = None

def zapReset ():
    global _zapIter
    _zapIter = None

# Recreatable flagging

class Flagger (object):
    def __init__ (self, src, destvar='af'):
        self.src = src
        self.dest = src.makeVariant (destvar, VisData)
        self.histname = str (src) + '.flaghist'
        self.ops = []

        if self.hasHistory ():
            self.loadfile (self.histname)

    def hasHistory (self):
        return os.path.exists (self.histname)
    
    def loadfile (self, fname):
        for l in file (fname, 'r'):
            l = l.strip ()
            if len (l) == 0: continue
            
            sel, line, flag, comment = l.split ('###')
            self.ops.append ((sel, line, bool (flag), comment))

    def apply (self):
        # Write out history file
        
        f = file (self.histname, 'w')

        for tup in self.ops:
            print >>f, '###'.join ([str (x) for x in tup])

        f.close ()

        # Actually regenerate dest.
        
        self.dest.delete ()

        miriad.TaskUVCat (vis=self.src, out=self.dest, nocal=True,
                          nopass=True, nopol=True).run ()
        
        for sel, line, flag, comment in self.ops:
            if flag: flagval = 'f'
            else: flagval = 'u'

            if sel == '': sel = None
            if line == '': line = None
            
            miriad.TaskUVFlag (vis=self.dest, select=sel,
                               line=line, flagval=flagval, brief=True).run ()

    def flag (self, select, comment, flag=True):
        self.ops.append ((select, '', flag, comment))

    def flagChans (self, select, chstart, chlen, comment, flag=True):
        """Flag the only certain channels in the given selection:
        flagChans (select, chstart, chlen, comment)."""

        line = 'chan,%d,%d' % (chlen, chstart)
        self.ops.append ((select, line, flag, comment))

    def smallUV (self):
        self.flag ('uvrange(0,0.1)', 'Flag UV distances less than 0.1 klambda.')
