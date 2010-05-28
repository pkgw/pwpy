#!/usr/bin/env python

import sys

if len(sys.argv) < 2:
    print 'dude, give me a log file.  wtf?'
    exit(1)

import asciidata, numpy

# load files
print 'loading ', sys.argv[1]
f = asciidata.AsciiData(sys.argv[1], comment_char='#')
nu = numpy.array(f.columns[0])
q = numpy.array(f.columns[1])
u = numpy.array(f.columns[2])
err = numpy.array(f.columns[3])

# flux model for stokes parameters
trueq = 0.6285 * (1.0035/nu)**(-0.359)
trueu = 1.4119 * (1.0035/nu)**(-0.359)

print q-trueq
print u-trueu

# fluxweight = numpy.sum(q/err**2)/numpy.sum(1/err**2)
# print 1/numpy.sqrt(numpy.sum(1/err**2))
meanq = (q-trueq).mean()
meanu = (u-trueu).mean()
stdq = (q-trueq).std()
stdu = (u-trueu).std()

print '%2f\pm%2f,%2f\pm%2f' % (1000*meanq,1000*stdq,1000*meanu,1000*stdu) 
