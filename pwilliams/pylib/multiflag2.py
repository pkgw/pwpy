#! /usr/bin/env python
"""A temporary multiflag implementation that just executes UVFLAG.
Do this while my multiflag implementation is still slow."""

import sys
from mirexec import TaskUVFlag

# Conditions are:
#
# ant bl pol auto cross chan atahalf freq time

class MultiFlag2 (object):
    def __init__ (self, freq, half):
        self.freq = freq
        self.half = half
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
                    print arg.split (',')
                    multi = [('ant(%s)(%s)' % tuple (x.split ('-'))) for x in arg.split (',')]
                elif cond == 'pol': shared.append ('pol(%s)' % arg)
                elif cond == 'chan':
                    assert lmulti is None
                    lmulti = ['chan,%s' % x for x in arg.split (';')]
                elif cond == 'atahalf':
                    ignore = ignore or self.half != int (arg)
                elif cond == 'freq':
                    ignore = ignore or self.freq != int (arg)
                elif cond == 'time':
                    shared.append ('time(%s)' % arg)
                else: assert False, 'Unbknown condition'

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
