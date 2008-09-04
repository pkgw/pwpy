#! /usr/bin/env python

"""= gpcat2.py - Print out antenna gain information
& pkgw
: calibration
+
 This task prints out the antenna gain amplitude information stored in
 a UV dataset. The task GPLIST performs a similar function, but
 crashes for data not from CARMA.

 The antenna gains are printed in a table format. The first column is
 the full date and time associated with the entry in the gain table,
 and the subsequent columns given the amplitudes of the antenna gains
 in that entry. Antennas with zero amplitudes in the first record are
 skipped in that record and all subsequent ones.

 With many antennas (e.g., ATA data), the individual lines can get
 very long.

 The gains-table reading code does not handle all possible
 configurations (e.g., ntau != 1) but should exit with an error if it
 encounters a table it cannot handle.

< vis
 Only a single input UV dataset is supported by GPCAT2.PY.

--
"""

import sys, os
import miriad
from mirtask import keys, readgains
from mirtask.util import jdToFull, printBannerSvn
import numpy as N

SVNID = '$Id$'
banner = printBannerSvn ('gpcat2', 'print antenna gains tables', SVNID)

keys.keyword ('vis', 'f', ' ')
opts = keys.process ()

if opts.vis == ' ':
    print >>sys.stderr, 'An input file must be given'
    sys.exit (1)

ds = miriad.Data (opts.vis).open ('r')
gr = readgains.GainsReader (ds)
gr.prep ()

print 'Found gain entries for %d antennas.' % (gr.nants)
print 'Printing gain amplitudes only.'

first = True

for (time, gains) in gr.readSeq ():
    if first:
        # Figure out which ants are present

        ants = []
        
        for i in xrange (0, gr.nants):
            if abs (gains[i * gr.nfeeds]) > 0: ants.append (i)

        # Now print a header row - the blanks offset the time prefix

        print '                   ', 
        for ant in ants:
            print ' Ant %4d' % (ant + 1, ),
        print

        first = False

    # Now print the data
    
    print jdToFull (time) + ':', 

    for ant in ants:
        print ' %8.7lg' % (abs (gains[ant * gr.nfeeds])),
    print

# All done.

del ds
