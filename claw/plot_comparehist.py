# claw, 4aug09
#
# quick and dirty script to plot and compare histograms from uvfit output

import pylab,numpy,asciidata

# prefs
#files = ['j0332-420p1o23-uvfit.txt','j0332-420p2o23-uvfit.txt','j0332-420p3o23-uvfit.txt','j0332-420p4o23-uvfit.txt','j0332-420p5o23-uvfit.txt','j0332-420p6o23-uvfit.txt']
files = ['j0332-0.1s-tst.txt','j0332-0.1s-tst-2bg.txt']
nbins = 15

# load files
f1 = asciidata.AsciiData(files[0])
f2 = asciidata.AsciiData(files[1])
"""
f3 = asciidata.AsciiData(files[2])
f4 = asciidata.AsciiData(files[3])
f5 = asciidata.AsciiData(files[4])
f6 = asciidata.AsciiData(files[5])
"""

# populate arrays
f1f = numpy.array(f1.columns[1])
f1e = numpy.array(f1.columns[3])
f2f = numpy.array(f2.columns[1])
f2e = numpy.array(f2.columns[3])
"""
f3f = numpy.array(f3.columns[1])
f3e = numpy.array(f3.columns[3])
f4f = numpy.array(f4.columns[1])
f4e = numpy.array(f4.columns[3])
f5f = numpy.array(f5.columns[1])
f5e = numpy.array(f5.columns[3])
f6f = numpy.array(f6.columns[1])
f6e = numpy.array(f6.columns[3])
"""

# define bins
bin0 = (numpy.arange(5,2994,0.7137/0.1)).astype(int)
bin1 = (numpy.arange(6,2994,0.7137/0.1)).astype(int)
bin2 = (numpy.arange(0,2994,0.7137/0.1)).astype(int)
bin3 = (numpy.arange(1,2994,0.7137/0.1)).astype(int)
bin4 = (numpy.arange(2,2994,0.7137/0.1)).astype(int)
bin5 = (numpy.arange(3,2994,0.7137/0.1)).astype(int)
bin6 = (numpy.arange(4,2994,0.7137/0.1)).astype(int)

# hist
hist01 = numpy.histogram(f1f[bin0]/f1e[bin0],nbins)
hist11 = numpy.histogram(f1f[bin1]/f1e[bin1],nbins)
hist21 = numpy.histogram(f1f[bin2]/f1e[bin2],nbins)
hist31 = numpy.histogram(f1f[bin3]/f1e[bin3],nbins)
hist41 = numpy.histogram(f1f[bin4]/f1e[bin4],nbins)
hist51 = numpy.histogram(f1f[bin5]/f1e[bin5],nbins)
hist61 = numpy.histogram(f1f[bin6]/f1e[bin6],nbins)
hist0 = numpy.histogram(f2f[bin0]/f2e[bin0],nbins)
hist1 = numpy.histogram(f2f[bin1]/f2e[bin1],nbins)
hist2 = numpy.histogram(f2f[bin2]/f2e[bin2],nbins)
hist3 = numpy.histogram(f2f[bin3]/f2e[bin3],nbins)
hist4 = numpy.histogram(f2f[bin4]/f2e[bin4],nbins)
hist5 = numpy.histogram(f2f[bin5]/f2e[bin5],nbins)
hist6 = numpy.histogram(f2f[bin6]/f2e[bin6],nbins)
"""
snroff = numpy.concatenate((f1f/f1e,f4f/f4e,f5f/f5e,f6f/f6e))
histoff = numpy.histogram(snroff,nbins)
"""

# plot
gaussian = lambda amp,x,x0: amp * numpy.exp(-0.5*(x-x0)**2)  # gaussian SNR distribution for comparison
gau = gaussian(max(hist0[0]),numpy.array(hist0[1]),hist0[1][numpy.where(max(hist0[0]) == hist0[0])])

#loff = pylab.errorbar(histoff[1],histoff[0],yerr=numpy.sqrt(histoff[0]),label='Off pulse')
pylab.figure(1)
pylab.errorbar(hist01[1],hist01[0],yerr=numpy.sqrt(hist01[0]),label='0')
pylab.errorbar(hist11[1],hist11[0],yerr=numpy.sqrt(hist11[0]),label='1')
pylab.errorbar(hist21[1],hist21[0],yerr=numpy.sqrt(hist21[0]),label='2')
pylab.errorbar(hist31[1],hist31[0],yerr=numpy.sqrt(hist31[0]),label='3')
pylab.errorbar(hist41[1],hist41[0],yerr=numpy.sqrt(hist41[0]),label='4')
pylab.errorbar(hist51[1],hist51[0],yerr=numpy.sqrt(hist51[0]),label='5')
pylab.errorbar(hist61[1],hist61[0],yerr=numpy.sqrt(hist61[0]),label='6')
lgau = pylab.plot(hist0[1],gau,'g',label='Gaussian')
pylab.xlabel('SNR')
pylab.ylabel('Number per SNR bin per pulse bin')
pylab.legend()

pylab.figure(2)
pylab.errorbar(hist0[1],hist0[0],yerr=numpy.sqrt(hist0[0]),label='0')
pylab.errorbar(hist1[1],hist1[0],yerr=numpy.sqrt(hist1[0]),label='1')
pylab.errorbar(hist2[1],hist2[0],yerr=numpy.sqrt(hist2[0]),label='2')
pylab.errorbar(hist3[1],hist3[0],yerr=numpy.sqrt(hist3[0]),label='3')
pylab.errorbar(hist4[1],hist4[0],yerr=numpy.sqrt(hist4[0]),label='4')
pylab.errorbar(hist5[1],hist5[0],yerr=numpy.sqrt(hist5[0]),label='5')
pylab.errorbar(hist6[1],hist6[0],yerr=numpy.sqrt(hist6[0]),label='6')
lgau = pylab.plot(hist0[1],gau,'g',label='Gaussian')
pylab.xlabel('SNR')
pylab.ylabel('Number per SNR bin per pulse bin')
pylab.legend()

pylab.show()

