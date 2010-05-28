#!/usr/bin/env python

import sys

if len(sys.argv) != 2:
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

print numpy.sum(q/err**2)/numpy.sum(1/err**2)
print numpy.sum(u/err**2)/numpy.sum(1/err**2)
print 1/numpy.sqrt(numpy.sum(1/err**2))
