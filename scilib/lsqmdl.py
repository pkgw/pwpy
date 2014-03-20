# Copyright 2012-2014 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""
lsqmdl - model data with least-squares fitting

Usage:

  Model(func, data, [invsigma], [args]).solve(guess).printsoln()
    func takes (p1, p2, p3[, *args]) and returns model data
  PolynomialModel(maxexponent, x, data, [invsigma]).solve().plot()
  ScaleModel(x, data, [invsigma]).solve().showcov() # data = m*x

The invsigma are *inverse sigmas*, NOT inverse *variances* (the usual
statistical weights). Since most applications deal in sigmas, take
care to write

  m = Model (func, data, 1./uncerts) # right!    not
  m = Model (func, data, uncerts) # WRONG

If you have zero uncertainty on a measurement, too bad.
"""

import numpy as np

try:
    # numpy 1.7
    import numpy.polynomial.polynomial as npoly
except ImportError:
    import numpy.polynomial as npoly


class _ModelBase (object):
    data = None
    invsigma = None

    params = None # ndarray of solved model parameters
    perror = None # ndarray of 1-sigma uncerts on pamams
    paramnames = None # iterable of string names for parameters
    covar = None # covariance matrix
    mfunc = None # function f(...) evaluating model fixed at best params
    mdata = None # modeled data at best params
    rchisq = None # reduced chi squared of the fit
    resids = None # resids = data - mdata

    def __init__ (self, data, invsigma=None):
        self.setdata (data, invsigma)


    def setdata (self, data, invsigma=None):
        self.data = np.array (data, dtype=np.float, ndmin=1)

        if invsigma is None:
            self.invsigma = np.ones (self.data.shape)
        else:
            i = np.array (invsigma, dtype=np.float)
            self.invsigma = np.broadcast_arrays (self.data, i)[1] # allow scalar invsigma

        if self.invsigma.shape != self.data.shape:
            raise ValueError ('data values and inverse-sigma values must have same shape')


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


    def plot (self, modelx, dlines=False, xmin=None, xmax=None,
              ymin=None, ymax=None, **kwargs):
        """This assumes that `data` is 1D and that `mfunc` takes one argument that
        should be treated as the X variable."""

        import omega as om

        modelx = np.asarray (modelx)
        if modelx.shape != self.data.shape:
            raise ValueError ('modelx and data arrays must have same shape')

        modely = self.mfunc (modelx)
        sigmas = self.invsigma**-1 # TODO: handle invsigma = 0

        vb = om.layout.VBox (2)
        vb.pData = om.quickXYErr (modelx, self.data, sigmas,
                                  'Data', lines=dlines, **kwargs)

        vb[0] = vb.pData
        vb[0].addXY (modelx, modely, 'Model')
        vb[0].setYLabel ('Y')
        vb[0].rebound (False, True)
        vb[0].setBounds (xmin, xmax, ymin, ymax)

        vb[1] = vb.pResid = om.RectPlot ()
        vb[1].defaultField.xaxis = vb[1].defaultField.xaxis
        vb[1].addXYErr (modelx, self.resids, sigmas, None, lines=False)
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
    def __init__ (self, func, data, invsigma=None, args=()):
        if func is not None:
            self.setfunc (func, args)
        if data is not None:
            self.setdata (data, invsigma)


    def setfunc (self, func, args=()):
        self.func = func
        self._args = args

        # Create the Problem here so the caller can futz with it
        # if so desired.
        npar = func.func_code.co_argcount - len (args)
        import lmmin
        self.lm_prob = lmmin.Problem (npar)

        if len (args):
            self.paramnames = func.func_code.co_varnames[:-len (args)]
        else:
            self.paramnames = func.func_code.co_varnames


    def solve (self, guess):
        guess = np.array (guess, dtype=np.float, ndmin=1)
        f = self.func
        args = self._args

        def lmfunc (params, vec):
            vec[:] = f (*(tuple (params) + args)).flatten ()

        self.lm_prob.setResidualFunc (self.data.flatten (),
                                      self.invsigma.flatten (),
                                      lmfunc, None)
        self.lm_soln = soln = self.lm_prob.solve (guess)

        self.params = soln.params
        self.perror = soln.perror
        self.covar = soln.covar

        from functools import partial
        self.mfunc = partial (f, *soln.params)
        self.mdata = soln.fvec.reshape (self.data.shape)

        if soln.ndof > 0:
            self.rchisq = soln.fnorm / soln.ndof
        self.resids = self.data - self.mdata
        return self


class PolynomialModel (_ModelBase):
    def __init__ (self, maxexponent, x, data, invsigma=None):
        self.maxexponent = maxexponent
        self.x = np.array (x, dtype=np.float, ndmin=1, copy=False, subok=True)
        self.setdata (data, invsigma)

    def solve (self):
        self.paramnames = ['a%d' % i for i in xrange (self.maxexponent + 1)]
        # Based on my reading of the polyfit() docs, I think w=invsigma**2 is right...
        self.params = npoly.polyfit (self.x, self.data, self.maxexponent,
                                     w=self.invsigma**2)
        self.perror = None # does anything provide this? could farm out to lmmin ...
        self.covar = None
        self.mfunc = lambda x: npoly.polyval (x, self.params)
        self.mdata = self.mfunc (self.x)
        self.resids = self.data - self.mdata
        self.rchisq = (((self.resids * self.invsigma)**2).sum ()
                       / (self.x.size - (self.maxexponent + 1)))
        return self


class ScaleModel (_ModelBase):
    def __init__ (self, x, data, invsigma=None):
        self.x = np.array (x, dtype=np.float, ndmin=1, copy=False, subok=True)
        self.setdata (data, invsigma)

    def solve (self):
        w2 = self.invsigma**2
        sxx = np.dot (self.x**2, w2)
        sxy = np.dot (self.x * self.data, w2)
        m = sxy / sxx
        uc_m = 1. / np.sqrt (sxx)

        self.paramnames = ['m']
        self.params = np.asarray ([m])
        self.perror = np.asarray ([uc_m])
        self.covar = self.perror.reshape ((1, 1))
        self.mfunc = lambda x: m * x
        self.mdata = m * self.x
        self.resids = self.data - self.mdata
        self.rchisq = ((self.resids * self.invsigma)**2).sum () / (self.x.size - 1)
        return self


# lmmin-based model-fitting when the model is broken down into composable
# components.

class ModelComponent (object):
    npar = 0
    name = None
    paramnames = ()
    nmodelargs = 0

    setguess = None
    setvalue = None
    setlimit = None
    _accum_mfunc = None

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

    def model (self, pars, y):
        """Modify `y` based on `pars`."""
        pass

    def deriv (self, pars, jac):
        """Compute the Jacobian. `jac[i]` is d`y`/d`pars[i]`."""
        pass

    def extract (self, pars, perr, cov):
        """Extract fit results into the object for ease of inspection."""
        self.covar = cov

    def _outputshape (self, *args):
        """This is a helper for evaluating the model function at fixed parameters. To
        work in the ComposedModel paradigm, we have to allocate an empty array
        to hold the model output before we can fill it via the _accum_mfunc
        functions. We can't do that without knowing what size it will be. That
        size has to be a function of the "free" parameters to the model
        function that are implicit/fixed during the fitting process. Given these "free"
        parameters, _outputshape returns the shape that the output will have."""
        raise NotImplementedError ()

    def mfunc (self, *args):
        if len (args) != self.nmodelargs:
            raise TypeError ('model function expected %d arguments, got %d' %
                             (self.nmodelargs, len (args)))

        result = np.zeros (self._outputshape (*args))
        self._accum_mfunc (result, *args)
        return result


class ComposedModel (_ModelBase):
    def __init__ (self, component, data, invsigma=None):
        if component is not None:
            self.setcomponent (component)
        if data is not None:
            self.setdata (data, invsigma)


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

        def model (pars, outputs):
            outputs.fill (0)
            self.component.model (pars, outputs)

        self.lm_model = model
        self.lm_deriv = deriv
        self.lm_prob.setResidualFunc (self.data, self.invsigma, model,
                                      self.component.deriv)
        self.lm_soln = soln = self.lm_prob.solve (guess)

        self.params = soln.params
        self.perror = soln.perror
        self.covar = soln.covar

        self.mdata = self.lm_soln.fvec.reshape (self.data.shape)
        if soln.ndof > 0:
            self.rchisq = soln.fnorm / soln.ndof
        self.resids = self.data - self.mdata

        self.component.extract (soln.params, soln.perror, soln.covar)
        return self


    def mfunc (self, *args):
        return self.component.mfunc (*args)


    def debug_derivative (self, guess):
        """returns (explicit, auto)"""
        import lmmin
        return lmmin.checkDerivative (self.component.npar, self.data.size,
                                      self.lm_model, self.lm_deriv, guess)


# Now specific components useful in the above framework. The general strategy
# is to err on the side of having additional parameters in the individual
# classes, and the user can call setvalue() to fix them if they're not needed.

class AddConstantComponent (ModelComponent):
    npar = 1
    paramnames = ('value', )
    nmodelargs = 0

    def model (self, pars, y):
        y += pars[0]

    def deriv (self, pars, jac):
        jac[0] = 1.

    def _outputshape (self):
        return ()

    def extract (self, pars, perr, cov):
        def _accum_mfunc (res):
            res += pars[0]
        self._accum_mfunc = _accum_mfunc

        self.covar = cov
        self.f_value = pars[0]
        self.u_value = perr[0]


class AddPolynomialComponent (ModelComponent):
    nmodelargs = 1

    def __init__ (self, maxexponent, x, name=None):
        self.npar = maxexponent + 1
        self.x = np.array (x, dtype=np.float, ndmin=1, copy=False, subok=True)

    def _param_names (self):
        for i in xrange (self.npar):
            yield 'c%d' % i

    def model (self, pars, y):
        y += npoly.polyval (self.x, pars)

    def deriv (self, pars, jac):
        w = np.ones_like (self.x)

        for i in xrange (self.npar):
            jac[i] = w
            w *= self.x

    def _outputshape (self, x):
        return x.shape

    def extract (self, pars, perr, cov):
        def _accum_mfunc (res, x):
            res += npoly.polyval (x, pars)
        self._accum_mfunc = _accum_mfunc

        self.covar = cov
        self.f_coeffs = pars
        self.u_coeffs = perr


def _broadcast_shapes (s1, s2):
    """Given array shapes `s1` and `s2`, compute the shape of the array that would
    result from broadcasting them together."""

    n1 = len (s1)
    n2 = len (s2)
    n = max (n1, n2)
    res = [1] * n

    for i in xrange (n):
        if i >= n1:
            c1 = 1
        else:
            c1 = s1[n1-1-i]

        if i >= n2:
            c2 = 1
        else:
            c2 = s2[n2-1-i]

        if c1 == 1:
            rc = c2
        elif c2 == 1 or c1 == c2:
            rc = c1
        else:
            raise ValueError ('array shapes %r and %r are not compatible' % (s1, s2))

        res[n-1-i] = rc

    return tuple (res)


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
        self.nmodelargs = 0

        for i, c in enumerate (self.components):
            if c.name is None:
                c.name = 'c%d' % i

            c.setguess = partial (self._offset_setguess, ofs, c.npar)
            c.setvalue = partial (self._offset_setvalue, ofs, c.npar)
            c.setlimit = partial (self._offset_setlimit, ofs, c.npar)
            ofs += c.npar
            self.nmodelargs += c.nmodelargs

        self.npar = ofs


    def prep_params (self):
        for c in self.components:
            c.prep_params ()


    def model (self, pars, y):
        ofs = 0

        for c in self.components:
            p = pars[ofs:ofs+c.npar]
            c.model (p, y)
            ofs += c.npar


    def deriv (self, pars, jac):
        ofs = 0

        for c in self.components:
            p = pars[ofs:ofs+c.npar]
            j = jac[ofs:ofs+c.npar]
            c.deriv (p, j)
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


    def _outputshape (self, *args):
        s = ()
        ofs = 0

        for c in self.components:
            cargs = args[ofs:ofs+c.nmodelargs]
            s = _broadcast_shapes (s, c._outputshape (*cargs))
            ofs += c.nmodelargs

        return s


    def _accum_mfunc (self, res, *args):
        ofs = 0

        for c in self.components:
            cargs = args[ofs:ofs+c.nmodelargs]
            c._accum_mfunc (res, *cargs)
            ofs += c.nmodelargs


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
        self.nmodelargs = self.subcomp.nmodelargs


    def prep_params (self):
        self.subcomp.prep_params ()


    def model (self, pars, y):
        self.subcomp.model (pars[1:], y)
        y *= pars[0]


    def deriv (self, pars, jac):
        self.subcomp.model (pars[1:], jac[0])
        self.subcomp.deriv (pars[1:], jac[1:])
        jac[1:] *= pars[0]


    def extract (self, pars, perr, cov):
        self.f_factor = pars[0]
        self.u_factor = perr[0]
        self.c_factor = cov[0]

        self.subcomp.extract (pars[1:], perr[1:], cov[1:,1:])


    def _outputshape (self, *args):
        return self.subcomp._outputshape (*args)


    def _accum_mfunc (self, res, *args):
        self.subcomp._accum_mfunc (res, *args)
