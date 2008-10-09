# Routines for doing basic fits with numpy

import numpy as _N

# Histogram binning suggestions
#
# Sturges' formula: N_bins = ceil(log_2(N_pts) + 1) (want n >~ 30)
# Sturges, H.A., 1926, "The choice of a class interval", J Am Stat Assn, 65-66
#
# Scott: bin_width = 3.5 sigma / n^(1/3)
# Scott, D.W., 1979, "On optimal and data-based histograms", Biometrika 66(3) 605-610
# doi:10.1093/biomet/66.3.605
#
# Freedman-Diaconis: bin_width = 2 * IQR(data) / n^(1/3)
# Here IQR is the interquartile range, IQR = 75th percentile - 25th percentile.
# Freedman, D & Diaconis, P, 1981, "On the histogram as a density estimator: 
# L_2 theory", Zeitschrift fur Wahrscheinlichkeitstheorie und verwandte Gebiete
# 57 (4) 453-476 doi:10.1007/BF01025868

def autohist (data, choice='scott', std=None, range=None, **kwargs):
    """Histogram with automatically-chosen bin sizes.

choice: one of 'scott', 'sturges', or 'f-d' (for Freedman-Diaconis)
"""

    if range is None: range = (data.min (), data.max ())

    if choice == 'scott':
        if std is None: std = data.std ()
        wbin = 3.5 * std / data.size**0.33333
        wdata = range[1] - range[0]
        n = int (_N.ceil (wdata / wbin))
        delta = (n * wbin - wdata) / 2
        range = (range[0] - delta, range[1] + delta)
    elif choice == 'sturges':
        n = int (_N.ceil (_N.log2 (data.size) + 1))
    elif choice == 'f-d':
        from scipy.stats import scoreatpercentile as sap

        iqr = sap (data, 75) - sap (data, 25)
        wbin = 2 * iqr / data.size**0.33333
        wdata = range[1] - range[0]
        n = int (_N.ceil (wdata / wbin))
        delta = (n * wbin - wdata) / 2
        range = (range[0] - delta, range[1] + delta)
    elif choice == 'custom':
        pass
    else:
        raise Exception ('Unknown histogram binning choice %s' % choice)

    return _N.histogram (data, n, range, **kwargs)

# Some cheesy fits

def linearConstrained (x, y, x0, y0, weights = None):
    """Perform a linear fit through the points given in x, y that is
    constrained to pass through x0, y0. Thus the only free parameter
    is the slope of the fit line, A, which is the return
    value. 'weights', if specified, gives a weight that is assigned to
    each point; otherwise, each point is weighted equally. (Suggested:
    1 / err). Thus x, y, and weights should all have the same length.

    Returns: A, the slope of the best fit. So 'A * (x - x0) + y0'
    yields the best-fit points.
    """

    x = _N.asarray (x)
    y = _N.asarray (y)

    if weights is None:
        weights = _N.ones (len (x))
    else:
        weights = _N.asarray (weights)

    A = (x - x0) * weights
    B = (y - y0) * weights

    # Upgrade precision in case all of our arrays were ints.
    # FIXME: is there a function to upgrade something to at least
    # a float? If all the inputs are float32's, we should also
    # return a float32.
    
    return _N.float64 (_N.dot (A, B)) / _N.dot (A, A)

# This is all copied from the Scipy Cookbook page on "Fitting Data"

def makeGauss2dFunc (A, xmid, ymid, xwidth, ywidth):
    return lambda x, y: A * _exp (-0.5 * (((xmid - x) / xwidth)**2 + \
                                          ((ymid - y) / ywidth)**2))

def guessGauss2dParams (data):
    from numpy import indices, sqrt, abs, arange, int

    total = data.sum ()
    X, Y = indices (data.shape)
    x = (X * data).sum () / total
    y = (Y * data).sum () / total

    col = data[:, int (y)]
    row = data[int (x), :]

    xwidth = sqrt (abs ((arange (col.size) - y)**2 * col).sum () / col.sum ())
    ywidth = sqrt (abs ((arange (row.size) - x)**2 * row).sum () / row.sum ())

    A = data.max ()

    return A, x, y, xwidth, ywidth

def gauss2d (data, guess=None, getResid=False, **kwargs):
    """guess and return value take the form: (height, xctr, yctr, xwidth, ywidth)."""
    
    from scipy import optimize

    if guess is None: guess = guessGauss2dParams (data)

    def err (params):
        model = makeGauss2dFunc (*params)(*_N.indices (data.shape))
        return _N.ravel (model - data)

    pfit, xx, xx, msg, success = optimize.leastsq (err, guess,
                                                   full_output=True, **kwargs)

    if success < 1 or success > 4:
        raise Exception ('Least square fit failed: ' + msg)

    if not getResid: return pfit

    model = makeGauss2dFunc (*pfit)(*_N.indices (data.shape))
    return pfit, data - model

# More organized fitting.

class FitBase (object):
    """A object holding information in a generic fitting operation.
    Fields are:

            x     - The data abscissa values.
            y     - The data ordinate values.
       sigmas     - The uncertainties in the ordinate values.
       params (*) - The best-fit parameters of the model describing the data.
      uncerts (*) - The uncertainties in those parameters.
        mfunc (*) - A function evaluating the best-fit model at arbitrary X values.
        mdata (*) - The best-fit model function evaluated at the given data X values.
       resids (*) - The residual values, mdata - y.
       rchisq (*) - The reduced chi squared of the fit.

    (An asterisk denotes values that are only available after fit() has been run.)
    
    Methods are:

             setData      - Set the X, Y, and (optionally) sigma input data.
           makeModel      - Create a function evaluating the model given a choice of
                            parameters.
      fakeDataSigmas      - Generate artificial data based on sample model parameters
                            and given uncertainties in measurements.
        fakeDataFrac      - Generate artificial data based on sample model parameters
                            and a given fractional error value.
          fakeSigmas (*)  - Set the sigma values to some fixed number.
               guess (*)  - Guess a set of initial parameters based on the data.
                 fit (*)  - Find the model parameters that best approximate the data.
         printParams (**) - Print out the model parameters and their uncertainties.
                plot (**) - Plot the data, the best-fit model, and the residuals.

    (One asterisk denotes that the function requires setData() to have been called,
    and two asterisks denote that the function requires fit () to have been called.)
    
    Subclassers must implement:

      _paramNames - A list of textual names corresponding to the model parameters.
            guess - The function to guess initial parameters, given the data.
        makeModel - The function to return a model evaluator function.
         _fitImpl - The function to actually perform the fit.
    
    """
    
    _paramNames = None

    def __init__ (self):
        if self._paramNames is None:
            raise Exception ('FitBase implementation %s needs to set _paramNames' \
                             % (self.__class__))
    
    def setData (self, x, y, sigmas=None):
        self.x = _N.asarray (x)
        self.y = _N.asarray (y)

        if sigmas is None:
            self.sigmas = None
        else:
            self.sigmas = _N.asarray (sigmas)

        return self

    def fakeSigmas (self, val):
        """Set the uncertainty of every data point to a fixed value."""
        self.sigmas = _N.zeros_like (self.x) + val
        return self

    def fakeDataSigmas (self, x, sigmas, *params):
        self.x = _N.asarray (x)
        self.sigmas = _N.asarray (sigmas)
        
        mfunc = self.makeModel (*params)
        self.y = mfunc (self.x) + _N.random.standard_normal (self.x.shape) * self.sigmas

        return self
        
    def fakeDataFrac (self, x, frac, *params):
        self.x = _N.asarray (x)
        
        mfunc = self.makeModel (*params)

        y = mfunc (self.x)
        self.sigmas = y * frac
        self.y = y + _N.random.standard_normal (self.x.shape) * self.sigmas

        return self
        
    def guess (self):
        """Return a tuple of parameter guesses based on the X and Y data."""
        raise NotImplementedError ()

    def makeModel (self, *params):
        """Return a function that maps X values into appropriate
        model values."""
        
        raise NotImplementedError ()

    def _fitImpl (self, x, y, sig, guess):
        """Obtain a fit in some way, and set at least the following
        fields:
        
          params - a tuple of best-fit parameters (compatible with the result of guess)
          uncerts - A tuple of uncertainties of the parameters.

        Can also set the following fields if their values are derived during
        the fit:

          mfunc - A function that evaluates the best-fit model at arbitrary X values
          mdata - mfunc evaluated at the given X values
          resids - The differences (y - mdata) 
          rchisq - The reduced chi squared of the fit

        You should also set any other fields that may be of use to someone
        examining the fit results.
        """
        
        raise NotImplementedError ()

    def fit (self, guess=None):
        guess = guess or self.guess ()

        self.params = None
        self.mfunc = None
        self.mdata = None
        self.resids = None
        self.rchisq = None

        if self.sigmas is None:
            raise ValueError ('Must assess uncertainties; try fakeSigmas')

        self._fitImpl (self.x, self.y, self.sigmas, guess)

        if self.params is None:
            raise RuntimeError ('Failed to find best-fit parameters')
        
        if self.uncerts is None:
            raise RuntimeError ('Failed to find uncertainties to fit parameters')

        if len (self.params) != len (self._paramNames):
            raise RuntimeError ('Should fit %d parameters; got %d' % (len (self._paramNames),
                                                                      len (self.params)))
        
        if len (self.params) != len (self.uncerts):
            raise RuntimeError ('Inconsistent params and uncerts fields')
        
        if self.mfunc is None:
            self.mfunc = self.makeModel (*self.params)

        if self.mdata is None:
            self.mdata = self.mfunc (self.x)

        if self.resids is None:
            self.resids = self.y - self.mdata

        if self.rchisq is None:
            self.rchisq = ((self.resids / self.sigmas)**2).sum () / \
                          (self.x.size - len (self.params))

        return self

    def assumeParams (self, *params):
        self.params = _N.asarray (params)
        self.uncerts = _N.zeros_like (self.params)
        self.mfunc = self.makeModel (*self.params)
        self.mdata = self.mfunc (self.x)
        self.resids = self.y - self.mdata
        self.rchisq = ((self.resids / self.sigmas)**2).sum () / \
                          (self.x.size - len (self.params))
        return self
    
    def printParams (self):
        lmax = len ('RChiSq')

        for pn in self._paramNames:
            if len (pn) > lmax: lmax = len (pn)
                
        for (pn, val, uncert) in zip (self._paramNames, self.params, self.uncerts):
            frac = abs (100. * uncert / val)
            print '%s: %14g +/- %14g (%.2f%%)' % (pn.rjust (lmax), val, uncert, frac)

        print '%s: %14g' % ('RChiSq'.rjust (lmax), self.rchisq)
        return self

    def plot (self, dlines=True, smoothModel=True):
        import omega

        if not smoothModel:
            modx = self.x
            mody = self.mdata
        else:
            modx = _N.linspace (self.x.min (), self.x.max (), 400)
            mody = self.mfunc (modx)

        vb = omega.layout.VBox (2)

        if self.sigmas is not None:
            vb.pData = omega.quickXYErr (self.x, self.y, self.sigmas, 'Data', lines=dlines)
        else:
            vb.pData = omega.quickXY (self.x, self.y, 'Data', lines=dlines)

        vb[0] = vb.pData
        vb[0].addXY (modx, mody, 'Model')
        vb[0].setYLabel ('Y')
        vb[0].nudgeBounds (False, True)
        
        vb[1] = vb.pResid = omega.RectPlot ()
        vb[1].defaultField.xaxis = vb[1].defaultField.xaxis
        if self.sigmas is not None:
            vb[1].addXYErr (self.x, self.resids, self.sigmas, 'Resid.', lines=False)
        else:
            vb[1].addXY (self.x, self.resids, 'Resid.', lines=False)
        vb[1].setLabels ('X', 'Residuals')
        vb[1].nudgeBounds (False, True)
        
        vb.setWeight (0, 3)
        return vb
    
class LinearFit (FitBase):
    _paramNames = ['a', 'b']
    
    def guess (self):
        return (0, 0)

    def makeModel (self, a, b):
        return lambda x: a + b * x

    def _fitImpl (self, x, y, sig, guess):
        # Ignore the guess since we can solve this exactly
        # Exact solution math copied out of Numerical Recipes in C
        # 2nd Ed. sec 15.2. (But no code copied)

        sm1 = sig ** -1
        sm2 = sm1 ** 2
        
        S = sm2.sum ()
        Sx = (x * sm2).sum ()
        Sy = (y * sm2).sum ()
        Sxx = (x**2 * sm2).sum ()
        Syy = (y**2 * sm2).sum ()
        Sxy = (x * y * sm2).sum ()

        D = S * Sxx - Sx**2

        t = (x - Sx / S) * sm1
        Stt = (t**2).sum ()
        
        self.b = (t * y * sm1).sum () / Stt
        self.a = (Sy - Sx * self.b) / S
        
        self.sigma_a = _N.sqrt ((1 + Sx**2 / S / Stt) / S)
        self.sigma_b = _N.sqrt (Stt ** -1)

        self.params = _N.asarray ((self.a, self.b))
        self.uncerts = _N.asarray ((self.sigma_a, self.sigma_b))

class LeastSquaresFit (FitBase):
    """A Fit object that implements its fit via a generic least-squares
    minimization algorithm. Extra fields are:

      cov (*) - The covariance matrix of the fitted parameters.

    Subclassers must implement:

      _paramNames - A list of textual names corresponding to the model parameters.
            guess - The function to guess initial parameters, given the data.
        makeModel - The function to return a model evaluator function.
       _fitExport - (Optional.) Set individual fields equivalent to the best-fit
                    parameters for ease of use.
    """
    
    _fitExport = None
    
    def _fitImpl (self, x, y, sig, guess, **kwargs):
        """Obtain a fit in some way, and set at least the following
        fields:
        
        params - a tuple of best-fit parameters (compatible with the result of guess)
        uncerts - A tuple of uncertainties of the parameters.
        """

        from scipy.optimize import leastsq
        
        w = sig ** -1
        
        def error (p):
            self.mfunc = f = self.makeModel (*p)
            return _N.ravel ((f (x) - y) * w)

        pfit, cov, xx, msg, success = leastsq (error, guess, full_output=True,
                                               **kwargs)

        if success < 1 or success > 4:
            raise Exception ('Least square fit failed: ' + msg)

        if cov is None:
            print 'No covariance matrix!'
            print 'Fit params:', pfit
            print 'Message:', msg
            print 'Success code:', success
            raise Exception ('No covariance matrix!')
        
        if len (guess) == 1:
            # Coerce into arrayness.
            self.params = _N.asarray ((pfit, ))
        else:
            self.params = pfit
            
        self.uncerts = _N.sqrt (cov.diagonal ())

        self.cov = cov

        if self._fitExport is not None:
            self._fitExport ()

class GaussianFit (LeastSquaresFit):
    _paramNames = ['height', 'xmid', 'width']
    
    def guess (self):
        height = self.y.max ()

        ytotal = self.y.sum ()
        byx = self.y * self.x
        xmid = byx.sum () / ytotal

        # Not at all sure if this is a good algorithm. Seems to
        # work OK.
        width = _N.sqrt (abs ((self.x - xmid)**2 * self.y).sum () / ytotal)

        return (height, xmid, width)

    def makeModel (self, height, xmid, width):
        return lambda x: height * _N.exp (-0.5 * ((x - xmid)/width)**2)

    def _fitExport (self):
        self.height, self.xmid, self.width = self.params
        self.sigma_h, self.sigma_x, self.sigma_w = self.uncerts

class PowerLawFit (LeastSquaresFit):
    _paramNames = ['q', 'alpha']
    
    def guess (self):
        l = _N.log
        
        dlx = l (self.x.max ()) - l (self.x.min ())
        dly = l (self.y.max ()) - l (self.y.min ())
        alpha = dly / dlx

        mlx = l (self.x).mean ()
        mly = l (self.y).mean ()
        q = _N.exp (- mly / alpha / mlx)

        return (q, alpha)

    def makeModel (self, q, alpha):
        return lambda x: q * x ** alpha

    def _fitExport (self):
        self.q, self.alpha = self.params
        self.sigma_q, self.sigma_a = self.uncerts

class BiPowerLawFit (LeastSquaresFit):
    _paramNames = ['xbr', 'ybr', 'alpha1', 'alpha2']
    
    def guess (self):
        l = _N.log
        
        dlx = l (self.x.max ()) - l (self.x.min ())
        dly = l (self.y.max ()) - l (self.y.min ())
        alpha = dly / dlx

        mx = self.x.mean ()
        my = self.y.mean ()
        
        return (mx, my, alpha, alpha)

    def makeModel (self, xbr, ybr, alpha1, alpha2):
        def f (x):
            a = (alpha2 - alpha1) * (x > xbr) + alpha1
            return ybr * (x / xbr) ** a

        return f

    def _fitExport (self):
        self.xbr, self.ybr, self.alpha1, self.alpha2 = self.params
        self.sigma_xbr, self.sigma_ybr, self.sigma_a1, self.sigma_a2 = self.uncerts

class LameQuadraticFit (LeastSquaresFit):
    """This is lame because it uses a least-squares fit when the
    problem can be solved analytically."""
    
    _paramNames = ['a', 'b', 'c']

    def guess (self):
        a = self.x.mean ()
        b = (self.y.max () - self.y.min ()) / (self.x.max () - self.x.min ())
        c = (self.y**2 - self.x * b - a).mean ()

        return (a, b, c)

    def makeModel (self, a, b, c):
        return _N.poly1d ([c, b, a])

    def _fitExport (self):
        self.a, self.b, self.c = self.params
        self.sigma_a, self.sigma_b, self.sigma_c = self.uncerts
        self.xExtremum = -self.b / 2 / self.c

# Todo: visibility amplitude and phase fitters
# cf. Thompson, Moran & Swenson 6.56a, 6.65b
# amplitude is Rice distribution reducing to Rayleigh distribution for |signal| = 0
# "the presence of a weak signal is more easily detected by examining the
# visibility phase than by examining the amplitude."
# cf. also TMS section 9.3, eqns 9.36 +
# if |signal|/sigma >> 1, sigma_phi ~= sigma / |signal|,
# where sigma is uncert in real and imag parts.
#
# if T_Sys / sqrt(2 BW tau) << T_a << T_sys,
#
# sigma_ph = T_Sys / (eta_quant T_a sqrt (2 BW tau))
#

# Temporary, more later ...
# This is sorta implemented by scipy.stats.distributions.rice.fit,
# but 1) a lot of that generic distribution code seems broken, and
# more importantly 2) that function lets location and width parameters
# float freely, while we know location = 0.

def ricefit (d):
    from scipy.optimize import fmin
    from numpy import log
    from scipy.special import i0

    def likelihood (params):
        v = params[0]
        s = params[1]
        return -(log (d/s**2 * i0 (d*v/s**2)) - (d**2 + v**2)/2/s**2).sum ()

    p = _N.array ((d.mean (), d.std ()))

    return fmin (likelihood, p)
