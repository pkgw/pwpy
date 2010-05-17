"""
claw, 7aug09

Script to take uvfit results from uvfitpulse.sh and find significant detections.
Major steps:
1) plot s/n distribution
2) set reasonable det threshold
3) plot positions of candidates
... profit?
"""

import pylab,numpy,asciidata

# user params
nbins=20  # for histograms
tint = 0.1 # integration time in seconds
period = 0.7137 # assumed pulsar period for finding on and off bins
shift=0.  # hack to fit shift in off distribution
precision = 0.01

# useful functions
gaussian = lambda amp,x,x0,sigma: amp/(sigma*numpy.sqrt(2*numpy.pi)) * numpy.exp(-0.5*((x-x0)/sigma)**2)  # normalized gaussian SNR distribution for comparison.
fitfunc = lambda p, x, binsize:  gaussian(p[0]*binsize, x, p[1], p[2])
errfunc = lambda p, x, binsize, y: fitfunc(p, x, binsize) - y
sigar = numpy.arange(-10, 10, precision)  # range of sigma values to consider

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

def snrhist(data, normed=False, show=True):
    """Plot the histogram of SNR for each fit.
    Requires stanadard data format.  Optionally can skip plotting histogram for show!=1.
    Returns histogram bins and centers.
    """

    hist = numpy.histogram(data[1]/data[2], nbins, normed=normed, new=True)
    print hist
    bincenters = [numpy.median([hist[1][i+1],hist[1][i]]) for i in range(len(hist[1])-1)]  # define bin centers
    binsize=(max(hist[1])-min(hist[1]))/nbins

    if show == 1:
        pylab.errorbar(bincenters,hist[0],numpy.sqrt(hist[0]),label='data')
        pylab.xlabel('SNR')
        pylab.ylabel('Number per bin')
        pylab.show()

    return hist[0],bincenters

def effectivesigma(p1, frac, show=True):
    """Converts a normalized rate into effective sigma limit of given Gaussian.
    Return value represents the effective sigma lower limit for the rate, not observed limit.
    Expects parameter tuple from fithist and a normalized (max=1) rate.
    Assumes Gaussian statistics.
    """

    fitsum, fitcenter, fitwidth = p1
    gau = gaussian(precision, sigar, fitcenter, fitwidth)  # amp normalized by bin size so integral (sum) is equal to 1
    
    if len(numpy.where(frac >= gau.cumsum())[0]) >= 1:
        effective_sigma = (-1)*(sigar[numpy.where(frac >= gau.cumsum())[0][-1]])/fitwidth  # need -1, since cumsum sums from bottom...
    else:
        effective_sigma = 10./fitwidth
        print 'Event rate is rarer than %.1f sigma!' % (effective_sigma)

    return effective_sigma

def fithist(hist, show=True):
    """Fit a gaussian to a histogram, keeping the integral of the histogram equal to its sum.
    Returns best fit center and width.
    """

    import scipy.optimize

    fitindex = (range(nbins/3,2*nbins/3))  # range to fit
#    fitindex = [0,1,2,3,16,17,18,19]
    binsize = (max(hist[1])-min(hist[1]))/(nbins-1)  # these are bin centers.  must add 1 to get full range of values.

    p0 = [sum(hist[0]), hist[1][numpy.where(max(hist[0]) == hist[0])[0][0]], 1.]  # initial guess of params
    p1, success = scipy.optimize.leastsq(errfunc, p0[:], args = (numpy.array(hist[1])[fitindex], binsize, numpy.array(hist[0])[fitindex]))

    if success and show == 1:
        print 'Fit successful!  Results:'
        print 'Integral of Histogram: %d.  Histogram center: %.1f.  Histogram width:  %.1f' % (p1[0],p1[1],p1[2])
        pylab.plot(hist[1],fitfunc(p1, numpy.array(hist[1]), binsize), label='Fit')
        pylab.errorbar(hist[1], hist[0], numpy.sqrt(hist[0]), label='Hist')
        pylab.legend()
        pylab.show()
        
    return p1

def nominalfrac(p1, sigma, show=True):
    """Converts observed sigma limit into fractional rate of given Gaussian.
    Expects parameter tuple from fithist and a sigma level.
    Returns normalized (integral=1) rate higher than given sigma level.
    """

    fitsum, fitcenter, fitwidth = p1
    gau = gaussian(precision, sigar, fitcenter, fitwidth) # define best fit gaussian
    nominal_frac = ((gau[numpy.where(sigma <= sigar)]).cumsum())[-1]  # sum up event rates for sigma threshold

    return nominal_frac

def snronoff(data, show=True):
    """Plots the observed SNR histograms for on and off bins.
    Fits Gaussian to off hist.
    Returns on and off histograms.
    Note:  Currently assumes 2-bin background for uvfit.  Some on subtraction likely for pulsars.
    """

    # set bin numbers.  numbers are cast as ints, so expect occasional slips
    bins = (data[0]%(0.7137/0.1)).astype(int)
    binon = numpy.where((bins == 3) | (bins == 4))[0]
    binoff = numpy.where((bins == 0) | (bins == 1) | (bins == 2) | (bins == 5) | (bins == 6))[0]

    histon = snrhist(data[:,binon], show=True)
    histoff = snrhist(data[:,binoff], show=True)

    binsize = (max(histoff[1])-min(histoff[1]))/(nbins-1)  # these are bin centers.  must add 1 to get full range of values.
    p1 = fithist(histoff, show=show)  # get fit results for hist
    
    print 'Off pulse gives noise distribution...'
    print '\t%.4f chance (effective %.1f sigma) of event higher than %.1f sigma' % (float(histoff[0][-1])/len(binoff), effectivesigma(p1, float(histoff[0][-1])/len(binoff)), numpy.mean([histoff[1][-2],histoff[1][-1]]))
    print '\t%.4f chance (effective %.1f sigma) of event higher than %.1f sigma' % (float(sum(histoff[0][[len(histoff[0])-2,len(histoff[0])-1]]))/len(binoff), effectivesigma(p1, float(sum(histoff[0][[len(histoff[0])-2,len(histoff[0])-1]]))/len(binoff)), numpy.mean([histoff[1][-3],histoff[1][-2]]))

    print 'On distribution from fit of off...'
    print '\t%.4f chance of events higher than %.1f sigma (%.6f expected off)' % (float(sum(histon[0][numpy.where(histon[1] >= histoff[1][-1])]))/len(binon),  numpy.mean([histoff[1][-2],histoff[1][-1]]), nominalfrac(p1, numpy.mean([histoff[1][-2],histoff[1][-1]]), show=True))

    if show == 1:
        fitsum, fitcenter, fitwidth = p1
        gau = gaussian(fitsum*binsize, numpy.arange(-10, 10, binsize), fitcenter, fitwidth)
        pylab.plot(numpy.arange(-10, 10, binsize), gau, label='Gaussian')  # plot fit hist over large range of sigma
        pylab.errorbar(histoff[1], histoff[0], numpy.sqrt(histoff[0]), label='Off')
        pylab.errorbar(histon[1], histon[0], numpy.sqrt(histon[0]), label='On')
        pylab.legend()
        pylab.xlabel('SNR')
        pylab.ylabel('Number per bin')
        pylab.show()

    return histon, histoff

def positions(data,threshold1,threshold2=-99):
    """Plot the positions for all fits with observed SNR greater than threshold."""

    if threshold2 == -99:
        threshold2 = max(data[1]/data[2])

    good = numpy.where((data[1]/data[2] >= threshold1) & (data[1]/data[2] <= threshold2))
    x = data[3][good]
    xerr = data[4][good]
    y = data[5][good]
    yerr = data[6][good]

    print 'Good integrations:'
    print data[0][good]

    pylab.figure(1)
    pylab.errorbar(x,y,xerr=xerr,yerr=yerr,fmt='.')
    pylab.xlabel('Fit x position (arcsec)')
    pylab.xlabel('Fit y position (arcsec)')
    pylab.show()

def truehist(hist, p1):
    """Function to make histogram of not observed SNR, but according to best fit histogram of off bins.
    Takes gaussian fit parameters for off, then scales and plots input hist bins.
    """

    print 'This needs to be checked...  "Effective sigma" only meaningful where Gaussian model is valid (SNR > 3)?'
    newhistbins = numpy.array(hist[1])/p1[2]
    
    pylab.errorbar(hist[1], hist[0], numpy.sqrt(hist[0]), label='Orig')
    pylab.errorbar(newhistbins, hist[0], numpy.sqrt(hist[0]), label='New')
    pylab.legend()
    pylab.show()

def comparehists(hist1,hist2,hist3=[0]):
    scale2 = 1.5
    pylab.errorbar(hist1[1], hist1[0], numpy.sqrt(hist1[0]), label='1')
    pylab.errorbar(hist2[1], scale2 * hist2[0], numpy.sqrt(hist2[0]), label='2')
    if len(hist3) > 1:
        pylab.errorbar(hist3[1], hist3[0], numpy.sqrt(hist3[0]), label='3')
    pylab.legend()
    pylab.show()
    
def onefalse(data, p1):
    """Finds the observed sigma threshold that returns 1 event for p1 distribution.
    Expects data and parameters of off Gaussian.
    Returns indices above sigma threshold.
    """

    for sigma in sigar[::-1]:
        if nominalfrac(p1, sigma, show=False) >= 1./data.shape[1]:
            break
    
    print 'One false event for threshold (observed) of %.2f' % (sigma)

    good = numpy.where((data[1]/data[2] >= sigma))

    return data[0][good]


def probhist(data, p1):
    """Plots histogram of observed SNR relative to expected normal distribution.
    Exceptional rates of events should stand out.
    """

    datahist, bincenters = snrhist(data, normed=True, show=False)

    fitsum, fitcenter, fitwidth = p1
    normgau = gaussian(1., bincenters, fitcenter, fitwidth)  # amp normalized by bin size so integral (sum) is equal to 1

    pylab.errorbar(bincenters, datahist, numpy.sqrt(datahist * fitsum)/fitsum, label='Data')
    pylab.plot(bincenters, normgau, label='Gaussian')
    pylab.errorbar(bincenters, datahist/normgau, numpy.sqrt(datahist * fitsum)/fitsum/normgau, label='Ratio')
    pylab.axis([-8,8,-2,10])
    pylab.xlabel('Observed SNR')
    pylab.ylabel('Ratio of observed events to Gaussian expectation')
    pylab.legend()
    pylab.show()
