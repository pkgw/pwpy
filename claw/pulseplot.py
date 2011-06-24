#!/usr/bin/env python
"""
Script to read in pulse text file, order associated pickle files, then build dynamic spectrum of pulse-only data.
"""

import asciidata, pickle, string, sys
import pocovis
import pylab as p
import numpy as n

def main(start=0, stop=10, save=1):
    print 'Plotting pulses from %d to %d (python-like)' % (start, stop)

    filename = 'b0329_fixdm_ph/poco_b0329_173027_fitsp.txt'
    f = asciidata.AsciiData(filename)
    name = n.array(f.columns[0])

    dynsp = []
    nint = []; nskip = []; chunk = []; pklname = []
    for nn in name:
        nskip.append(int((nn.split('.'))[1].split('-')[0]))
        nint.append(int((nn.split('-dm0t'))[1].split('.')[0]))
        chunk.append(int((nn.split('_'))[3].split('.')[0]))
        tmp = [(nn.split('/')[1].split('-')[0])]
        tmp.append('pkl')
        tmp[0] = 'b0329_fixdm_ph/' + tmp[0]
        pklname.append(string.join(tmp, '.'))
            
    ntot = n.array(chunk)*131000 + n.array(nskip) + n.array(nint)
    dtype1 = [('ntot', int), ('name', 'S50'), ('nint', int)]
    sortar = []

    for i in range(len(ntot)):
        sortar.append( (ntot[i], pklname[i], nint[i]) )

    sortar = n.array(sortar, dtype=dtype1)
    newsortar = n.sort(sortar, order=['ntot'])
    pathin = 'data/'
    bgwindow = 10

    for pulse in newsortar.tolist()[start:stop]:
        file = open(pulse[1], 'rb')
        dump = pickle.load(file)
        dataname = dump[0]
        nints = dump[2]
        nintskip = dump[1]
        dmbinarr = dump[3]
        dmarr = dump[4]
        tbin = pulse[2]

        if len(dmbinarr) >= 1:
            print
            print 'Starting candidate', pulse[0]
            pv = pocovis.poco(pathin + dataname, nints=nints, nskip=nintskip)
            pv.prep()
            track = pv.tracksub(0, tbin, bgwindow=bgwindow)
            spec = (track[0]).mean(axis=0).real
            dynsp.append(spec)

    p.figure(1)
    ax = p.imshow(n.array(dynsp), aspect='equal', origin='lower', interpolation='nearest')
    p.colorbar(ax)
    p.xticks(n.arange(0,len(pv.chans),8), (pv.chans[(n.arange(0,len(pv.chans), 8))]))
    p.yticks(n.arange(0,len(dynsp)-1,10), (n.arange(start,stop-1,10)))
    p.xlabel('Channels (flagged data removed)')
    p.ylabel('Pulse number')
    if save:
        savename = filename.split('.')[:-1]
        savename.append(str(start) + '-' + str(stop) + '_dynsp.ps')
        savename = string.join(savename,'.')
        print 'Saving file as ', savename
        p.savefig(savename)
    else:
        p.show()
    p.clf()

if __name__ == '__main__':
    save = 1
    spacing = 100
    if len(sys.argv) == 1:
        starts = n.arange(1600,2000,spacing)
        stops = n.arange(1700,2100,spacing)

        for i in range(len(starts)):
            main(starts[i], stops[i], save=save)

    elif len(sys.argv) == 3:
        main( int(sys.argv[1]), int(sys.argv[2]), save=save )
