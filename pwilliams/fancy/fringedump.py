#! /usr/bin/env python

"""Fringe Fix -- scale vis amplitudes by a correction factor
to compensate for our lack of fringe rotation."""

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

    g = vis.readLowlevel (False, select='-auto', line='chan,1,1,512')
    src = None
    
    for dIn, preamble, data, flags, nread in g:
        if not flags.any (): continue # skip all-flagged records
        assert (nread == 1)

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

