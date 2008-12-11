#! /usr/bin/env python
#
# Do a quick scan with the ATA using the Python control routines.

"""pyscan - Perform a single scan using the Python ATA control routines.

Usage: pyscan.py [debug|real] <instrument> <source> <freqMHz> <durMins>
 E.g.: pyscan.py debug default 3c147 3140 1

The arguments are:

  mode - If the argument is "real", the script actually
    runs live observations. If it is "debug", the script runs in no-op
    mode and doesn't actually do anything with any hardware. Any other
    value is unacceptable and will cause the script to exit. (The
    intention of this is to ensure that there's no chance that a script
    invoked with improper arguments will do anything to the array at
    all.)
    
  instrument - The instrument to use can be specified in the usual way
    (as "<instrument>:<subarray>") or as "default", which currently
    maps to fx64a:fxa.
    
  source - The name of the source to observe; it must be somewhere in
    the ATA catalog database.
    
  freqMHZ - The observing frequency to use, in MHz.
  
  durMins - The duration of the scan, in minutes.
"""

import sys
from atactl import *

me = 'pyscan'


# Settings from the commandline. Two of them are parsed nontrivially:
#
# reallyDoIt - Boolean. True if the mode was "real", false if it was "debug".
# h          - A "Hookup" object containing information about the instrument we're
#              controlling. Information is gathered by running 'fxconf.rb
#              hookup_tab {instrumentname}'

if len (sys.argv) != 6:
    print >>sys.stderr, __doc__
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
            useattens=False, # Don't bother to find and set optimal attemplifier settings.
            )

try:
    # Load hookup info via fxconf.rb
    h.load ()

    # Set PAMs to default values and turn on LNAs for all of the
    # ants that we're using.
    initAntennas (h.ants ())

    # Get the current integration time. We need this to know how
    # many frames to run fxmir.rb for. (Though at the moment we
    # only invoke atafx.)
    checkIntegTime (h)

    # Acquire a lock on the LO we need. This is automatically unlocked
    # on program exit.
    lockServer ('lo' + h.lo)

    # Launch the datacatcher and integrate. This will generate an ephemeris,
    # tune the LO, drive the antennas, set the focus, and control the
    # fringe rotator. It normally also sets the attemplifiers, but we
    # specified that that shouldn't be done in our call to initScript.
    observe (h, 'scan', source, freq, durMins * 60)

    # If we got this far, we actually succeeded.
    retcode = 0
except:
    logAbort (sys.exc_info ())
    
sys.exit (retcode)
