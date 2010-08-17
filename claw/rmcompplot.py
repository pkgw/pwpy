#!/usr/bin/env python
# claw, 15may2010
#
# Script to read in text file with names, fluxes, and rm components, shift and add all components
# Answer question:  what is rm bias in low-resolution rm spectra?

import numpy, pylab, asciidata
import scipy.optimize as opt
import matplotlib.pyplot as plt

hammer=0

f = asciidata.AsciiData('/big_scr3/claw/data/ata/nvss-rm-best/RM-hires-join3.txt')

n = numpy.array(f.columns[0])
fl = numpy.array(f.columns[1])
rm = numpy.array(f.columns[2])
erm  = numpy.array(f.columns[3])
flvla = numpy.array(f.columns[6])
rmvla = numpy.array(f.columns[7])
ermvla = numpy.array(f.columns[9])

print 'Set arrays of lengths %d, %d, %d, %d' % (len(n), len(fl), len(rm), len(rmvla))

oldn = ''

fig = plt.figure(1)
for name in n:
    if name != oldn:
        print 'Working with %s' % (name)

        rmcomps = numpy.where(n == name)
        print n[rmcomps], fl[rmcomps], rm[rmcomps], flvla[rmcomps], rmvla[rmcomps]
        frfl = fl[rmcomps]/max(fl[rmcomps])
#        pylab.errorbar(rmvla[rmcomps],rm[rmcomps],xerr=ermvla[rmcomps],yerr=erm[rmcomps],fmt='bo')
        meanrm = (fl[rmcomps]*rm[rmcomps]).sum()/fl[rmcomps].sum()

        for i in range(len(rmcomps[0])):
            print rmvla[rmcomps]
            print rmvla[rmcomps][i]
            pylab.plot([rmvla[rmcomps][i]],[rm[rmcomps][i]],'k*',ms=15*frfl[i],alpha=0.2,mew=1.0,mec='r')
        pylab.plot([rmvla[rmcomps][i],rmvla[rmcomps][i]],[min(rm[rmcomps]),max(rm[rmcomps])],'k:')
#        rm[rmcomps][0] = meanrm

    oldn = name

pylab.plot([-5000,5000],[-5000,5000],'k-')
pylab.xlabel('T09 RM (rad/m2)')
pylab.ylabel('ATA RM (rad/m2)')
#pylab.show()

if hammer == 1:
    f2 = asciidata.AsciiData('/big_scr3/claw/data/ata/nvss-rm-best/log-merged-hires/RMCatalogue-compare.txt')
    n2 = numpy.array(f2.columns[0])
    l = numpy.array(f2.columns[1])
    b = numpy.array(f2.columns[2])

    pylab.figure(2)
    pylab.subplot(111, projection="hammer")
    pylab.grid()
    pylab.xticks(numpy.radians(numpy.arange(-150,180,30)),('150','120','90','60','30','0','-30','-60','-90','-120','-150','-180'))

    for i in range(len(l)):
        rm2 = rm[numpy.where(n2[i] == n)][0]
        print l[i], b[i], rm2
        if rm2 > 0.0:
            pylab.plot(numpy.radians([-1*l[i]]), numpy.radians([b[i]]), 'o', markersize=abs(rm2/2.), color='red', alpha=0.9)
        else:
            pylab.plot(numpy.radians([-1*l[i]]), numpy.radians([b[i]]), 'x', markersize=abs(rm2/2.), color='blue', alpha=0.9)
        print i

pylab.show()
