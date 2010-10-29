#!/usr/bin/env python

import sys, asciidata, numpy, pylab

f1 = '/indirect/big_scr2/claw/data/ata/polcal2/oct2010/log.3c286.1430.self-new'
f2 = '/indirect/big_scr2/claw/data/ata/polcal2/oct2010/log.3c286.1430.polcal-new'
f3 = '/indirect/big_scr2/claw/data/ata/hex14-polcal/oct2010/log.3c286.1430.self-new'
f4 = '/indirect/big_scr2/claw/data/ata/hex14-polcal/oct2010/log.3c286.1430.polcal-new'
f5 = '/indirect/big_scr2/claw/data/ata/hex14-polcal-sep7/oct2010/log.3c286.1430.self-new'
f6 = '/indirect/big_scr2/claw/data/ata/hex14-polcal-sep7/oct2010/log.3c286.1430.polcal-new'

def plot(file1, file2, color='blue'):
# load files
    print 'loading reference ', file1
    f = asciidata.AsciiData(file1, comment_char='5')
    nu = numpy.array(f.columns[0])
    q = numpy.array(f.columns[1])
    u = numpy.array(f.columns[2])
    err = numpy.array(f.columns[3])

    print 'loading other ', file2
    f2 = asciidata.AsciiData(file2, comment_char='5')
    nu2 = numpy.array(f2.columns[0])
    q2 = numpy.array(f2.columns[1])
    u2 = numpy.array(f2.columns[2])
    err2 = numpy.array(f2.columns[3])

    meanq = (q2-q).mean()
    meanu = (u2-u).mean()
    stdq = (q2-q).std()
    stdu = (u2-u).std()
    p = numpy.sqrt(q.mean()**2 + u.mean()**2)

    perr = numpy.sqrt(meanq**2 + meanu**2)/p
    stdp = numpy.sqrt(stdq**2 + stdu**2)/p
    therr = numpy.degrees(0.5*numpy.arctan2(meanu,meanq))
    print '$%1.3f\pm%1.3f$ & $%3.0f$ ' % (perr,stdp,therr)
    
    pylab.figure(1)
    pylab.plot(q,u,'b.')
    pylab.plot(q2,u2,'r.')
    pylab.xlabel('Q/Jy and Qerr/%p')
    pylab.ylabel('U/Jy and Uerr/%p')

    for i in range(len(nu)):
        pylab.arrow(0, 0, (q2[i] - q[i])/p, (u2[i] - u[i])/p, fill=0, edgecolor=color)

    pylab.axis([-0.4*p,0.5*p,-0.4*p,1.1*p])

if __name__ == '__main__':
#    plot(f1, f2)
#    plot(f3, f4)
    plot(f5, f6)

    pylab.show()
