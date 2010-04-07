#! /usr/bin/env python

"""amprfi - Interactive tool for finding RFI by summing spectra

We find RFI by summing spectra and searching for amplitude spikes.

This documentation is wildly insufficient.

Note that this is not a standalone script, but a module that should
be imported into IPython and used interactively."""

import numpy as N
import miriad
from mirexec import TaskUVCal
import os.path

widthLimit = 30

class AmpFlagsAccum (object):
    def __init__ (self):
        self._clear ()

    def _clear (self):
        self.data = self.flags = self.times = self.dsq = None
        self.maxnchan = 0

    def _accum (self, tup):
        inp, preamble, data, flags, nread = tup
        inttime = inp.getVarFirstFloat ('inttime', 10.0)

        self.maxnchan = max (self.maxnchan, nread)

        data = N.abs (data[0:nread] * inttime)
        times = N.zeros (nread) + inttime

        w = N.where (flags[0:nread] == 0)
        data[w] = 0.
        times[w] = 0.

        if self.data is None:
            self.data = data.copy ()
            self.dsq = data**2
            self.times = times.copy ()
        else:
            self.data += data
            self.dsq += data**2
            self.times += times
            
    def process (self, dset, **kwargs):
        from mirtask.util import decodeBaseline
        #from mirtask.uvdat import getPol
        #thepol = None
        
        for tup in dset.readLowlevel (False, nopass=True, nocal=True, nopol=True):
            ant1, ant2 = decodeBaseline (tup[1][4])
            #pol = getPol ()
            
            if ant1 == ant2: continue

            #if thepol is None:
            #    thepol = pol
            #elif pol != thepol:
            #    raise Exception ('Must have single-polarization input!')
            
            self._accum (tup)

    def done (self):
        w = N.where (self.times > 0.)
        ch = w[0]
        
        self.ch = ch
        self.y = self.data[w] / self.times[w]
        self.ystd = N.sqrt (self.dsq[w] / self.times[w] - self.y**2)

class AmpRfi (object):
    def setupNext (self, vises, fname, freq, noshow=False, **kwargs):
        self.vises = vises
        self.fname = fname
        self.freq = freq
        
        self._yBounds = None
        
        print 'Working on freq %04d' % freq

        afa = AmpFlagsAccum ()
        any = False
        
        for v in self.vises:
            if not v.exists: continue
            if len (kwargs) ==  0: print 'Reading %s ...' % v
            else:
                kws = ' '.join ('%s=%s' % x for x in kwargs.iteritems ())
                print 'Reading %s with %s...' % (v, kws)
            any = True
            afa.process (v, **kwargs)

        if not any:
            print 'No actual data for this!'
            return
        
        afa.done ()

        if os.path.exists (self.fname):
            print
            print '!!!! Results file %s already exists' % self.fname
            print
        
        self.ch, self.y = afa.ch, afa.y
        self.maxnchan = afa.maxnchan

        if self.y.size == 0:
            print 'All data flagged for this!'
            return
        
        self.suggFlag (noshow=noshow)

    def plotRaw (self):
        from omega import quickXY
        return quickXY (self.ch, self.y)

    def showRaw (self):
        self.rawPlot = self.plotRaw ().show ('amprfi-raw')
        
    def suggFlag (self, mfactor=15, boxcar=1, noshow=False):
        deltas = self.y[1:] - self.y[:-1]

        if boxcar > 1:
            # Boxcar averaging will kill narrow spikes, since the large
            # plus and minus deltas add to about zero. So don't do this
            # by default.
            deltas = N.convolve (deltas, N.ones (boxcar) / boxcar, 'same')
        
        cutoff = mfactor * N.median (N.abs (deltas))

        self.mfactor = mfactor
        self.boxcar = boxcar
        
        S_INOK, S_ENTERING, S_LEAVING = range (0, 3)
        state = S_INOK
        toFlag = []
    
        for i in xrange (0, len (deltas)):
            if state == S_INOK:
                if deltas[i] > cutoff:
                    state = S_ENTERING
                    flagBeginChan = self.ch[i]
                    beganRising = True
                elif deltas[i] < -cutoff:
                    state = S_ENTERING
                    flagBeginChan = self.ch[i]
                    beganRising = False
            elif state == S_ENTERING:
                if beganRising and deltas[i] < -cutoff:
                    state = S_LEAVING
                elif not beganRising and deltas[i] > cutoff:
                    state = S_LEAVING
            elif state == S_LEAVING:
                if (beganRising and deltas[i] > -cutoff) or \
                       (not beganRising and deltas[i] < cutoff):
                    state = S_INOK
                        
                    if self.ch[i+1] - flagBeginChan > widthLimit:
                        print '!!! very wide:', flagBeginChan, self.ch[i+1], '; i =', i
                    
                    toFlag.append ((flagBeginChan, self.ch[i+1])) # widen out the flag zone
        
        if state != S_INOK:
            print '!!! Uneven number of edges detected! Try bigger mfactor in suggFlag'
        
        self.toFlagSugg = toFlag
        self.mergeRegions (noshow=noshow)

    def suggestYCutoff (self, cutoff):
        self.toFlagSugg = [(ch, ch) for ch in self.ch[N.where (self.y > cutoff)]]
        self.mergeRegions ()
    
    def plotDeltas (self, boxcar=1, ylim=None):
        from omega import quickXY

        deltas = self.y[1:] - self.y[:-1]
        if boxcar > 1:
            deltas = N.convolve (deltas, N.ones (boxcar) / boxcar, 'same')
        my = self.mfactor * N.median (N.abs (deltas))
        p = quickXY (self.ch[0:-1], deltas, 'Deltas')
        p.addXY ((0, self.maxnchan), (my, my), '+MFactor')
        p.addXY ((0, self.maxnchan), (-my, -my), '-MFactor')

        if ylim is not None:
            p.setBounds (None, None, -ylim, ylim)
        
        return p
    
    def _mergeImpl (self, flaglist, pad):
        # Assume channel numbers here are all 0-indexed
        merged = []

        for bound in flaglist:
            bmin = max (0, bound[0] - pad)
            bmax = min (self.maxnchan - 1, bound[1] + pad)
            startIdx = -1
            endIdx = -1

            # Find the parts of the merged list that we overlap or subsume
            
            for i in xrange (0, len (merged)):
                mmin, mmax = merged[i]

                if mmax < bmin: continue
            
                if mmin > bmax:
                    endIdx = i - 1
                    break
                
                if startIdx == -1:
                    startIdx = i

            #print 'm', merged
            
            if startIdx == -1 and endIdx == -1:
                #print 'creating new entry', bmin, bmax
                # We're off the end of the list one one side or the other
                if len (merged) == 0 or bmax < merged[0][0]:
                    merged.insert (0, (bmin, bmax))
                else:
                    merged.append ((bmin, bmax))
            elif endIdx == -1:
                # We overwrite the last entry.
                bmin = min (bmin, merged[-1][0])
                bmax = max (bmax, merged[-1][1])
                merged[-1] = (bmin, bmax)
            else:
                #print 'inserting into middle', startIdx, endIdx, bmin, bmax
                bmin = min (bmin, merged[startIdx][0])
                bmax = max (bmax, merged[endIdx][1])
                del merged[startIdx:endIdx+1]
                merged.insert (startIdx, (bmin, bmax))

        return merged
    
    def mergeRegions (self, pad=4, noshow=False):
        self.pad = pad
        self.toFlag = self._mergeImpl (self.toFlagSugg, pad)
        if not noshow:
            self.show ()

    def plot (self, merged=True):
        from omega.rect import RectPlot, XBand
        p = RectPlot ()

        if merged: set = self.toFlag
        else: set = self.toFlagSugg
        
        for bound in self.toFlag:
            r = XBand (*bound)
            p.add (r)

        p.addXY (self.ch, self.y, None)

        if self._yBounds is None:
            p.setBounds (0, self.maxnchan)
        else:
            p.setBounds (0, self.maxnchan, self._yBounds[0], self._yBounds[1])
        return p

    def show (self):
        self.p = self.plot ().show ('amprfi')

    def ybounds (self, ymin, ymax):
        self._yBounds = (ymin, ymax)
        self.p.setBounds (ymin=ymin, ymax=ymax)
    
    def write (self, extraCond=None):
        if len (self.toFlag) == 0:
            print 'Nothing to write, skipping'
            return
        
        f = file (self.fname, 'w')
        print 'Writing %s ...' % self.fname

        print >>f, '# amprfi %d %d %d' % (self.mfactor, self.boxcar, self.pad)

        if extraCond is None: cstr = ''
        else: cstr = str (extraCond) + ' '
        
        def makeChans ():
            for bound in self.toFlag:
                start = bound[0] + 1 # convert to 1-based
                num = bound[1] - bound[0]
                yield '%d,%d' % (num, start)

        print >>f, cstr + 'freq=%04d chan=%s' \
              % (self.freq, ';'.join (makeChans ()))

        f.close ()

def vglob (match):
    from glob import glob
    for p in glob (match):
        yield miriad.VisData (p)

__all__ = ['AmpRfi', 'vglob']

if __name__ == '__main__':
    import sys, IPython
    
    if len (sys.argv) < 4:
        print 'Usage: %s flagfile freq vis1 ...' % sys.argv[0]
        sys.exit (0)

    flags, freq = sys.argv[1], int (sys.argv[2])
    vises = [miriad.VisData (x) for x in sys.argv[3:]]
    
    a = AmpRfi ()
    a.setupNext (vises, flags, freq, noshow=True)

    ns = {'a': a, 'vises': vises, 'freq': freq, 'fname': flags}
    sys.argv = [sys.argv[0], '-gthread']
    sh = IPython.Shell.start (ns)
    print 'AmpRfi instance is in variable "a". Exit to write'
    sh.mainloop ('')
    print 'Writing to', flags, '...'
    a.write ()
    sys.exit (0)
