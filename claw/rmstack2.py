#!/usr/bin/env python
# claw, 16may2010

# script reads in cleaned rm spectra, shifts to mean-rm=0 and adds them

import pylab,numpy,asciidata
import scipy.optimize as opt

path='/indirect/big_scr2/claw/data/ata/nvss-rm-best/tmpfiles/'
use = ['074948+555421','084124+705341','104244+120331','123039+121758','125611-054720','133108+303032','153150+240243','165111+045919','165112+045917','172025-005852','172025-005857','184226+794517','184150+794728','192451-291431','211636-205551']
rmssum=0

for n in use:
    print ''
    print 'loading ', n
    f = asciidata.AsciiData(path + 'tmp-rmsall' + n, comment_char='#')
    rms = float(numpy.array(f.columns[0]))
    print 'loaded rms = %.3f' % (rms)

    f2 = asciidata.AsciiData(path + 'tmp-rmspectrumall' + n, comment_char='#')
    rm = numpy.array(f2.columns[1])
    if use.index(n) == 0:
        rmorig = rm
        flarr = numpy.zeros(len(rmorig))
        flarrorig = numpy.zeros(len(rmorig))
    clean_re = numpy.array(f2.columns[4])
    clean_im = numpy.array(f2.columns[5])
    fl = numpy.sqrt(clean_re**2 + clean_im**2)

    f3 = asciidata.AsciiData(path + 'tmp-rms1430' + n, comment_char='#')
    rms3 = float(numpy.array(f3.columns[0]))
    print 'loaded rms3 = %.3f' % (rms3)

    f3 = asciidata.AsciiData(path + 'tmp-rmspectrum1430' + n, comment_char='#')
    rm3 = numpy.array(f3.columns[1])
    clean_re3 = numpy.array(f3.columns[4])
    clean_im3 = numpy.array(f3.columns[5])
    fl3 = numpy.sqrt(clean_re3**2 + clean_im3**2)

# approach 1:  measure rm from low-res spectrum.  shift hi-res, sum, etc.
    gaussian = lambda amp,x,x0,sigma: amp * numpy.exp(-1.*((x-x0)/(numpy.log(2)*sigma))**2)  # normalized gaussian SNR distribution for comparison.
    fitfunc = lambda p, x:  gaussian(p[0], x, p[1], p[2])
    errfunc = lambda p, x, y: fitfunc(p, x)**2 - y**2 + rms3**2  # optimize including noise bias
    p0 = [400., 0., 600.]

    p1, success = opt.leastsq(errfunc, p0[:], args = (rm3, fl3))

    if success:
        print 'Fit successful!  Results:'
        print p1
        meanrm = p1[1]
        meanfl = p1[0]

# approach 2:  measure mean rm of all bins > 5sigma
#    index = numpy.where(fl > 5*rms)
#    meanrm = (fl[index]*rm[index]).sum()/fl[index].sum()
#    print 'Flux-weighted RM: %.3f' % (meanrm)

#    print 'Fractional flux of shifted RM components'
#    frfl = fl[index]/(numpy.sqrt(fl[index]**2-rms**2)).sum()
#    rmshift = rm[index]-meanrm
#    print rmshift, frfl
#    flarr = flarr + frfl[where(rmshift == rmorig)]

    meanrmindex = numpy.where(rm >= meanrm-1)[0][0]  # hack!  ok for binsize of 2 rad/m2 probably
    print meanrmindex

    flarr[500:4500] = flarr[500:4500] + fl[meanrmindex-2000:meanrmindex+2000]/meanfl
    flarrorig = flarrorig + fl/meanfl

    pylab.figure(1)
    pylab.subplot(211)
    pylab.plot(rm[500:4500],fl[meanrmindex-2000:meanrmindex+2000]/meanfl)
    pylab.subplot(212)
    pylab.plot(rm[500:4500],fl[500:4500]/meanfl)

print 'Fitting Gaussian to sum of normalized, shifted cleaned RM spectra...'
sigma = 60.
gaussian = lambda amp,x,x0,sigma,shift: amp * numpy.exp(-1.*((x-x0)/(numpy.log(2)*sigma))**2) + shift  # normalized gaussian SNR distribution for comparison.
fitfunc = lambda p, x:  gaussian(p[0], x, p[1], p[2], p[3])
errfunc = lambda p, x, y: fitfunc(p, x)**2 - y**2
p0 = [0.03,0.,80.,0.001]

p1, success = opt.leastsq(errfunc, p0[:], args = (rmorig[500:4500], flarr[500:4500]))
p2, success = opt.leastsq(errfunc, p0[:], args = (rmorig[500:4500], flarrorig[500:4500]))

pylab.figure(2)
if success:
    print 'Fit successful!  Results:'
    print p1
    print p2
    pylab.plot(rmorig,flarr)
    pylab.plot(rmorig,flarrorig)
    pylab.plot(rmorig, fitfunc(p1, rmorig), '--')
    pylab.plot(rmorig, fitfunc(p2, rmorig), '--')
    pylab.xlabel('RM (rad/m2)')
    pylab.ylabel('Relative flux')

pylab.show()
