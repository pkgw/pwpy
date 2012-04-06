# Copyright 2012 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""
lsqmdl - model data with least-squares fitting

Model(func, x, y, [w]).solve(guess).printsoln()
  func = lambda x, p1, p2, p3: ...
PolynomialModel(degree, x, y, [w]).solve().plot()
ScaleModel(x, y, [w]).solve().showcov()

The w are *weights* and NOT *uncertainties*. If you have zero
uncertainty on a measurement that's your problem.
"""

import numpy as np


class _ModelBase (object):
    x = None
    y = None
    w = None

    params = None # ndarray of solved model parameters
    perror = None # ndarray of 1-sigma uncerts on pamams
    paramnames = None # iterable of string names for parameters
    covar = None # covariance matrix
    modelfunc = None # function f(x) -> y evaluating best model at arbitrary x
    modely = None # modely = modelfunc (x)
    rchisq = None # reduced chi squared of the fit
    resids = None # resids = y - modely

    def __init__ (self, x, y, w=None):
        self.setdata (x, y, w)


    def setdata (self, x, y, w=None):
        self.x = np.array (x, dtype=np.float, ndmin=1)
        self.y = np.array (y, dtype=np.float, ndmin=1)

        if w is None:
            self.w = np.ones (self.y.shape)
        else:
            w = np.array (w, dtype=np.float)
            self.w = np.broadcast_arrays (self.y, w)[1] # allow scalar w

        if self.w.shape != self.y.shape:
            raise ValueError ('y values and weight values must have same shape')


    def printsoln (self):
        lmax = reduce (max, (len (x) for x in self.paramnames), len ('r chi sq'))

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

        sigmas = self.w**-1 # TODO: zero weights

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
    def __init__ (self, func, x, y, w=None):
        if func is not None:
            self.setfunc (func)
        if x is not None:
            self.setdata (x, y, w)


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

        self.lm_prob.setResidualFunc (self.y, self.w, yfunc, None)
        self.lm_soln = soln = self.lm_prob.solve (guess)

        self.paramnames = f.func_code.co_varnames[1:]
        self.params = soln.params
        self.perror = soln.perror
        self.covar = soln.covar
        self.modelfunc = lambda x: f (x, *soln.params)
        self.modely = self.modelfunc (x)
        self.rchisq = soln.fnorm / soln.ndof
        self.resids = self.y - self.modely
        return self


class PolynomialModel (_ModelBase):
    def __init__ (self, degree, x, y, w=None):
        self.degree = degree
        self.setdata (x, y, w)


    def solve (self):
        from numpy.polynomial import polyfit, polyval

        self.paramnames = ['a%d' % i for i in xrange (self.degree)]
        self.params, info = polyfit (self.x, self.y, self.degree, w=self.w, full=True)
        self.perror = None # does anything provide this? could farm out to lmmin ...
        self.covar = None
        self.modelfunc = lambda x: polyval (x, self.params)
        self.modely = self.modelfunc (self.x)
        self.rchisq = info[0] / (self.x.size - self.degree)
        self.resids = self.y - self.modely
        return self


class ScaleModel (_ModelBase):
    def solve (self):
        w2 = self.w**2
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
        self.rchisq = ((self.resids * self.w)**2).sum () / (self.x.size - 1)
        return self
