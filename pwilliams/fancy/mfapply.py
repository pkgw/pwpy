#! /usr/bin/env python

import sys, miriad

if len (sys.argv) < 6:
    raise Exception ('Usage: %s [vis] [freq] [half] [pol] [flags file]')

miriad.basicTrace ()

vis = miriad.VisData (sys.argv[1])
freq = int (sys.argv[2])
half = int (sys.argv[3])
pol = sys.argv[4]
if pol != 'xx' and pol != 'yy':
    print 'Assuming meant to ignore pol', pol
    pol = None

for ff in sys.argv[5:]:
    vis.fMulti (ff, freq, half, pol)
    
sys.exit (0)
