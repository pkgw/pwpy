#! /usr/bin/env python
#
# Do a quick scan with the ATA using the Python control routines.

import sys
from atactl import *
import ataprobe

me = 'pyscan'

# Settings from the commandline

if len (sys.argv) != 6:
    print >>sys.stderr, 'Usage: %s [debug|real] instrument source freq durMins' % sys.argv[0]
    print >>sys.stderr, 'E.g.: %s debug default 3c147 1430 1' % sys.argv[0]
    sys.exit (1)

if sys.argv[1] == 'real':
    reallyDoIt = True
elif sys.argv[1] == 'debug':
    reallyDoIt = False
else:
    print >>sys.stderr, 'First argument must be "debug" or "real"; got', sys.argv[1]
    sys.exit (1)

instr = sys.argv[2]
if instr == 'default': instr = None

source = sys.argv[3]
freq = int (sys.argv[4])
durMins = int (sys.argv[5])

# Do it!

retcode = 1

initScript (reallyDoIt, me + '.log')

try:
    h = ataprobe.Hookup (instr)
    initAntennas (h.ants ())
    setIntegTime ()
    lockServer ('lo' + h.lo)
    observe (me, h, 'scan', source, freq, durMins * 60)
    showAccounting ()
    retcode = 0
except Exception, e:
    logAbort (e)
    
sys.exit (retcode)
