#! /usr/bin/env python

"""=ampadd.py - Average UV amplitudes over everything but frequency.
& pkgw
: uv Analysis
+

 This task is intended to aid in the detection of high-duty-cycle RFI.
 By averaging amplitudes over everything but channel number, those
 channels that frequently have above-average amplitudes stand
 out. Thus, this approach is most sensitive to signals that are
 omnipresent: detectible at all times, in all polarizations, on all
 baselines, etc.

< vis
 The more files are input, the more data will be averaged and the more
 prominent RFI should be. All input files must have the same
 correlator configuration.

@ log
 The name of an output log file. The logfile contains three columns of
 numbers. The first column is channel number, the second column is
 chqannel frequency, and the third column is averaged amplitude. Not
 all channels will be present if the channel was flagged in all input
 visibilities. The contents of the logfile are intended to be plotted
 in whatever means are convenient to the user.

--
"""

# TODO: maybe use uvdat to read the data? No real reason not to I think
# TODO: plot the data with pgplot? but it'd be nice to be able to zoom in
# somehow.

from miriad import *
from mirtask import util, keys
import numpy as N
import sys

SVNID = '$Id$'
banner = util.printBannerSvn ('ampadd', 'average UV amplitudes over everything but frequency', SVNID)

keys.keyword ('log', 'f', ' ')
keys.keyword ('vis', 'f', None, 64)

class AmpFlagsAccum (object):
    def __init__ (self):
        self._clear ()

    def _clear (self):
        self.data = self.flags = self.times = self.freq = self.sfreq = None

    def _accum (self, tup):
        inp, preamble, data, flags, nread = tup
        inttime = inp.getVarFirstFloat ('inttime', 10.0)
        
        data = N.abs (data[0:nread] * inttime)
        times = N.ndarray (nread)
        times.fill (inttime)

        w = N.where (flags[0:nread] == 0)
        data[w] = 0.
        times[w] = 0.

        if self.data is None:
            self.data = data.copy ()
            self.times = times
        else:
            self.data += data
            self.times += times
            
    def process (self, dset):
        #from mirtask.uvdat import getPol
        #thepol = None
        first = True
        
        for tup in dset.readLowlevel (False, nopass=True, nocal=True, nopol=True):
            if first:
                # Read in freq and half
                first = False
                freq = tup[0].getVarFirstDouble ('freq', -1)
                sfreq = tup[0].getVarFirstDouble ('sfreq', -1)

                if self.freq is None:
                    self.freq = freq
                    self.sfreq = sfreq
                    self.sdf = tup[0].getVarFirstDouble ('sdf', -1)
                else:
                    if self.freq != freq or self.sfreq != sfreq:
                        print >>sys.stderr, 'Error: Previous datasets have freq = %g and sfreq = %g' \
                              % (self.freq, self.sfreq)
                        print >>sys.stderr, 'Error: This one (%s) has freq = %g and sfreq = %g' \
                              % (tup[0].name, freq, sfreq)
                        sys.exit (1)

            ant1, ant2 = util.decodeBaseline (tup[1][4])
            #pol = getPol ()
            
            if ant1 == ant2: continue

            #if thepol is None:
            #    thepol = pol
            #elif pol != thepol:
            #    raise Exception ('Must have single-polarization input!')
            
            self._accum (tup)

    def done (self):
        w = N.where (self.times > 0.)
        ch = w[0]
        
        self.ch = ch
        self.y = self.data[w] / self.times[w]

afa = AmpFlagsAccum ()
args = keys.process ()

if len (args.vis) < 1:
    print >>sys.stderr, 'Error: No input datasets specified!'
    sys.exit (1)

if args.log == ' ':
    print >>sys.stderr, 'Error: No output logfile specified!'
    sys.exit (1)

print 'Reading data ...'

for v in args.vis:
    v = VisData (v)
    
    if not v.exists:
        print >>sys.stderr, 'Error: No such dataset', v
        sys.exit (1)
        
    print '    ', v
    afa.process (v)

afa.done ()

fout = file (args.log, 'w')
print 'Writing', args.log, '...'

for i in xrange (0, afa.ch.size):
    ch = afa.ch[i] + 1
    y = afa.y[i]
    freq = afa.sfreq + i * afa.sdf

    print >>fout, '%d %g %g' % (ch, freq, y)

fout.close ()
print 'Done.'
sys.exit (0)
