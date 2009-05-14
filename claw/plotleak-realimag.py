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
    for i in range(1,33):
        a.append(asciidata.open ('3c138-leak%d.amp.txt' % i))
        p.append(asciidata.open ('3c138-leak%d.phase.txt' % i))
        a2.append(asciidata.open ('split32/3c138-leak%d.amp.txt' % i))
        p2.append(asciidata.open ('split32/3c138-leak%d.phase.txt' % i))

    nants = len(a[0][0])
    print '%d antennas...' % (nants)
    antnum = [1,4,7,10,13,16,19,22,25,28,31,34,37,40,43,2,5,8,11,14,17,20,23,26,29,32,35,38,41,3,6,9,12,15,18,21,24,27,30,33,36,39,42]  # hack for how rows messed up by 'cut'

    # group 3c286
    # original phase and amplitude
#    px = numpy.array([p[0].columns[0],p[1].columns[0],p[2].columns[0],p[3].columns[0],p[4].columns[0],p[5].columns[0],p[6].columns[0],p[7].columns[0]])
#    ax = numpy.array([a[0].columns[0],a[1].columns[0],a[2].columns[0],a[3].columns[0],a[4].columns[0],a[5].columns[0],a[6].columns[0],a[7].columns[0]])
#    py = numpy.array([p[0].columns[1],p[1].columns[1],p[2].columns[1],p[3].columns[1],p[4].columns[1],p[5].columns[1],p[6].columns[1],p[7].columns[1]])
#    ay = numpy.array([a[0].columns[1],a[1].columns[1],a[2].columns[1],a[3].columns[1],a[4].columns[1],a[5].columns[1],a[6].columns[1],a[7].columns[1]])
    px = numpy.array([p[0].columns[0],p[1].columns[0],p[2].columns[0],p[3].columns[0],p[4].columns[0],p[5].columns[0],p[6].columns[0],p[7].columns[0],p[8].columns[0],p[9].columns[0],p[10].columns[0],p[11].columns[0],p[12].columns[0],p[13].columns[0],p[14].columns[0],p[15].columns[0],p[16].columns[0],p[17].columns[0],p[18].columns[0],p[19].columns[0],p[20].columns[0],p[21].columns[0],p[22].columns[0],p[23].columns[0],p[24].columns[0],p[25].columns[0],p[26].columns[0],p[27].columns[0],p[28].columns[0],p[29].columns[0],p[30].columns[0],p[31].columns[0]])
    ax = numpy.array([a[0].columns[0],a[1].columns[0],a[2].columns[0],a[3].columns[0],a[4].columns[0],a[5].columns[0],a[6].columns[0],a[7].columns[0],a[8].columns[0],a[9].columns[0],a[10].columns[0],a[11].columns[0],a[12].columns[0],a[13].columns[0],a[14].columns[0],a[15].columns[0],a[16].columns[0],a[17].columns[0],a[18].columns[0],a[19].columns[0],a[20].columns[0],a[21].columns[0],a[22].columns[0],a[23].columns[0],a[24].columns[0],a[25].columns[0],a[26].columns[0],a[27].columns[0],a[28].columns[0],a[29].columns[0],a[30].columns[0],a[31].columns[0]])
    py = numpy.array([p[0].columns[1],p[1].columns[1],p[2].columns[1],p[3].columns[1],p[4].columns[1],p[5].columns[1],p[6].columns[1],p[7].columns[1],p[8].columns[1],p[9].columns[1],p[10].columns[1],p[11].columns[1],p[12].columns[1],p[13].columns[1],p[14].columns[1],p[15].columns[1],p[16].columns[1],p[17].columns[1],p[18].columns[1],p[19].columns[1],p[20].columns[1],p[21].columns[1],p[22].columns[1],p[23].columns[1],p[24].columns[1],p[25].columns[1],p[26].columns[1],p[27].columns[1],p[28].columns[1],p[29].columns[1],p[30].columns[1],p[31].columns[1]])
    ay = numpy.array([a[0].columns[1],a[1].columns[1],a[2].columns[1],a[3].columns[1],a[4].columns[1],a[5].columns[1],a[6].columns[1],a[7].columns[1],a[8].columns[1],a[9].columns[1],a[10].columns[1],a[11].columns[1],a[12].columns[1],a[13].columns[1],a[14].columns[1],a[15].columns[1],a[16].columns[1],a[17].columns[1],a[18].columns[1],a[19].columns[1],a[20].columns[1],a[21].columns[1],a[22].columns[1],a[23].columns[1],a[24].columns[1],a[25].columns[1],a[26].columns[1],a[27].columns[1],a[28].columns[1],a[29].columns[1],a[30].columns[1],a[31].columns[1]])

    npts = len(ax)
    print '%d frequency points...' % (npts)

    # derived r and i
    rx = ax * numpy.cos(numpy.radians(px))
    ix = ax * numpy.sin(numpy.radians(px))
    ry = ay * numpy.cos(numpy.radians(py))
    iy = ay * numpy.sin(numpy.radians(py))

    # group 3c138
    # original phase and amplitude
#    px2 = numpy.array([p2[0].columns[0],p2[1].columns[0],p2[2].columns[0],p2[3].columns[0],p2[4].columns[0],p2[5].columns[0],p2[6].columns[0],p2[7].columns[0]])
#    ax2 = numpy.array([a2[0].columns[0],a2[1].columns[0],a2[2].columns[0],a2[3].columns[0],a2[4].columns[0],a2[5].columns[0],a2[6].columns[0],a2[7].columns[0]])
#    py2 = numpy.array([p2[0].columns[1],p2[1].columns[1],p2[2].columns[1],p2[3].columns[1],p2[4].columns[1],p2[5].columns[1],p2[6].columns[1],p2[7].columns[1]])
#    ay2 = numpy.array([a2[0].columns[1],a2[1].columns[1],a2[2].columns[1],a2[3].columns[1],a2[4].columns[1],a2[5].columns[1],a2[6].columns[1],a2[7].columns[1]])
    px2 = numpy.array([p2[0].columns[0],p2[1].columns[0],p2[2].columns[0],p2[3].columns[0],p2[4].columns[0],p2[5].columns[0],p2[6].columns[0],p2[7].columns[0],p2[8].columns[0],p2[9].columns[0],p2[10].columns[0],p2[11].columns[0],p2[12].columns[0],p2[13].columns[0],p2[14].columns[0],p2[15].columns[0],p2[16].columns[0],p2[17].columns[0],p2[18].columns[0],p2[19].columns[0],p2[20].columns[0],p2[21].columns[0],p2[22].columns[0],p2[23].columns[0],p2[24].columns[0],p2[25].columns[0],p2[26].columns[0],p2[27].columns[0],p2[28].columns[0],p2[29].columns[0],p2[30].columns[0],p2[31].columns[0]])
    ax2 = numpy.array([a2[0].columns[0],a2[1].columns[0],a2[2].columns[0],a2[3].columns[0],a2[4].columns[0],a2[5].columns[0],a2[6].columns[0],a2[7].columns[0],a2[8].columns[0],a2[9].columns[0],a2[10].columns[0],a2[11].columns[0],a2[12].columns[0],a2[13].columns[0],a2[14].columns[0],a2[15].columns[0],a2[16].columns[0],a2[17].columns[0],a2[18].columns[0],a2[19].columns[0],a2[20].columns[0],a2[21].columns[0],a2[22].columns[0],a2[23].columns[0],a2[24].columns[0],a2[25].columns[0],a2[26].columns[0],a2[27].columns[0],a2[28].columns[0],a2[29].columns[0],a2[30].columns[0],a2[31].columns[0]])
    py2 = numpy.array([p2[0].columns[1],p2[1].columns[1],p2[2].columns[1],p2[3].columns[1],p2[4].columns[1],p2[5].columns[1],p2[6].columns[1],p2[7].columns[1],p2[8].columns[1],p2[9].columns[1],p2[10].columns[1],p2[11].columns[1],p2[12].columns[1],p2[13].columns[1],p2[14].columns[1],p2[15].columns[1],p2[16].columns[1],p2[17].columns[1],p2[18].columns[1],p2[19].columns[1],p2[20].columns[1],p2[21].columns[1],p2[22].columns[1],p2[23].columns[1],p2[24].columns[1],p2[25].columns[1],p2[26].columns[1],p2[27].columns[1],p2[28].columns[1],p2[29].columns[1],p2[30].columns[1],p2[31].columns[1]])
    ay2 = numpy.array([a2[0].columns[1],a2[1].columns[1],a2[2].columns[1],a2[3].columns[1],a2[4].columns[1],a2[5].columns[1],a2[6].columns[1],a2[7].columns[1],a2[8].columns[1],a2[9].columns[1],a2[10].columns[1],a2[11].columns[1],a2[12].columns[1],a2[13].columns[1],a2[14].columns[1],a2[15].columns[1],a2[16].columns[1],a2[17].columns[1],a2[18].columns[1],a2[19].columns[1],a2[20].columns[1],a2[21].columns[1],a2[22].columns[1],a2[23].columns[1],a2[24].columns[1],a2[25].columns[1],a2[26].columns[1],a2[27].columns[1],a2[28].columns[1],a2[29].columns[1],a2[30].columns[1],a2[31].columns[1]])
    # derived r and i
    rx2 = ax2 * numpy.cos(numpy.radians(px2))
    ix2 = ax2 * numpy.sin(numpy.radians(px2))
    ry2 = ay2 * numpy.cos(numpy.radians(py2))
    iy2 = ay2 * numpy.sin(numpy.radians(py2))

    if type == 'polar':
    # polar plot
        for i in range(nants):
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
        for i in range(nants):
            pylab.figure(1)
            pylab.plot(rx[:,i],ix[:,i],'.-')
            pylab.text(rx[0,i],ix[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
            pylab.figure(2)
            pylab.plot(ry[:,i],iy[:,i],'.-')
            pylab.text(ry[0,i],iy[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
            pylab.figure(3)
            pylab.plot(rx2[:,i],ix2[:,i],'.-')
            pylab.text(rx2[0,i],ix2[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
            pylab.figure(4)
            pylab.plot(ry2[:,i],iy2[:,i],'.-')
            pylab.text(ry2[0,i],iy2[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')

    pylab.show()

if __name__ == '__main__':
    run()
