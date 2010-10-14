#! /usr/bin/env python

"""= fringedump.py - Not of general interest.
& pkgw
: Other
+
 This task logs some data related to fringe rate corrections.
 You don't need it.
--
"""

import sys
import miriad, mirtask
import mirtask.lowlevel as ll
from mirtask import uvdat, keys
import numpy as N
from cgs import c
from calmodels import models

omega_e = 2. * N.pi / 86400 # Earth rot rate in rads per sec
deg2rad = N.pi / 180.

fout = file ('fringedump.dat', 'w')

for vname in sys.argv[1:]:
    vis = miriad.VisData (vname)
    print vname

    g = vis.readLowlevel ('3', False, select='-auto', line='chan,1,1,512')
    src = None
    
    for dIn, preamble, data, flags in g:
        if not flags.any (): continue # skip all-flagged records
        assert data.size == 1

        if src is None:
            src = dIn.getVarFirstString ('source', 'unknown')

        # Calculate fringe rate. From Thompson, Moran, & Swenson sec. 4.4.
        # Need to convert u from nanoseconds to wavelengths.

        amp = abs (data[0])
        sfreq = dIn.getVarDouble ('sfreq', 1)
        u = preamble[0] * sfreq
        flux = models[src] (sfreq * 1000.)
        dec = dIn.getVarDouble ('dec', 1) * deg2rad
        rate = -omega_e * u * N.cos (dec)
        inttime = dIn.getVarFirstFloat ('inttime', 10.0)
        dphi = rate * inttime
        corr = N.abs (1. / N.sinc (dphi))

        print >>fout, ' '.join (str (x) for x in (amp / flux, dphi, rate, u, corr, amp))

fout.close ()

