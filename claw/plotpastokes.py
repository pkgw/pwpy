#!/usr/bin/env python
# claw, 17aug10
#
# Script to read in text file with pa and stokes for two files
# plots all stokes parameters for two files vs pa to show cal quality

import numpy, asciidata
from pylab import *

f = asciidata.AsciiData('/big_scr3/claw/data/ata/nvss-rm-best/2253-pa1430.txt', comment_char='#')
f2 = asciidata.AsciiData('/big_scr3/claw/data/ata/nvss-rm-best/2253-pa2010.txt', comment_char='#')

pa = numpy.array(f.columns[0])
i1 = numpy.array(f.columns[1])
pa2 = numpy.array(f2.columns[0])
i2 = numpy.array(f2.columns[1])
q1 = numpy.array(f.columns[3])
q2 = numpy.array(f2.columns[3])
u1 = numpy.array(f.columns[5])
u2 = numpy.array(f2.columns[5])
v1 = numpy.array(f.columns[7])
v2 = numpy.array(f2.columns[7])

print 'Set arrays of lengths %d, %d, %d, %d' % (len(pa), len(i1), len(pa2), len(i2))

def stats(p,s):
# takes position angle and stokes parameter as input
# returns one mean,stdev pair for each unique pa value
    posang = numpy.array([])
    mean = numpy.array([])
    stdev= numpy.array([])

    for pval in numpy.unique(p):
        index = where(p == pval)
        posang = numpy.append(posang, pval)
        mean = numpy.append(mean, s[index].mean())
        stdev = numpy.append(stdev, s[index].std())

    return posang, mean, stdev

fig = figure()
subplots_adjust(hspace=0.0001)

ax1 = subplot(411)
title('Stokes Parameters vs Parallactic Angle for J225357+160853')
posang,mean,stdev = stats(pa, i1)
errorbar(posang,mean,yerr=stdev,fmt='g*',label='1.4 GHz')
posang,mean,stdev = stats(pa2, i2)
errorbar(posang,mean,yerr=stdev,fmt='b.', label='2.0 GHz')
legend(loc=0)
ylim(10,22)
ylabel('I (Jy)')

ax2 = subplot(412, sharex=ax1)
posang,mean,stdev = stats(pa, q1)
errorbar(posang,mean,yerr=stdev,fmt='g*')
posang,mean,stdev = stats(pa2, q2)
errorbar(posang,mean,yerr=stdev,fmt='b.')
ylim(-1.6,1.6)
ylabel('Q (Jy)')

ax3 = subplot(413, sharex=ax1)
posang,mean,stdev = stats(pa, u1)
errorbar(posang,mean,yerr=stdev,fmt='g*')
posang,mean,stdev = stats(pa2, u2)
errorbar(posang,mean,yerr=stdev,fmt='b.')
ylim(-1.6,1.6)
ylabel('U (Jy)')

ax4 = subplot(414, sharex=ax1)
posang,mean,stdev = stats(pa, v1)
errorbar(posang,mean,yerr=stdev,fmt='g*')
posang,mean,stdev = stats(pa2, v2)
errorbar(posang,mean,yerr=stdev,fmt='b.')
ylim(-1.6,1.6)
ylabel('V (Jy)')

xlim(-57,23)
xticklabels = ax1.get_xticklabels()+ax2.get_xticklabels()+ax3.get_xticklabels()
setp(xticklabels, visible=False)
xlabel('Parallactic angle (deg)')
show()

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

