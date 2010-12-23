#!/usr/bin/env python
"""Script to simulate RM synthesis.
First, create arbitrary complex polarization plots for given Faraday dispersion function.
Ultimately, simlate range of Faraday dispersion functions over range of z.
"""

import numpy as n
import pylab as p
import scipy.optimize as opt

# params
stdlen = 1000

def fd_tophat(width,height=1.,center=0,show=0):
    """Returns a tophat Faraday disperison function"""

    fd = n.zeros(stdlen, dtype='double')
    fd[stdlen/2 - width: stdlen/2 + width] = height

    if show:
        p.plot(fd)
        p.show()

    return fd

def fd_gaussian(width, height=1., center=0, show=0):
    """Returns a Gaussian Faraday disperison function"""
    fd = n.zeros(stdlen, dtype='double')
    for i in range(stdlen):
        fd[i] = height*n.exp(-1.*((i-stdlen/2)/float(width))**2)

    if show:
        p.plot(fd)
        p.show()

    return fd

def fd_point(height=1., center=0, show=0):
    """Returns a point-like Faraday disperison function"""
    fd = n.zeros(stdlen, dtype='double')
    fd[center] = height

    if show:
        p.plot(fd)
        p.show()

    return fd

def calc_fft(fd, show=0):
    """Returns the fft of an fd.  Optionally plots"""

    fft = n.fft.fft(fd)

    if show:
        p.plot(n.abs(fft[:len(fft)/2]))
        p.show()

    return fft

def sample_fft(fft, center, width, show=0):
    """Samples a set of channels of fft.  Optionally plots"""

    fft2 = fft.copy()
    fft2[0:center-width/2] = 0.
    fft2[center+width/2:stdlen-(center+width/2)] = 0.
    fft2[stdlen-(center-width/2):] = 0.

    if show:
        p.figure(1)
        p.plot(n.abs(fft[0:len(fft)/2]))
        p.plot(n.abs(fft2[0:len(fft2)/2]))
        p.show()

    return fft2

def plot_fft(fft):
    """Plots the real and imaginary parts of the fft (i.e., Stokes Q and U)"""

    p.plot(fft.real,fft.imag,',')
    p.show()

def fit_angle(fft,show=0):
    """Fit line to angle of fft real-imag (i.e., Q-U)"""

    line = lambda a,b,x: a + x*b
    fitfunc = lambda p, x:  line(p[0], p[1], x)
    errfunc = lambda p, x, y: fitfunc(p, x)**2 - y**2
    p0 = [0.,0.]
    p1, success = opt.leastsq(errfunc, p0[:], args = (n.arange(len(fft)), n.angle(fft)))
    print 'Fit results:', p1

    if show:
        p.plot(fitfunc(p1, n.arange(len(fft))), '--')
        p.plot(n.angle(fft))

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
