#!/usr/bin/env python

"""
claw, 22sep09
Script to take Bryan's RM imaging results log file and plot diagnostic plots.
"""

import sys

if len(sys.argv) < 3:
    print 'dude, give me a log and rmspectrum file.  wtf?'
    exit(1)

import asciidata, numpy, pylab
import matplotlib.pyplot as plt

# load files
print 'loading ', sys.argv[1]
f = asciidata.AsciiData(sys.argv[1], comment_char='#')
nu = numpy.array(f.columns[0])
q = numpy.array(f.columns[1])
u = numpy.array(f.columns[2])
err = numpy.array(f.columns[3])

print 'loading ', sys.argv[2]
f2 = asciidata.AsciiData(sys.argv[2], comment_char='#')
rm = numpy.array(f2.columns[1])
dirty_re = numpy.array(f2.columns[2])
dirty_im = numpy.array(f2.columns[3])
clean_re = numpy.array(f2.columns[4])
clean_im = numpy.array(f2.columns[5])
resid_re = numpy.array(f2.columns[8])
resid_im = numpy.array(f2.columns[9])

pola = 0.5*numpy.arctan2(u,q)
lsq = numpy.array((3e-1/nu)**2)

# now plot
fig = plt.figure()
ax1 = fig.add_subplot(211)
ax1.plot(lsq, numpy.degrees(pola), 'b.')
ax1.set_xlabel('Lambda^2 (m^2)')
ax1.set_ylabel('Polarization Angle (degrees)',color='b')
ax1.set_ylim(-180.,180.)
for tl in ax1.get_yticklabels():
    tl.set_color('b')

#pylab.axis([nu[0],nu[len(nu)-1],-180,180])
#pylab.subplot(3,1,2)
#pylab.plot(q,u)
#pylab.errorbar(q,u,xerr=err,yerr=err,fmt='.-')
#pylab.xlabel('Q (Jy)')
#pylab.ylabel('U (Jy)')
#meanp = numpy.mean(numpy.sqrt(q**2 + u**2))
#ar = numpy.arange(100*2*3.14)/100.
#pylab.plot(meanp*numpy.cos(ar), meanp*numpy.sin(ar),'--')
#pylab.axis([-1.5*meanp,1.5*meanp,-1.5*meanp,1.5*meanp])
#pylab.subplot(3,1,2)
ax2 = ax1.twinx()
sigmap = (q**2*err + u**2*err)/(q**2 + u**2)
ax2.errorbar(lsq,numpy.sqrt(q**2 + u**2),yerr=sigmap,fmt='r*')
ax2.set_ylabel('Polarized flux (Jy)', color='r')
#pylab.axis([nu[0],nu[len(nu)-1],0,2])
for tl in ax2.get_yticklabels():
    tl.set_color('r')

#ax1 = fig.add_subplot(211)
pylab.subplot(2,1,2)
pylab.plot(rm, numpy.sqrt(dirty_re**2 + dirty_im**2), 'b-', label='Dirty', linewidth=0.5)
pylab.plot(rm, numpy.sqrt(clean_re**2 + clean_im**2), 'b-', label='Clean', linewidth=2)
pylab.xlabel('RM (rad/m^2)')
pylab.ylabel('Polarized flux (mJy/RM bin)')
pylab.legend()

plt.show()
