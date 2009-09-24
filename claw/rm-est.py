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

pola = 0.5*numpy.arctan2(q,u)
dpola = numpy.array([pola[i+1]-pola[i] for i in range(len(pola)-1)])
dlsq = numpy.array([(3e-1/nu[i+1])**2-(3e-1/nu[i])**2 for i in range(len(nu)-1)])
lsq = numpy.array([3e-1/numpy.mean([nu[i],nu[i+1]])**2 for i in range(len(nu)-1)])
rm = -1*numpy.mean(dpola/dlsq)  # in rad/m2

pylab.figure(1)
pylab.subplot(2,2,1)
pylab.plot(nu, numpy.degrees(pola), '.')
pylab.xlabel('Freq (GHz)')
pylab.ylabel('Polarization Angle (degrees)')
#pylab.axis([nu[0],nu[len(nu)-1],-180,180])
pylab.subplot(2,2,2)
#pylab.plot(q,u)
pylab.errorbar(q,u,xerr=err,yerr=err,fmt='.-')
pylab.xlabel('Q (Jy)')
pylab.ylabel('U (Jy)')
meanp = numpy.mean(numpy.sqrt(q**2 + u**2))
ar = numpy.arange(100*2*3.14)/100.
pylab.plot(meanp*numpy.cos(ar), meanp*numpy.sin(ar),'--')
pylab.axis([-1.5*meanp,1.5*meanp,-1.5*meanp,1.5*meanp])
pylab.subplot(2,2,3)
sigmap = (q**2*err + u**2*err)/(q**2 + u**2)
pylab.errorbar(nu,numpy.sqrt(q**2 + u**2),yerr=sigmap,fmt='.')
pylab.xlabel('Freq (GHz)')
pylab.ylabel('Polarized Flux (Jy)')
#pylab.axis([nu[0],nu[len(nu)-1],0,2])
pylab.subplot(2,2,4)
pylab.plot(lsq, dpola, '.', label='RM = '+str(rm))
pylab.xlabel('Lambda^2 (m2)')
pylab.ylabel('dPola (rad)')
pylab.legend()

# plot two log results on same plots
# optionally load file 2
if len(sys.argv) == 3:
    print 'loading ', sys.argv[2]
    f = asciidata.AsciiData(sys.argv[2])
    nu = numpy.array(f.columns[0])
    q = numpy.array(f.columns[1])
    u = numpy.array(f.columns[2])
    err = numpy.array(f.columns[3])

    pola = 0.5*numpy.arctan2(q,u)
    dpola = numpy.array([pola[i+1]-pola[i] for i in range(len(pola)-1)])
    dlsq = numpy.array([(3e-1/nu[i+1])**2-(3e-1/nu[i])**2 for i in range(len(nu)-1)])
    lsq = numpy.array([3e-1/numpy.mean([nu[i],nu[i+1]])**2 for i in range(len(nu)-1)])
    rm = -1*numpy.mean(dpola/dlsq)  # in rad/m2

    pylab.figure(1)
    pylab.subplot(2,2,1)
    pylab.plot(nu, numpy.degrees(pola), '.')
    pylab.xlabel('Freq (GHz)')
    pylab.ylabel('Polarization Angle (degrees)')
#    pylab.axis([nu[0],nu[len(nu)-1],-180,180])
    pylab.subplot(2,2,2)
    #pylab.plot(q,u)
    pylab.errorbar(q,u,xerr=err,yerr=err,fmt='.-')
    pylab.xlabel('Q (Jy)')
    pylab.ylabel('U (Jy)')
    meanp = numpy.mean(numpy.sqrt(q**2 + u**2))
    ar = numpy.arange(100*2*3.14)/100.
    pylab.plot(meanp*numpy.cos(ar), meanp*numpy.sin(ar),'--')
    pylab.axis([-1.5*meanp,1.5*meanp,-1.5*meanp,1.5*meanp])
    pylab.subplot(2,2,3)
    sigmap = (q**2*err + u**2*err)/(q**2 + u**2)
    pylab.errorbar(nu,numpy.sqrt(q**2 + u**2),yerr=sigmap,fmt='.')
    pylab.xlabel('Freq (GHz)')
    pylab.ylabel('Polarized Flux (Jy)')
#    pylab.axis([nu[0],nu[len(nu)-1],0,2])
    pylab.subplot(2,2,4)
    pylab.plot(lsq, dpola, '.', label='RM = '+str(rm))
    pylab.xlabel('Lambda^2 (m2)')
    pylab.ylabel('dPola (rad)')
    pylab.legend()
    
pylab.show()
