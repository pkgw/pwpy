#
# script to take "standard" uvfit output and find significant detections
# major steps:
# 1) plot s/n distribution
# 2) set reasonable det threshold
# 3) plot positions of candidates
# ... profit?

import pylab,numpy,asciidata

def getdata(fileroot):
    """Read in three files output by uvfitpulse.sh.  Assumes naming convention.
    The data is read into a data structure with:
    col1 integration number
    col2,3 flux and its error
    col4,5 x pos and its error
    col6,7 y pos and its error.

    To do:  extend to multifreq.
    """

    print 'Loading ascii text files with root: %s' % (fileroot)
    # load fluxes..
    f = asciidata.AsciiData(fileroot+'-flux.txt')
    dataf1 = list(f.columns[1])
    dataf3 = list(f.columns[3])
    findex = numpy.array(f.columns[0])
    # load x and y...
    f = asciidata.AsciiData(fileroot+'-x.txt')
    datax1 = list(f.columns[1])
    datax3 = list(f.columns[3])
    if (findex-numpy.array(f.columns[0])).any() == True:
        print 'Indexes of $s different from flux file.' % (file)
        print 'I\'m outta here...'
        exit(1)
    f = asciidata.AsciiData(fileroot+'-y.txt')
    datay1 = list(f.columns[1])
    datay3 = list(f.columns[3])
    if (findex-numpy.array(f.columns[0])).any() == True:
        print 'Indexes of $s different from flux file.' % (file)
        print 'I\'m outta here...'
        exit(1)

    data = numpy.array([findex,dataf1,dataf3,datax1,datax3,datay1,datay3])

    return numpy.array(data)

def snrhist(data):
    """Plot the histogram of SNR for each fit."""

    # useful stuff
    nbins=20
    gaussian = lambda amp,x,x0: amp * numpy.exp(-0.5*(x-x0)**2)  # gaussian SNR distribution for comparison

    hist = numpy.histogram(data[1]/data[2],nbins)
    binends = numpy.append(hist[1],max(data[1]/data[2]))
    bincenters = [numpy.median([binends[i+1],binends[i]]) for i in range(len(binends)-1)]

    print numpy.where(max(hist[0]) == hist[0])[0][0]
    gau = gaussian(max(hist[0]),numpy.array(bincenters),bincenters[numpy.where(max(hist[0]) == hist[0])[0][0]])
    pylab.errorbar(bincenters,hist[0],numpy.sqrt(hist[0]),label='data')
    pylab.plot(bincenters,gau,label='Gaussian')
    pylab.legend()
    pylab.xlabel('SNR')
    pylab.ylabel('Number per bin')
    pylab.show()

def positions(data,threshold1,threshold2=-99):
    """Plot the positions for all fits with SNR greater than threshold."""

    if threshold2 == -99:
        threshold2 = max(data[1]/data[2])

    good = numpy.where((data[1]/data[2] >= threshold1) & (data[1]/data[2] <= threshold2))
    x = data[3][good]
    xerr = data[4][good]
    y = data[5][good]
    yerr = data[6][good]

    pylab.figure(1)
    pylab.errorbar(x,y,xerr=xerr,yerr=yerr,fmt='.')
    pylab.xlabel('Fit x position (arcsec)')
    pylab.xlabel('Fit y position (arcsec)')

    pylab.show()

