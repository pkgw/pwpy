#! /usr/bin/env python

"""Varcat -- print values of UV variables.

It looks like the UVIO task basically does the same thing
as this. But my formatting is prettier.
"""

import sys
import mirtask
from mirtask import uvdat, keys

#print 'varcat'

keys.keyword ('vars', 'a', None, 64)
keys.keyword ('context', 'a', None, 64)
keys.keyword ('format', 'a', None, 64)
keys.keyword ('cformat', 'a', None, 64)
keys.doUvdat ('dsl3', True)
opts = keys.process ()

if len (opts.vars) == 0:
    print 'Must specify variables to print out!'
    sys.exit (1)

if len (opts.context) == 0:
    opts.context = ['time']

if len (opts.format) > len (opts.vars):
    print 'More formatting commands than variables to print!'
    sys.exit (1)
else:
    while len (opts.format) < len (opts.vars):
        opts.format.append ('')

if len (opts.cformat) > len (opts.context):
    print 'More context formatting commands than context variables to print!'
    sys.exit (1)
else:
    while len (opts.cformat) < len (opts.context):
        opts.cformat.append ('')

# Formatting utilities

def fBaseline (val):
    return '%d-%d' % (mirtask.util.decodeBaseline (val))

formatters = {
    'time': mirtask.util.jdToFull,
    'baseline': fBaseline,
    'pol': mirtask.util.polarizationName,
    'default': str
    }

autoFormat = {
    'time': 'time',
    'baseline': 'baseline',
    'pol': 'pol'
    }

# Header row

s = ''
for v in opts.context + opts.vars:
    s += v.ljust (20)
print s

# Print the variables!

curFile = None

for dIn, p, d, f, n in uvdat.readAll ():
    if dIn is not curFile:
        uvt = dIn.makeVarTracker ()
        uvt.track (*opts.vars)

        vinfo = []
        
        for v, fname in zip (opts.context + opts.vars, opts.cformat + opts.format):
            tup = dIn.probeVar (v)

            if tup is None:
                print 'No such variable "%s" in %s!' % (v, dIn.name)
                sys.exit (1)

            vtype = tup[0]
            vlen = tup[1]

            # How should we format this variable into a string?

            if fname == '':
                if v in autoFormat: fname = autoFormat[v]
                else: fname = 'default'
                
            formatter = formatters[fname]

            # How do we obtain the value of this var when it's updated?
            
            if vtype == 'a': get = lambda: dIn.getVarString (v)
            elif vtype == 'r': get = lambda: dIn.getVarFloat (v, vlen)
            elif vtype == 'i': get = lambda: dIn.getVarInt (v, vlen)
            elif vtype == 'd': get = lambda: dIn.getVarDouble (v, vlen)
            elif vtype == 'c': get = lambda: dIn.getVarComplex (v, vlen)
            else:
                print 'Unhandled or ungettable variable type "%s" for "%s" in %s!' \
                      % (vtype, v, dIn.name)
                sys.exit (1)

            # Ok, we have all the info we need. For some reason I need to stuff
            # vlen into the tuple, otherwise old values seem to get thrown away or
            # something. Maybe a single instance of vlen is getting captured and
            # reused each time unless we stuff it in a tuple to force a new variable
            # to be used?
            
            vinfo.append ((v, vlen, get, formatter))
            
        curFile = dIn

    if not uvt.updated (): continue

    s = ''

    for (v, vlen, get, formatter) in vinfo:
        #print v, get, formatter, vtype, vlen
        f = formatter (get ())

        if len (f) < 20:
            s += f.ljust (20)
        else:
            s += '%s... ' % (f[0:16])

    print s
