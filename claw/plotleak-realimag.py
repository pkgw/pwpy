# claw, 7may09
#
# script to plot complex leakages for comparison

import asciidata, pylab, numpy

def run():
    # params
    type = 'xy'

    a1 = asciidata.open('3c286-leak1.amp.txt')
    p1 = asciidata.open('3c286-leak1.phase.txt')
    a2 = asciidata.open('3c286-leak2.amp.txt')
    p2 = asciidata.open('3c286-leak2.phase.txt')
    a3 = asciidata.open('3c286-leak3.amp.txt')
    p3 = asciidata.open('3c286-leak3.phase.txt')
    a4 = asciidata.open('3c286-leak4.amp.txt')
    p4 = asciidata.open('3c286-leak4.phase.txt')
    a5 = asciidata.open('3c286-leak5.amp.txt')
    p5 = asciidata.open('3c286-leak5.phase.txt')
    a6 = asciidata.open('3c286-leak6.amp.txt')
    p6 = asciidata.open('3c286-leak6.phase.txt')
    a7 = asciidata.open('3c286-leak7.amp.txt')
    p7 = asciidata.open('3c286-leak7.phase.txt')
    a8 = asciidata.open('3c286-leak8.amp.txt')
    p8 = asciidata.open('3c286-leak8.phase.txt')

    a12 = asciidata.open('3c138-leak1.amp.txt')
    p12 = asciidata.open('3c138-leak1.phase.txt')
    a22 = asciidata.open('3c138-leak2.amp.txt')
    p22 = asciidata.open('3c138-leak2.phase.txt')
    a32 = asciidata.open('3c138-leak3.amp.txt')
    p32 = asciidata.open('3c138-leak3.phase.txt')
    a42 = asciidata.open('3c138-leak4.amp.txt')
    p42 = asciidata.open('3c138-leak4.phase.txt')
    a52 = asciidata.open('3c138-leak5.amp.txt')
    p52 = asciidata.open('3c138-leak5.phase.txt')
    a62 = asciidata.open('3c138-leak6.amp.txt')
    p62 = asciidata.open('3c138-leak6.phase.txt')
    a72 = asciidata.open('3c138-leak7.amp.txt')
    p72 = asciidata.open('3c138-leak7.phase.txt')
    a82 = asciidata.open('3c138-leak8.amp.txt')
    p82 = asciidata.open('3c138-leak8.phase.txt')

    # group 3c286
    # original phase and amplitude
    px = numpy.array([p1.columns[0],p2.columns[0],p3.columns[0],p4.columns[0],p5.columns[0],p6.columns[0],p7.columns[0],p8.columns[0]])
    ax = numpy.array([a1.columns[0],a2.columns[0],a3.columns[0],a4.columns[0],a5.columns[0],a6.columns[0],a7.columns[0],a8.columns[0]])
    py = numpy.array([p1.columns[1],p2.columns[1],p3.columns[1],p4.columns[1],p5.columns[1],p6.columns[1],p7.columns[1],p8.columns[1]])
    ay = numpy.array([a1.columns[1],a2.columns[1],a3.columns[1],a4.columns[1],a5.columns[1],a6.columns[1],a7.columns[1],a8.columns[1]])
    # derived r and i
    rx = ax * numpy.cos(numpy.radians(px))
    ix = ax * numpy.sin(numpy.radians(px))
    ry = ay * numpy.cos(numpy.radians(py))
    iy = ay * numpy.sin(numpy.radians(py))

    # group 3c138
    # original phase and amplitude
    px2 = numpy.array([p12.columns[0],p22.columns[0],p32.columns[0],p42.columns[0],p52.columns[0],p62.columns[0],p72.columns[0],p82.columns[0]])
    ax2 = numpy.array([a12.columns[0],a22.columns[0],a32.columns[0],a42.columns[0],a52.columns[0],a62.columns[0],a72.columns[0],a82.columns[0]])
    py2 = numpy.array([p12.columns[1],p22.columns[1],p32.columns[1],p42.columns[1],p52.columns[1],p62.columns[1],p72.columns[1],p82.columns[1]])
    ay2 = numpy.array([a12.columns[1],a22.columns[1],a32.columns[1],a42.columns[1],a52.columns[1],a62.columns[1],a72.columns[1],a82.columns[1]])
    # derived r and i
    rx2 = ax2 * numpy.cos(numpy.radians(px2))
    ix2 = ax2 * numpy.sin(numpy.radians(px2))
    ry2 = ay2 * numpy.cos(numpy.radians(py2))
    iy2 = ay2 * numpy.sin(numpy.radians(py2))

    if type == 'polar':
    # polar plot
        for i in range(len(px[0])):
            pylab.figure(1)
            pylab.polar(numpy.radians(px[:,i]),ax[:,i],'.-')
            pylab.figure(2)
            pylab.polar(numpy.radians(py[:,i]),ay[:,i],'.-')
            pylab.figure(3)
            pylab.polar(numpy.radians(px2[:,i]),ax2[:,i],'.-')
            pylab.figure(4)
            pylab.polar(numpy.radians(py2[:,i]),ay2[:,i],'.-')

    if type == 'xy':
    # real-imag (x-y) plot
        for i in range(len(px[0])):
            pylab.figure(1)
            pylab.plot(rx[:,i],ix[:,i],'.-')
            pylab.figure(2)
            pylab.plot(ry[:,i],iy[:,i],'.-')
            pylab.figure(3)
            pylab.plot(rx2[:,i],ix2[:,i],'.-')
            pylab.figure(4)
            pylab.plot(ry2[:,i],iy2[:,i],'.-')

    pylab.show()

if __name__ == '__main__':
    run()
