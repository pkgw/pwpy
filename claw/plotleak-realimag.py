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

    a12 = asciidata.open('3c138-leak1.amp.txt')
    p12 = asciidata.open('3c138-leak1.phase.txt')
    a22 = asciidata.open('3c138-leak2.amp.txt')
    p22 = asciidata.open('3c138-leak2.phase.txt')
    a32 = asciidata.open('3c138-leak3.amp.txt')
    p32 = asciidata.open('3c138-leak3.phase.txt')
    a42 = asciidata.open('3c138-leak4.amp.txt')
    p42 = asciidata.open('3c138-leak4.phase.txt')

    # group 3c286
    # original phase and amplitude
    px = numpy.array([p1.columns[0],p2.columns[0],p3.columns[0],p4.columns[0]])
    ax = numpy.array([a1.columns[0],a2.columns[0],a3.columns[0],a4.columns[0]])
    py = numpy.array([p1.columns[1],p2.columns[1],p3.columns[1],p4.columns[1]])
    ay = numpy.array([a1.columns[1],a2.columns[1],a3.columns[1],a4.columns[1]])
    # derived x and y
    xx = ax * numpy.cos(numpy.radians(px))
    yx = ax * numpy.sin(numpy.radians(px))
    xy = ay * numpy.cos(numpy.radians(py))
    yy = ay * numpy.sin(numpy.radians(py))

    # group 3c138
    # original phase and amplitude
    px2 = numpy.array([p12.columns[0],p22.columns[0],p32.columns[0],p42.columns[0]])
    ax2 = numpy.array([a12.columns[0],a22.columns[0],a32.columns[0],a42.columns[0]])
    py2 = numpy.array([p12.columns[1],p22.columns[1],p32.columns[1],p42.columns[1]])
    ay2 = numpy.array([a12.columns[1],a22.columns[1],a32.columns[1],a42.columns[1]])
    # derived x and y
    xx2 = ax2 * numpy.cos(numpy.radians(px2))
    yx2 = ax2 * numpy.sin(numpy.radians(px2))
    xy2 = ay2 * numpy.cos(numpy.radians(py2))
    yy2 = ay2 * numpy.sin(numpy.radians(py2))

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
    # x-y plot
        for i in range(len(px[0])):
            pylab.figure(1)
            pylab.plot(xx[:,i],yx[:,i],'.-')
            pylab.figure(2)
            pylab.plot(xy[:,i],yy[:,i],'.-')
            pylab.figure(3)
            pylab.plot(xx2[:,i],yx2[:,i],'.-')
            pylab.figure(4)
            pylab.plot(xy2[:,i],yy2[:,i],'.-')

    pylab.show()

if __name__ == '__main__':
    run()
