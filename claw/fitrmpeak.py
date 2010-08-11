#!/usr/bin/env python

#claw, 5May2010
#Script to take a cleaned rm spectrum and rms and fit rm peaks
#First shows clean rm spectrum with 7sigma line.
#Next asks for rm range for fitting.
#Finally fits gaussian in requested range.

import sys

if len(sys.argv) != 3:
    print 'sorry dude, need a rmspectrum and rms file'
    exit(1)

import numpy,pylab,asciidata
import scipy.optimize as opt

interactive = 1
end = 0

print 'loading ', sys.argv[1]
f2 = asciidata.AsciiData(sys.argv[1], comment_char='#')
rm = numpy.array(f2.columns[1])
dirty_re = numpy.array(f2.columns[2])
dirty_im = numpy.array(f2.columns[3])
dirty_am = numpy.sqrt(dirty_re**2 + dirty_im**2)
clean_re = numpy.array(f2.columns[4])
clean_im = numpy.array(f2.columns[5])
clean_am = numpy.sqrt(clean_re**2 + clean_im**2)

print 'loading ', sys.argv[2]
f = asciidata.AsciiData(sys.argv[2])
rms = float(numpy.array(f.columns[0]))
print 'loaded rms = %.3f' % (rms)

# useful functions
gaussian = lambda amp,x,x0,sigma: amp * numpy.exp(-1.*((x-x0)/(numpy.log(2)*sigma))**2)  # normalized gaussian SNR distribution for comparison.
fitfunc = lambda p, x:  gaussian(p[0], x, p[1], p[2])
errfunc = lambda p, x, y: fitfunc(p, x)**2 - y**2 + rms**2  # optimize including noise bias

while 1:
    if interactive:
        # identify rm range to fit
        print 'Need to identify range to fit...'
        pylab.figure(1)
        pylab.plot(rm, clean_am)
        pylab.plot(rm, dirty_am)
        pylab.plot(rm, 5*rms*numpy.ones(len(rm)),'-.')
        pylab.plot(rm, 7*rms*numpy.ones(len(rm)),'--')
        pylab.show()

    # use input rm range to cut area for fit
    if interactive:
        try:
            rmmin = float(raw_input('What is the min RM?\n'))
        except:
            rmmin = numpy.min(rm)-1
            print 'Using min of range'
        try:
            rmmax = float(raw_input('What is the max RM?\n'))
        except:
            rmmax = numpy.max(rm)+1
            print 'Using max of range'
    else:
        rmmin = numpy.min(rm)-1
        print 'Using min of range'
        rmmax = numpy.max(rm)+1
        print 'Using max of range'

    fitindex = numpy.arange(numpy.where(rm>=rmmin)[0][0],numpy.where(rm<=rmmax)[0][-1])
#    fitindex = numpy.concatenate((fitindex[0:2000],fitindex[len(fitindex)-20:len(fitindex)]))  # hackalicious!
    rm = rm[fitindex]
    clean_am = clean_am[fitindex]
    dirty_am = dirty_am[fitindex]

    if interactive:
        try:
            amp = float(raw_input('amp?'))
            center = float(raw_input('center?'))
            width = float(raw_input('width?'))
            p0 = [amp, center, width]
        except:
            p0 = [max(clean_am), 0., 50.]  # initial guess of params
    else:
        p0 = [max(clean_am), 0., 50.]  # initial guess of params

    print 'Using p0:', p0

    # fit
    p1, success = opt.leastsq(errfunc, p0[:], args = (rm, clean_am))

    if success:
        print 'Fit successful!  Results:'
        print p1
        print
        print 'Peak, center +- err, SNR'
        print '%.1f & %.1f +- %.1f & %d \\\\' % (p1[0],p1[1],p1[2]/(2*p1[0]/rms),p1[0]/rms)
        print
        print 'RM 5sigma limit (poli/RMbeam)'
        print '%.1f/%.1f ' % (5*rms,p1[2])
        print
        if interactive == 1:
            pylab.figure(2)
            pylab.clf()
            pylab.plot(rm, fitfunc(p1, rm), label='Fit')
            pylab.plot(rm, clean_am, label='Cleaned')
            pylab.legend()
            pylab.show()

    if interactive:
        try: 
            end = int(raw_input('Done? (1 or enter for yes)'))
        except:
            end = 1
    else:
        end = 1

    if end == 1:
        break
