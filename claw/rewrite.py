#!/usr/bin/env python
# claw, 21jan11
#
# Function to copy one integration to new miriad visibility file
# Crude copy of pkgw function in calctsys.py.

from miriad import *

def rewriteData (vis, out):
    dOut = out.open ('c')
    dOut.setPreambleType ('uvw', 'time', 'baseline')

    i = 0
    for inp, preamble, data, flags in vis.readLowlevel ('dsl3', False):

        if i == 0:
            nants = inp.getVarFirstInt ('nants', 0)
            inttime = inp.getVarFirstFloat ('inttime', 10.0)
            nspect = inp.getVarFirstInt ('nspect', 0)
            nwide = inp.getVarFirstInt ('nwide', 0)
            sdf = inp.getVarDouble ('sdf', nspect)
            inp.copyHeader (dOut, 'history')
            inp.initVarsAsInput (' ') # ???

            dOut.writeVarInt ('nants', nants)
            dOut.writeVarFloat ('inttime', inttime)
            dOut.writeVarInt ('nspect', nspect)
            dOut.writeVarDouble ('sdf', sdf)
            dOut.writeVarInt ('nwide', nwide)
            dOut.writeVarInt ('nschan', inp.getVarInt ('nschan', nspect))
            dOut.writeVarInt ('ischan', inp.getVarInt ('ischan', nspect))
            dOut.writeVarDouble ('sfreq', inp.getVarDouble ('sfreq', nspect))
            dOut.writeVarDouble ('restfreq', inp.getVarDouble ('restfreq', nspect))
            dOut.writeVarInt ('pol', inp.getVarInt ('pol'))

        inp.copyLineVars (dOut)
        dOut.write (preamble, data, flags)

        i = i+1
        if i > 35: break

    dOut.close ()


if __name__ == '__main__':
    inname = 'poco_crab_201103_9.mir'   # template data with one integration
    outname = 'tmp2.mir'  # should not exist yet

    vis = VisData(inname)
    out = VisData(outname)

    rewriteData(vis, out)
