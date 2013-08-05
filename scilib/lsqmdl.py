# Copyright 2012, 2013 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""
lsqmdl - model data with least-squares fitting

Usage:

  Model(func, x, y, [invsigma]).solve(guess).printsoln()
    func = lambda x, p1, p2, p3: ...
  PolynomialModel(degree, x, y, [invsigma]).solve().plot()
  ScaleModel(x, y, [invsigma]).solve().showcov()

The invsigma are *inverse sigmas*, NOT inverse *variances* (the usual
statistical weights). Since most applications deal in sigmas, take
care to write

  right = Model (func, x, y, 1./u)   not
  WRONG = Model (func, x, y, u)

If you have zero uncertainty on a measurement, too bad.
"""

import numpy as np


class _ModelBase (object):
    x = None
    y = None
    invsigma = None

    params = None # ndarray of solved model parameters
    perror = None # ndarray of 1-sigma uncerts on pamams
    paramnames = None # iterable of string names for parameters
    covar = None # covariance matrix
    modelfunc = None # function f(x) -> y evaluating best model at arbitrary x
    modely = None # modely = modelfunc (x)
    rchisq = None # reduced chi squared of the fit
    resids = None # resids = y - modely

    def __init__ (self, x, y, invsigma=None):
        self.setdata (x, y, invsigma)


    def setdata (self, x, y, invsigma=None):
        self.x = np.array (x, dtype=np.float, ndmin=1)
        self.y = np.array (y, dtype=np.float, ndmin=1)

        if invsigma is None:
            self.invsigma = np.ones (self.y.shape)
        else:
            i = np.array (invsigma, dtype=np.float)
            self.invsigma = np.broadcast_arrays (self.y, i)[1] # allow scalar invsigma

        if self.invsigma.shape != self.y.shape:
            raise ValueError ('y values and inverse-sigma values must have same shape')


    def printsoln (self):
        lmax = reduce (max, (len (x) for x in self.paramnames), len ('r chi sq'))

        if self.perror is None:
            for pn, val in zip (self.paramnames, self.params):
                print '%s: %14g' % (pn.rjust (lmax), val)
        else:
            for pn, val, err in zip (self.paramnames, self.params, self.perror):
                frac = abs (100. * err / val)
                print '%s: %14g +/- %14g (%.2f%%)' % (pn.rjust (lmax), val, err, frac)

        print '%s: %14g' % ('r chi sq'.rjust (lmax), self.rchisq)
        return self


    def plot (self, dlines=False, densemodel=True, xmin=None, xmax=None,
              ymin=None, ymax=None, mxmin=None, mxmax=None, **kwargs):
        import omega as om

        if not densemodel:
            modx = self.x
            mody = self.modely
        else:
            if mxmin is None:
                mxmin = self.x.min ()
            if mxmax is None:
                mxmax = self.x.max ()
            modx = np.linspace (mxmin, mxmax, 400)
            mody = self.modelfunc (modx)

        sigmas = self.invsigma**-1 # TODO: handle invsigma = 0

        vb = om.layout.VBox (2)
        vb.pData = om.quickXYErr (self.x, self.y, sigmas,
                                  'Data', lines=dlines, **kwargs)

        vb[0] = vb.pData
        vb[0].addXY (modx, mody, 'Model')
        vb[0].setYLabel ('Y')
        vb[0].rebound (False, True)
        vb[0].setBounds (xmin, xmax, ymin, ymax)

        vb[1] = vb.pResid = om.RectPlot ()
        vb[1].defaultField.xaxis = vb[1].defaultField.xaxis
        vb[1].addXYErr (self.x, self.resids, sigmas, None, lines=False)
        vb[1].setLabels ('X', 'Residuals')
        vb[1].rebound (False, True)
        # ignore Y values since residuals are on different scale:
        vb[1].setBounds (xmin, xmax)

        vb.setWeight (0, 3)
        return vb


    def showcov (self):
        import ndshow
        # would be nice: labels with parameter names
        ndshow.view (self.covar, title='Covariance Matrix')


class Model (_ModelBase):
    def __init__ (self, func, x, y, invsigma=None):
        if func is not None:
            self.setfunc (func)
        if x is not None:
            self.setdata (x, y, invsigma)


    def setfunc (self, func):
        self.func = func
        # Create the Problem here so the caller can futz with it
        # if so desired.
        npar = func.func_code.co_argcount - 1
        import lmmin
        self.lm_prob = lmmin.Problem (npar)


    def solve (self, guess):
        guess = np.array (guess, dtype=np.float, ndmin=1)
        x = self.x
        f = self.func

        def yfunc (params, vec):
            vec[:] = f (x, *params)

        self.lm_prob.setResidualFunc (self.y, self.invsigma, yfunc, None)
        self.lm_soln = soln = self.lm_prob.solve (guess)

        self.paramnames = f.func_code.co_varnames[1:]
        self.params = soln.params
        self.perror = soln.perror
        self.covar = soln.covar
        self.modelfunc = lambda x: f (x, *soln.params)
        self.modely = self.modelfunc (x)
        if soln.ndof > 0:
            self.rchisq = soln.fnorm / soln.ndof
        self.resids = self.y - self.modely
        return self


class PolynomialModel (_ModelBase):
    def __init__ (self, nterms, x, y, invsigma=None):
        self.nterms = nterms
        self.setdata (x, y, invsigma)


    def solve (self):
        try:
            # numpy 1.7
            from numpy.polynomial.polynomial import polyfit, polyval
        except ImportError:
            from numpy.polynomial import polyfit, polyval

        self.paramnames = ['a%d' % i for i in xrange (self.nterms)]
        # Based on my reading of the polyfit() docs, I think w=invsigma**2 is right...
        self.params = polyfit (self.x, self.y, self.nterms - 1,
                               w=self.invsigma**2)
        self.perror = None # does anything provide this? could farm out to lmmin ...
        self.covar = None
        self.modelfunc = lambda x: polyval (x, self.params)
        self.modely = self.modelfunc (self.x)
        self.resids = self.y - self.modely
        self.rchisq = ((self.resids * self.invsigma)**2).sum () / (self.x.size - self.nterms)
        return self


class ScaleModel (_ModelBase):
    def solve (self):
        w2 = self.invsigma**2
        sxx = np.dot (self.x**2, w2)
        sxy = np.dot (self.x * self.y, w2)
        m = sxy / sxx
        uc_m = 1. / np.sqrt (sxx)

        self.paramnames = ['m']
        self.params = np.asarray ([m])
        self.perror = np.asarray ([uc_m])
        self.covar = self.perror.reshape ((1, 1))
        self.modelfunc = lambda x: m * x
        self.modely = m * self.x
        self.resids = self.y - self.modely
        self.rchisq = ((self.resids * self.invsigma)**2).sum () / (self.x.size - 1)
        return self
