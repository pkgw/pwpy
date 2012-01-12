#!/usr/bin/env python
# claw 9jan12
#
# script to plot bispectrum and other statistics for transient detection

import numpy as n
import pylab as p
import matplotlib.pyplot as plt

def compute():
    """Plots the computational demand of various interferometric transient detection techniques.
    """

    ar = n.arange(3,65)

    nbeam = lambda distratio: (distratio*3)**2   # distratio is the ratio of the longest baseline to the dish size (or f.o.v. to beam size)

    bisp = lambda na: 4480*(na*(na-1)/2)*2*16 + 10*(na*(na-1)/2)*2*1024*2 + 16*(na*(na-1)*(na-2)/6)*2*200*2 + na*(na-1)/2*2*1024*200*2
    imag = lambda na,distratio: 4480*(na*(na-1)/2)*2*16 + 10*(na*(na-1)/2)*2*1024*2 + (na*(na-1)/2)*2*1024*200*2 + ii(na,distratio)*200*2
    cobf = lambda na,distratio: 4480*(na*(na-1)/2)*2*16 + 10*(na*(na-1)/2)*2*1024*2 + 3*nbeam(distratio)*(na*(na-1)/2)*2*1024*2 + nbeam(distratio)*1024*200*2
    ii = lambda na,distratio: (na*(na-1)/2 * 1024 + 5 * (3*distratio)**2 * n.log2((3*distratio)**2))

    dr_evlad = 1000/25.  # eval d-config
    dr_evlaa = 36000/25.
    dr_askap = 6000/12.    # askap, 36-element
    dr_meerkat = 20000/13.5  # meerkat, 64-element

    tot = n.array([2+n.log10(bisp(ar)),2+n.log10(cobf(ar,dr_meerkat)),2+n.log10(imag(ar,dr_meerkat))])  # to define min and max

    fig = plt.figure()
    ax1 = plt.axes((0.18, 0.20, 0.55, 0.65))

    plt.plot([27,27], [0, 20], 'k--')
    plt.text(26.8,12, 'EVLA', horizontalalignment='right',verticalalignment='center',fontsize=12,fontweight="bold", rotation='vertical')
    plt.plot(ar, 2+n.log10(bisp(ar)), 'r', label='Bispectrum',lw=2,clip_on=False)
    plt.fill_between(ar, 2+n.log10(cobf(ar,dr_evlad)), 2+n.log10(cobf(ar,dr_evlaa)), clip_on=False, alpha=0.3, facecolor='b')
    plt.plot(ar, 2+n.log10(cobf(ar,dr_evlad)), 'b--', label='Coherent Beamforming',lw=1,clip_on=False)
    plt.plot(ar, 2+n.log10(cobf(ar,dr_evlaa)), 'b--',lw=1,clip_on=False)
    plt.fill_between(ar, 2+n.log10(imag(ar,dr_evlad)), 2+n.log10(imag(ar,dr_evlaa)), clip_on=False, alpha=0.3, facecolor='y')
    plt.plot(ar, 2+n.log10(imag(ar,dr_evlad)), 'y-.', label='Imaging',lw=1,clip_on=False)
    plt.plot(ar, 2+n.log10(imag(ar,dr_evlaa)), 'y-.',lw=1,clip_on=False)
    plt.text(36, 2+n.log10(imag(36,dr_askap)), 'ASKAP Imaging', horizontalalignment='center',verticalalignment='center',fontsize=12,fontweight="bold")
    plt.text(64, 2+n.log10(imag(64,dr_meerkat)), 'MeerKAT Imaging', horizontalalignment='center',verticalalignment='center',fontsize=12,fontweight="bold")
    plt.title('Computational Demand for EVLA-like Array')
    ax1.set_xlim((ar.min(), ar.max()))
    ax1.set_ylim((tot.min(), tot.max()))
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_position(('outward', 20))
    ax1.spines['left'].set_position(('outward', 30))
    ax1.yaxis.set_ticks_position('left')
    ax1.xaxis.set_ticks_position('bottom')
    plt.xlabel('Number of Antnenas',fontsize=12,fontweight="bold")
    plt.ylabel('log of Computational demand (flops)',fontsize=12,fontweight="bold")
    plt.legend(numpoints=1,loc=2)

    plt.show()


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
    ax1 = p.axes((0.18, 0.20, 0.55, 0.65))
    p.loglog()
    p.plot(s, snrbi(s,num), 'r', label='Bispectrum', linewidth=3)
    p.plot(s, snrco(s,num), 'b--', label='Coherent Beamforming', linewidth=3)
    p.plot(s, snrin(s,num), 'g.', label='Incoherent Baseline Beamforming', linewidth=3)
    p.plot(s, snrinin(s,num), 'y-.', label='Incoherent Antenna Beamforming', linewidth=3)
    ax1.set_xlim((s.min(), s.max()))
    ax1.set_ylim((snrbi(s,num).min(), snrbi(s,num).max()))
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_position(('outward', 20))
    ax1.spines['left'].set_position(('outward', 30))
    ax1.yaxis.set_ticks_position('left')
    ax1.xaxis.set_ticks_position('bottom')
    p.xlabel('SNR per baseline', fontsize=12, fontweight="bold")
    p.ylabel('SNR', fontsize=12, fontweight="bold")
    p.yticks(n.array([0.01,0.03,0.1,0.3,1,3,10,30,100]))
    p.legend(loc=4, numpoints=1)

    # invert equations to get flux limits
    # option 1: analytic inversion
    num = n.arange(3,65)
    sig_vla = 0.063 # 1 sigma, EVLA baseline sensitivity in 10 ms, 1 GHz, dual pol
    sbi = lambda num,thresh: sig_vla * n.power(2*thresh/n.sqrt(num*(num-1)*(num-2)/6.), 1/3.) # cornwell 1987 ... s * num**(-1/2)
    sco = lambda num,thresh: sig_vla * thresh/n.sqrt(num*(num-1)/2.)
#    1/s**4 + 1/s**2 - nbl/(thresh)**2 = 0
    sin = lambda num,thresh: sig_vla * n.sqrt( 2 / (n.sqrt(1 + 2*num*(num-1)/(thresh)**2) - 1) )

    # option 2: computational inversion
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

    gaussian = lambda amp,x,sigma: 1+amp * n.exp(-1.*(x/(n.log(2)*sigma))**2)  # function fit to sensitivity change from 5sigma theory and simulation
    p1 = n.array([ 0.66264219,  8.7812165 ])  # best fit to params for na=3,4,5,6,7,10

    ax1 = p.axes((0.18, 0.20, 0.55, 0.65))

    # analytic...
#    p.plot(num, sbi(num,t), label='Bispectrum')
#    p.plot(num, sco(num,t), label='Coherent Beamforming')
#    p.plot(num, sin(num,t), label='Incoherent Beamforming')
    # computational...
    tot = n.array([scoarr,sinarr,sininarr])
    p.plot(num, gaussian(p1[0],num,p1[1])*sbiarr, 'r', label='Bispectrum', linewidth=3)
    p.plot(num, scoarr, 'b--', label='Coherent Beamforming', linewidth=3)
    p.plot(num, sinarr, 'g.', label='Incoherent Baseline Beamforming', linewidth=3)
    p.plot(num, sininarr, 'y-.', label='Incoherent Antenna Beamforming', linewidth=3)
#    plt.plot(num, sininarr, 'y-.', label='Incoherent Beamforming', linewidth=3)
    p.text(5, 0.2, 'PoCo', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14, fontweight="bold")
    p.text(27, 0.2, 'EVLA', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14, fontweight="bold")
    p.text(36, 0.2, 'ASKAP', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14, fontweight="bold")
    p.text(48, 0.2, 'LOFAR', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14, fontweight="bold")
    p.text(64, 0.2, 'MeerKAT', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14, fontweight="bold")
#    p.title('Flux limits in 10 ms for EVLA-like Array')
    ax1.set_xlim((num.min(), num.max()))
    ax1.set_ylim((tot.min(), tot.max()))
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_position(('outward', 20))
    ax1.spines['left'].set_position(('outward', 30))
    ax1.yaxis.set_ticks_position('left')
    ax1.xaxis.set_ticks_position('bottom')
    p.legend(numpoints=1,loc=1)
    p.xlabel('Number of Antennas', fontsize=12, fontweight="bold")
    p.ylabel('Flux Limit (%d sigma; Jy)' % (t), fontsize=12, fontweight="bold")
    p.show()
