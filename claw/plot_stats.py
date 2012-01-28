#!/usr/bin/env python
# claw 9jan12
#
# script to plot bispectrum and other statistics for transient detection

import numpy as n
import pylab as p
import matplotlib.pyplot as plt
import scipy.misc
import scipy.optimize as opt

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
    p.ylabel('Apparent SNR', fontsize=12, fontweight="bold")
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

    plaw = lambda amp, alpha, x: 1 + amp * (x/3.)**alpha
    gaussian = lambda amp,x,sigma: 1+amp * n.exp(-1.*(x/(n.log(2)*sigma))**2)  # function fit to sensitivity change from 5sigma theory and simulation
    p1 = n.array([ 0.66264219,  8.7812165 ])  # best fit to params for na=3,4,5,6,7,10 with wrong sim
    p2 = n.array([ 0.52286653, -0.945686 ])  # best fit to params for na=3,4,5,6,7,8,9,10 with right sim

    ax1 = p.axes((0.18, 0.20, 0.55, 0.65))

    # analytic...
#    p.plot(num, sbi(num,t), label='Bispectrum')
#    p.plot(num, sco(num,t), label='Coherent Beamforming')
#    p.plot(num, sin(num,t), label='Incoherent Beamforming')
    # computational...
    tot = n.array([scoarr,sinarr,sininarr])
#    p.plot(num, gaussian(p1[0],num,p1[1])*sbiarr, 'r', label='Bispectrum', linewidth=3)
    p.plot(num, plaw(p2[0],p2[1],num)*sbiarr, 'r', label='Bispectrum', linewidth=3)
    print gaussian(p1[0],49,p1[1]),plaw(p2[0],p2[1],48),sbiarr[n.where(num == 48)]
    p.plot(num, scoarr, 'b--', label='Coherent Beamforming', linewidth=3)
    p.plot(num, sinarr, 'g.', label='Incoherent Baseline Beamforming', linewidth=3)
    p.plot(num, sininarr, 'y-.', label='Incoherent Antenna Beamforming', linewidth=3)
#    plt.plot(num, sininarr, 'y-.', label='Incoherent Beamforming', linewidth=3)
    p.text(5, 0.2, 'PoCo', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14, fontweight="bold")
    p.text(27, 0.2, 'VLA', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14, fontweight="bold")
    p.text(36, 0.2, 'ASKAP', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14, fontweight="bold")
    p.text(48, 0.2, 'LOFAR', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14, fontweight="bold")
    p.text(64, 0.2, 'MeerKAT', rotation='vertical', horizontalalignment='center',verticalalignment='center',fontsize=14, fontweight="bold")
#    p.title('Flux limits in 10 ms for VLA-like Array')
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


def bispsim():
    """Plots distributions...
    """

    import det_noise
    gaussian = lambda sigma,x: 1/n.sqrt(2*n.pi*sigma**2) * n.exp(-1.*(x/(n.sqrt(2)*sigma))**2)
    arr = n.arange(-500,501)/100.

    h3 = det_noise.distribution(na=3)
    h6 = det_noise.distribution(na=6)
    h12 = det_noise.distribution(na=12)
    gg = gaussian(1,arr)

    p.figure(1)
    ax1 = p.axes()
    p.plot(n.array(h3[0]),n.log10(h3[1]),'b', label='$n_a=3$', linewidth=2)
    p.plot(n.array(h6[0]),n.log10(h6[1]),'g', label='$n_a=6$', linewidth=2)
    p.plot(n.array(h12[0]),n.log10(h12[1]),'r', label='$n_a=12$', linewidth=2)
    p.plot(arr, n.log10(gg), 'k', label='Gaussian', linewidth=3)

    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_position(('outward', 20))
    ax1.spines['left'].set_position(('outward', 30))
    ax1.yaxis.set_ticks_position('left')
    ax1.xaxis.set_ticks_position('bottom')
    p.legend()
    p.xlabel('Apparent SNR', fontsize=12, fontweight="bold")
    p.ylabel('log$_{10}$ of Relative Rate', fontsize=12, fontweight="bold")
    p.axis([-5,5,-2.5,0.05])

    p.show()


def sim_results():
    sim3_old = n.array( [ [3,4,5,7,9,10,11,15,20,22,25,27],[2.197,1.666,1.4011,1.0464,0.87,0.836,0.78,0.655,0.558,0.537,0.500,0.478] ] )
    sim4_old = n.array( [ [4,8,12,15,17,20,22,25],[2.063,1.097,0.835,0.732,0.676,0.625,0.590,0.550] ] )
    sim5_old = n.array( [ [3,4,5,6,7,8,10],[3.248,2.495,1.947,1.618,1.395,1.243,1.038] ] )

    theory3 = n.array( [ [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,27],[1.817,1.442,1.238,1.103,1.005,0.929,0.868,0.818,0.776,0.740,0.708,0.680,0.655,0.633,0.613,0.594,0.578,0.562,0.548,0.535,0.522,0.511,0.500,0.481] ] )
    theory4 = n.array( [ [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,27],[2.000,1.587,1.363,1.214,1.106,1.023,0.956,0.901,0.854,0.814,0.779,0.748,0.721,0.697,0.674,0.654,0.636,0.619,0.603,0.589,0.575,0.562,0.550,0.529] ] )
    theory5 = n.array( [ [3,4,5,6,7,8,9,10,11,12,13,14],[2.15443469,  1.70997595,  1.46779927,  1.30766049,  1.1912109 ,  1.10145983,  1.02948523,  0.97007012, 0.91992554,  0.87685857,   0.83934208,  0.80627483] ] )
#    theory5 = n.array( [ [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27],[2.15443469,  1.70997595,  1.46779927,  1.30766049,  1.1912109 ,  1.10145983,  1.02948523,  0.97007012,  0.91992554,  0.87685857,   0.83934208,  0.80627483,  0.77683974,  0.75041584,  0.72652157,   0.70477687,  0.68487719,  0.66657526,  0.64966788,  0.63398631,   0.61938912,  0.60575673,  0.59298726,  0.58099328,  0.5696993] ] )

    sim3 = n.array( [ [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,27],[2.2341,1.7068, 1.350, 1.241, 1.102, 0.968, 0.909, 0.864, 0.816, 0.773, 0.725, 0.711, 0.688, 0.642, 0.619, 0.607, 0.593, 0.576, 0.557, 0.536, 0.532, 0.519, 0.500, 0.484] ] )
    sim4 = n.array( [ [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,27],[2.7122, 2.0318, 1.6697, 1.4225, 1.267, 1.146, 1.065, 0.998, 0.916, 0.866, 0.8266, 0.789, 0.759, 0.72613, 0.702, 0.673, 0.664, 0.632, 0.616, 0.600, 0.587, 0.572, 0.560, 0.540] ] )
    sim5 = n.array( [ [3,4,5,6,7,8,9,10,11,12,13,14],[3.2559,2.4193,1.9510,1.6867,1.4629, 1.320, 1.208, 1.120, 1.038, 0.9766, 0.92, 0.882] ] )

    bf3 = n.array( [ [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,27],[1.75208047926269, 1.19243808600164, 0.95824570274179, 0.77276647429923, 0.62327085251299, 0.56073721609684, 0.49224408566996, 0.47003752697561, 0.40726216607240, 0.36881832376607, 0.34271750148941, 0.32519903783076, 0.29386667402896, 0.28223612373069, 0.25392716314416, 0.24093327994493, 0.23780340805854, 0.22418922077704, 0.20389490916881, 0.20329503998755, 0.18871948307756, 0.18282973583140, 0.17747952133728, 0.15358594031471] ] )
    bf3t = n.array( [ [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,27],[1.73205081,  1.22474487,  0.9486833 ,  0.77459667,  0.65465367,        0.56694671,  0.5       ,  0.4472136 ,  0.40451992,  0.36927447,        0.33968311,  0.31448545,  0.29277002,  0.27386128,  0.25724788,        0.24253563,  0.22941573,  0.21764288,  0.20701967,  0.19738551,        0.18860838,  0.18057878,  0.17320508,  0.16012815] ] )

    p.figure(1)
    p.plot(sim3[0], sim3[1], 'r', label='s3')
    p.plot(sim4[0], sim4[1], 'b', label='s4')
    p.plot(sim5[0], sim5[1], 'g', label='s5')
    p.plot(theory3[0], theory3[1], 'r*', label='t3')
    p.plot(theory4[0], theory4[1], 'b*', label='t4')
    p.plot(theory5[0], theory5[1], 'g*', label='t5')
    p.legend()
    p.xlabel('$n_a$')
    p.ylabel('s$_{lim}$')

    r3 = []; r4 = []; r5 = []
    for i in range(len(sim3_old[0])):
        ww = n.where( sim3_old[0][i] == theory3[0] )[0]
        r3.append( (sim3_old[1][i]/theory3[1][ww])[0] )
    for i in range(len(sim4_old[0])):
        ww = n.where( sim4_old[0][i] == theory4[0] )[0]
        r4.append( (sim4_old[1][i]/theory4[1][ww])[0] )
    for i in range(len(sim5_old[0])):
        ww = n.where( sim5_old[0][i] == theory5[0] )[0]
        r5.append( (sim5_old[1][i]/theory5[1][ww])[0] )

    p.figure(2)
    p.plot(sim3_old[0], r3, 'r--', label='r3o')
    p.plot(sim4_old[0], r4, 'b--', label='r4o')
    p.plot(sim5_old[0], r5, 'g--', label='r5o')
    p.plot(sim3[0], sim3[1]/theory3[1], 'r', label='r3')
    p.plot(sim4[0], sim4[1]/theory4[1], 'b', label='r4')
    p.plot(sim5[0], sim5[1]/theory5[1], 'g', label='r5')
    p.legend()
    p.xlabel('$n_a$')
    p.ylabel('Limit ratio')

#    p.figure(3)
#    p.plot(bf3[0], bf3[1], '--')
#    p.plot(bf3t[0], bf3t[1], '.')

    p.figure(4)
    if 1:   # new simulation
        narr3 = sim3[0]
        narr4 = sim4[0]
        narr5 = sim5[0]
        ratio3 = sim3[1]/theory3[1]
        ratio4 = sim4[1]/theory4[1]
        ratio5 = sim5[1]/theory5[1]
    else:    # old simulation
        narr3 = sim3_old[0]
        narr4 = sim4_old[0]
        narr5 = sim5_old[0]
        ratio3 = n.array(r3)
        ratio4 = n.array(r4)
        ratio5 = n.array(r5)

    plaw = lambda amp, alpha, x: 1 + amp * (x/3.)**alpha
    fitfunc = lambda p, x: plaw(p[0],p[1],x)
    errfunc = lambda p, x, y: fitfunc(p, x)**2 - y**2
    p0 = [0.5, -0.5]
    p3, success = opt.leastsq(errfunc, p0[:], args = (narr3, ratio3))
    p4, success = opt.leastsq(errfunc, p0[:], args = (narr4, ratio4))
    p5, success = opt.leastsq(errfunc, p0[:], args = (narr5, ratio5))

    p.plot(narr3, ratio3, 'b.', label='obs3')
    p.plot(narr3, fitfunc(p3,narr3), 'b', label='fit3')
    p.plot(narr4, ratio4, 'r.', label='obs4')
    p.plot(narr4, fitfunc(p4,narr4), 'r', label='fit4')
    p.plot(narr5, ratio5, 'g.', label='obs5')
    p.plot(narr5, fitfunc(p5,narr5), 'g', label='fit5')
    p.legend()
    p.xlabel('$n_a$')
    p.ylabel('Limit ratio')
    print '**Best fits**'
    print '3:', p3
    print '4:', p4
    print '5:', p5
    print '**VLA limit**'
    print '3:', plaw(p3[0],p3[1], 27)
    print '4:', plaw(p4[0],p3[1], 27)
    print '5:', plaw(p5[0],p5[1], 27)
    print narr3, plaw(p5[0],p5[1], narr3)

    p.show()

