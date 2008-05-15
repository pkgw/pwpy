#! /usr/bin/env python

"""mfapply - Apply a "multiflag" file to a UV dataset.

My flagging scripts generate .flags files in a special format.
This script applies them to a UV dataset by invoking UVFLAG.
Note that all the heavy lifting is done in the miriad-python
wrapper."""

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
