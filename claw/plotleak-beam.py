# claw, 7may09
#
# script to plot complex leakages for comparison

import asciidata, pylab, numpy

def run():
    # params
    type = 'xy'
    locs = 7
    freqs = 8
    antnum = [1,4,7,10,13,16,19,22,25,28,31,34,37,40,43,2,5,8,11,14,17,20,23,26,29,32,35,38,41,3,6,9,12,15,18,21,24,27,30,33,36,39,42]  # hack for how rows messed up by 'cut'
    beamx = [0.,-1.,+1.,-0.5,+0.5,-0.5,+0.5,]
    beamy = [0.,0.,0.,-1.,-1.,+1.,+1.]

    ax = []; ay = []
    px = []; py = []
    for freq in range(freqs):
        for loc in range(locs):
            ax.append(asciidata.AsciiData ('3c138-p%d-leak%d.amp.txt' % (loc, freq+1)).columns[0])
            px.append(asciidata.AsciiData ('3c138-p%d-leak%d.phase.txt' % (loc, freq+1)).columns[0])
            ay.append(asciidata.AsciiData ('3c138-p%d-leak%d.amp.txt' % (loc, freq+1)).columns[1])
            py.append(asciidata.AsciiData ('3c138-p%d-leak%d.phase.txt' % (loc, freq+1)).columns[1])

    nants = len(ax[0])
    print '%d antennas...' % (nants)
    print numpy.shape(ax)

    # derived r and i
    rx = ax * numpy.cos(numpy.radians(px))
    ix = ax * numpy.sin(numpy.radians(px))
    ry = ay * numpy.cos(numpy.radians(py))
    iy = ay * numpy.sin(numpy.radians(py))

    if type == 'xy':
        # real-imag (x-y) plot
        # array of seven vectors in primary beam
        for nant in range(1):        
            for freq in range(1):
                print 'Plotting for freq %d, nant %d' % (freq+1, nant+1)
                for loc in range(locs):
                    index = freq * locs + loc
#                    index = freq * (locs * nants) + loc * (nants) + nant
                    if rx[index,nant] == 0:
                        break
                    pylab.figure(freq + freqs*nant)
                    pylab.arrow(beamx[loc], beamy[loc], rx[index,nant], ix[index,nant], color='blue')
                    pylab.arrow(beamx[loc], beamy[loc], ry[index,nant], iy[index,nant], color='red')
#                    pylab.text(ry[index],iy[index],str(antnum[index]))
                pylab.axis([-1.2,1.2,-1.2,1.2])
                pylab.xlabel('X Offset')
                pylab.ylabel('Y Offset')
                pylab.title('Leakages across primary beam')

                pylab.show()

if __name__ == '__main__':
    run()
