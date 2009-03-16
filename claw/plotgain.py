# A little script of how to plot gains with miriad-python
# claw 26feb09

import miriad, numpy, pylab
from mirtask import readgains

# read in data
ds = miriad.Data ('fx64c-cyga-32-480-0.2s-2').open ('rw')
gr = readgains.GainsReader (ds)
gr.prep ()

# read data into array
(time, gains) = gr.readAll()

# each time has an average gain for reach antenna in a 86-element array (43 dual pol?).  only 2x7 populated for this obs.
len(time), len(gains)
len(gains[0])

# plot phase
pylab.plot(time,numpy.degrees(numpy.arctan2(gains[:,24].real,gains[:,24].imag)),',')   # for ant 13x, with odd jump
pylab.show()
# something funny with python plot...  the phase plot isn't identical to that of miriad.  seems inverted and scaled relative to miriad.
