#!/usr/bin/env python
# claw, 15may2010
#
# Script to read in text file with names, fluxes, and rm components, shift and add all components
# Answer question:  what is rm bias in low-resolution rm spectra?

import numpy, pylab, asciidata
import scipy.optimize as opt
import matplotlib.pyplot as plt

f = asciidata.AsciiData('/big_scr3/claw/data/ata/nvss-rm-best/RM-hires.txt')

n = numpy.array(f.columns[0])
fl = numpy.array(f.columns[1])
rm = numpy.array(f.columns[2])

print 'Set arrays of lengths %d, %d, %d' % (len(n), len(fl), len(rm))

oldn = ''
rmarr = numpy.array([])
rmarr2 = numpy.array([])
flarr = numpy.array([])
use = ['074948+555421','084124+705341','104244+120331','123039+121758','125611-054720','133108+303032','153150+240243','165111+045919','165112+045917','172025-005852','172025-005857','184226+794517','184150+794728','192451-291431','211636-205551']

for name in n:
    if name != oldn and name in use:
        print 'Working with %s' % (name)

        rmcomps = numpy.where(n == name)
        print n[rmcomps], fl[rmcomps], rm[rmcomps]
        meanrm = (fl[rmcomps]*rm[rmcomps]).sum()/fl[rmcomps].sum()
        print 'Flux-weighted RM: %.3f' % (meanrm)

        print 'Fractional flux of shifted RM components'
        frfl = fl[rmcomps]/fl[rmcomps].sum()
        rmshift = rm[rmcomps]-meanrm
        print n[rmcomps], frfl, rmshift

        # build rm array
        rmarr = numpy.concatenate((rmarr,rmshift))
        rmarr2 = numpy.concatenate((rmarr2,rm[rmcomps]))
        flarr = numpy.concatenate((flarr,frfl))
    oldn = name

# calc RM limits for containing specific fractions of flux
print len(flarr)

# need to sort for cumsum
#rmarr.sort()
#flarr.sort()
#pylab.plot(rmarr, flarr, '.')
#pylab.show()

rm = numpy.arange(-1000.,1000.)

sigma = 60.
gaussian = lambda amp,x,x0,sigma: amp * numpy.exp(-1.*((x-x0)/(numpy.log(2)*sigma))**2)  # normalized gaussian SNR distribution for comparison.
fitfunc = lambda p, x:  gaussian(p[0], x, p[1], p[2])
errfunc = lambda p, x, y: fitfunc(p, x)**2 - y**2  # optimize including noise bias
p0 = [3.,0.,100.]

fig = plt.figure()
fig.subplots_adjust(hspace=0.)
pylab.subplot(211)
pylab.ylabel('Relative flux')
pylab.setp(pylab.gca(), xticklabels=[], xticks=(0.,-500.,500.))
#pylab.setp(pylab.gca(), xticklabels=[], xticks=(0.,10.), yticks=[0.2,0.4,0.6,0.8,1.0])
gauarr = numpy.zeros(2000)
gauarr2 = numpy.zeros(2000)
for i in range(len(rmarr)):
    pylab.plot(rm, gaussian(flarr[i],rm,rmarr[i],sigma))
    gauarr = gauarr + gaussian(flarr[i],rm,rmarr[i],sigma)
    gauarr2 = gauarr2 + gaussian(flarr[i],rm,rmarr2[i],sigma)

pylab.axis([-1000,1000,0.0,1.07])

gauarr = gauarr/max(gauarr)

p1, success = opt.leastsq(errfunc, p0[:], args = (rm, gauarr))
p2, success = opt.leastsq(errfunc, p0[:], args = (rm, gauarr2))

pylab.subplot(212)
if success:
    print 'Fit successful!  Results:'
    print p1
    print p2
    pylab.plot(rm, fitfunc(p1, rm), '--')
    pylab.plot(rm, gauarr)
    pylab.xlabel('RM (rad/m2)')
    pylab.ylabel('Relative flux')
    pylab.axis([-1000,1000,0.0,1.07])
    pylab.show()

