# claw, 7may09
#
# script to plot complex leakages for comparison

import asciidata, pylab, numpy

def run():
    # params
    type = 'test'

# funky variable iterating (doesn't work when run as script)
#    l = locals()
#    for i in range(8):
#        l['a'+str(i)] = asciidata.open('3c286-leak1.amp.txt')
#        l['p'+str(i)] = asciidata.open('3c286-leak1.phase.txt')

    a = []
    for i in range(8):
        a.append(asciidata.open ('3c286-leak%d.amp.txt' % i))
        p.append(asciidata.open ('3c286-leak%d.phase.txt' % i))
        a2.append(asciidata.open ('3c138-leak%d.amp.txt' % i))
        p2.append(asciidata.open ('3c138-leak%d.phase.txt' % i))

    # group 3c286
    # original phase and amplitude
    px = numpy.array([p[0].columns[0],p[1].columns[0],p[2].columns[0],p[3].columns[0],p[4].columns[0],p[5].columns[0],p[6].columns[0],p[7].columns[0]])
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
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
            pylab.figure(2)
            pylab.plot(ry[:,i],iy[:,i],'.-')
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
            pylab.figure(3)
            pylab.plot(rx2[:,i],ix2[:,i],'.-')
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
            pylab.figure(4)
            pylab.plot(ry2[:,i],iy2[:,i],'.-')
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')

    pylab.show()

if __name__ == '__main__':
    run()
