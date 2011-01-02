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
stdlen = 1000   # fd=0 at index=stdlen/2
fdscale = 10.

def find_nearest(array,value):
    idx=(n.abs(array-value)).argmin()
    return array[idx]

def fd_gaussian(width=1., height=1., center=0., show=0):
    """Returns a Gaussian Faraday disperison function tuple (depth, pol)
    Units are rad/m2 scaled by fdscale.
    """

    # to do:  include phase in complex fd
    # to do:  normalize differently?

    pol = n.zeros(stdlen, dtype='complex')

    fd = n.arange(-1*stdlen/2, stdlen/2, dtype='double') * fdscale
    index = n.where(fd == find_nearest(fd, center))[0]

    for i in range(stdlen):
        pol[i] = height*n.exp(-1.*(float(fd[i]-fd[index])/float(width))**2) + 0.j

    if show:
        p.plot(fd, pol)
        p.xlabel('Faraday depth (rad/m2)')
        p.ylabel('Polarized flux (Jy)')
        p.show()

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
    """Plots the fd.
    """

    p.plot(fd[0], n.abs(fd[1]))
    p.xlabel('Faraday depth (rad/m2)')
    p.ylabel('Polarized flux (Jy)')

def calc_spectrum(fd, show=0):
    """Returns the fft of a fd, which is Stokes Q, U spectrum.  Optionally plots.
    fd index number is in units of rad/m2.  fd is tuple of (depth, pol).
    fft index number is therefore in units of m2/rad, scaled by 2*pi/stdlen.
    output is spectrum tuple with (lambda2, stokes).
    """

    # to do:  plot only first half?  test whether complex fd produces asymmetric fft.

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

    lambda2_obs = lambda2 * (1 + z)**2

    return lambda2_obs

def sample_band_average_two(spectrum, center, width, separation, show=0):
    """Samples a 2 sets of channels of fft with averaging.  Optionally plots.
    Sampling set in lambda^2 units.
    """

    lambda2 = spectrum[0]
    stokes = spectrum[1]

    stokes2 = n.zeros(2, dtype='complex')
    lambda22 = n.zeros(2, dtype='double')
    indices1 = n.where( (lambda2 > (center-separation/2) - width/2) & (lambda2 < (center-separation/2) + width/2))
    indices2 = n.where( (lambda2 > (center+separation/2) - width/2) & (lambda2 < (center+separation/2) + width/2))
    stokes2[0] = n.mean(stokes[indices1])
    lambda22[0] = center-separation/2
    stokes2[1] = n.mean(stokes[indices2])
    lambda22[1] = center+separation/2
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

    lambda2 = spectrum[0]
    stokes = spectrum[1]

    # define good channels to avoid zeros
    good = n.where(stokes != 0)[0]

    line = lambda a,b,x: n.mod((a - n.pi + x*b), 2*n.pi) - n.pi
    fitfunc = lambda p, x:  line(p[0], p[1], x)
    errfunc = lambda p, x, y: y - fitfunc(p, x)

    # attempt one, using two channels
    p0 = [0.,0.]
    p1, success = opt.leastsq(errfunc, p0[:], args = (lambda2[good][0:2], -1*n.angle(stokes[good][0:2])))
    if success and show and verbose:
        print 'First attempt...'
        print 'Chi^2, Results: ', n.sum(errfunc(p1, lambda2[good], -1*n.angle(stokes))**2), p1

    # attempt two, using first fit
    p0 = p1
    p1, success = opt.leastsq(errfunc, p0[:], args = (lambda2[good], -1*n.angle(stokes[good])))
    if success:
        print 'Chi^2, Results: ', n.sum(errfunc(p1, lambda2[good], -1*n.angle(stokes[good]))**2), p1

    if show:
        p.plot(lambda2[good], fitfunc(p1, lambda2[good]), '--')
        p.plot(lambda2[good], -1*n.angle(stokes[good]))

    return p1

def simulate_redshift(trials=1000):
    """Simulate a single distribution of source models.  
    Measure sources fixed lambda^2 coverage over range of redshift.
    Inputs should be given as redshift range and bands at z=0.
    Question:  Does rms of RRM values increase at higher redshift?
    """

    # source model
    width=50
    num=3
    distribution=300

    # bands 
    band1 = 1.4  # in GHz
    band2 = 1.5  # in GHz
    s_center = ((0.3/band1)**2 + (0.3/band2)**2)/2.
    s_sep = abs((0.3/band1)**2 - (0.3/band2)**2)
    s_width = s_sep
    print 'Band center=%.3f, sep=%.3f, width=%.3f' % (s_center, s_sep, s_width)

    zrrm = []
    for z in n.arange(0,5)/2.:
        rrm = []
        for i in range(trials):
            fd = fd_gaussian_random(width=width, num=num, distribution=distribution)
            spectrum = calc_spectrum(fd)
            lambda2z = redshift_lambda2(spectrum[0], z)
            spectrum2 = sample_band_average_two((lambda2z, spectrum[1]), s_center, s_width, s_sep)
            
            result = fit_angle(spectrum2)
            rrm.append(result[1])
        zrrm.append(rrm)

    return zrrm

###########################################
##############Old Versions#################
###########################################

def fd_tophat_old(width, height=1., center=0, show=0):
    """Returns a tophat Faraday disperison function.
    Units are rad/m2.
    """

    fd = n.zeros(stdlen, dtype='complex')
    fd[stdlen/2 - width + center: stdlen/2 + width + center] = height + 0.j

    if show:
        p.plot(fd)
        p.show()

    return fd

def fd_gaussian_old(width, height=1., center=0, show=0):
    """Returns a Gaussian Faraday disperison function.
    Units are rad/m2.
    """

    # to do:  include phase in complex fd

    fd = n.zeros(stdlen, dtype='complex')
    for i in range(stdlen):
        fd[i] = height*n.exp(-1.*((i-(center+stdlen/2))/float(width))**2) + 0.j

    if show:
        p.plot(fd)
        p.show()

    print 'Simulated Gaussian FD of width %f, height %f, and center %f' % (float(width), float(height), float(center))

    return fd

def fd_point_old(height=1., center=0, show=0, verbose=1):
    """Returns a point-like Faraday disperison function.
    Units are rad/m2.
    """

    # to do:  include phase in complex fd
    # to do:  flux not normalized?

    fd = n.zeros(stdlen, dtype='complex')
    fd[stdlen/2 + center] = height + 0.j

    if show:
        p.plot(fd)
        p.show()

    if show or verbose:
        print 'Simulated point FD of height %f and center %f' % (float(height), float(center))

    return fd

def fd_point_random_old(num=2, height=1., width=100):
    """Returns a Faraday dispersion function with n point-like components randomly spread in 
    Gaussian distribution of width.
    """
    import random

    center = int(n.round(random.gauss(0., width), 0))
    fd = fd_point(height=height, center=center)

    for i in range(1, num):
        center = int(n.round(random.gauss(0., width), 0))
        fd = fd + fd_point(height=height, center=center)

    return fd

def fd_gaussian_random_old(width, num=2, height=1., distribution=100):
    """Returns a Faraday dispersion function with n gaussian components randomly spread in 
    a Gaussian distribution with width equal to distribution.  Each width is equal to width.
    """
    import random

    center = int(n.round(random.gauss(0., distribution), 0))
    fd = fd_gaussian(width=width, height=height, center=center)

    for i in range(1, num):
        center = int(n.round(random.gauss(0., width), 0))
        fd = fd + fd_gaussian(width=width, height=height, center=center)

    return fd, pol

def calc_fft_old(fd, show=0):
    """Returns the fft of an fd, which is Stokes Q, U.  Optionally plots.
    fd index number is in units of rad/m2.
    fft index number is therefore in units of m2/rad, scaled by 2*pi/stdlen.
    """

    # to do:  plot only first half?  test whether complex fd produces asymmetric fft.

    fft = n.fft.fft(fd)

    # create fft reference at origin to have 0th fourier mode at index=stdlen/2
    fftref = n.fft.fft(fd_point(height=1,center=0,verbose=0))
    fft = fft * fftref
    if show:
       p.plot((2*n.pi/stdlen)*n.arange(stdlen), n.abs(fft))
       p.show()

    return fft

def sample_band_old(fft, center, width, show=0):
    """Samples a set of channels in lambda^2 space.  
    Returns band at original resolution.  Optionally plots.
    """

    # to do:  sample linearly in lambda space

    fft2 = n.zeros(len(fft), dtype='complex')
    indices = n.arange(center-width/2, center+width/2)
    fft2[indices] = fft[indices]

    if show:
        p.figure(1)
        p.plot((2*n.pi/stdlen)*n.arange(stdlen), n.abs(fft))
        p.plot((2*n.pi/stdlen)*n.arange(stdlen), n.abs(fft2))
        p.show()

    return fft2

def sample_band_average_two_old(fft, center, width, separation, show=0):
    """Samples a 2 sets of channels of fft with averaging.  Optionally plots"""

    fft2 = n.zeros(len(fft), dtype='complex')
    indices1 = n.arange(center-separation/2-width/2, center-separation/2+width/2)
    indices2 = n.arange(center+separation/2-width/2, center+separation/2+width/2)
    fft2[center-separation/2] = n.mean(fft[indices1])
    fft2[center+separation/2] = n.mean(fft[indices2])

    if show:
        p.figure(1)
        p.plot((2*n.pi/stdlen)*n.arange(stdlen), n.abs(fft))
        p.plot((2*n.pi/stdlen)*n.arange(stdlen), n.abs(fft2))
        p.show()

    return fft2

def plot_fft_old(fft):
    """Plots the real and imaginary parts of the fft (i.e., Stokes Q and U)"""

    # define good channels to avoid zeros
    good = n.where(fft != 0)[0]

    p.figure(1)
    p.subplot(311)
    p.plot(fft[good].real[:stdlen/2],fft[good].imag[:stdlen/2],'.-')
    p.xlabel("Stokes Q (Jy)")
    p.ylabel("Stokes U (Jy)")
    p.subplot(312)
    p.plot(good*(2*n.pi/stdlen), fft[good].real, 'b.')
    p.plot(good*(2*n.pi/stdlen), fft[good].imag, 'r*')
    p.xlabel('Obs Lambda^2 (m^2)')
    p.ylabel('Stokes Q,U (Jy)')
    logx = p.subplot(313)
    logx.set_xscale('log')
    p.plot(0.3/n.sqrt(good*(2*n.pi/stdlen)), fft[good].real, 'b.')
    p.plot(0.3/n.sqrt(good*(2*n.pi/stdlen)), fft[good].imag, 'r*')
    p.xlabel('Obs Freq (GHz)')
    p.ylabel('Stokes Q,U (Jy)')
    p.show()

def fit_angle_old(fft, show=0, verbose=0):
    """Fit line to angle of fft real-imag (i.e., Q-U).
    Guesses based on initial fit to two channels.
    Note:  defined slope of angle vs. index to be -1*stdlen of input FD.
    """

    # define good channels to avoid zeros
    good = n.where(fft != 0)[0]

    line = lambda a,b,x: (a + x*b/(stdlen/2.)) % 2*n.pi - n.pi   # WRONG!  should use n.mod()
    fitfunc = lambda p, x:  line(p[0], p[1], x)
    errfunc = lambda p, x, y: y - fitfunc(p, x)

    # attempt one, using two channels
    p0 = [0.,0.]
    p1, success = opt.leastsq(errfunc, p0[:], args = (good[0:2], -1*n.angle(fft[good][0:2])))
    if success and show and verbose:
        print 'First attempt...'
        print 'Chi^2, Results: ', n.sum(errfunc(p1, good, -1*n.angle(fft))**2), p1

    # attempt two, using first fit
    p0 = p1
    p1, success = opt.leastsq(errfunc, p0[:], args = (good, -1*n.angle(fft[good])))
    if success:
        print 'Chi^2, Results: ', n.sum(errfunc(p1, good, -1*n.angle(fft[good]))**2), p1

    if show:
        p.plot(good, fitfunc(p1, good), '--')
        p.plot(good, -1*n.angle(fft[good]))

    return p1

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

def simulate_rrmrms_old(trials = 1000, s_center = 11, s_width = 10, s_sep = 10):
    """Creates many trials of fd and samples Q-U (fft) to simulate theta-lambda^2 fit results.
    Optionally can sample at different redshifts.
    Question:  Does rms of RRM values increase at higher redshift?"""

    rrm = []

    # source model Gaussians in rad/m2
    width=10
    num=2
    distribution=100

    print 'Bands centered at ', 2*n.pi/stdlen * (s_center - s_sep), 2*n.pi/stdlen * (s_center + s_sep), ' m^2.'
    print 'Bands centered at ', 0.3/n.sqrt(2*n.pi/stdlen * (s_center - s_sep)), 0.3/n.sqrt(2*n.pi/stdlen * (s_center + s_sep)), ' GHz.'
    for i in range(trials):
        fd = fd_gaussian_random(width=width, num=num, distribution=distribution)
#        fd = fd_point_random(width=width, num=num)
        fft = calc_fft(fd)
#        fft2 = sample_band(fft, 10, 10)
        fft2 = sample_band_average_two(fft, s_center, s_width, s_sep)

        result = fit_angle(fft2)
        rrm.append(result[1])

    return rrm

def simulate_redshift_old():
    """Simulate a single source model, then measure at fixed redshifted lambda^2 coverage.
    """

    # to do:  inputs should be given as redshift range and bands at z=0

    rrm8 = simulate_rrmrms(s_center = 8, s_width = 2, s_sep = 2)
    rrm7 = simulate_rrmrms(s_center = 7, s_width = 2, s_sep = 2)
    rrm6 = simulate_rrmrms(s_center = 6, s_width = 2, s_sep = 2)
    rrm5 = simulate_rrmrms(s_center = 5, s_width = 2, s_sep = 2)
    rrm4 = simulate_rrmrms(s_center = 4, s_width = 2, s_sep = 2)
    rrm3 = simulate_rrmrms(s_center = 3, s_width = 2, s_sep = 2)

    return (rrm8,rrm7,rrm6,rrm5,rrm4,rrm3)

