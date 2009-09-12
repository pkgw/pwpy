# claw, 7may09
#
# script to plot complex leakages for comparison

import asciidata, pylab, numpy

def run():
    # params
    type = 'freq'  # 'pol' groups by pol, 'freq' groups by freq, 'freqdiff' groups by freq and differences to center
    locs = 7
    freqs = 8  # ignores higher
    antnum = [1,4,7,10,13,16,19,22,25,28,31,34,37,40,43,2,5,8,11,14,17,20,23,26,29,32,35,38,41,3,6,9,12,15,18,21,24,27,30,33,36,39,42]  # hack for how rows messed up by 'cut'
    scale = 0.4
    beamra = numpy.array([0.,1.,0.5,-0.5,-1.,-0.5,+0.5,]) * scale
    beamdec = numpy.array([0.,0.,numpy.sqrt(3)/2.,numpy.sqrt(3)/2.,0.,-numpy.sqrt(3)/2.,-numpy.sqrt(3)/2.]) * scale
    prefix = 'hexa-3c286'
    prefix2 = 'hexc-3c286'
    obsfreq = '1430'
    hpqp = 1

    ax = []; ay = []
    px = []; py = []
    axq = []; ayq = []
    pxq = []; pyq = []
    for freq in range(freqs):
        print 'Reading for freq %d' % (freq)
        for loc in range(locs):
            ax.append(asciidata.AsciiData ('%s-hp%d-%s-leakamp%d.txt' % (prefix, loc, obsfreq, freq+1)).columns[0])
            px.append(asciidata.AsciiData ('%s-hp%d-%s-leakphase%d.txt' % (prefix, loc, obsfreq, freq+1)).columns[0])
            ay.append(asciidata.AsciiData ('%s-hp%d-%s-leakamp%d.txt' % (prefix, loc, obsfreq, freq+1)).columns[1])
            py.append(asciidata.AsciiData ('%s-hp%d-%s-leakphase%d.txt' % (prefix, loc, obsfreq, freq+1)).columns[1])
            if hpqp:
                axq.append(asciidata.AsciiData ('%s-qp%d-%s-leakamp%d.txt' % (prefix2, loc, obsfreq, freq+1)).columns[0])
                pxq.append(asciidata.AsciiData ('%s-qp%d-%s-leakphase%d.txt' % (prefix2, loc, obsfreq, freq+1)).columns[0])
                ayq.append(asciidata.AsciiData ('%s-qp%d-%s-leakamp%d.txt' % (prefix2, loc, obsfreq, freq+1)).columns[1])
                pyq.append(asciidata.AsciiData ('%s-qp%d-%s-leakphase%d.txt' % (prefix2, loc, obsfreq, freq+1)).columns[1])

    nants = len(ax[0])
    print '%d antennas...' % (nants)
    print numpy.shape(ax)

    # derived r and i
    rx = ax * numpy.cos(numpy.radians(px))
    ix = ax * numpy.sin(numpy.radians(px))
    ry = ay * numpy.cos(numpy.radians(py))
    iy = ay * numpy.sin(numpy.radians(py))
    if hpqp:
        rxq = axq * numpy.cos(numpy.radians(pxq))
        ixq = axq * numpy.sin(numpy.radians(pxq))
        ryq = ayq * numpy.cos(numpy.radians(pyq))
        iyq = ayq * numpy.sin(numpy.radians(pyq))

    if type == 'pol':
        # array of seven vectors in primary beam per (chan, ant, freq)
        for nant in range(nants):
            for freq in range(freqs):
                print 'Plotting for freq %d, nant %d' % (freq+1, antnum[nant])
                for loc in range(locs):
                    index = freq * locs + loc
#                    index = freq * (locs * nants) + loc * (nants) + nant
                    if rx[index,nant] == 0:
                        break
                    pylab.figure(freq + freqs*antnum[nant])
                    pylab.arrow(beamra[loc], beamdec[loc], rx[index,nant], ix[index,nant], fill=0, edgecolor='red')
                    pylab.arrow(beamra[loc], beamdec[loc], ry[index,nant], iy[index,nant],fill=0, edgecolor='blue')
#                    pylab.text(ry[index],iy[index],str(antnum[index]))
                if rx[index,nant] == 0:
                    print '...  bad ant.  skipping.'
                    continue
                pylab.axis([-1.3*scale,1.3*scale,-1.3*scale,1.3*scale])
                pylab.xlabel('RA pointing offset')
                pylab.ylabel('Dec pointing offset')
                pylab.title('Leakages across primary beam')

        pylab.show()

    elif type == 'freq':
        # array of seven vectors in primary beam per (ant, pol)
        # define color scheme for vectors in freq
        color = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'black']

        for nant in range(nants):
            print 'Plotting for nant %d' % (antnum[nant])
            for freq in range(freqs):
                for loc in range(locs):
                    index = freq * locs + loc
                    if rx[index,nant] == 0:
                        break
                    pylab.figure(antnum[nant])
                    pylab.arrow(beamra[loc], beamdec[loc], rx[index,nant], ix[index,nant], edgecolor=color[freq], facecolor=color[freq])
                    if hpqp:
                        pylab.arrow(0.5*beamra[loc], 0.5*beamdec[loc], rxq[index,nant], ixq[index,nant], edgecolor=color[freq], facecolor=color[freq])
                    pylab.figure(antnum[nant] + nants)
                    pylab.arrow(beamra[loc], beamdec[loc], ry[index,nant], iy[index,nant], edgecolor=color[freq], facecolor=color[freq])
                    if hpqp:
                        pylab.arrow(0.5*beamra[loc], 0.5*beamdec[loc], ryq[index,nant], iyq[index,nant], edgecolor=color[freq], facecolor=color[freq])
#                    pylab.text(ry[index],iy[index],str(antnum[index]))
            if rx[index,nant] == 0:
                print '...  bad ant.  skipping.'
                continue

            pylab.figure(antnum[nant])
            pylab.axis([-1.3*scale,1.3*scale,-1.3*scale,1.3*scale])
            pylab.xlabel('RA pointing offset')
            pylab.ylabel('Dec pointing offset')
            pylab.title('X-pol leakages across primary beam')
            pylab.figure(antnum[nant] + nants)
            pylab.axis([-1.3*scale,1.3*scale,-1.3*scale,1.3*scale])
            pylab.xlabel('RA pointing offset')
            pylab.ylabel('Dec pointing offset')
            pylab.title('Y-pol leakages across primary beam')
        pylab.show()

    elif type == 'freqdiff':
        # array of seven vectors in primary beam per (ant, pol).  this one plots difference relative to center
        # define color scheme for vectors in freq
        color = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'black']

        for nant in range(nants):
            print 'Plotting for nant %d' % (antnum[nant])
            for freq in range(freqs):

                # first plot central without diff, as reference
                loc = 0
                index = freq * locs + loc
                if rx[index,nant] == 0:
                    break
                pylab.figure(antnum[nant])
                pylab.arrow(beamra[loc], beamdec[loc], rx[index,nant], ix[index,nant], edgecolor=color[freq], fill=0, ls='dotted')
                pylab.figure(antnum[nant] + nants)
                pylab.arrow(beamra[loc], beamdec[loc], ry[index,nant], iy[index,nant], edgecolor=color[freq], fill=0, ls='dotted')

                # loop through the diffs
                for loc in range(1,locs):
                    index = freq * locs + loc
                    index0 = freq * locs
                    if rx[index,nant] == 0:
                        break
                    pylab.figure(antnum[nant])
                    pylab.arrow(beamra[loc], beamdec[loc], rx[index,nant] - rx[index0,nant], ix[index,nant] - ix[index0,nant], edgecolor=color[freq], facecolor=color[freq])
                    if hpqp:
                        pylab.arrow(0.5*beamra[loc], 0.5*beamdec[loc], rxq[index,nant] - rx[index0,nant], ixq[index,nant] - ix[index0,nant], edgecolor=color[freq], facecolor=color[freq])
                    pylab.figure(antnum[nant] + nants)
                    pylab.arrow(beamra[loc], beamdec[loc], ry[index,nant] - ry[index0,nant], iy[index,nant] - iy[index0,nant], edgecolor=color[freq], facecolor=color[freq])
                    if hpqp:
                        pylab.arrow(0.5*beamra[loc], 0.5*beamdec[loc], ryq[index,nant] - ry[index0,nant], iyq[index,nant] - iy[index0,nant], edgecolor=color[freq], facecolor=color[freq])
#                    pylab.text(ry[index],iy[index],str(antnum[index]))
            if rx[index,nant] == 0:
                print '...  bad ant.  skipping.'
                continue

            pylab.figure(antnum[nant])
            pylab.axis([-1.3*scale,1.3*scale,-1.3*scale,1.3*scale])
            pylab.xlabel('RA pointing offset')
            pylab.ylabel('Dec pointing offset')
            pylab.title('X-pol leakage differences across primary beam')
            pylab.figure(antnum[nant] + nants)
            pylab.axis([-1.3*scale,1.3*scale,-1.3*scale,1.3*scale])
            pylab.xlabel('RA pointing offset')
            pylab.ylabel('Dec pointing offset')
            pylab.title('Y-pol leakage differences across primary beam')
        pylab.show()

if __name__ == '__main__':
    run()
