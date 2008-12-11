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

reallyDoIt = parseMode (sys.argv[1])
h = getHookup (sys.argv[2])
source = sys.argv[3]
freq = int (sys.argv[4])
durMins = int (sys.argv[5])


# Initialize hardware, observe a source, and clean up.

retcode = 1

initScript (reallyDoIt, me + '.log',
            realwarn=False, # Don't pause and give the "actually going to run" message
            )

try:
    h.load ()
    initAntennas (h.ants ())
    checkIntegTime (h)
    lockServer ('lo' + h.lo)
    observe (h, 'scan', source, freq, durMins * 60)
    retcode = 0
except Exception:
    logAbort (sys.exc_info ())
    
sys.exit (retcode)
