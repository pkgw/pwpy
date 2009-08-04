# claw, 4aug09
#
# quick and dirty script to plot histograms from flux files

import pylab,numpy,asciidata

# prefs
files = ['j0332-420p1o23-uvfit.txt','j0332-420p2o23-uvfit.txt','j0332-420p3o23-uvfit.txt','j0332-420p4o23-uvfit.txt','j0332-420p5o23-uvfit.txt','j0332-420p6o23-uvfit.txt']
nbins = 25

# load files
f1 = asciidata.AsciiData(files[0])
f2 = asciidata.AsciiData(files[1])
f3 = asciidata.AsciiData(files[2])
f4 = asciidata.AsciiData(files[3])
f5 = asciidata.AsciiData(files[4])
f6 = asciidata.AsciiData(files[5])

# populate arrays
f1f = numpy.array(f1.columns[1])
f1e = numpy.array(f1.columns[3])
f2f = numpy.array(f2.columns[1])
f2e = numpy.array(f2.columns[3])
f3f = numpy.array(f3.columns[1])
f3e = numpy.array(f3.columns[3])
f4f = numpy.array(f4.columns[1])
f4e = numpy.array(f4.columns[3])
f5f = numpy.array(f5.columns[1])
f5e = numpy.array(f5.columns[3])
f6f = numpy.array(f6.columns[1])
f6e = numpy.array(f6.columns[3])

# hist
hist = numpy.histogram(f3f/f3e,nbins)
snroff = numpy.concatenate((f1f/f1e,f4f/f4e,f5f/f5e,f6f/f6e))
histoff = numpy.histogram(snroff,nbins)

# plot
loff = pylab.errorbar(histoff[1],histoff[0]/4,yerr=numpy.sqrt(histoff[0])/4,fmt='b',label='Off pulse')
lon = pylab.errorbar(hist[1],hist[0],yerr=numpy.sqrt(hist[0]),fmt='r',label='On pulse')

gaussian = lambda amp,x,x0: amp * numpy.exp(-0.5*(x-x0)**2)  # gaussian SNR distribution for comparison
gau = gaussian(max(histoff[0])/4,numpy.array(histoff[1]),histoff[1][numpy.where(max(histoff[0]) == histoff[0])])
lgau = pylab.plot(histoff[1],gau,'g',label='Gaussian')

pylab.xlabel('SNR')
pylab.ylabel('Number per SNR bin per pulse bin')
pylab.legend()
pylab.show()

