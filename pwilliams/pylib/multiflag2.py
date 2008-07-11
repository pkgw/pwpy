#! /usr/bin/env python
"""A temporary multiflag implementation that just executes UVFLAG.
Do this while my multiflag implementation is still slow."""

import sys
from mirexec import TaskUVFlag

# Conditions are:
#
# ant bl pol auto cross chan atahalf freq time

class MultiFlag2 (object):
    def __init__ (self, freq, half, pol):
        self.freq = freq
        self.half = half
        self.pol = pol
        self.lines = []
        
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

            shared = []
            multi = None
            lmulti = None
            ignore = False
            
            for b in bits:
                split = b.split ('=', 2)
                if len (split) == 1: cond, arg = split[0], None
                else: cond, arg = split

                if cond == 'auto': shared.append ('auto')
                elif cond == 'cross': shared.append ('-auto')
                elif cond == 'ant': shared.append ('ant(%s)' % arg)
                elif cond == 'bl':
                    assert multi is None
                    multi = [('ant(%s)(%s)' % tuple (x.split ('-'))) for x in arg.split (',')]
                elif cond == 'pol':
                    if self.pol is None: shared.append ('pol(%s)' % arg)
                    else:
                        ignore = ignore or self.pol.lower () not in \
                                 (x.lower () for x in arg.split (','))
                elif cond == 'chan':
                    assert lmulti is None
                    lmulti = ['chan,%s' % x for x in arg.split (';')]
                elif cond == 'atahalf':
                    ignore = ignore or self.half != int (arg)
                elif cond == 'freq':
                    ignore = ignore or self.freq != int (arg)
                elif cond == 'time':
                    shared.append ('time(%s)' % arg)
                elif cond == 'uvrange':
                    shared.append ('uvrange(%s)' % arg)
                else: assert False, 'Unknown condition'

            if ignore: continue

            if len (shared) == 0:
                if multi is not None: selects = multi
                else: selects = [None]
            else:
                selects = [','.join (shared)]

                if multi is not None:
                    selects = [selects[0] + ',' + x for x in multi]

            if lmulti is not None:
                for x in selects:
                    for y in lmulti:
                        self.lines.append ((x, y))
            else:
                for x in selects:
                    self.lines.append ((x, None))

    def applyDataSet (self, dset, banner):
        t = TaskUVFlag (vis=dset, flagval='f')
        
        for select, line in self.lines:
            t.select = select
            t.line = line
            t.run ()

def task ():
    from mirtask import keys
    from miriad import VisData, basicTrace

    basicTrace ()
    
    banner = 'MULTIFLAG2 (Python): Apply groups of flags by calling UVFLAG'
    print banner

    keys.keyword ('spec', 'f', None, 128)
    keys.keyword ('vis', 'f', None, 128)
    keys.keyword ('freq', 'd', -1)
    keys.keyword ('half', 'i', 0)
    keys.keyword ('pol', 'a', ' ')
    opts = keys.process ()

    if opts.pol == ' ': opts.pol = None
    
    if len (opts.spec) < 1:
        print >>sys.stderr, 'Error: must give at least one "spec" filename'
        sys.exit (1)

    if opts.freq < 0:
        print >>sys.stderr, 'Error: must specify "freq" keyword.'
        sys.exit (1)
    
    mf = MultiFlag2 (opts.freq, opts.half, opts.pol)
    
    for fname in opts.spec: mf.loadSpec (fname)

    print 'Parsed conditions from %d file(s).' % (len (opts.spec))

    for vf in opts.vis:
        mf.applyDataSet (VisData (vf), 'unused')

if __name__ == '__main__':
    task ()
    sys.exit (0)
