# claw, 7may09
#
# Script to plot complex leakages for two different datasets.
# Assumes there are 8 frequency chunks.  File naming convention hardwired;  should change accordingly.
# Run as "python plotleak-realimag.py"

import asciidata, pylab, numpy

def run():
    # params for possible customization
    type = 'xy'

    a = []; a2 = []
    p = []; p2 = []
    print 'now building leak plot 1'
    for i in range(1,17):
        # specify ascii files output by 'split-cal-leak.csh'
        try:
            a.append(asciidata.AsciiData ('/indirect/big_scr3/claw/data/ata/nvss-rm/try3-2010/mosfxc-3c286-2010-100-leakamp%d.txt' % i))
            p.append(asciidata.AsciiData ('/indirect/big_scr3/claw/data/ata/nvss-rm/try3-2010/mosfxc-3c286-2010-100-leakphase%d.txt' % i))
        except:
            print 'skipping %d' % (i)
    print 'now building leak plot 2'
    for i in range(1,17):
        try:
            a2.append(asciidata.AsciiData ('/indirect/big_scr3/claw/data/ata/nvss-rm2/try5-1000/mosfxa-3c286-1000-100-flagged-leakamp%d.txt' % i))
            p2.append(asciidata.AsciiData ('/indirect/big_scr3/claw/data/ata/nvss-rm2/try5-1000/mosfxa-3c286-1000-100-flagged-leakphase%d.txt' % i))
        except:
            print 'skipping %d' % (i)

    nants = len(a[0][0])
    print '%d antennas...' % (nants)
    antnum = [1,4,7,10,13,16,19,22,25,28,31,34,37,40,43,2,5,8,11,14,17,20,23,26,29,32,35,38,41,3,6,9,12,15,18,21,24,27,30,33,36,39,42]  # hack for how rows messed up by 'cut' in 'split-cal-leak.csh'

    print numpy.shape(a)
    print numpy.shape(a2)

    # group for data set 1
    # original phase and amplitude
    # assuming 7 frequency chunks
#    px = numpy.array([p[0].columns[0],p[1].columns[0],p[2].columns[0],p[3].columns[0],p[4].columns[0],p[5].columns[0],p[6].columns[0]])
#    ax = numpy.array([a[0].columns[0],a[1].columns[0],a[2].columns[0],a[3].columns[0],a[4].columns[0],a[5].columns[0],a[6].columns[0]])
#    py = numpy.array([p[0].columns[1],p[1].columns[1],p[2].columns[1],p[3].columns[1],p[4].columns[1],p[5].columns[1],p[6].columns[1]])
#    ay = numpy.array([a[0].columns[1],a[1].columns[1],a[2].columns[1],a[3].columns[1],a[4].columns[1],a[5].columns[1],a[6].columns[1]])
# assuming 16 frequency chunks
    px = numpy.array([p[0].columns[0],p[1].columns[0],p[2].columns[0],p[3].columns[0],p[4].columns[0],p[5].columns[0],p[6].columns[0],p[7].columns[0],p[8].columns[0],p[9].columns[0],p[10].columns[0],p[11].columns[0],p[12].columns[0],p[13].columns[0],p[14].columns[0]])#,p[15].columns[0]])
    ax = numpy.array([a[0].columns[0],a[1].columns[0],a[2].columns[0],a[3].columns[0],a[4].columns[0],a[5].columns[0],a[6].columns[0],a[7].columns[0],a[8].columns[0],a[9].columns[0],a[10].columns[0],a[11].columns[0],a[12].columns[0],a[13].columns[0],a[14].columns[0]])#,a[15].columns[0]])
    py = numpy.array([p[0].columns[1],p[1].columns[1],p[2].columns[1],p[3].columns[1],p[4].columns[1],p[5].columns[1],p[6].columns[1],p[7].columns[1],p[8].columns[1],p[9].columns[1],p[10].columns[1],p[11].columns[1],p[12].columns[1],p[13].columns[1],p[14].columns[1]])#,p[15].columns[1]])
    ay = numpy.array([a[0].columns[1],a[1].columns[1],a[2].columns[1],a[3].columns[1],a[4].columns[1],a[5].columns[1],a[6].columns[1],a[7].columns[1],a[8].columns[1],a[9].columns[1],a[10].columns[1],a[11].columns[1],a[12].columns[1],a[13].columns[1],a[14].columns[1]])#,a[15].columns[1]])
# assuming 32 frequency chunks
#    px = numpy.array([p[0].columns[0],p[1].columns[0],p[2].columns[0],p[3].columns[0],p[4].columns[0],p[5].columns[0],p[6].columns[0],p[7].columns[0],p[8].columns[0],p[9].columns[0],p[10].columns[0],p[11].columns[0],p[12].columns[0],p[13].columns[0],p[14].columns[0],p[15].columns[0],p[16].columns[0],p[17].columns[0],p[18].columns[0],p[19].columns[0],p[20].columns[0],p[21].columns[0],p[22].columns[0],p[23].columns[0],p[24].columns[0],p[25].columns[0],p[26].columns[0],p[27].columns[0],p[28].columns[0],p[29].columns[0],p[30].columns[0],p[31].columns[0]])
#    ax = numpy.array([a[0].columns[0],a[1].columns[0],a[2].columns[0],a[3].columns[0],a[4].columns[0],a[5].columns[0],a[6].columns[0],a[7].columns[0],a[8].columns[0],a[9].columns[0],a[10].columns[0],a[11].columns[0],a[12].columns[0],a[13].columns[0],a[14].columns[0],a[15].columns[0],a[16].columns[0],a[17].columns[0],a[18].columns[0],a[19].columns[0],a[20].columns[0],a[21].columns[0],a[22].columns[0],a[23].columns[0],a[24].columns[0],a[25].columns[0],a[26].columns[0],a[27].columns[0],a[28].columns[0],a[29].columns[0],a[30].columns[0],a[31].columns[0]])
#    py = numpy.array([p[0].columns[1],p[1].columns[1],p[2].columns[1],p[3].columns[1],p[4].columns[1],p[5].columns[1],p[6].columns[1],p[7].columns[1],p[8].columns[1],p[9].columns[1],p[10].columns[1],p[11].columns[1],p[12].columns[1],p[13].columns[1],p[14].columns[1],p[15].columns[1],p[16].columns[1],p[17].columns[1],p[18].columns[1],p[19].columns[1],p[20].columns[1],p[21].columns[1],p[22].columns[1],p[23].columns[1],p[24].columns[1],p[25].columns[1],p[26].columns[1],p[27].columns[1],p[28].columns[1],p[29].columns[1],p[30].columns[1],p[31].columns[1]])
#    ay = numpy.array([a[0].columns[1],a[1].columns[1],a[2].columns[1],a[3].columns[1],a[4].columns[1],a[5].columns[1],a[6].columns[1],a[7].columns[1],a[8].columns[1],a[9].columns[1],a[10].columns[1],a[11].columns[1],a[12].columns[1],a[13].columns[1],a[14].columns[1],a[15].columns[1],a[16].columns[1],a[17].columns[1],a[18].columns[1],a[19].columns[1],a[20].columns[1],a[21].columns[1],a[22].columns[1],a[23].columns[1],a[24].columns[1],a[25].columns[1],a[26].columns[1],a[27].columns[1],a[28].columns[1],a[29].columns[1],a[30].columns[1],a[31].columns[1]])

    npts = len(ax)
    print '%d frequency points...' % (npts)

    # calculate real and imag for plotting
    rx = ax * numpy.cos(numpy.radians(px))
    ix = ax * numpy.sin(numpy.radians(px))
    ry = ay * numpy.cos(numpy.radians(py))
    iy = ay * numpy.sin(numpy.radians(py))

    # group for data set 2
    # original phase and amplitude
    # assuming 7 frequency chunks
    px2 = numpy.array([p2[0].columns[0],p2[1].columns[0],p2[2].columns[0],p2[3].columns[0],p2[4].columns[0],p2[5].columns[0],p2[6].columns[0],p2[7].columns[0]])
    ax2 = numpy.array([a2[0].columns[0],a2[1].columns[0],a2[2].columns[0],a2[3].columns[0],a2[4].columns[0],a2[5].columns[0],a2[6].columns[0],a2[7].columns[0]])
    py2 = numpy.array([p2[0].columns[1],p2[1].columns[1],p2[2].columns[1],p2[3].columns[1],p2[4].columns[1],p2[5].columns[1],p2[6].columns[1],p2[7].columns[1]])
    ay2 = numpy.array([a2[0].columns[1],a2[1].columns[1],a2[2].columns[1],a2[3].columns[1],a2[4].columns[1],a2[5].columns[1],a2[6].columns[1],a2[6].columns[1]])
# assuming 16 frequency chunks
#    px2 = numpy.array([p2[0].columns[0],p2[1].columns[0],p2[2].columns[0],p2[3].columns[0],p2[4].columns[0],p2[5].columns[0],p2[6].columns[0],p2[7].columns[0],p2[8].columns[0],p2[9].columns[0],p2[10].columns[0],p2[11].columns[0],p2[12].columns[0],p2[13].columns[0],p2[14].columns[0]])#,p2[15].columns[0]])
#    ax2 = numpy.array([a2[0].columns[0],a2[1].columns[0],a2[2].columns[0],a2[3].columns[0],a2[4].columns[0],a2[5].columns[0],a2[6].columns[0],a2[7].columns[0],a2[8].columns[0],a2[9].columns[0],a2[10].columns[0],a2[11].columns[0],a2[12].columns[0],a2[13].columns[0],a2[14].columns[0]])#,a2[15].columns[0]])
#    py2 = numpy.array([p2[0].columns[1],p2[1].columns[1],p2[2].columns[1],p2[3].columns[1],p2[4].columns[1],p2[5].columns[1],p2[6].columns[1],p2[7].columns[1],p2[8].columns[1],p2[9].columns[1],p2[10].columns[1],p2[11].columns[1],p2[12].columns[1],p2[13].columns[1],p2[14].columns[1]])#,p2[15].columns[1]])
#    ay2 = numpy.array([a2[0].columns[1],a2[1].columns[1],a2[2].columns[1],a2[3].columns[1],a2[4].columns[1],a2[5].columns[1],a2[6].columns[1],a2[7].columns[1],a2[8].columns[1],a2[9].columns[1],a2[10].columns[1],a2[11].columns[1],a2[12].columns[1],a2[13].columns[1],a2[14].columns[1]])#,a2[15].columns[1]])
# assuming 32 frequency chunks
#    px2 = numpy.array([p2[0].columns[0],p2[1].columns[0],p2[2].columns[0],p2[3].columns[0],p2[4].columns[0],p2[5].columns[0],p2[6].columns[0],p2[7].columns[0],p2[8].columns[0],p2[9].columns[0],p2[10].columns[0],p2[11].columns[0],p2[12].columns[0],p2[13].columns[0],p2[14].columns[0],p2[15].columns[0],p2[16].columns[0],p2[17].columns[0],p2[18].columns[0],p2[19].columns[0],p2[20].columns[0],p2[21].columns[0],p2[22].columns[0],p2[23].columns[0],p2[24].columns[0],p2[25].columns[0],p2[26].columns[0],p2[27].columns[0],p2[28].columns[0],p2[29].columns[0],p2[30].columns[0],p2[31].columns[0]])
#    ax2 = numpy.array([a2[0].columns[0],a2[1].columns[0],a2[2].columns[0],a2[3].columns[0],a2[4].columns[0],a2[5].columns[0],a2[6].columns[0],a2[7].columns[0],a2[8].columns[0],a2[9].columns[0],a2[10].columns[0],a2[11].columns[0],a2[12].columns[0],a2[13].columns[0],a2[14].columns[0],a2[15].columns[0],a2[16].columns[0],a2[17].columns[0],a2[18].columns[0],a2[19].columns[0],a2[20].columns[0],a2[21].columns[0],a2[22].columns[0],a2[23].columns[0],a2[24].columns[0],a2[25].columns[0],a2[26].columns[0],a2[27].columns[0],a2[28].columns[0],a2[29].columns[0],a2[30].columns[0],a2[31].columns[0]])
#    py2 = numpy.array([p2[0].columns[1],p2[1].columns[1],p2[2].columns[1],p2[3].columns[1],p2[4].columns[1],p2[5].columns[1],p2[6].columns[1],p2[7].columns[1],p2[8].columns[1],p2[9].columns[1],p2[10].columns[1],p2[11].columns[1],p2[12].columns[1],p2[13].columns[1],p2[14].columns[1],p2[15].columns[1],p2[16].columns[1],p2[17].columns[1],p2[18].columns[1],p2[19].columns[1],p2[20].columns[1],p2[21].columns[1],p2[22].columns[1],p2[23].columns[1],p2[24].columns[1],p2[25].columns[1],p2[26].columns[1],p2[27].columns[1],p2[28].columns[1],p2[29].columns[1],p2[30].columns[1],p2[31].columns[1]])
#    ay2 = numpy.array([a2[0].columns[1],a2[1].columns[1],a2[2].columns[1],a2[3].columns[1],a2[4].columns[1],a2[5].columns[1],a2[6].columns[1],a2[7].columns[1],a2[8].columns[1],a2[9].columns[1],a2[10].columns[1],a2[11].columns[1],a2[12].columns[1],a2[13].columns[1],a2[14].columns[1],a2[15].columns[1],a2[16].columns[1],a2[17].columns[1],a2[18].columns[1],a2[19].columns[1],a2[20].columns[1],a2[21].columns[1],a2[22].columns[1],a2[23].columns[1],a2[24].columns[1],a2[25].columns[1],a2[26].columns[1],a2[27].columns[1],a2[28].columns[1],a2[29].columns[1],a2[30].columns[1],a2[31].columns[1]])

    # calculate real and imag for plotting
    rx2 = ax2 * numpy.cos(numpy.radians(px2))
    ix2 = ax2 * numpy.sin(numpy.radians(px2))
    ry2 = ay2 * numpy.cos(numpy.radians(py2))
    iy2 = ay2 * numpy.sin(numpy.radians(py2))

    if type == 'ratio':
        for i in range(nants):
            if ax2[0,i] == 0:  
                continue
            ratampx = ax2[12:,i]/ax[0:8,i]
            ratphx = px2[12:,i]-px[0:8,i]
            ratampy = ay2[12:,i]/ay[0:8,i]
            ratphy = py2[12:,i]-py[0:8,i]
            pylab.figure(1)
            pylab.subplot(211)
            pylab.plot(range(8), ratphx)
            pylab.text(7,ratphx[0],str(antnum[i]))
            pylab.subplot(212)
            pylab.plot(range(8), ratampx)
            pylab.text(7, ratampx[0],str(antnum[i]))
            pylab.figure(2)
            pylab.subplot(211)
            pylab.plot(range(8), ratphy)
            pylab.text(7,ratphy[0],str(antnum[i]))
            pylab.subplot(212)
            pylab.plot(range(8), ratampy)
            pylab.text(7, ratampy[0],str(antnum[i]))

    if type == 'xy':
        # real-imag (x-y) plot
        # two pols per source
        for i in range(nants/2,nants):
            if rx[0,i] == 0:
                continue
            pylab.figure(1)
            pylab.plot(rx[:,i],ix[:,i],'.-')
            pylab.text(rx[0,i],ix[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
        for i in range(nants/2,nants):
            if ry[0,i] == 0:
                continue
            pylab.figure(2)
            pylab.plot(ry[:,i],iy[:,i],'.-')
            pylab.text(ry[0,i],iy[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
        for i in range(nants/2,nants):
            if rx2[0,i] == 0:
                continue
            pylab.figure(3)
            pylab.plot(rx2[:,i],ix2[:,i],'.-')
            pylab.text(rx2[0,i],ix2[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
        for i in range(nants/2,nants):
            if ry2[0,i] == 0:
                continue
            pylab.figure(4)
            pylab.plot(ry2[:,i],iy2[:,i],'.-')
            pylab.text(ry2[0,i],iy2[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')

    if type == 'corr':
        sqfile = asciidata.AsciiData('/o/claw/big_scr3/data/ata/nvss-rm2/squint.tab')
        sqamp = numpy.array(sqfile.columns[7])

        # plot amp of leak vs. amp of squint
        for i in range(nants):
            if sqamp[antnum[i]-1] == '    --':  continue
            avax = numpy.average(ax[:,i])
            avay = numpy.average(ay[:,i])
            pylab.figure(1)
            pylab.plot([float(sqamp[antnum[i]-1])], [numpy.sqrt(avax**2+avay**2)], '.')
            pylab.text(float(sqamp[antnum[i]-1]), numpy.sqrt(avax**2+avay**2), str(antnum[i]))
# average x and y leakage
#            pylab.plot([float(sqamp[antnum[i]-1])], [numpy.sqrt(avax**2 + avay**2)], '.')
#            pylab.text(float(sqamp[antnum[i]-1]), numpy.sqrt(avax**2 + avay**2), str(antnum[i]))

            pylab.xlabel('Antenna squint (arcmin)')
            pylab.ylabel('Leak amplitude, freq avg')
            print '%d %.1f %.3f' % (antnum[i], float(sqamp[antnum[i]-1]), numpy.sqrt(avax**2 + avay**2))


    if type == 'joint':
        # real-imag (x-y) plot
        # two pols per source
        for i in range(nants):
            rxj = numpy.concatenate((rx[:,i],rx2[:,i]))
            ixj = numpy.concatenate((ix[:,i],ix2[:,i]))
            ryj = numpy.concatenate((ry[:,i],ry2[:,i]))
            iyj = numpy.concatenate((iy[:,i],iy2[:,i]))
            pylab.figure(1)
            pylab.plot(rxj,ixj,'.-')
            pylab.text(rx[0,i],ix[0,i],str(antnum[i]))
            pylab.text(rx2[0,i],ix2[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
            pylab.figure(2)
            pylab.plot(ryj,iyj,'.-')
            pylab.text(ry[0,i],iy[0,i],str(antnum[i]))
            pylab.text(ry2[0,i],iy2[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')

    if type == 'overlap':
        # real-imag (x-y) plot
        # two pols per source
        for i in range(nants):
            pylab.figure(1)
            pylab.plot(rx,ix,'.-')
            pylab.plot(rx2,ix2,'--')
            pylab.text(rx[0,i],ix[0,i],str(antnum[i]))
            pylab.text(rx2[0,i],ix2[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
            pylab.figure(2)
            pylab.plot(ry,iy,'.-')
            pylab.plot(ry2,iy2,'--')
            pylab.text(ry[0,i],iy[0,i],str(antnum[i]))
            pylab.text(ry2[0,i],iy2[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
            pylab.figure(3)
            pylab.plot(ry-ry2,iy-iy2,'.-')
            pylab.plot(rx-rx2,ix-ix2,'--')
            pylab.text(ry[0,i]-ry2[0,i],iy[0,i]-iy2[0,i],str(antnum[i]))
            pylab.text(rx[0,i]-rx2[0,i],ix[0,i]-ix2[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakage Differences')

    pylab.show()

if __name__ == '__main__':
    run()
