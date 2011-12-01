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

def plotfig(s=-1, num=-1, t=5):
    """Plots figure showing snr of signal seen by various algorithms.
    """

    s = n.arange(1,14)/10.
    num = 64

    # functions for statistic of snr vs. snr per baseline (s) and antenna number (num)
    snrbi = lambda s,num: 1/2. * s**3 * n.sqrt(num*(num-1)*(num-2)/6.)    # cornwell 1987, kulkarni 1989, rogers et al. 1995
    snrbi2 = lambda s,num: 1 / ( 1/(3 * s**3 * n.sqrt(num*(num-1)*(num-2)/6.)) + 1/(s * n.sqrt(num*(num-1)/2.)))  # kulkarni 1989 ** with correlated noise! **
    snrmega = lambda s,num: 1/2. * s**5 * n.sqrt(num*(num-1)*(num-2)*(num-3)*(num-4)/120.)
    snrco = lambda s,num: s * n.sqrt(num*(num-1)/2.)
    snrin = lambda s,num: 1/2. * s**2/n.sqrt(1+s**2) * n.sqrt(num*(num-1)/2.)  # tms
    snrinin = lambda s,num: 1/n.sqrt(2) * s * n.sqrt(num)

    p.figure(1)
    p.loglog()
    p.plot(s, snrbi(s,num), 'b', label='Bispectrum', linewidth=3)
#    p.plot(s, snrmega(s,num), 'y', label='Mega')
    p.plot(s, snrco(s,num), 'r--', label='Coherent Beamforming', linewidth=3)
    p.plot(s, snrin(s,num), 'g.', label='Incoherent Baseline Beamforming', linewidth=3)
    p.plot(s, snrinin(s,num), 'y-.', label='Incoherent Antenna Beamforming', linewidth=3)
    p.xlabel('SNR per baseline')
    p.ylabel('SNR')
    p.legend(loc=0)

    # invert equations to get flux limits
    # option 1: analytic inversion
    sig_vla = 0.063 # 1 sigma, EVLA baseline sensitivity in 10 ms, 1 GHz, dual pol
    sbi = lambda num,thresh: sig_vla * n.power(2*thresh/n.sqrt(num*(num-1)*(num-2)/6.), 1/3.) # cornwell 1987 ... s * num**(-1/2)
    sco = lambda num,thresh: sig_vla * thresh/n.sqrt(num*(num-1)/2.)
#    1/s**4 + 1/s**2 - nbl/(thresh)**2 = 0
    sin = lambda num,thresh: sig_vla * n.sqrt( 2 / (n.sqrt(1 + 2*num*(num-1)/(thresh)**2) - 1) )

    # option 2: computational inversion
    num = n.arange(3,65)
    sbiarr = []
#    smegaarr = []
    scoarr = []
    sinarr = []
    sininarr = []
    sarr = n.arange(1,10000)/1000.
    for nn in num:
        sbiarr.append(sarr[n.where(snrbi(sarr,nn) > t)[0][0]])
#        smegaarr.append(sarr[n.where(snrmega(sarr,nn) > t)[0][0]])
        scoarr.append(sarr[n.where(snrco(sarr,nn) > t)[0][0]])
        sinarr.append(sarr[n.where(snrin(sarr,nn) > t)[0][0]])
        sininarr.append(sarr[n.where(snrinin(sarr,nn) > t)[0][0]])

    sbiarr = sig_vla*n.array(sbiarr)
#    smegaarr = sig_vla*n.array(smegaarr)
    scoarr = sig_vla*n.array(scoarr)
    sinarr = sig_vla*n.array(sinarr)
    sininarr = sig_vla*n.array(sininarr)
    p.figure(2)
    # analytic...
#    p.plot(num, sbi(num,t), label='Bispectrum')
#    p.plot(num, sco(num,t), label='Coherent Beamforming')
#    p.plot(num, sin(num,t), label='Incoherent Beamforming')
    # computational...
    p.plot(num, sbiarr, 'b', label='Bispectrum', linewidth=3)
#    p.plot(num, smegaarr, 'y', label='Mega')
    p.plot(num, scoarr, 'r--', label='Coherent Beamforming', linewidth=3)
    p.plot(num, sinarr, 'g.', label='Incoherent Baseline Beamforming', linewidth=3)
    p.plot(num, sininarr, 'y-.', label='Incoherent Antenna Beamforming', linewidth=3)
    p.text(5, 0.2, 'PoCo', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14)
    p.text(27, 0.2, 'EVLA', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14)
    p.text(36, 0.2, 'ASKAP', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14)
    p.text(48, 0.2, 'LOFAR', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14)
    p.text(64, 0.2, 'MeerKAT', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14)
    p.xlabel('Number of Antennas')
    p.ylabel('Flux Limit (%d sigma; Jy)' % (t))
    p.legend()

    p.show()
