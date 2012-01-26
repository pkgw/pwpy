#!/usr/bin/env python
# claw 11oct11
#
# script to simulate noise in complex and detected valued data

import numpy as n
import pylab as p
import scipy.misc
import random

class noise:
    def __init__(self, len=100, std=1.):
        self.std = std
        self.len = len

        self.data = n.zeros(len, dtype='complex')
        self.datat = n.zeros(3*len, dtype='complex')
        for i in xrange(len):
            self.data[i] = n.complex(random.gauss(0, std), random.gauss(0, std))
        for i in xrange(3*len):
            self.datat[i] = n.complex(random.gauss(0, std), random.gauss(0, std))

    def add_source(self, flux=1+0j):
        self.data = self.data + flux
        self.datat = self.datat + flux

    def det(self,show=0):
        self.datadet = n.abs(self.data)

        if show:
            print 'datadet:', self.datadet
        return self.datadet

    def trip(self):
        bisp = n.zeros(self.len, dtype='complex')
        for i in xrange(self.len):
            bisp[i] = self.datat[3*i] * self.datat[3*i+1] * self.datat[3*i+2]
        self.bisp = bisp

    def show(self):
        p.plot(self.bisp, '.')
        p.show()

def repeat(num=100, source=0+0j, show=0):
    bglen = 100000

    # make detected visibilities on source
    nn = noise(len=num)
    nn.add_source(source)
    nn.trip()
    bion = nn.bisp.real.mean()
    dmon = nn.det().mean()

    # make background detected visibilities
    dmarr = []
    mdarr = []
    biarr = []
    for i in xrange(bglen):
        nnoff = noise(len=num)
        nnoff.trip()
#        mdarr.append(n.abs(nnoff.data.mean()))
        mdarr.append(nnoff.data.real.mean())
        biarr.append(nnoff.bisp.real.mean())
        dmarr.append(nnoff.det().mean())
    mdarr = n.array(mdarr)
    dmarr = n.array(dmarr)
    biarr = n.array(biarr)

    meanoff = dmarr.mean()
    stdoff = dmarr.std()
    dmsig = (dmon - meanoff)/stdoff

    meanoff = biarr.mean()
    stdoff = biarr.std()
    bisig = (bion - meanoff)/stdoff

    # make background mean visibilities and det significance
    meanoff = mdarr.mean()
    stdoff = mdarr.std()

    nn = noise(len=num)
    nn.add_source(source)
    dmon = n.abs(nn.data.mean())
    mdsig = (dmon - meanoff)/stdoff

    intsig = n.abs(source)/nn.std
    print 'snr per int:', intsig
    print 'det then mean:', dmsig, 'sigma'
    print 'mean then det:', mdsig, 'sigma'
    print 'bispectrum:', bisig, 'sigma'

#    return n.array([intsig, dmsig, mdsig, bisig])
    return mdarr, biarr


def threshold(na=3,thresh=3):
    """Simulate the bispectrum to find threshold in terms of S/Q.
    Sorts output of both statistics and then takes value based on index where threshold is expected.
    """

    if thresh == 3:
        thresh = 1.3e-3  # 3sigma
        simlen = 10000
    elif thresh == 4:
        thresh = 3.2e-5  # 4sigma
        simlen = 1000000
    elif thresh == 5:
        thresh = 2.9e-7  # 5sigma
        simlen = 100000000   # product of thresh*simlen must be much larger than 1
    else:
        print 'Not a standard sigma threshold'
        return 0

    print 'thresh=%.1e, simlen=%d' % (thresh,simlen)

    # make mean bi and bf
    bimean = n.zeros(thresh*simlen)
    bfmean = n.zeros(thresh*simlen)
    ntrip = na*(na-1)*(na-2)/6
    nbl = na*(na-1)/2
    print 'nbl=%d, ntrip=%d' % (nbl,ntrip)

    if ntrip >= nbl:
        nlong = ntrip
    else:
        nlong = nbl

    for i in xrange(simlen):
        nn = noise(len=nlong)
        nn.trip()
        bfm = nn.data[0:nbl].real.mean()
        bim = nn.bisp[0:ntrip].real.mean()
        if n.any(bfm > bfmean):
            bfmean[0] = bfm
            bfmean.sort()
        if n.any(bim > bimean):
            bimean[0] =  bim
            bimean.sort()
        if not float(i)/simlen - n.round(float(i)/simlen,1):
            print "%.0f pct complete" % (float(i)/simlen * 100)

    return bfmean.min(), n.power(bimean.min(),1/3.)


def distribution(na=3):
    """Returns distribution of mean bispectrum from array of size na.
    """

    simlen = 100000
    ntrip = na*(na-1)*(na-2)/6
    bimean = n.zeros(simlen)

    for i in xrange(simlen):
        nn = noise(len=ntrip, std=1.)
        nn.trip()
        bimean[i] = nn.bisp.real.mean()

    hist = n.histogram(bimean, bins=200, range=(-5.,5.),density=True)
    binc = [(hist[1][i+1] + hist[1][i])/2. for i in xrange(len(hist[1])-1)]

    return binc,hist[0]


