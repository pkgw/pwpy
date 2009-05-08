# claw, 7may09
#
# script to plot complex leakages for comparison

import asciidata, pylab, numpy

def run():
    # params
    type = 'xy'

# funky variable iterating (doesn't work when run as script)
#    l = locals()
#    for i in range(8):
#        l['a'+str(i)] = asciidata.open('3c286-leak1.amp.txt')
#        l['p'+str(i)] = asciidata.open('3c286-leak1.phase.txt')

    a = []; a2 = []
    p = []; p2 = []
    for i in range(1,9):
        a.append(asciidata.open ('3c286-leak%d.amp.txt' % i))
        p.append(asciidata.open ('3c286-leak%d.phase.txt' % i))
        a2.append(asciidata.open ('3c138-leak%d.amp.txt' % i))
        p2.append(asciidata.open ('3c138-leak%d.phase.txt' % i))

    # group 3c286
    # original phase and amplitude
    px = numpy.array([p[0].columns[0],p[1].columns[0],p[2].columns[0],p[3].columns[0],p[4].columns[0],p[5].columns[0],p[6].columns[0],p[7].columns[0]])
    ax = numpy.array([a[0].columns[0],a[1].columns[0],a[2].columns[0],a[3].columns[0],a[4].columns[0],a[5].columns[0],a[6].columns[0],a[7].columns[0]])
    py = numpy.array([p[0].columns[1],p[1].columns[1],p[2].columns[1],p[3].columns[1],p[4].columns[1],p[5].columns[1],p[6].columns[1],p[7].columns[1]])
    ay = numpy.array([a[0].columns[1],a[1].columns[1],a[2].columns[1],a[3].columns[1],a[4].columns[1],a[5].columns[1],a[6].columns[1],a[7].columns[1]])
    # derived r and i
    rx = ax * numpy.cos(numpy.radians(px))
    ix = ax * numpy.sin(numpy.radians(px))
    ry = ay * numpy.cos(numpy.radians(py))
    iy = ay * numpy.sin(numpy.radians(py))

    # group 3c138
    # original phase and amplitude
    px2 = numpy.array([p2[0].columns[0],p2[1].columns[0],p2[2].columns[0],p2[3].columns[0],p2[4].columns[0],p2[5].columns[0],p2[6].columns[0],p2[7].columns[0]])
    ax2 = numpy.array([a2[0].columns[0],a2[1].columns[0],a2[2].columns[0],a2[3].columns[0],a2[4].columns[0],a2[5].columns[0],a2[6].columns[0],a2[7].columns[0]])
    py2 = numpy.array([p2[0].columns[1],p2[1].columns[1],p2[2].columns[1],p2[3].columns[1],p2[4].columns[1],p2[5].columns[1],p2[6].columns[1],p2[7].columns[1]])
    ay2 = numpy.array([a2[0].columns[1],a2[1].columns[1],a2[2].columns[1],a2[3].columns[1],a2[4].columns[1],a2[5].columns[1],a2[6].columns[1],a2[7].columns[1]])
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
        # two per source
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
