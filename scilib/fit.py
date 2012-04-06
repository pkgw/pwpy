# Copyright 2012 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

# Routines for doing basic fits with numpy

import numpy as np


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

    Subclassers may optionally implement:

       _fitExport - Set individual fields equivalent to the best-fit
                    parameters for ease of use.
    """

    _paramNames = None
    _fitExport = None

    def __init__ (self):
        self.x = self.y = self.sigmas = None

    def setData (self, x, y, sigmas=None):
        # Get the floating-point coercion of asfarray without doing a large
        # number of needless computations, and also making it so that if the
        # user provides a complex value don't crash. (By my reading of the docs
        # N.asfarray ([complex]) should succeed but it doesn't for numpy <= 1.3)
        x[0] += 0.0
        y[0] += 0.0
        self.x = np.asarray (x)
        self.y = np.asarray (y)

        if sigmas is None:
            self.sigmas = None
        else:
            self.sigmas = np.asfarray (sigmas)

        return self

    def fakeSigmas (self, val):
        """Set the uncertainty of every data point to a fixed value."""
        self.sigmas = np.zeros_like (self.y) + val
        return self

    def fakeDataSigmas (self, x, sigmas, *params):
        # See comment in setData
        x[0] += 0.0
        self.x = np.asarray (x)
        self.sigmas = np.asfarray (sigmas)

        mfunc = self.makeModel (*params)
        self.y = mfunc (self.x) + np.random.standard_normal (self.y.shape) * self.sigmas

        return self

    def fakeDataFrac (self, x, frac, *params):
        # See comment in setData
        x[0] += 0.0
        self.x = np.asarray (x)

        mfunc = self.makeModel (*params)

        y = mfunc (self.x)
        self.sigmas = y * frac
        self.y = y + np.random.standard_normal (self.y.shape) * self.sigmas

        return self

    def augmentSigmas (self, val):
        self.sigmas = np.sqrt (self.sigmas**2 + val**2)
        return self

    def guess (self):
        """Return a tuple of parameter guesses based on the X and Y data."""
        raise NotImplementedError ()

    def makeModel (self, *params):
        """Return a function that maps X values into appropriate
        model values."""

        raise NotImplementedError ()

    def _fitImpl (self, x, y, sig, guess, reckless):
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

    def fit (self, guess=None, reckless=False, **kwargs):
        if guess is None: guess = self.guess ()

        self.params = None
        self.mfunc = None
        self.mdata = None
        self.resids = None
        self.rchisq = None

        if self.sigmas is None:
            raise ValueError ('Must assess uncertainties; try fakeSigmas')

        self._fitImpl (self.x, self.y, self.sigmas, guess,
                       reckless, **kwargs)

        if reckless:
            if self._fitExport is not None:
                self._fitExport ()
            return self

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
            # resids may be complex
            self.rchisq = (self.resids * self.resids.conj () / self.sigmas**2).sum () / \
                          (self.x.size - len (self.params))

        if self._fitExport is not None:
            self._fitExport ()

        return self

    def assumeParams (self, *params):
        self.params = np.asfarray (params)
        self.uncerts = np.zeros_like (self.params)
        self.mfunc = self.makeModel (*self.params)

        if self.x is not None:
            self.mdata = self.mfunc (self.x)
            self.resids = self.y - self.mdata

        if self.sigmas is not None:
            # resids may be complex
            self.rchisq = (self.resids * self.resids.conj () / self.sigmas**2).sum () / \
                          (self.x.size - len (self.params))

        if self._fitExport is not None:
            self._fitExport ()

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

    def plot (self, dlines=True, smoothModel=True, xmin=None, xmax=None,
              ymin=None, ymax=None, mxmin=None, mxmax=None,
              xcomponent='real', ycomponent='real', **kwargs):
        import omega

        _cmplx = {'real': lambda x: x.real,
                  'imag': lambda x: x.imag,
                  'amp': lambda x: np.abs (x),
                  'pha': lambda x: np.arctan2 (x.imag, x.real)}

        if not smoothModel:
            modx = self.x
            mody = self.mdata
            resy = mody
        else:
            if mxmin is None:
                mxmin = self.x.min ()
            if mxmax is None:
                mxmax = self.x.max ()
            modx = np.linspace (mxmin, mxmax, 400)
            mody = self.mfunc (modx)
            resy = self.mdata

        plotx = _cmplx[xcomponent] (self.x)
        plotmodx = _cmplx[xcomponent] (modx)
        y = _cmplx[ycomponent] (self.y)
        mody = _cmplx[ycomponent] (mody)
        resy = _cmplx[ycomponent] (resy)

        resids = y - resy
        if ycomponent == 'pha':
            resids = ((resids + np.pi) % (2 * np.pi)) - np.pi

        vb = omega.layout.VBox (2)

        if self.sigmas is not None:
            vb.pData = omega.quickXYErr (plotx, y, self.sigmas, 'Data', lines=dlines, **kwargs)
        else:
            vb.pData = omega.quickXY (plotx, y, 'Data', lines=dlines, **kwargs)

        vb[0] = vb.pData
        vb[0].addXY (plotmodx, mody, 'Model')
        vb[0].setYLabel ('Y')
        vb[0].rebound (False, True)
        vb[0].setBounds (xmin, xmax, ymin, ymax)

        vb[1] = vb.pResid = omega.RectPlot ()
        vb[1].defaultField.xaxis = vb[1].defaultField.xaxis
        if self.sigmas is not None:
            vb[1].addXYErr (plotx, resids, self.sigmas, 'Resid.', lines=False)
        else:
            vb[1].addXY (plotx, resids, 'Resid.', lines=False)
        vb[1].setLabels ('X', 'Residuals')
        vb[1].rebound (False, True)
        vb[1].setBounds (xmin, xmax) # ignore Y values since residuals are on different scale

        vb.setWeight (0, 3)
        return vb


class LinearFit (FitBase):
    _paramNames = ['a', 'b']

    def guess (self):
        return (0, 0)

    def makeModel (self, a, b):
        return lambda x: a + b * x

    def _fitImpl (self, x, y, sig, guess, reckless):
        # Ignore the guess since we can solve this exactly
        # Exact solution math copied out of Numerical Recipes in C
        # 2nd Ed. sec 15.2. (But no code copied)

        sm1 = sig ** -1
        sm2 = sm1 ** 2

        S = sm2.sum ()
        Sx = np.dot (x, sm2)
        Sy = np.dot (y, sm2)
        Sxx = np.dot (x**2, sm2)
        Syy = np.dot (y**2, sm2)
        Sxy = np.dot (x * y, sm2)

        D = S * Sxx - Sx**2

        t = (x - Sx / S) * sm1
        Stt = (t**2).sum ()

        b = np.dot (t * y, sm1) / Stt
        a = (Sy - Sx * b) / S

        sigma_a = np.sqrt ((1 + Sx**2 / S / Stt) / S)
        sigma_b = np.sqrt (Stt ** -1)

        self.params = np.asarray ((a, b))
        self.uncerts = np.asarray ((sigma_a, sigma_b))


    def _fitExport (self):
        self.a, self.b = self.params
        self.sigma_a, self.sigma_b = self.uncerts


class SlopeFit (FitBase):
    _paramNames = ['m']

    def guess (self):
        return (0, )

    def makeModel (self, m):
        return lambda x: m * x

    def _fitImpl (self, x, y, sig, guess, reckless):
        # Ignore the guess since we can solve this exactly

        sm2 = sig ** -2

        Sxx = np.dot (x**2, sm2)
        Sxy = np.dot (x * y, sm2)

        m = Sxy / Sxx
        sigma_m = 1. / np.sqrt (Sxx)

        self.params = np.asarray ((m, ))
        self.uncerts = np.asarray ((sigma_m, ))


    def _fitExport (self):
        self.m = self.params[0]
        self.sigma_m = self.uncerts[0]


class ConstrainedMinFit (FitBase):
    """A Fit object that implements its fit via a generic constrained
    function minimization algorithm. Extra fields are:

      ??

    Subclassers must implement:

      _paramNames - A list of textual names corresponding to the model parameters.
            guess - The function to guess initial parameters, given the data.
        makeModel - The function to return a model evaluator function.
    """

    makeModelDeriv = None

    """Returns a function d(x) such that

    d(x) = J

    J.shape = (len (params), x.size)
    J[ip,ix] = dModel(x[ix])/dparams[ip]

    """

    def __init__ (self):
        super (ConstrainedMinFit, self).__init__ ()

        self._info = [{'parname': self._paramNames[i],
                       'fixed': False,
                       'limited': [False, False], 'limits': [0., 0.]}
                      for i in xrange (0, len (self._paramNames))]

    def setBounds (self, pidx, min=None, max=None):
        if pidx < 0 or pidx >= len (self._paramNames):
            raise ValueError ('pidx')

        if min is None:
            limitsmin = 0.
            limitedmin = False
        else:
            limitsmin = min
            limitedmin = True

        if max is None:
            limitsmax = 0.
            limitedmax = False
        else:
            limitsmax = max
            limitedmax = True

        t = self._info[pidx]
        t['limits'] = (limitsmin, limitsmax)
        t['limited'] = (limitedmin, limitedmax)
        t['fixed'] = False # this is implicitly called for
        return self

    def fix (self, pidx, fixval):
        if pidx < 0 or pidx >= len (self._paramNames):
            raise ValueError ('pidx')

        t = self._info[pidx]

        if fixval is None:
            t['fixed'] = False
        else:
            t['fixed'] = True
            t['value'] = float (fixval)

        return self


    def tie (self, pidx, tieexpr):
        if pidx < 0 or pidx >= len (self._paramNames):
            raise ValueError ('pidx')

        t = self._info[pidx]

        if tieexpr is None:
            del t['tied']
        else:
            t['tied'] = str (tieexpr)

        return self


    def _fitImpl (self, x, y, sig, guess, reckless, **kwargs):
        from mpfit import mpfit

        w = sig ** -1
        ndof = x.size - len (guess)

        def error (p, fjac=None):
            self.mfunc = f = self.makeModel (*p)
            self.mdata = d = f (x)
            self.resids = r = y - d
            #print 'W:', w
            #print 'R:', r
            return 0, np.ravel (r * w)

        for i in xrange (0, len (self._paramNames)):
            if self._info[i]['fixed']:
                ndof += 1
                continue
            self._info[i]['value'] = guess[i]

        self.mpobj = o = mpfit (error, parinfo=self._info, quiet=True, **kwargs)

        if not reckless and (o.status < 0 or o.status == 5):
            raise Exception ('MPFIT minimization failed: %d, %s' % (o.status,
                                                                    o.errmsg))

        if not reckless and (o.perror is None):
            raise Exception ('MPFIT failed to find uncerts: %d, %s' % (o.status,
                                                                       o.errmsg))

        if not reckless and np.any (~np.isfinite (o.params)):
            raise Exception ('MPFIT converged on infinite parameters')

        # Coerce into arrayness. Calculate rchisq ourselves since
        # fixed parameters may change ndof over what the naive code
        # expects.
        self.params = np.atleast_1d (o.params)
        self.uncerts = np.atleast_1d (o.perror)
        self.cov = o.covar
        self.chisq = o.fnorm
        self.rchisq = o.fnorm / ndof


class GaussianFit (LeastSquaresFit):
    _paramNames = ['height', 'xmid', 'width']

    def guess (self):
        height = self.y.max ()

        ytotal = self.y.sum ()
        byx = self.y * self.x
        xmid = byx.sum () / ytotal

        # Not at all sure if this is a good algorithm. Seems to
        # work OK.
        width = np.sqrt (abs ((self.x - xmid)**2 * self.y).sum () / ytotal)

        return (height, xmid, width)

    def makeModel (self, height, xmid, width):
        return lambda x: height * np.exp (-0.5 * ((x - xmid)/width)**2)

    def _fitExport (self):
        self.height, self.xmid, self.width = self.params
        self.sigma_h, self.sigma_x, self.sigma_w = self.uncerts


class PowerLawFit (LeastSquaresFit):
    _paramNames = ['q', 'alpha']

    def guess (self):
        lx = np.log (self.x)
        ly = np.log (self.y)

        dlx = lx.max () - lx.min ()
        dly = ly.max () - ly.min ()
        alpha = dly / dlx

        mlx = lx.mean ()
        mly = ly.mean ()
        q = np.exp (mly - alpha * mlx)

        return (q, alpha)

    def makeModel (self, q, alpha):
        return lambda x: q * x ** alpha

    def _fitExport (self):
        self.q, self.alpha = self.params
        self.sigma_q, self.sigma_a = self.uncerts


class BiPowerLawFit (LeastSquaresFit):
    _paramNames = ['xbr', 'ybr', 'alpha1', 'alpha2']

    def guess (self):
        l = np.log

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
        return np.poly1d ([c, b, a])

    def _fitExport (self):
        self.a, self.b, self.c = self.params
        self.sigma_a, self.sigma_b, self.sigma_c = self.uncerts
        self.xExtremum = -self.b / 2 / self.c
