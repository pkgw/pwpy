#!/usr/bin/env python
# claw, 15may2010
#
# Script to read in text file with names, fluxes, and rm components, shift and add all components
# Answer question:  what is rm bias in low-resolution rm spectra?

import numpy, pylab, asciidata
import scipy.optimize as opt
import matplotlib.pyplot as plt

f = asciidata.AsciiData('/big_scr3/claw/data/ata/nvss-rm-best/RM-hires-join.txt')

n = numpy.array(f.columns[0])
fl = numpy.array(f.columns[1])
rm = numpy.array(f.columns[2])
erm  = numpy.array(f.columns[3])
flvla = numpy.array(f.columns[6])
rmvla = numpy.array(f.columns[7])
ermvla = numpy.array(f.columns[9])

print 'Set arrays of lengths %d, %d, %d, %d' % (len(n), len(fl), len(rm), len(rmvla))

oldn = ''

fig = plt.figure()
for name in n:
    if name != oldn:
        print 'Working with %s' % (name)

        rmcomps = numpy.where(n == name)
        print n[rmcomps], fl[rmcomps], rm[rmcomps], flvla[rmcomps], rmvla[rmcomps]
        frfl = fl[rmcomps]/fl[rmcomps].sum()
#        pylab.errorbar(rmvla[rmcomps],rm[rmcomps],xerr=ermvla[rmcomps],yerr=erm[rmcomps],fmt='b*')

        for i in range(len(rmcomps[0])):
            print rmvla[rmcomps]
            print rmvla[rmcomps][i]
            pylab.plot([rmvla[rmcomps][i]],[rm[rmcomps][i]],'k*',ms=20*frfl[i],alpha=0.6,mew=1,mec='r')
        pylab.plot([rmvla[rmcomps][i],rmvla[rmcomps][i]],[min(rm[rmcomps]),max(rm[rmcomps])],'k--')

    oldn = name

pylab.plot([-5000,5000],[-5000,5000],'k-')
pylab.xlabel('VLA RM (rad/m2)')
pylab.ylabel('ATA RM (rad/m2)')
pylab.show()

