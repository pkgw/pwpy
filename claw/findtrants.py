#
# script to take "standard" uvfit output and find significant detections
# major steps:
# 1) plot s/n distribution
# 2) set reasonable det threshold
# 3) plot positions of candidates
# ... profit?

import pylab,numpy,asciidata

# user params
nbins=20  # for histograms
gaussian = lambda amp,x,x0: amp * numpy.exp(-0.5*(x-x0)**2)  # gaussian SNR distribution for comparison
tint = 0.1 # integration time in seconds
period = 0.7137 # assumed pulsar period for finding on and off bins

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

def snrhist(data, show=1):
    """Plot the histogram of SNR for each fit.
    Requires stanadard data format.  Optionally can skip plotting histogram for show!=1.
    Returns histogram bins and centers.
    """

    hist = numpy.histogram(data[1]/data[2],nbins)
    binends = numpy.append(hist[1],max(data[1]/data[2]))
    bincenters = [numpy.median([binends[i+1],binends[i]]) for i in range(len(binends)-1)]  # define bin centers

    if show == 1:
        gau = gaussian(max(hist[0]),numpy.array(bincenters),bincenters[numpy.where(max(hist[0]) == hist[0])[0][0]])
        pylab.errorbar(bincenters,hist[0],numpy.sqrt(hist[0]),label='data')
        pylab.plot(bincenters,gau,label='Gaussian')
        pylab.legend()
        pylab.xlabel('SNR')
        pylab.ylabel('Number per bin')
        pylab.show()

    return hist[0],bincenters

def nominalsigma(frac):
    """Function to return the nominal sigma value based on a fractional rate.  Assumes Gaussian statistics.
    """
    sigar = numpy.arange(0,100,0.1)  # range of sigma values to consider

    print '\t\t\tNominal sigma should be tested more...'
    return sigar[numpy.where(frac >= (gaussian(1.,sigar,0.)))[0][0]]

def snronoff(data, show=1):
    """Plots the SNR histograms for on and off bins.
    Note:  Currently assumes 2-bin background for uvfit.
    """

    # set bin numbers.  numbers are cast as ints, so expect occasional slips
    bins = (data[0]%(0.7137/0.1)).astype(int)
    binon = numpy.where((bins == 3) | (bins == 4))[0]
    binoff = numpy.where((bins == 0) | (bins == 1) | (bins == 2) | (bins == 5) | (bins == 6))[0]

    histon = snrhist(data[:,binon], show=0)
    histoff = snrhist(data[:,binoff], show=0)
    
    print 'Off pulse gives noise distribution...'
    print '\t%.4f chance (nominal %.1f sigma) of event higher than %.1f sigma' % (1./len(binoff), nominalsigma(1./len(binoff)), max(data[1,binoff]/data[2,binoff]))
    print '\t%.4f chance (nominal %.1f sigma) of event higher than %.1f sigma' % (float(histoff[0][-1])/len(binoff), nominalsigma(float(histoff[0][-1])/len(binoff)), numpy.mean([histoff[1][-2],histoff[1][-1]]))
    print '\t%.4f chance (nominal %.1f sigma) of event higher than %.1f sigma' % (float(histoff[0][-2])/len(binoff), nominalsigma(float(histoff[0][-2])/len(binoff)), numpy.mean([histoff[1][-3],histoff[1][-2]]))

    if show == 1:
        gau = gaussian(max(histoff[0]),numpy.array(histoff[1]),histoff[1][numpy.where(max(histoff[0]) == histoff[0])[0][0]])
        pylab.errorbar(histoff[1],histoff[0],numpy.sqrt(histoff[0]),label='Off')
        pylab.errorbar(histon[1],histon[0],numpy.sqrt(histon[0]),label='On')
        pylab.plot(histoff[1],gau,label='Gaussian')
        pylab.legend()
        pylab.xlabel('SNR')
        pylab.ylabel('Number per bin')
        pylab.show()

    return histon, histoff

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

