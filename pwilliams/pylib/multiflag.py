#! /usr/bin/env python
"""A flagging script"""
#* multiflag - Apply complex flagging operations to UV data in one pass.
#& pkgw
#: calibration, uv analysis
#+
#  MULTIFLAG changes the flags embedded in visibility data. Unlike UVFLAG,
#  blah blah.
#-

import sys
from mirtask import uvdat, keys, util
import numpy as N

class Condition (object):
    __slots__ = ['isSubRecord']

    def __init__ (self, isSubRecord):
        self.isSubRecord = isSubRecord

    def matchRecord (self, inp, uvw, time, bl):
        # This function works as an AND with to-flagness:
        # return True if you DO match this record.
        raise NotImplementedError ()

    def matchSubRecord (self, inp, uvw, time, bl, data, flags):
        # This function works as an OR with flags: set flags[x]
        # to 1 for all X that you do NOT match.
        raise NotImplementedError ()

    def formatParams (self):
        # Return a string-formatted version of your parameters
        # or None
        raise NotImplementedError ()
        

class CAnt (Condition):
    __slots__ = ['ants']
    
    def __init__ (self, paramstr):
        Condition.__init__ (self, False)
        self.ants = set (int (x) for x in paramstr.split (','))

    def matchRecord (self, inp, uvw, time, bl):
        return bl[0] in self.ants or bl[1] in self.ants

    def formatParams (self):
        return ','.join (str (x) for x in self.ants)
    
class CBaseline (Condition):
    __slots__ = ['bls']
    
    def __init__ (self, paramstr):
        Condition.__init__ (self, False)

        def blParse (s):
            a1, a2 = s.split ('-')
            a1, a2 = int (a1), int (a2)
            if a1 > a2: return (a2, a1)
            return (a1, a2)
        
        self.bls = set (blParse (s) for s in paramstr.split (','))

    def matchRecord (self, inp, uvw, time, bl):
        return bl in self.bls

    def formatParams (self):
        return ','.join ('%d-%d' % x for x in self.bls)

class CPol (Condition):
    __slots__ = ['pols']
    
    def __init__ (self, paramstr):
        Condition.__init__ (self, False)

        self.pols = set (util.polarizationNumber (s) for s in paramstr.split (','))

    def matchRecord (self, inp, uvw, time, bl):
        return uvdat.getPol () in self.pols

    def formatParams (self):
        return ','.join (util.polarizationName (p) for p in self.pols)

class CAuto (Condition):
    __slots__ = []

    def __init__ (self, paramstr):
        Condition.__init__ (self, False)
        assert (paramstr is None)

    def matchRecord (self, inp, uvw, time, bl):
        return bl[0] == bl[1]

    def formatParams (self): return None

class CCross (Condition):
    __slots__ = []

    def __init__ (self, paramstr):
        Condition.__init__ (self, False)
        assert (paramstr is None)

    def matchRecord (self, inp, uvw, time, bl):
        return bl[0] != bl[1]

    def formatParams (self): return None

class CFreq (Condition):
    __slots__ = ['freqs']

    def __init__ (self, paramstr):
        Condition.__init__ (self, False)
        self.freqs = [float (x) for x in paramstr.split (',')]

    def matchRecord (self, inp, uvw, time, bl):
        freq = inp.getVarDouble ('freq') * 1000 # convert to MHz

        for f in self.freqs:
            if abs (freq - f) / f < 0.005:
                return True

        return False

    def formatParams (self):
        return ','.join (str (x) for x in self.freqs)
    
def mergeChannels (chanlist):
    # Assume channel numbers here are all 0-indexed
    merged = []

    for bmin, bmax in chanlist:
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
    
class CChannel (Condition):
    __slots__ = ['intervals']

    def __init__ (self, paramstr):
        Condition.__init__ (self, True)

        def chParse (x):
            n, s = x.split (',')
            n, s = int (n), int (s)
            s -= 1 # FORTRAN-style indices to C-style
            return (s, s+n)

        chinfo = mergeChannels (chParse (s) for s in paramstr.split (';'))
        iStart = 0
        self.intervals = intervals = []
        
        for start, end in chinfo:
            iEnd = start

            if iEnd > iStart: intervals.append ((iStart, iEnd))

            iStart = end

        intervals.append ((iStart, -1))
        
    def matchSubRecord (self, inp, uvw, time, bl, data, flags):
        for (start, end) in self.intervals:
            if end == -1: flags[start:] = 1
            else: flags[start:end] = 1

    def formatParams (self):
        def getChans ():
            lastEnd = None

            for start, end in self.intervals:
                if lastEnd is not None:
                    s = lastEnd + 1
                    n = start - lastEnd
                    yield n, s
                lastEnd = end

        return ';'.join ('%d,%d' % x for x in getChans ())

class CATAHalf (Condition):
    __slots__ = ['half']

    def __init__ (self, paramstr):
        Condition.__init__ (self, False)
        self.half = int (paramstr)
        assert (self.half == 1 or self.half == 2)

    def matchRecord (self, inp, uvw, time, bl):
        freq = inp.getVarDouble ('freq')
        sfreq = inp.getVarDouble ('sfreq')

        if freq == sfreq: half = 2
        elif abs (freq - sfreq - 0.0524288) < 0.001: half = 1
        else: assert (False), 'ATA corr half unknown!'

        return half == self.half

    def formatParams (self): return str (self.half)

class CTime (Condition):
    __slots__ = ['tStart', 'tEnd']

    def __init__ (self, paramstr):
        Condition.__init__ (self, False)

        # We attempt to match the semantics of the time(a,b)
        # select command here. Except time(fulldate) matches
        # anything between fulldate and fulldate+24hours,
        # whereas we match anything after fulldate. I have
        # never used time(fulldate).
        
        st, end = paramstr.split (',')

        if st == '': self.tStart = None
        else: self.tStart = util.dateOrTimeToJD (st)

        if end == '': self.tEnd = None
        else: self.tEnd = util.dateOrTimeToJD (end)

        if self.tStart is not None and self.tEnd is not None:
            if max (self.tStart, self.tEnd) > 1 and \
               min (self.tStart, self.tEnd) < 1:
                assert (False), 'Cannot mix full and offset time specifications!'

    def matchRecord (self, inp, uvw, time, bl):
        ts, te = self.tStart, self.tEnd
        
        ofs = time - int (time - 1) - 0.5
        
        if ts is not None:
            if ts < 1:
                if ofs < ts: return False
            elif time < ts: return False

        if te is not None:
            if te < 1:
                if ofs > te: return False
            elif time > te: return False

        return True

    def formatParams (self):
        def tostr (jd):
            if jd is None: return ''
            elif jd > 1: return util.jdToFull (jd)

            from math import floor
            jd *= 24
            hours = floor (jd)
            jd = 60 * (jd - hours)
            mins = floor (jd)
            secs = (jd - mins) * 60

            if secs >= 0.05:
                return '%02d:%02d:%3.1f' % (hours, mins, secs)

            return '%02d:%02d' % (hours, mins)
            
        return '%s,%s' % (tostr (self.tStart), tostr (self.tEnd))

conditions = {
    'ant': CAnt, 'bl': CBaseline, 'pol': CPol,
    'auto': CAuto, 'cross': CCross, 'chan': CChannel,
    'atahalf': CATAHalf, 'freq': CFreq, 'time': CTime
    }

names = {}

for name, cls in conditions.iteritems (): names[cls] = name

class Line (object):
    __slots__ = ['rconds', 'srconds', 'matches', '_formatted']
    
    def __init__ (self):
        self.rconds = []
        self.srconds = []
        self.matches = 0
        self._formatted = None

    def add (self, cond):
        if cond.isSubRecord:
            self.srconds.append (cond)
        else:
            self.rconds.append (cond)

    def clearStats (self): self.matches = 0

    def format (self):
        if self._formatted is not None: return self._formatted

        def cformat (cond):
            name = names[cond.__class__]
            params = cond.formatParams ()

            if params is None: return name
            return name + '=' + params
            
        def conds ():
            for c in self.rconds: yield cformat (c)
            for c in self.srconds: yield cformat (c)

        self._formatted = ' '.join (conds ())
        return self._formatted
    
    def anySubRecord (self):
        return len (self.srconds) > 0
    
    def matchRecord (self, inp, uvw, time, bl):
        for c in self.rconds:
            if not c.matchRecord (inp, uvw, time, bl):
                return False
        self.matches += 1
        return True

    def matchSubRecord (self, inp, uvw, time, bl, data, flags):
        if not self.matchRecord (inp, uvw, time, bl):
            return False

        #print 'srb', matched[0:10]
        for c in self.srconds:
            c.matchSubRecord (inp, uvw, time, bl, data, flags)
        self.matches += 1 # the best we can reasonably do...
        #print 'sra', matched[0:10]
        return True

# The actual multiflag implementation ...

class MultiFlag (object):
    def __init__ (self):
        self.rLines = []
        self.srLines = []
        self.nR = self.nSR = self.nSeen = 0
        self.lineFlags = None
        
    # Read in the conditions
    #
    # The basic format is line-oriented
    # If an entry matches a line, it is flagged.
    # An entry matches a line if it matches *all* of the conditions in the line
    # A condition in a line just looks like "attr=match"
    # Conditions are separated by spaces
    # If there are multiple match values, a condition is matched if *any* of those
    # values are matched
    # So the overall logical flow is
    #  flag if [match any line]
    #  match line if [match every condition]
    #  match condition if [match any value]
    #
    # E.g. ...
    #
    # ant=24 pol=xx
    # bl=1-4 cross
    # pol=xx chan=128,1

    def loadSpec (self, fname):
        for l in file (fname, 'r'):
            bits = l.strip ().split ()

            if len (bits) < 1: continue
            if bits[0][0] == '#': continue

            thisLine = Line ()

            for b in bits:
                split = b.split ('=', 2)
                if len (split) == 1: cond, arg = split[0], None
                else: cond, arg = split

                thisLine.add (conditions[cond] (arg))

            if thisLine.anySubRecord (): self.srLines.append (thisLine)
            else: self.rLines.append (thisLine)

    def numLines (self): return len (self.rLines) + len (self.srLines)

    def applyVis (self, inp, preamble, data, flags, nread):
        self.nSeen += 1
        lineFlags = self.lineFlags
        data = data[0:nread]
        flags = flags[0:nread]

        uvw = preamble[0:3]
        time = preamble[3]
        bl = util.decodeBaseline (preamble[4])

        hit = False
        for line in self.rLines:
            if line.matchRecord (inp, uvw, time, bl):
                hit = True
                break

        if hit:
            self.nR += 1
            flags.fill (0)
        elif len (self.srLines) > 0:
            if lineFlags is None or lineFlags.shape != flags.shape:
                self.lineFlags = lineFlags = flags.copy ()

            for line in self.srLines:
                lineFlags.fill (0)
                if line.matchSubRecord (inp, uvw, time, bl, data, lineFlags):
                    # Only do the op if this line matched some parts (ie,
                    # marked some channels for flagging)
                    flags &= lineFlags
            
            nUnflagged = flags.sum ()

            if nUnflagged == 0:
                self.nR += 1
            elif nUnflagged < flags.size:
                self.nSR += 1
        
        inp.rewriteFlags (flags)

    def doneFile (self, inp):
        nR, nSR, nSeen = self.nR, self.nSR, self.nSeen
        
        print '   %d of %d (%.1f%%) are now completely flagged' % (nR, nSeen,
                                                                   100. * nR / nSeen)
        print '   %d of %d (%.1f%%) are now partially flagged' % (nSR, nSeen,
                                                                  100. * nSR / nSeen)

        inp.openHistory ()
        inp.writeHistory ('MULTIFLAG: %d of %d (%.1f%%) are now completely flagged' \
                          % (nR, nSeen, 100. * nR / nSeen))
        inp.writeHistory ('MULTIFLAG: %d of %d (%.1f%%) are now partially flagged' \
                          % (nSR, nSeen, 100. * nSR / nSeen))
        inp.writeHistory ('MULTIFLAG: Hit stats of normalized conditions:')

        for line in self.rLines:
            inp.writeHistory ('MULTIFLAG:   %s : %d' % (line.format (), line.matches))
        for line in self.srLines:
            inp.writeHistory ('MULTIFLAG:   %s : %d' % (line.format (), line.matches))

        inp.closeHistory ()

        for line in self.rLines: line.clearStats ()
        for line in self.srLines: line.clearStats ()
    
    def applyUvdat (self, banner):
        curInp = None

        for inp, preamble, data, flags, nread in uvdat.readAll ():
            if inp is not curInp:
                if curInp is not None:
                    self.doneFile (curInp)

                curInp = inp
                inp.openHistory ()
                inp.writeHistory (banner)
                inp.logInvocation ('MULTIFLAG')
                inp.closeHistory ()

                nR = nSR = nSeen = 0

                print inp.name, '...'

            self.applyVis (inp, preamble, data, flags, nread)
        
        # Need to reopen the dataset to be able to get back to the history.
        # Not too elegant, but life goes on.
        curInp = curInp.refobj.open ('r')
        self.doneFile (curInp)
        curInp.close ()

    def applyDataSet (self, dset, banner):
        first = True
        
        for inp, preamble, data, flags, nread in dset.readLowlevel (False):
            if first:
                inp.openHistory ()
                inp.writeHistory (banner)
                inp.logInvocation ('MULTIFLAG')
                inp.closeHistory ()

                nR = nSR = nSeen = 0
                first = False

            self.applyVis (inp, preamble, data, flags, nread)
        
        # Need to reopen the dataset to be able to get back to the history.
        # Not too elegant, but life goes on.
        inp = dset.open ('r')
        self.doneFile (inp)
        inp.close ()

def task ():
    print 'This script is UNFINISHED and EXPERIMENTAL!!!!'

    banner = 'MULTIFLAG (Python): UV data multiflagger $Id$'
    print banner

    keys.keyword ('spec', 'f', ' ', 128)
    keys.doUvdat ('3', False)
    opts = keys.process ()

    if len (opts.spec) < 1:
        print >>sys.stderr, 'Error: must give at least one "spec" filename'
        sys.exit (1)

    mf = MultiFlag ()
    
    for fname in opts.spec: mf.loadSpec (fname)

    print 'Parsed %d condition lines from %d file(s).' % (mf.numLines (),
                                                          len (opts.spec))

    mf.applyUvdat (banner)

if __name__ == '__main__':
    task ()
    sys.exit (0)
