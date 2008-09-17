#! /usr/bin/env python

"""= gpcat2.py - Print out antenna gain information
& pkgw
: calibration
+
 This task prints out the antenna gain amplitude information stored in
 a UV dataset. The task GPLIST performs a similar function, but
 crashes for data not from CARMA.

 By default, the antenna gains are printed in a table format. The
 first column is the full date and time associated with the entry in
 the gain table, and the subsequent columns given the amplitudes of
 the antenna gains in that entry. Antennas with zero amplitudes in the
 first record are skipped in that record and all subsequent ones.

 With many antennas (e.g., ATA data), the individual lines can get
 very long.

 The "rank" mode (see documentation for the keyword "rank") prints out
 a subset of the antennas sorted by gain, providing a ranking of their
 sensitivity or lack thereof.

 The gains-table reading code does not handle all possible
 configurations (e.g., ntau != 1) but should exit with an error if it
 encounters a table it cannot handle.

< vis
 Only a single input UV dataset is supported by GPCAT2.PY.

@ rank
 An integer, defaulting to zero. Zero implies that no ranking is
 performed and the default output format is used. A non-zero value
 activates "rank mode". In this case, for each epoch, the list of
 antennas is sorted by gain, and this keyword gives the number entries
 at each end of the list whose information is printed. For instance,
 "rank=3" causes a list of six antennas to be printed out: the three
 with the lowest gains and the three with the highest gains.
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
keys.keyword ('rank', 'i', 0)
opts = keys.process ()

if opts.vis == ' ':
    print >>sys.stderr, 'An input file must be given'
    sys.exit (1)

if opts.rank > 0:
    rankMode = True
    print 'Showing %d antennas at each end of gain distribution at each epoch.' % opts.rank
else:
    rankMode = False
    
ds = miriad.Data (opts.vis).open ('r')
gr = readgains.GainsReader (ds)
gr.prep ()

print 'Found gain entries for %d antennas.' % (gr.nants)
print 'Computing gain amplitudes only.'

first = True

for (time, gains) in gr.readSeq ():
    if first:
        # Figure out which ants are present

        ants = []
        
        for i in xrange (0, gr.nants):
            if abs (gains[i * gr.nfeeds]) > 0: ants.append (i)

        if not rankMode:
            # Default mode: print a header row - the blanks offset the time prefix

            print '                   ', 
            for ant in ants:
                print ' Ant %4d' % (ant + 1, ),
            print

        first = False

    # Now print the data
    
    print jdToFull (time) + ':', 

    if rankMode:
        # rank mode: print list of ants sorted by gain
        print
        info = [(a, abs (gains[a * gr.nfeeds])) for a in ants]
        info.sort (key = lambda tup: tup[1], reverse=False)
        for tup in info[0:opts.rank]:
            print '   % 3d: %g' % tup
        print '        [skipping %d antennas]' % (len (ants) - 2 * opts.rank)
        for tup in info[-opts.rank:]:
            print '   % 3d: %g' % tup
    else:
        # default mode: print table of gains in numerical order
        for ant in ants:
            print ' %8.7lg' % (abs (gains[ant * gr.nfeeds])),
    print

# All done.

del ds
