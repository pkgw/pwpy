#!/usr/bin/env python

"""
claw, 22sep09
Quick and dirty script to take Bryan's RM imaging results log file and plot diagnostic plots.
"""

import sys

if len(sys.argv) < 2:
    print 'dude, give me at least 1-2 log files.'
    exit(1)

import asciidata, numpy, pylab


# load file 1
print 'loading ', sys.argv[1]
f = asciidata.AsciiData(sys.argv[1])
nu = numpy.array(f.columns[0])
q = numpy.array(f.columns[1])
u = numpy.array(f.columns[2])
err = numpy.array(f.columns[3])

pylab.figure(1)
pylab.subplot(2,2,1)
#pylab.plot(q,u)
pylab.errorbar(q,u,xerr=err,yerr=err)
pylab.subplot(2,2,2)
pylab.plot(nu,q**2 + u**2)

# plot two log results on same plots
# optionally load file 2
if len(sys.argv) == 3:
    print 'loading ', sys.argv[2]
    f2 = asciidata.AsciiData(sys.argv[2])
    nu2 = numpy.array(f2.columns[0])
    q2 = numpy.array(f2.columns[1])
    u2 = numpy.array(f2.columns[2])
    err2 = numpy.array(f2.columns[3])

    pylab.subplot(2,2,1)
#    pylab.plot(q2,u2)
    pylab.errorbar(q2,u2,xerr=err2,yerr=err2)
    pylab.subplot(2,2,2)
    pylab.plot(nu2,q2**2 + u2**2)

pylab.show()
