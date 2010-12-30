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

def fd_tophat(width, height=1., center=0, show=0):
    """Returns a tophat Faraday disperison function.
    Units are rad/m2.
    """

    fd = n.zeros(stdlen, dtype='complex')
    fd[stdlen/2 - width + center: stdlen/2 + width + center] = height + 0.j

    if show:
        p.plot(fd)
        p.show()

    return fd

def fd_gaussian(width, height=1., center=0, show=0):
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

def fd_point2(height=1., center=0, show=0, verbose=1):
    """Returns a point-like Faraday disperison function.
    Units are rad/m2.
    """

    # to do:  include phase in complex fd
    # to do:  flux not normalized?

    pol = n.zeros(stdlen, dtype='complex')
    pol[stdlen/2 + center] = height + 0.j

    fd = n.arange(-1*stdlen/2, stdlen/2)

    if show:
        p.plot(fd, pol)
        p.show()

    if show or verbose:
        print 'Simulated point FD of height %f and center %f' % (float(height), float(center))

    return (fd,pol)

def fd_point(height=1., center=0, show=0, verbose=1):
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

def fd_point_random(num=2, height=1., width=100):
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

def fd_gaussian_random(width, num=2, height=1., distribution=100):
    """Returns a Faraday dispersion function with n gaussian components randomly spread in 
    a Gaussian distribution with width equal to distribution.  Each width is equal to width.
    """
    import random

    center = int(n.round(random.gauss(0., distribution), 0))
    fd = fd_gaussian(width=width, height=height, center=center)

    for i in range(1, num):
        center = int(n.round(random.gauss(0., width), 0))
        fd = fd + fd_gaussian(width=width, height=height, center=center)

    return fd

def calc_fft(fd, show=0):
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

def calc_fft2(fd, pol, show=0):
    """Returns the fft of an fd, which is Stokes Q, U.  Optionally plots.
    fd index number is in units of rad/m2.
    fft index number is therefore in units of m2/rad, scaled by 2*pi/stdlen.
    version 2 tries to package pol with fd axis.  outputs fft with scale axis.
    """

    # to do:  plot only first half?  test whether complex fd produces asymmetric fft.

    fft = n.fft.fft(pol)

    # create fft reference at origin to have 0th fourier mode at index=stdlen/2
    fftref = n.fft.fft(fd_point2(height=1,center=0,verbose=0)[1])   # what is unit brightness?
    fft = fft * fftref
    if show:
        p.plot((2*n.pi/stdlen)*fd, n.abs(fft))
        p.show()

    return (2*n.pi/stdlen*fd, fft)

def redshift_fft(fft, z):
    """Takes fft (Q-U vs. lambda^2) and redshifts to z.
    """

    lambda_obs = lambda_rest * (1 + z)

    return lambda_obs

def sample_band(fft, center, width, show=0):
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

def sample_band_average_two(fft, center, width, separation, show=0):
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

def sample_2pt(fft, ch1, ch2, show=0):
    """Samples two channels of fft at original resolution.  Optionally plots"""
    pass

def plot_fft(fft):
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
    p.xlabel('lambda^2 (m^2)')
    p.ylabel('Stokes Q,U (Jy)')
    logx = p.subplot(313)
    logx.set_xscale('log')
    p.plot(0.3/n.sqrt(good*(2*n.pi/stdlen)), fft[good].real, 'b.')
    p.plot(0.3/n.sqrt(good*(2*n.pi/stdlen)), fft[good].imag, 'r*')
    p.xlabel('Freq (GHz)')
    p.ylabel('Stokes Q,U (Jy)')
    p.show()

def fit_angle(fft, show=0, verbose=0):
    """Fit line to angle of fft real-imag (i.e., Q-U).
    Guesses based on initial fit to two channels.
    Note:  defined slope of angle vs. index to be -1*stdlen of input FD.
    """

    # define good channels to avoid zeros
    good = n.where(fft != 0)[0]

    line = lambda a,b,x: (a + x*b/(stdlen/2.)) % 2*n.pi - n.pi
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

def calc_rmbeam(center, width, show=0):
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

def calc_ifft(fft, fd=[0], beam=[0]):
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

def simulate_rrmrms(trials = 1000, s_center = 11, s_width = 10, s_sep = 10):
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


def simulate_redshift():
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
