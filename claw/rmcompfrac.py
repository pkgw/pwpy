#!/usr/bin/env python
# claw, 15may2010
#
# Script to read in text file with names, fluxes, and rm components, shift and add all components
# Answer question:  what is rm bias in low-resolution rm spectra?

import numpy, pylab, asciidata
import scipy.optimize as opt
import matplotlib.pyplot as plt

#f = asciidata.AsciiData('/big_scr3/claw/data/ata/nvss-rm-best/RM-hires2.txt')
f = asciidata.AsciiData('/big_scr3/claw/data/ata/nvss-rm-best/rm-allres-allsrc2.txt')

n = numpy.array(f.columns[0])
fl1 = numpy.array(f.columns[2])
rm1 = numpy.array(f.columns[4])
erm1 = numpy.array(f.columns[6])
rm2 = numpy.array(f.columns[12])
erm2 = numpy.array(f.columns[13])
print 'Set arrays of lengths %d, %d, %d' % (len(n), len(rm1), len(rm2))

sigdiff = (rm1 - rm2)/numpy.sqrt(erm1**2 + erm2**2)

hist, bin_edges = numpy.histogram(sigdiff,range=(-17,17),bins=34, normed=True)

gaussian = lambda amp,x,sigma: amp/(numpy.sqrt(2 * numpy.pi)*sigma) * numpy.exp(-0.5*(x/numpy.array([sigma]))**2)  # normalized gaussian SNR distribution for comparison.
bins = [bin_edges[i:i+2].mean() for i in range(len(bin_edges)-1)]
pylab.plot(bins, gaussian(42,bins,1), label='Gaussian')
pylab.plot(bins, 42*hist, label='Observed')
pylab.xlabel('RM-highres - RM-lowres (sigma)')
pylab.ylabel('Number of Sources')
pylab.legend()
pylab.show()

#oldn = ''
#for name in n:
#    if name != oldn:
#        print 'Working with %s' % (name)
#        rmcomps = numpy.where((n == name) & (snr >= 7))
#        print n[rmcomps], fl[rmcomps], rm[rmcomps]
#        meanrm = (fl[rmcomps]*rm[rmcomps]).sum()/fl[rmcomps].sum()
#        print 'Flux-weighted RM: %.3f' % (meanrm)
#
#        print 'Fractional flux of shifted RM components'
#        frfl = fl[rmcomps]/fl[rmcomps].sum()
#        rmshift = rm[rmcomps]-meanrm
#        print n[rmcomps], frfl, rmshift, snr[rmcomps]
#
#    oldn = name

