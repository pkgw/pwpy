#!/usr/bin/env python
"""Script to simulate RM synthesis.
First, visualize complex polarization for range of Faraday dispersion functions.
Ultimately, simlate range of Faraday dispersion functions over range of z,
including sampling in lambda^2 space.
"""

import numpy as n
import pylab as p
import scipy.optimize as opt

# params
stdlen = 10000   # fd=0 at index=stdlen/2
fdscale = 10.

def find_nearest(array,value):
    """Function to help set fd values at grid points.
    """

    idx=(n.abs(array-value)).argmin()
    return array[idx]

def fd_gaussian(width=1., height=1., center=0., show=0):
    """Returns a Gaussian Faraday disperison function tuple (depth, pol)
    Units are rad/m2 scaled by fdscale.
    """

    # to do:  include phase in complex fd

    pol = n.zeros(stdlen, dtype='complex')

    fd = n.arange(-1*stdlen/2, stdlen/2, dtype='double') * fdscale
    index = n.where(fd == find_nearest(fd, center))[0]

    for i in range(stdlen):
        pol[i] = (height/n.sqrt(2*n.pi*width**2))*n.exp(-1.*(float(fd[i]-fd[index])/(n.sqrt(2)*width))**2) + 0.j

    print 'Simulated Gaussian FD of width %f, height %f, and center %f' % (float(width), float(height), float(fd[index]))

    return (fd, pol)

def fd_point(height=1., center=0., show=0):
    """Returns a point-like Faraday disperison function tuple (depth, pol).
    Units are rad/m2 scaled by fdscale.
    """

    # to do:  include phase in complex fd?

    fd = n.arange(-1*stdlen/2, stdlen/2, dtype='double') * fdscale

    pol = n.zeros(stdlen, dtype='complex')
    index = n.where(fd == find_nearest(fd,center))[0]
    pol[index] = height + 0.j

    if show:
        p.plot(fd, pol)
        p.show()

    print 'Simulated point FD of height %f and center %f' % (float(height), float(fd[index]))

    return (fd, pol)

def fd_point_random(num=1, distribution=100., dis_center=0., height=1.):
    """Returns a Faraday dispersion function tuple with n point-like components 
    randomly spread in Gaussian distribution of width.
    """
    import random

    center = random.gauss(dis_center, distribution)   # random distribution centered at 0.
    depth, pol = fd_point(height=height, center=center)

    for i in range(1, num):
        center = random.gauss(dis_center, distribution)
        pol = pol + fd_point(height=height, center=center)[1]

    return (depth, pol)

def fd_gaussian_random(num=1, distribution=100., dis_center=0., height=1., width=1.):
    """Returns a Faraday dispersion function with n gaussian components randomly spread in 
    a Gaussian distribution with width equal to distribution.  Each width is equal to width.
    """
    import random

    center = random.gauss(dis_center, distribution)   # random distribution centered at 0.
    depth, pol = fd_gaussian(width=width, height=height, center=center)

    for i in range(1, num):
        center = random.gauss(dis_center, distribution)
        pol = pol + fd_gaussian(width=width, height=height, center=center)[1]

    return (depth, pol)

def plot_fd(fd):
    """Plots the fd (where bright).
    """

    p.plot(fd[0], n.abs(fd[1]))
    stuff = fd[0][n.where(fd[1] >= 1e-5)[0]]  # show just bright stuff
    p.xlim(min(stuff), max(stuff))
    p.xlabel('Faraday depth (rad/m2)')
    p.ylabel('Polarized flux (Jy)')
    p.show()

def calc_spectrum(fd, show=0):
    """Returns the fft of a fd, which is Stokes Q, U spectrum.  Optionally plots.
    fd index number is in units of rad/m2.  fd is tuple of (depth, pol).
    fft index number is therefore in units of m2/rad, scaled by 2*pi/stdlen.
    output is spectrum tuple with (lambda2, stokes).
    """

    # to do:  test whether complex fd produces asymmetric fft.

    fft = n.fft.fft(fd[1])

    # create fft reference at origin to have 0th fourier mode at index=stdlen/2
    fftref = n.fft.fft(fd_point(height=1,center=0.)[1])
    fft = fft * fftref

    lambda2 = (n.pi/(-1*min(fd[0])))*n.arange(stdlen/2)   # "-1*min() is a hack to get extreme positive value
    stokes = fft[0:stdlen/2]

    if show:
        plot_spectrum((lambda2, stokes))

    return (lambda2, stokes)

def redshift_lambda2(lambda2, z):
    """Takes true lambda^2 and redshifts to lambda_obs for given z.
    """

    print 'Redshifted to z = ', z

    lambda2_obs = lambda2 * (1 + z)**2

    return lambda2_obs

def sample_band_average_two(spectrum, band1l, band1h, band2l, band2h, show=0):
    """Samples a 2 sets of channels of fft with averaging.  Optionally plots.
    Sampling set in lambda^2 units.
    """

    lambda2 = spectrum[0]
    stokes = spectrum[1]

    print 'Band 1: %.3f -- %.3f, Band 2: %.3f -- %.3f, n-pi: %.1f' % (band1l, band1h, band2l, band2h, n.pi/n.abs(n.mean([band1l, band1h]) - n.mean([band2l, band2h])))


    stokes2 = n.zeros(2, dtype='complex')
    lambda22 = n.zeros(2, dtype='double')
    indices1 = n.where( (lambda2 > band1l) & (lambda2 < band1h))
    indices2 = n.where( (lambda2 > band2l) & (lambda2 < band2h))
#    indices1 = n.where( (lambda2 > (center-separation/2) - width/2) & (lambda2 < (center-separation/2) + width/2))
#    indices2 = n.where( (lambda2 > (center+separation/2) - width/2) & (lambda2 < (center+separation/2) + width/2))
    stokes2[0] = n.mean(stokes[indices1])
    lambda22[0] = n.mean([band1l, band1h])
    stokes2[1] = n.mean(stokes[indices2])
    lambda22[1] = n.mean([band2l, band2h])
    print 'Averaged %d and %d indices for band 1 and band 2.' % (len(indices1[0]), len(indices2[0]))

    if show:
        p.figure(1)
        p.plot(lambda2, n.abs(stokes))
        p.plot(lambda22, n.abs(stokes2))
        p.show()

    return lambda22, stokes2

def plot_spectrum(spectrum):
    """Plots the real and imaginary parts of the spectrum (i.e., fft or Stokes Q and U).
    Works for lambda^2 and stokes given as input.
    """

    lambda2 = spectrum[0]
    stokes = spectrum[1]

    # define good channels to avoid zeros
    good = n.where(stokes != 0)[0]

    p.figure(1)
    p.subplot(311)
    p.plot(stokes[good].real[:stdlen/2],stokes[good].imag[:stdlen/2],'.-')
    p.xlabel("Stokes Q (Jy)")
    p.ylabel("Stokes U (Jy)")
    p.subplot(312)
    p.plot(lambda2[good], stokes[good].real, 'b.')
    p.plot(lambda2[good], stokes[good].imag, 'r*')
    p.xlabel('Obs Lambda^2 (m^2)')
    p.ylabel('Stokes Q,U (Jy)')
    logx = p.subplot(313)
    logx.set_xscale('log')
    p.plot(0.3/n.sqrt(lambda2[good]), stokes[good].real, 'b.')
    p.plot(0.3/n.sqrt(lambda2[good]), stokes[good].imag, 'r*')
    p.xlabel('Obs Freq (GHz)')
    p.ylabel('Stokes Q,U (Jy)')
    p.show()

def fit_angle(spectrum, show=0, verbose=0):
    """Fit line to angle of Stokes spectrum (i.e., fft real-imag or Q-U).
    Guesses based on initial fit to two channels.
    Requires lambda2 and stokes input separately.
    Note:  defined slope of angle vs. index to be -1*stdlen of input FD.
    """

    # to do:  needs better way to find global minimum or reject bad fits

    guess = 1

    lambda2 = spectrum[0]
    stokes = spectrum[1]

    print 'Low band:  %.3f, High band: %.3f, n-pi: %.1f' % (min(spectrum[0]), max(spectrum[0]), n.pi/n.abs(max(spectrum[0])-min(spectrum[0])))

    # define good channels to avoid zeros
    good = n.where(stokes != 0)[0]

    line = lambda a,b,x: n.mod((a - n.pi + x*b), 2*n.pi) - n.pi
    fitfunc = lambda p, x:  line(p[0], p[1], x)
    errfunc = lambda p, x, y: y - fitfunc(p, x)

    # attempt one, using two channels
    p0 = [0.,0.]

    if guess:
        p1, success = opt.leastsq(errfunc, p0[:], args = (lambda2[good][0:2], -1*n.angle(stokes[good][0:2])))
        if success and show and verbose:
            print 'First attempt...'
            print 'Chi^2, Results: ', n.sum(errfunc(p1, lambda2[good], -1*n.angle(stokes))**2), p1
            p0 = p1

    # final fit
    p1, success = opt.leastsq(errfunc, p0[:], args = (lambda2[good], -1*n.angle(stokes[good])))
    if success:
        chisq = n.sum(errfunc(p1, lambda2[good], -1*n.angle(stokes[good]))**2)
        print 'Chi^2, Results: ', chisq, p1

    if show:
        p.plot(lambda2[good], fitfunc(p1, lambda2[good]), '--')
        p.plot(lambda2[good], -1*n.angle(stokes[good]))

    print
    return chisq, p1

def simulate_rrmpol(trials=1, z=0., width=50., num=1, distribution=200., show=0, verbose=0):
    """Simulate to measure the distribution of rrm and pol for
    a source model distribution at a given redshift.
    """

    chisqlimit = 0.5  # ok "eyeball" fit for 4-point spectrum?

    # Define bands 
    band1 = n.array([1.4, 1.45])  # in GHz
    band2 = n.array([1.45, 1.5])  # in GHz
    band3 = n.array([1.8, 1.85])  # in GHz
    band4 = n.array([3.0, 3.05])  # in GHz
    s_band1 = (0.3/band1)**2
    s_band2 = (0.3/band2)**2
    s_band3 = (0.3/band3)**2
    s_band4 = (0.3/band4)**2

    rrm = []; pol = []

    for i in range(trials):
        fd = fd_gaussian_random(width=width, num=num, distribution=distribution)
        if show:
            plot_fd(fd)
            p.show()
        spectrum = calc_spectrum(fd, show=show)
        lambda2z = redshift_lambda2(spectrum[0], z)
        spectrum2 = sample_band_average_two((lambda2z, spectrum[1]), n.min(s_band1), n.max(s_band1), n.min(s_band2), n.max(s_band2))
        spectrum3 = sample_band_average_two((lambda2z, spectrum[1]), n.min(s_band3), n.max(s_band3), n.min(s_band4), n.max(s_band4))
        spectrum4 = (n.concatenate((spectrum2[0], spectrum3[0])), n.concatenate((spectrum2[1], spectrum3[1])))
        chisq, result = fit_angle(spectrum4, show=show, verbose=verbose)
        if chisq < chisqlimit:
            rrm.append(result[1])
            pol.append(spectrum4[1])

    return (n.array(rrm), n.array(pol))

def simulate_redshift():
    """
    Runs simulate_rrmpol for a range of z.
    Simulates three source model distributions.  Results plotted with plot_sim.
    Question:  Does rms of RRM values increase at higher redshift?  What source property does this?
    """

    rrm1 = []; pol1 = []; rrm2 = []; pol2 = []; rrm3 = []; pol3 = []
    for z in n.arange(0,13)/3.:
        rrm, pol = simulate_rrmpol(trials=200, z=z, width=10., num=1, distribution=100.)
        rrm1.append(rrm); pol1.append(pol)
        rrm, pol = simulate_rrmpol(trials=200, z=z, width=30., num=1, distribution=100.)
        rrm2.append(rrm); pol2.append(pol)
        rrm, pol = simulate_rrmpol(trials=200, z=z, width=100., num=1, distribution=100.)
        rrm3.append(rrm); pol3.append(pol)

    return rrm1, pol1, rrm2, pol2, rrm3, pol3

def simulate_redshift2():
    """
    Runs simulate_rrmpol for a range of z.
    Simulates three source model distributions.  Results plotted with plot_sim.
    Question:  Does rms of RRM values increase at higher redshift?  What source property does this?
    """

    rrm1 = []; pol1 = []; rrm2 = []; pol2 = []; rrm3 = []; pol3 = []
    for z in n.arange(0,4)/1.:
        rrm, pol = simulate_rrmpol(trials=10, z=z, width=7., num=10, distribution=70.)
        rrm1.append(rrm); pol1.append(pol)
        rrm2 = rrm1; rrm3 = rrm1
        pol2 = pol1; pol3 = pol1

    return rrm1, pol1, rrm2, pol2, rrm3, pol3


def plot_sim(res):
    """Plots result from simulate_redshift.
    Assumes three source models in res tuple.  Each source model gives a rrm and pol.
    """

    rrm1 = res[0]; pol1 = res[1]
    rrm2 = res[2]; pol2 = res[3]
    rrm3 = res[4]; pol3 = res[5]

    trim = 999999.  # trim abs(rrm) larger than this value

    rrm1rms = [n.std(rrm1[i][n.where ( n.abs(rrm1[i]) < trim)]) for i in range(len(rrm1))]
    rrm2rms = [n.std(rrm2[i][n.where ( n.abs(rrm2[i]) < trim)]) for i in range(len(rrm2))]
    rrm3rms = [n.std(rrm3[i][n.where ( n.abs(rrm3[i]) < trim)]) for i in range(len(rrm3))]
    pol1ave = n.mean(n.abs(pol1), axis=1)
    pol2ave = n.mean(n.abs(pol2), axis=1)
    pol3ave = n.mean(n.abs(pol3), axis=1)

    p.figure(1)
    rrm1con = [[n.std(rrm1[j][n.where ( n.abs(rrm1[j]) < trim)][:i]) for i in range(len(rrm1[0]))] for j in range(len(rrm1))]
    rrm2con = [[n.std(rrm2[j][n.where ( n.abs(rrm2[j]) < trim)][:i]) for i in range(len(rrm2[0]))] for j in range(len(rrm2))]
    rrm3con = [[n.std(rrm3[j][n.where ( n.abs(rrm3[j]) < trim)][:i]) for i in range(len(rrm3[0]))] for j in range(len(rrm3))]
    for i in range(len(rrm1con)):
        p.plot(rrm1con[i])
        p.plot(rrm2con[i])
        p.plot(rrm3con[i])
    p.xlabel('iteration number')
    p.ylabel('RRM RMS')
    p.title('Convergence test')

    print 'Pol 1, 2, 3 averages:'
    print pol1ave
    print pol2ave
    print pol3ave
    p.figure(2)
    p.plot(rrm1rms, label='rrm1')
    p.plot(rrm2rms, label='rrm2')
    p.plot(rrm3rms, label='rrm3')
    p.legend()
    p.xlabel('redshift bin')
    p.ylabel('RRM RMS')
    p.title('RRM RMS redshift dependence')

    p.figure(3)
    for i in range(len(rrm1)):
        p.subplot(311)
        p.hist(rrm1[i],bins=20, label=str(i))
        p.subplot(312)
        p.hist(rrm2[i],bins=20, label=str(i))
        p.subplot(313)
        p.hist(rrm3[i],bins=20, label=str(i))

    p.legend()
    p.xlabel('RRM (rad/m2)')
    p.ylabel('Number of sources')
    p.title('Distribution of RRM')

###########################################
########Still to convert to new system#####
###########################################

def calc_rmbeam_old(center, width, show=0):
    """Returns beam in RM (fd) space for a given sampling function"""

    sample = n.ones(stdlen)
    sample[0:center-width/2] = 0.
    sample[center+width/2:stdlen-(center+width/2)] = 0.
    sample[stdlen-(center-width/2):] = 0.

    beam = n.fft.ifft(sample)

    if show:
        p.figure(2)
        p.plot(beam[:stdlen/2])

    return beam[:stdlen/2]

def calc_ifft_old(fft, fd=[0], beam=[0]):
    """Calculates the inverse fft, producing Faraday dispersion function.  
    Optionally plots comparison to initial fd and rmbeam."""

    fd2 = n.fft.ifft(fft)

    if len(fd) > 1:
        p.plot(fd, label="fd")
        p.plot(fd2, label="fd2")
        if len(beam) > 1:
            norm = max(fd2)/max(beam)
            beam2 = norm*n.concatenate((beam[stdlen/2:],beam[:stdlen/2-1]))
            p.plot(beam2, label="beam")
        p.legend()
        p.show()

    return fd2


if __name__ == '__main__':
    print 'Generating Faraday depth distribution...'
    fd = fd_point_random(num=2)
    plot_fd(fd)
    print
    print 'Transforming to RM spectrum...'
    sp = calc_spectrum(fd, show=1)
