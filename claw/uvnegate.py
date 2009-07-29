#! /usr/bin/env python
#
# claw, 28jul09
# Read uv data and write its opposite

import aipy, sys

file = sys.argv[1]

uvi = aipy.miriad.UV(file)
uvo = aipy.miriad.UV(file+'-neg', status='new')

uvo.init_from_uv(uvi)

def negate(uv, preamble, data):
    uvw, t, (i,j) = preamble
    return preamble, data * (-1)

uvo.pipe(uvi, mfunc=negate, append2hist="Negated data\n")
del(uvo)
