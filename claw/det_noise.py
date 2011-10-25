#!/usr/bin/env python
# claw 11oct11
#
# script to simulate noise in complex and detected valued data

import numpy as n
import pylab as p
import random

class noise:
    def __init__(self, len=100, std=1.):
        self.std = std
        self.len = len

        self.data = n.zeros(len, dtype='complex')
        self.datat = n.zeros(len+2, dtype='complex')
        for i in range(len):
            self.data[i] = n.complex(random.gauss(0, std), random.gauss(0, std))
        for i in range(len+2):
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
        bisp = []
        for i in range(self.len):
            bisp.append(self.datat[i] * self.datat[i+1] * self.datat[i+2])
        self.bisp = n.array(bisp)

    def show(self):
        p.plot(self.bisp, '.')
        p.show()

def repeat(num=100, source=0+0j, show=0):
    bglen = 1000

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
    for i in range(bglen):
        nnoff = noise(len=num)
        nnoff.trip()
        mdarr.append(n.abs(nnoff.data.mean()))
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

    return n.array([intsig, dmsig, mdsig, bisig])

def plotfig(s=1, num=27, t=5):
    """Plots figure showing snr of signal seen by various algorithms.
    """

    snrbi = lambda s,num: 1/2. * s**3 * n.sqrt((num-1)*(num-2)/2.)
    snrco = lambda s,num: s * n.sqrt(num*(num-1)/2.)
    snrin = lambda s,num: s**2/n.sqrt(1+s**2) * n.sqrt(num*(num-1)/2.)

    p.figure(1)
    p.plot(s, snrbi(s,num), label='Bispectrum')
    p.plot(s, snrco(s,num), label='Coherent Beamforming')
    p.plot(s, snrin(s,num), label='Incoherent Beamforming')
    p.xlabel('SNR per baseline')
    p.ylabel('SNR')
    p.legend()

    sig_vla = 0.05 # 1 sigma, EVLA baseline sensitivity in 10 ms, 1 GHz, dual pol
    sbi = lambda num,thresh: sig_vla * n.power(2*thresh/n.sqrt((num-1)*(num-2)/2.), 1/3.)
    sco = lambda num,thresh: sig_vla * thresh/n.sqrt(num*(num-1)/2.)
#    1/s**4 + 1/s**2 - nbl/(thresh)**2 = 0
    sin = lambda num,thresh: sig_vla * n.sqrt( 2 / (n.sqrt(1 + 2*num*(num-1)/(thresh)**2) - 1) )

    p.figure(2)
    num = n.arange(3,30)
    p.plot(num, sbi(num,t), label='Bispectrum')
    p.plot(num, sco(num,t), label='Coherent Beamforming')
    p.plot(num, sin(num,t), label='Incoherent Beamforming')
    p.xlabel('Number of Antennas')
    p.ylabel('Flux Limit (Jy)')
    p.legend()

    p.show()
