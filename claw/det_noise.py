#!/usr/bin/env python
# claw 11oct11
#
# script to simulate noise in complex and detected valued data

import numpy as n
import pylab as p
import scipy.misc
import random

class noise:
    """The wrong way... Simulates ntr independent values then the mean bispectrum.
    """

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


class noise2:
    """The right way... Simulates na by na array of data (with complex conjugates), then calculates bispectra.
    """
    def __init__(self, na=3, std=1.):
        self.std = std
        self.na = na
        self.nbl = na*(na-1)/2
        self.ntr = na*(na-1)*(na-2)/6
        nbl = self.nbl
        ntr = self.ntr
        self.data = n.zeros(shape=(na,na), dtype='complex')
        rands = n.random.normal(size=(nbl,2))

        ind = 0
        for i in xrange(na):
            for j in xrange(i+1,na):
                re = rands[ind,0]
                im = rands[ind,1]
#                re = n.random.normal()
#                im = n.random.normal()
                self.data[i,j] = n.complex(re,im)
                self.data[j,i] = n.complex(re,-im)
                ind = ind+1

    def trip(self):
        na = self.na
        nbl = self.nbl
        ntr = self.ntr

        self.bisp = n.zeros(ntr, dtype='complex')
        tr = 0
        for i in xrange(0,na-2):
            for j in xrange(i+1,na-1):
                for k in xrange(j+1,na):
                    self.bisp[tr] = self.data[i,j] * self.data[j,k] * self.data[k,i]   # data are conjugated in lower half (k,i)
                    tr = tr+1

    def beamform(self):
        na = self.na

        sum = 0.
        for i in xrange(na):
            for j in xrange(i+1,na):
                sum = sum + self.data[i,j]

        return sum.real/self.nbl


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
        sigma = 3
        simlen = 10000
    elif thresh == 4:
        thresh = 3.2e-5  # 4sigma
        sigma = 4
        simlen = 1000000
    elif thresh == 5:
        thresh = 2.9e-7  # 5sigma
        sigma = 5
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
    print '*Theory* bf: %.3f, bisp: %.3f' % (float(sigma)/n.sqrt(nbl), n.power(2*float(sigma)/n.sqrt(ntrip), 1/3.))

    for i in xrange(simlen):
        nn = noise2(na=na)
        nn.trip()
        bfm = nn.beamform()
        bim = nn.bisp.real.mean()
        if n.any(bfm > bfmean):
            bfmean[0] = bfm
            bfmean.sort()
        if n.any(bim > bimean):
            bimean[0] =  bim
            bimean.sort()
        ww = n.where(i==simlen/10*n.arange(10))
        if len(ww[0] > 0): print '%d pct complete' % (10*ww[0][0])

#        if not float(i)/simlen - n.round(float(i)/simlen,1):
#            print "%.0f pct complete" % (float(i)/simlen * 100)

    return bfmean.min(), n.power(bimean.min(),1/3.)


def distribution(na=3):
    """Returns distribution of mean bispectrum from array of size na.
    """

    simlen = 300000
    ntrip = na*(na-1)*(na-2)/6
    bimean = n.zeros(simlen)

    for i in xrange(simlen):
        nn = noise2(na=na, std=1.)
        nn.trip()
        bimean[i] = nn.bisp.real.mean()

    hist = n.histogram(1/2. * n.sqrt(ntrip) * bimean, bins=200, range=(-5.,5.),density=True)
    binc = [(hist[1][i+1] + hist[1][i])/2. for i in xrange(len(hist[1])-1)]

    return binc,hist[0]


