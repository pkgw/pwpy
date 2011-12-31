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
        bisp = n.zeros(self.len, dtype='complex')
        for i in range(self.len):
            bisp[i] = self.datat[i] * self.datat[i+1] * self.datat[i+2]
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
    for i in range(bglen):
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


def threshold(na=3):
    """Simulate the bispectrum to find threshold in terms of S/Q.
    Sorts output of both statistics and then takes value based on index where threshold is expected.
    """

    thresh = 2.9e-7
    simlen = 100000000   # product of thresh*simlen must be much larger than 1

    thresh = 1.4e-3
    simlen = 10000

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


def bispdist():
    """Function to plot the bispectrum distribution. Assumes Gaussian-distributed visibilities multiplied together.
    Based on Lomnicki 1967, JRSS-B, Vol 29, 3.
    Not quite right. Doesn't account for multiplying complex numbers (vectors).
    """

    bign = 100

    mg = lambda x, sigma: ((2*n.pi)**(3/2.) * sigma**3)**(-1) * n.sum([phi(x**2 / (2.**3 * sigma**6),j) for j in range(0,bign)])
    phi = lambda x,j: 1/2. * (x**j * (-1)**j / (scipy.misc.factorial(j))**3) * ( ll(x,j)**2 + 3*pp(j) )
    pp = lambda j: n.sum([i**(-2.) for i in range(1,bign)]) + n.sum([i**(-2.) for i in range(1,j+1)])
    ll = lambda x,j: -1*n.log(x) + 3*(-0.577215665 + n.sum([1./i for i in range(1,j+1)]))
    
    arr = n.arange(1,100)/10.
    pl = n.array([mg(x,1) for x in arr])
    p.plot(arr,pl)
    p.show()

    return arr,pl


def plotfig(s=-1, num=-1, t=5):
    """Plots figure showing snr of signal seen by various algorithms.
    """

    s = n.arange(1,14)/10.
    num = 27

    # functions for statistic of snr vs. snr per baseline (s) and antenna number (num)
    mu = lambda s: s / (3*(1+s))  # a possible functional form for mu covariance term in kulkarni 1989
    sigmat = lambda num, s: n.sqrt( ((1 + 3*(num-3)*mu(s)) / (num * (num-1) * (num-2)/6.)) * (4 + 3*s**4 + 6*s**2))

    snrbi = lambda s,num: 1/2. * s**3 * n.sqrt(num*(num-1)*(num-2)/6.)    # cornwell 1987
    snrbi2 = lambda s, num: s**3/n.sqrt( (1 + 3*(num-3)*mu(s)) / (num * (num-1) * (num-2)/6.) * (4 + 3*s**4 + 6*s**2))
    snrco = lambda s,num: s * n.sqrt(num*(num-1)/2.)
    snrin = lambda s,num: 1/2. * s**2/n.sqrt(1+s**2) * n.sqrt(num*(num-1)/2.)  # tms
    snrinin = lambda s,num: 1/n.sqrt(2) * s * n.sqrt(num)

    p.figure(1)
    p.loglog()
    p.plot(s, snrbi(s,num), 'b', label='Bispectrum (orig)', linewidth=3)
    p.plot(s, snrbi2(s,num), 'b--', label='Bispectrum (new)', linewidth=3)
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
    sbiarr2 = []
    scoarr = []
    sinarr = []
    sininarr = []
    sarr = n.arange(1,20000)/1000.
    for nn in num:
        sbiarr.append(sarr[n.where(snrbi(sarr,nn) > t)[0][0]])
        sbiarr2.append(sarr[n.where(snrbi2(sarr,nn) > t)[0][0]])
        scoarr.append(sarr[n.where(snrco(sarr,nn) > t)[0][0]])
        sinarr.append(sarr[n.where(snrin(sarr,nn) > t)[0][0]])
        sininarr.append(sarr[n.where(snrinin(sarr,nn) > t)[0][0]])

    sbiarr = sig_vla*n.array(sbiarr)
    sbiarr2 = sig_vla*n.array(sbiarr2)
    scoarr = sig_vla*n.array(scoarr)
    sinarr = sig_vla*n.array(sinarr)
    sininarr = sig_vla*n.array(sininarr)
    p.figure(2)
    # analytic...
#    p.plot(num, sbi(num,t), label='Bispectrum')
#    p.plot(num, sco(num,t), label='Coherent Beamforming')
#    p.plot(num, sin(num,t), label='Incoherent Beamforming')
    # computational...
    p.plot(num, sbiarr, 'b', label='Bispectrum (orig)', linewidth=3)
    p.plot(num, sbiarr2, 'b--', label='Bispectrum (new)', linewidth=3)
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
