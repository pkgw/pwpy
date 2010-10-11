#!/usr/bin/env python
# plot lightcurve from fast imaging uv fit text files
import sys, asciidata
import numpy as n
import pylab as p
import scipy as s
import scipy.optimize as opt

# params
nbins = 100
tint = 0.1   # integration time in seconds

# read data
if len(sys.argv) < 2:
    print 'Need text file with fluxes, dude.'
    exit(1)

filename = sys.argv[1]
file = asciidata.AsciiData(filename)
it = n.array(file.columns[0])
f = n.array(file.columns[1])
ef = n.array(file.columns[3])

# statistics
gaussian = lambda amp,x,x0,sigma: amp/(sigma*n.sqrt(2*n.pi)) * n.exp(-0.5*((x-x0)/sigma)**2)  # normalized gaussian SNR distribution for comparison.
fitfunc = lambda p, x:  gaussian(p[0], x, p[1], p[2])
errfunc = lambda p, x, y: fitfunc(p, x) - y
fitindex = (range(nbins/3,2*nbins/3))  # range to fit
std3 = 3*f.std()
mean = f.mean()

# plot lightcurve
p.figure(1)
p.subplot(2,2,1)
p.errorbar(it,f,yerr=ef)
p.plot(it, (mean+std3)*n.ones(len(it)), 'r--')
p.plot(it, (mean-std3)*n.ones(len(it)), 'r--')
p.xlabel('Iteration')
p.ylabel('Flux')
p.title('Lightcurve')

# plot histogram and gaussian
#p.figure(2)
p.subplot(2,2,2)
(hist,edges) = n.histogram(f,bins=nbins)
centers = [(edges[i+1] + edges[i])/2 for i in range(len(edges)-1)]
widths = [(edges[i+1] - edges[i]) for i in range(len(edges)-1)]

p0 = [sum(hist), centers[n.where(max(hist) == hist)[0]], 1.]  # initial guess of params
p1, success = opt.leastsq(errfunc, p0[:], args = (n.array(centers)[fitindex], n.array(hist)[fitindex]))

print 'Fit successful!  Results:'
print 'Integral of Histogram: %d.  Histogram center: %.1f.  Histogram width:  %.1f' % (p1[0],p1[1],p1[2])
p.bar(edges[:-1], hist, yerr=n.sqrt(hist), width=widths, label='Hist')
p.plot(centers,fitfunc(p1, n.array(centers)), 'r--', label='Fit')
p.xlabel('Flux (Jy)')
p.ylabel('Number of Measurements')
p.legend()
p.title('Flux Histograms')

# plot fft
#p.figure(3)
p.subplot(2,2,3)
ft = s.fft(f)/(n.sqrt(len(f)) * f.std())
freq = n.arange(len(ft)/2)/(tint*len(f))
p.plot(freq, n.abs(ft[0:len(ft)/2]), ',')
p.xlabel('Frequency (Hz)')
p.ylabel('Amplitude')
p.title('FFT')

#plot fft with tone
#p.figure(4)
p.subplot(2,2,4)
amp = 0.2
tonefreq = 1000.
tone = amp*n.sin(2*n.pi*tonefreq*n.arange(len(f))/len(f))
f2 = f + tone
ft2 = s.fft(f2)/(n.sqrt(len(f2)) * f2.std())
p.plot(freq, n.abs(ft2[0:len(ft)/2]), ',')
p.xlabel('Frequency (1/s)')
p.ylabel('Amplitude')
p.title('FFT with %.1f Jy tone' % (amp))

p.show()
