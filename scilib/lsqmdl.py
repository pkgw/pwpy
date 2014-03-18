# Copyright 2012-2014 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""
lsqmdl - model data with least-squares fitting

Usage:

  Model(func, x, y, [invsigma]).solve(guess).printsoln()
    func = lambda x, p1, p2, p3: ...
  PolynomialModel(maxexponent, x, y, [invsigma]).solve().plot()
  ScaleModel(x, y, [invsigma]).solve().showcov() # y = mx

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
    def __init__ (self, maxexponent, x, y, invsigma=None):
        self.maxexponent = maxexponent
        self.setdata (x, y, invsigma)


    def solve (self):
        try:
            # numpy 1.7
            from numpy.polynomial.polynomial import polyfit, polyval
        except ImportError:
            from numpy.polynomial import polyfit, polyval

        self.paramnames = ['a%d' % i for i in xrange (self.maxexponent + 1)]
        # Based on my reading of the polyfit() docs, I think w=invsigma**2 is right...
        self.params = polyfit (self.x, self.y, self.maxexponent,
                               w=self.invsigma**2)
        self.perror = None # does anything provide this? could farm out to lmmin ...
        self.covar = None
        self.modelfunc = lambda x: polyval (x, self.params)
        self.modely = self.modelfunc (self.x)
        self.resids = self.y - self.modely
        self.rchisq = (((self.resids * self.invsigma)**2).sum ()
                       / (self.x.size - (self.maxexponent + 1)))
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


# lmmin-based model-fitting when the model is broken down into composable
# components.

class ModelComponent (object):
    npar = 0
    name = None
    paramnames = ()

    setguess = None
    setvalue = None
    setlimit = None

    def __init__ (self, name=None):
        self.name = name

    def _param_names (self):
        """Overridable in case the list of parameter names needs to be
        generated on the fly."""
        return self.paramnames

    def finalize_setup (self):
        """If the component has subcomponents, this should set their `name`,
        `setguess`, `setvalue`, and `setlimit` properties. It should also
        set `npar` (on self) to the final value."""
        pass

    def prep_params (self):
        """This should make any necessary calls to `setvalue` or `setlimit`,
        though in straightforward cases it should just be up to the user to
        do this. If the component has subcomponents, their `prep_params`
        functions should be called."""
        pass

    def model (self, pars, x, y):
        """Modify `y` based on `x` and `pars`."""
        pass

    def deriv (self, pars, x, jac):
        """Compute the Jacobian. `jac[i]` is d`y`/d`pars[i]`."""
        pass

    def extract (self, pars, perr, cov):
        """Extract fit results into the object for ease of inspection."""
        self.covar = cov


class ComposedModel (_ModelBase):
    def __init__ (self, component, x, y, invsigma=None):
        if component is not None:
            self.setcomponent (component)
        if x is not None:
            self.setdata (x, y, invsigma)


    def _component_setguess (self, vals, ofs=0):
        vals = np.asarray (vals)
        if ofs < 0 or ofs + vals.size > self.component.npar:
            raise ValueError ('ofs %d, vals.size %d, npar %d' %
                              (ofs, vals.size, self.component.npar))
        self.force_guess[ofs:ofs+vals.size] = vals


    def _component_setvalue (self, cidx, val, fixed=False):
        if cidx < 0 or cidx >= self.component.npar:
            raise ValueError ('cidx %d, npar %d' % (cidx, self.component.npar))
        self.lm_prob.pValue (cidx, val, fixed=fixed)
        self.force_guess[cidx] = val


    def _component_setlimit (self, cidx, lower=-np.inf, upper=np.inf):
        if cidx < 0 or cidx >= self.component.npar:
            raise ValueError ('cidx %d, npar %d' % (cidx, self.component.npar))
        self.lm_prob.pLimit (cidx, lower, upper)


    def setcomponent (self, component):
        self.component = component

        component.setguess = self._component_setguess
        component.setvalue = self._component_setvalue
        component.setlimit = self._component_setlimit
        component.finalize_setup ()

        import lmmin
        self.lm_prob = lmmin.Problem (component.npar)
        self.force_guess = np.empty (component.npar)
        self.force_guess.fill (np.nan)
        self.paramnames = list (component._param_names ())

        component.prep_params ()


    def solve (self, guess=None):
        if guess is None:
            guess = self.force_guess
        else:
            guess = np.array (guess, dtype=np.float, ndmin=1, copy=True)

            for i in xrange (self.force_guess.size):
                if np.isfinite (self.force_guess[i]):
                    guess[i] = self.force_guess[i]

        x = self.x

        def model (pars, outputs):
            outputs.fill (0)
            self.component.model (pars, x, outputs)

        def deriv (pars, jac):
            self.component.deriv (pars, x, jac)

        self.lm_model = model
        self.lm_deriv = deriv
        self.lm_prob.setResidualFunc (self.y, self.invsigma, model, deriv)
        self.lm_soln = soln = self.lm_prob.solve (guess)

        self.params = soln.params
        self.perror = soln.perror
        self.covar = soln.covar

        def modelfunc (x):
            y = np.zeros_like (x)
            self.component.model (self.params, x, y)
            return y

        self.modelfunc = modelfunc
        self.modely = modelfunc (x)
        if soln.ndof > 0:
            self.rchisq = soln.fnorm / soln.ndof
        self.resids = self.y - self.modely

        self.component.extract (soln.params, soln.perror, soln.covar)
        return self


    def debug_derivative (self, guess):
        """returns (explicit, auto)"""
        import lmmin
        return lmmin.checkDerivative (self.component.npar, self.x.size,
                                      self.lm_model, self.lm_deriv, guess)


# Now specific components useful in the above framework. The general strategy
# is to err on the side of having additional parameters in the individual
# classes, and the user can call setvalue() to fix them if they're not needed.

class AddConstantComponent (ModelComponent):
    npar = 1
    paramnames = ('value', )

    def model (self, pars, x, y):
        y += pars[0]

    def deriv (self, pars, x, jac):
        jac[0] = 1.

    def extract (self, pars, perr, cov):
        self.covar = cov
        self.f_value = pars[0]
        self.u_value = perr[0]


class AddSinComponent (ModelComponent):
    npar = 3
    paramnames = ('amp', 'angfreq', 'phase')

    def model (self, pars, x, y):
        y += pars[0] * np.sin (pars[1] * x + pars[2])

    def deriv (self, pars, x, jac):
        th = pars[1] * x + pars[2]
        jac[0] = np.sin (th)
        jac[2] = pars[0] * np.cos (th)
        jac[1] = jac[1] * x

    def extract (self, pars, perr, cov):
        self.covar = cov
        self.f_amp, self.f_angfreq, self.f_phase = pars
        self.u_amp, self.u_angfreq, self.u_phase = perr

        if self.f_amp < 0:
            self.f_amp *= -1
            self.f_phase += np.pi

        self.f_phase = (self.f_phase + np.pi) % (2 * np.pi) - np.pi


class SeriesComponent (ModelComponent):
    """Apply a set of subcomponents in series, isolating each from the other. This
    is only valid if every subcomponent except the first is additive --
    otherwise, the Jacobian won't be right."""

    def __init__ (self, name=None, components=()):
        super (SeriesComponent, self).__init__ (name)
        self.components = list (components)


    def add (self, component):
        """This helps, but direct manipulation of self.components should be
        supported."""
        self.components.append (component)
        return self


    def _param_names (self):
        for c in self.components:
            pfx = c.name + '.' if c.name is not None else ''
            for p in c._param_names ():
                yield pfx + p


    def _offset_setguess (self, ofs, npar, vals, subofs=0):
        vals = np.asarray (vals)
        if subofs < 0 or subofs + vals.size > npar:
            raise ValueError ('subofs %d, vals.size %d, npar %d' %
                              (subofs, vals.size, npar))
        return self.setguess (vals, ofs + subofs)


    def _offset_setvalue (self, ofs, npar, cidx, value, fixed=False):
        if cidx < 0 or cidx >= npar:
            raise ValueError ('cidx %d, npar %d' % (cidx, npar))
        return self.setvalue (ofs + cidx, value, fixed)


    def _offset_setlimit (self, ofs, npar, cidx, lower=-np.inf, upper=np.inf):
        if cidx < 0 or cidx >= npar:
            raise ValueError ('cidx %d, npar %d' % (cidx, npar))
        return self.setlimit (ofs + cidx, lower, upper)


    def finalize_setup (self):
        from functools import partial

        ofs = 0

        for i, c in enumerate (self.components):
            if c.name is None:
                c.name = 'c%d' % i

            c.setguess = partial (self._offset_setguess, ofs, c.npar)
            c.setvalue = partial (self._offset_setvalue, ofs, c.npar)
            c.setlimit = partial (self._offset_setlimit, ofs, c.npar)
            ofs += c.npar

        self.npar = ofs


    def prep_params (self):
        for c in self.components:
            c.prep_params ()


    def model (self, pars, x, y):
        ofs = 0

        for c in self.components:
            p = pars[ofs:ofs+c.npar]
            c.model (p, x, y)
            ofs += c.npar


    def deriv (self, pars, x, jac):
        ofs = 0

        for c in self.components:
            p = pars[ofs:ofs+c.npar]
            j = jac[ofs:ofs+c.npar]
            c.deriv (p, x, j)
            ofs += c.npar


    def extract (self, pars, perr, cov):
        ofs = 0

        for c in self.components:
            n = c.npar

            spar = pars[ofs:ofs+n]
            serr = perr[ofs:ofs+n]
            scov = cov[ofs:ofs+n,ofs:ofs+n]
            c.extract (spar, serr, scov)
            ofs += n


class ScaleComponent (ModelComponent):
    npar = 1

    def __init__ (self, name=None, subcomp=None):
        super (ScaleComponent, self).__init__ (name)
        self.setsubcomp (subcomp)


    def setsubcomp (self, subcomp):
        self.subcomp = subcomp
        return self


    def _param_names (self):
        yield 'factor'

        pfx = self.subcomp.name + '.' if self.subcomp.name is not None else ''
        for p in self.subcomp._param_names ():
            yield pfx + p


    def _sub_setguess (self, npar, cidx, vals, ofs=0):
        vals = np.asarray (vals)
        if ofs < 0 or ofs + vals.size > npar:
            raise ValueError ('ofs %d, vals.size %d, npar %d' %
                              (ofs, vals.size, npar))
        return self.setguess (vals, ofs + 1)


    def _sub_setvalue (self, npar, cidx, value, fixed=False):
        if cidx < 0 or cidx >= npar:
            raise ValueError ('cidx %d, npar %d' % (cidx, npar))
        return self.setvalue (1 + cidx, value, fixed)


    def _sub_setlimit (self, npar, cidx, lower=-np.inf, upper=np.inf):
        if cidx < 0 or cidx >= npar:
            raise ValueError ('cidx %d, npar %d' % (cidx, npar))
        return self.setlimit (1 + cidx, lower, upper)


    def finalize_setup (self):
        if self.subcomp.name is None:
            self.subcomp.name = 'c'

        from functools import partial
        self.subcomp.setvalue = partial (self._sub_setvalue, self.subcomp.npar)
        self.subcomp.setlimit = partial (self._sub_setvalue, self.subcomp.npar)
        self.subcomp.finalize_setup ()

        self.npar = self.subcomp.npar + 1


    def prep_params (self):
        self.subcomp.prep_params ()


    def model (self, pars, x, y):
        self.subcomp.model (pars[1:], x, y)
        y *= pars[0]


    def deriv (self, pars, x, jac):
        self.subcomp.model (pars[1:], x, jac[0])

        self.subcomp.deriv (pars[1:], x, jac[1:])
        jac[1:] *= pars[0]


    def extract (self, pars, perr, cov):
        self.f_factor = pars[0]
        self.u_factor = perr[0]
        self.c_factor = cov[0]

        self.subcomp.extract (pars[1:], perr[1:], cov[1:,1:])
