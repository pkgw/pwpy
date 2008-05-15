#! /usr/bin/env python

"""amprfi - Interactive tool for finding RFI by summing spectra

We find RFI by summing spectra and searching for amplitude spikes.

This documentation is wildly insufficient.

Note that this is not a standalone script, but a module that should
be imported into IPython and used interactively."""

from bbs import *
import omega
from mirexec import TaskUVCal
import os.path

widthLimit = 30

class AmpFlagsAccum (object):
    def __init__ (self):
        self._clear ()

    def _clear (self):
        self.data = self.flags = self.times = None

    def _accum (self, tup):
        inp, preamble, data, flags, nread = tup
        inttime = inp.getVarFirstFloat ('inttime', 10.0)
        
        data = N.abs (data[0:nread] * inttime)
        times = N.zeros (nread) + inttime

        w = N.where (flags[0:nread] == 0)
        data[w] = 0.
        times[w] = 0.

        if self.data is None:
            self.data = data.copy ()
            self.times = times.copy ()
        else:
            self.data += data
            self.times += times
            
    def process (self, dset):
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

class AmpRfi (object):
    def setupNext (self, vises, fname, freq, half):
        self.vises = vises
        self.fname = fname
        self.freq = freq
        self.half = half

        print 'Working on freq %04d half %d' % (freq, half)

        afa = AmpFlagsAccum ()
        any = False
        
        for v in self.vises:
            if not v.exists: continue
            print 'Reading %s ...' % v
            any = True
            afa.process (v)

        if not any:
            print 'No actual data for this!'
            return
        
        afa.done ()

        if os.path.exists (self.fname):
            print
            print '!!!! Results file %s already exists' % self.fname
            print
        
        self.ch, self.y = afa.ch, afa.y
        self.manualFlag = []
        self.suggFlag ()

    def plotRaw (self):
        return omega.quickXY (self.ch, self.y)

    def showRaw (self):
        self.rawPlot = self.plotRaw ().show ('amprfi-raw')
        
    def manualFlag (self, start, num):
        self.manualFlag.append ((start, start + num))
        
    def suggFlag (self, mfactor=15, boxcar=1):
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
        self.mergeRegions ()
        
    def plotDeltas (self, boxcar=1, ylim=None):
        deltas = self.y[1:] - self.y[:-1]
        if boxcar > 1:
            deltas = N.convolve (deltas, N.ones (boxcar) / boxcar, 'same')
        my = self.mfactor * N.median (N.abs (deltas))
        p = omega.quickXY (self.ch[0:-1], deltas, 'Deltas')
        p.addXY ((0, 512), (my, my), '+MFactor')
        p.addXY ((0, 512), (-my, -my), '-MFactor')

        if ylim is not None:
            p.setBounds (None, None, -ylim, ylim)
        
        return p
    
    def _mergeImpl (self, flaglist, pad):
        # Assume channel numbers here are all 0-indexed
        merged = []

        for bound in flaglist:
            bmin = max (0, bound[0] - pad)
            bmax = min (numChans - 1, bound[1] + pad)

            for i in xrange (0, len (merged)):
                mmin, mmax = merged[i]

                if mmax < bmin: continue
            
                if mmin > bmax:
                    # We need to insert a new entry here
                    merged.insert (i, (bmin, bmax))
                    break

                newmin = min (mmin, bmin)
                newmax = max (mmax, bmax)
                merged[i] = (newmin, newmax)
                break
            else:
                merged.append ((bmin, bmax))

        return merged
    
    def mergeRegions (self, pad=2):
        self.pad = pad
        self.toFlag = self._mergeImpl (self.toFlagSugg, pad)
        self.show ()

    def plot (self, merged=True):
        import omega.rect
        p = self.plotRaw ()

        if merged: set = self.toFlag
        else: set = self.toFlagSugg
        
        for bound in self.toFlag:
            r = omega.rect.XBand (*bound)
            p.add (r)

        return p

    def show (self):
        self.p = self.plot ().show ('amprfi')
        
    def write (self):
        f = file (self.fname, 'w')
        print 'Writing %s ...' % self.fname

        print >>f, '# amprfi %d %d %d' % (self.mfactor, self.boxcar, self.pad)
        print >>f, '!%04d---%d---' % (self.freq, self.half)
        
        for bound in self.toFlag:
            start = bound[0] + 1 # convert to 1-based
            num = bound[1] - bound[0]
            print >>f, '---chan,%d,%d---f' % (num, start)

        f.close ()

class WorkRfi (AmpRfi,FlagWork):
    def __init__ (self):
        FlagWork.__init__ (self)
        
        try: os.mkdir (self.fdata)
        except OSError: pass

        self.fh = None
        self.byfh = byfh = {}

        for pol in 'xx', 'yy':
            for vis in self.raws:
                fh = (vis.freq, vis.half)

                if fh in byfh: byfh[fh].append (vis.fxcal (pol, False))
                else: byfh[fh] = [vis.fxcal (pol, False)]
        
        print 'Run runFxcals () to create the fxcaled bypol datasets'
        print 'Or doNext () to get going.'
        print 'Or pruneDone () to skip redoing FHs that have already been flagged.'

    def runFxcals (self):
        self.makeFxs (True, True)
    
    def pruneDone (self):
        toprune = []

        for fh in self.byfh.iterkeys ():
            f = '%s/amprfi-%04d-%d.flags' % ((self.fdata, ) + fh)

            if os.path.exists (f): toprune.append (fh)

            any = False
            for vis in self.byfh[fh]:
                any = any or vis.exists

            if not any: toprune.append (fh)

        if len (toprune) == 0: return

        print 'Already done:'
        
        for fh in toprune:
            print '   %04d %d' % fh
            del self.byfh[fh]

    def doNext (self, fh=None):
        if self.fh is not None: self.write ()
        self.skipNext (fh)
        
    def skipNext (self, fh=None):
        if len (self.byfh) == 0:
            print 'No more to do'
            return

        if fh is None:
            fh = self.byfh.keys ()[0]

        self.fh = fh
        vises = self.byfh[fh]
        del self.byfh[fh]

        fname = '%s/amprfi-%04d-%d.flags' % ((self.fdata, ) + fh)

        self.setupNext (vises, fname, fh[0], fh[1])

__all__ = ['AmpRfi', 'WorkRfi']
