#! /usr/bin/env python
"""= multiflag - Apply many kinds of flags to UV data.
& pkgw
: calibration
+
 This task is a work in progress. Use MULTIFLAG2 instead.
--
"""

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

    def __hash__ (self): raise NotImplementedError ()

    def __eq__ (self, other): raise NotImplementedError ()
        
class VarCondition (Condition):
    """A condition whose result is solely dependent upon the value of
    a UV variable."""

    __slots__ = ['varname', 'vartype', 'ctxt']

    V_STRING = 0
    V_INT = 1
    V_FLOAT = 2
    V_DOUBLE = 3
    V_COMPLEX = 4
    
    def __init__ (self, varname, vartype):
        Condition.__init__ (self, False)
        self.varname = varname
        self.vartype = vartype

    def register (self, ctxt):
        ctxt.addVar (self.varname, self.vartype)
        self.ctxt = ctxt
        
    def matchRecord (self, inp, uvw, time, bl):
        return self.matchVar (self.ctxt.getVar (self.varname))
    
    def matchVar (self, var):
        raise NotImplementedError ()

class CAnt (Condition):
    __slots__ = ['ants']
    
    def __init__ (self, paramstr):
        Condition.__init__ (self, False)
        self.ants = frozenset (int (x) for x in paramstr.split (','))

    def matchRecord (self, inp, uvw, time, bl):
        return bl[0] in self.ants or bl[1] in self.ants

    def formatParams (self):
        return ','.join (str (x) for x in self.ants)

    def __hash__ (self): return hash (self.ants)

    def __eq__ (self, other):
        return isinstance (other, CAnt) and self.ants == other.ants
    
class CBaseline (Condition):
    __slots__ = ['bls']
    
    def __init__ (self, paramstr):
        Condition.__init__ (self, False)

        def blParse (s):
            a1, a2 = s.split ('-')
            a1, a2 = int (a1), int (a2)
            if a1 > a2: return (a2, a1)
            return (a1, a2)
        
        self.bls = frozenset (blParse (s) for s in paramstr.split (','))

    def matchRecord (self, inp, uvw, time, bl):
        return bl in self.bls

    def formatParams (self):
        return ','.join ('%d-%d' % x for x in self.bls)

    def __hash__ (self): return hash (self.bls)

    def __eq__ (self, other):
        return isinstance (other, CBaseline) and self.bls == other.bls

class CPol (VarCondition):
    __slots__ = ['pols']
    
    def __init__ (self, paramstr):
        VarCondition.__init__ (self, 'pol', VarCondition.V_INT)

        self.pols = frozenset (util.polarizationNumber (s) for s in paramstr.split (','))

    def matchVar (self, value):
        return value in self.pols

    def formatParams (self):
        return ','.join (util.polarizationName (p) for p in self.pols)

    def __hash__ (self): return hash (self.pols)

    def __eq__ (self, other):
        return isinstance (other, CPol) and self.pols == other.pols

class CAuto (Condition):
    __slots__ = []

    def __init__ (self, paramstr):
        Condition.__init__ (self, False)
        assert (paramstr is None)

    def matchRecord (self, inp, uvw, time, bl):
        return bl[0] == bl[1]

    def formatParams (self): return None

    def __hash__ (self): return 0

    def __eq__ (self, other):
        return isinstance (other, CAuto)

class CCross (Condition):
    __slots__ = []

    def __init__ (self, paramstr):
        Condition.__init__ (self, False)
        assert (paramstr is None)

    def matchRecord (self, inp, uvw, time, bl):
        return bl[0] != bl[1]

    def formatParams (self): return None

    def __hash__ (self): return 0

    def __eq__ (self, other):
        return isinstance (other, CCross)

class CFreq (VarCondition):
    __slots__ = ['freqs']

    def __init__ (self, paramstr):
        VarCondition.__init__ (self, 'freq', VarCondition.V_DOUBLE)
        self.freqs = frozenset (float (x) for x in paramstr.split (','))

    def matchVar (self, val):
        freq = val * 1000 # convert to MHz

        for f in self.freqs:
            if abs (freq - f) / f < 0.005:
                return True

        return False

    def formatParams (self):
        return ','.join (str (x) for x in self.freqs)

    def __hash__ (self): return hash (self.freqs)

    def __eq__ (self, other):
        return isinstance (other, CFreq) and self.freqs == other.freqs
    
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

    def __hash__ (self):
        h = 0
        for p in self.intervals: h ^= hash (p)
        return h

    def __eq__ (self, other):
        if not isinstance (other, CChannel): return False

        if len (self.intervals) != len (other.intervals): return False

        for p1, p2 in zip (self.intervals, other.intervals):
            if p1 != p2: return False

        return True

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

    def __hash__ (self): return hash (self.half)

    def __eq__ (self, other):
        return isinstance (other, CATAHalf) and self.half == other.half

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

    def __hash__ (self): return hash (self.tStart) ^ hash (self.tEnd)

    def __eq__ (self, other):
        return isinstance (other, CTime) and self.tStart == other.tStart \
               and self.tEnd == other.tEnd

conditions = {
    'ant': CAnt, 'bl': CBaseline, 'pol': CPol,
    'auto': CAuto, 'cross': CCross, 'chan': CChannel,
    'atahalf': CATAHalf, 'freq': CFreq, 'time': CTime
    }

names = {}

for name, cls in conditions.iteritems (): names[cls] = name

class Line (object):
    __slots__ = ['rconds', 'srconds', 'rfuncs', 'srfuncs', 'matches', '_formatted']
    
    def __init__ (self):
        self.rconds = []
        self.srconds = []
        self.rfuncs = []
        self.srfuncs = []
        self.matches = 0
        self._formatted = None

    def add (self, cond):
        if cond.isSubRecord:
            self.srconds.append (cond)
            self.srfuncs.append (cond.matchSubRecord)
        else:
            self.rconds.append (cond)
            self.rfuncs.append (cond.matchRecord)

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

    def registerVars (self, ctxt):
        for c in self.rconds:
            if isinstance (c, VarCondition):
                c.register (ctxt)
        for c in self.srconds:
            if isinstance (c, VarCondition):
                c.register (ctxt)
                
    def matchRecord (self, cache, inp, uvw, time, bl):
        for f in self.rfuncs:
            res = cache.get (f)

            if res is None:
                res = f (inp, uvw, time, bl)
                cache[f] = res

            if not res: return False
        self.matches += 1
        return True

    def matchSubRecord (self, cache, inp, uvw, time, bl, data, flags):
        # Save a function call here by not relying on self.matchRecord
        # -- this function is called millions of times so this makes
        # a difference.
        for f in self.rfuncs:
            res = cache.get (f)

            if res is None:
                res = f (inp, uvw, time, bl)
                cache[f] = res

            if not res: return False
        
        for f in self.srfuncs:
            f (inp, uvw, time, bl, data, flags)
        self.matches += 1 # the best we can reasonably do...
        return True

# The actual multiflag implementation ...

class MultiFlag (object):
    def __init__ (self):
        self.conditions = {}
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

                try:
                    condobj = conditions[cond] (arg)
                except Exception, e:
                    print 'Error parsing file \"%s\", line:' % fname, l
                    raise e
                
                # Share instances of identical conditions so that
                # we can cache their results effectively.
                
                if condobj in self.conditions:
                    condobj = self.conditions[condobj]
                else:
                    self.conditions[condobj] = condobj
                    
                thisLine.add (condobj)

            if thisLine.anySubRecord (): self.srLines.append (thisLine)
            else: self.rLines.append (thisLine)

    def numLines (self): return len (self.rLines) + len (self.srLines)

    def FAKEapplyVis (self, inp, preamble, data, flags, nread):
        self.nSeen += 1
        inp.rewriteFlags (flags[0:nread])

    def applyVis (self, inp, preamble, data, flags, nread):
        self.nSeen += 1
        ns = self.nSeen
        cache = {}
        lineFlags = self.lineFlags
        data = data[0:nread]
        flags = flags[0:nread]

        uvw = preamble[0:3]
        time = preamble[3]
        bl = util.decodeBaseline (preamble[4])

        hit = False
        for line in self.rLines:
            if line.matchRecord (cache, inp, uvw, time, bl):
                hit = True
                break

        if hit:
            self.nR += 1
            flags.fill (0)
        elif self.anySR:
            if lineFlags is None or lineFlags.shape != flags.shape:
                self.lineFlags = lineFlags = flags.copy ()

            lineFlags.fill (0)

            for line in self.srLines:
                if line.matchSubRecord (cache, inp, uvw, time, bl, data, lineFlags):
                    # Only do the op if this line matched some parts (ie,
                    # marked some channels for flagging). If no channels were marked for
                    # flagging, lineFlags will not have been altered and we need not
                    # re-zero it. The logical_and invocation below modifies 'flags'
                    # in-place, saving an expensive allocation.
                    N.logical_and (flags, lineFlags, flags)
                    lineFlags.fill (0)
            
            nUnflagged = flags.sum ()

            if nUnflagged == 0:
                self.nR += 1
            elif nUnflagged < flags.size:
                self.nSR += 1
        
        inp.rewriteFlags (flags)

    def setupFile (self, inp, banner):
        #print self.conditions.keys ()
        
        self.vartypes = {}
        self.varvals = {}
        self.vartrackers = {}
        self.curInp = inp
        
        for l in self.rLines: l.registerVars (self)
        for l in self.srLines: l.registerVars (self)

        for vname in self.vartypes.iterkeys ():
            self.vartrackers[vname] = vt = inp.makeVarTracker ()
            vt.track (vname)
            
        inp.openHistory ()
        inp.writeHistory (banner)
        inp.logInvocation ('MULTIFLAG')
        inp.closeHistory ()

        self.nR = self.nSR = self.nSeen = 0
        self.anySR = len (self.srLines) > 0

    def addVar (self, varname, vartype):
        self.vartypes[varname] = vartype

    def getVar (self, varname):
        vt = self.vartrackers[varname]

        if varname in self.varvals and not vt.updated ():
            return self.varvals[varname]

        vtype = self.vartypes[varname]

        if vtype == VarCondition.V_DOUBLE:
            val = self.curInp.getVarDouble (varname)
        elif vtype == VarCondition.V_INT:
            val = self.curInp.getVarInt (varname)
        elif vtype == VarCondition.V_FLOAT:
            val = self.curInp.getVarFloat (varname)
        elif vtype == VarCondition.V_COMPLEX:
            val = self.curInp.getVarComplex (varname)
        elif vtype == VarCondition.V_STRING:
            val = self.curInp.getVarString (varname)

        self.varvals[varname] = val
        return val
    
    def doneFile (self, inp):
        self.vartrackers = self.varvals = self.vartypes = None
        self.curInp = None
        
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
                    # See comment below.
                    curInp = curInp.refobj.open ('r')
                    self.doneFile (curInp)
                    curInp.close ()

                curInp = inp
                self.setupFile (inp, banner)
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
                self.setupFile (inp, banner)
                first = False

            self.applyVis (inp, preamble, data, flags, nread)
        
        # Need to reopen the dataset to be able to get back to the history.
        # Not too elegant, but life goes on.
        inp = dset.open ('r')
        self.doneFile (inp)
        inp.close ()

_SVNID = '$Id$'

def task ():
    print 'This script is UNFINISHED and EXPERIMENTAL!!!!'
    print 'Use multiflag2 instead!!!!'
    
    banner = util.printBannerSvn ('multiflag', 'UV data multiflagger', _SVNID)
    
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
