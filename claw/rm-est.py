#!/usr/bin/env python

"""
claw, 22sep09
Script to take Bryan's RM imaging results log file and plot diagnostic plots.
"""

import sys

if len(sys.argv) < 3:
    print 'dude, give me a log and rmspectrum file.  wtf?'
    exit(1)
elif len(sys.argv) == 4:
    print 'will plot rmspectrum with 5sigma threshold.'
elif len(sys.argv) == 5:
    print 'i\'m afraid i can\'t do that, dave.'
elif len(sys.argv) == 6:
    print 'will plot two rmspectra with 5sigma threshold.'
elif len(sys.argv) == 7:
    print 'will save two rmspectra with 5sigma threshold.'

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
fig.subplots_adjust(hspace=0.3)
ax1 = fig.add_subplot(211)
if len(sys.argv) == 7:
    plt.title(sys.argv[6])
ax1.plot(lsq, numpy.degrees(pola), 'b.')
ax1.set_xlabel('Lambda^2 (m^2)')
ax1.set_ylabel('Pol. Angle (degrees)',color='b')
ax1.set_ylim(-200.,95.)
pylab.yticks(numpy.array([-90,-45,0,+45,+90]))
for tl in ax1.get_yticklabels():
    tl.set_color('b')

ax2 = ax1.twinx()
p = numpy.sqrt(q**2 + u**2)
sigmap = (q**2*err + u**2*err)/p**2
ax2.errorbar(lsq,p,yerr=sigmap,fmt='r*',linewidth=0.3)
ax2.set_ylim(min(p) - 0.1*(max(p)-min(p)), 2.0*max(p))
ax2.set_ylabel('Pol. flux (Jy)', color='r')
#pylab.axis([nu[0],nu[len(nu)-1],0,2])
for tl in ax2.get_yticklabels():
    tl.set_color('r')

ax3 = fig.add_subplot(413)
#ax3.plot(rm, numpy.sqrt(dirty_re**2 + dirty_im**2), 'b--', label='Dirty', linewidth=0.3)
ax3.plot(rm, numpy.sqrt(clean_re**2 + clean_im**2), 'b-', label='Clean', linewidth=2)
if len(sys.argv) == 3 or len(sys.argv) == 4:
    ax3.set_xlabel('RM (rad/m^2)')
#pylab.legend()

if len(sys.argv) > 3:
    print 'loading ', sys.argv[3]
    f = asciidata.AsciiData(sys.argv[3])
    rms1 = float(numpy.array(f.columns[0]))
    print 'loaded rms = %.3f' % (rms1)
    ax3.plot(rm, 5*rms1*(numpy.ones(len(rm))), '-.')

ax3.set_xlim(-5000.,5000.)

if len(sys.argv) > 5:
    # load files
    print 'loading ', sys.argv[4]
    f3 = asciidata.AsciiData(sys.argv[4], comment_char='#')
    rm = numpy.array(f3.columns[1])
    dirty_re = numpy.array(f3.columns[2])
    dirty_im = numpy.array(f3.columns[3])
    clean_re = numpy.array(f3.columns[4])
    clean_im = numpy.array(f3.columns[5])

    ax4 = fig.add_subplot(414)
#    ax4.plot(rm, numpy.sqrt(dirty_re**2 + dirty_im**2), 'b--', label='Dirty', linewidth=0.3)
    ax4.plot(rm, numpy.sqrt(clean_re**2 + clean_im**2), 'b-', label='Clean', linewidth=2)
    ax4.set_xlabel('RM (rad/m^2)')
    ax4.set_ylabel('Pol. flux (mJy/RM bin)',verticalalignment='bottom')
#    pylab.legend()

    print 'loading ', sys.argv[5]
    f = asciidata.AsciiData(sys.argv[5])
    rms2 = float(numpy.array(f.columns[0]))
    print 'loaded rms = %.3f' % (rms2)
    ax4.plot(rm, 5*rms2*(numpy.ones(len(rm))), '-.')
    ax4.set_xlim(-90000.,90000.)

fwhmhigh = 2.*numpy.sqrt(3.)/numpy.abs((3e-1/nu[len(nu)-1])**2-(3e-1/nu[0])**2)

# need fwhm of 1.4 and 2.0 bands
nu = nu[numpy.where((nu >= 1.2) & (nu <= 1.5))]
fwhmlow = 2.*numpy.sqrt(3.)/numpy.abs((3e-1/nu[len(nu)-1])**2-(3e-1/nu[0])**2)

if len(sys.argv) > 5:
    print 'highres 5sig, fwhm, lowres 5sig, fwhm:'
    print '%d & %d & %d & %d' % (5*rms1, fwhmhigh, 5*rms2, fwhmlow)

if len(sys.argv) == 7:
    print 'saving file to ', sys.argv[6]
    plt.savefig('plotrm-'+ sys.argv[6] + '-nice.png')
else:
    plt.show()
