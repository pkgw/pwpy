"""pwmpfit - Pythonic, Numpy-based port of MPFIT.
"""

# Test problem: http://www.maxthis.com/curviex.htm

import numpy as N

# Quickie testing infrastructure

_testfuncs = []

def test (f):
    """A decorator for functions to be run as part of
    the test suite."""
    _testfuncs.append (f)
    return f

def _runtests ():
    for f in _testfuncs:
        f ()

# Parameter Info attributes that can be specified
#
# Each parameter can be described by five floats:

PI_F_VALUE = 0 # specified initial value
PI_F_LLIMIT = 1 # lower bound on param value (can be -inf)
PI_F_ULIMIT = 2 # upper bound (can be +inf)
PI_F_STEP = 3 # fixed parameter step size to use (abs or rel), 0. for unspecified
PI_F_MAXSTEP = 4 # maximum step to take
PI_NUM_F = 5

# Five bits of data
PI_M_SIDE = 0x3 # sidedness of derivative - two bits
PI_M_FIXED = 0x4 # fixed value
PI_M_PRINT = 0x8 # whether to print parameter value periodically
PI_M_RELSTEP = 0x10 # whether the specified stepsize is relative

# And two objects
PI_O_NAME = 0 # textual name of the parameter
PI_O_TIED = 1 # fixed to be a function of other parameters
PI_NUM_O = 2


# Norm-calculating functions. Apparently the "careful"
# norm calculator can be slow, while the "fast" version
# can be susceptible to under- or overflows.

_enorm_fast = lambda v, finfo: N.sqrt (N.dot (v, v))

def _enorm_careful (v, finfo):
    agiant = finfo.max / v.size
    adwarf = finfo.tiny * v.size

    # "This is hopefully a compromise between speed and robustness.
    # Need to do this because of the possibility of over- or under-
    # flow.
    
    mx = v.max ()
    mn = v.min ()
    mx = max (abs (mx), abs (mn))
    
    if mx == 0:
        return v[0] * 0.
    if mx > agiant or mx < adwarf:
        return mx * N.sqrt (N.dot (v / mx, v / mx))
    
    return N.sqrt (N.dot (v, v))


class Solution (object):
    prob = None
    status = -1
    perror = None
    params = None
    covar = None
    fnorm = None
    fvec = None
    fjac = None
    
    def __init__ (self, prob):
        self.prob = prob


class Problem (object):
    _func = None
    _npar = None
    _nout = None

    _pinfof = None
    _pinfob = None
    _pinfoo = None

    # These ones are set in _fixupCheck
    _ifree = None
    _qanytied = None

    # Public fields, settable by user at will
    
    solclass = None
    
    ftol = 1e-10
    xtol = 1e-10
    gtol = 1e-10
    damp = 0.
    factor = 100.
    epsfunc = None

    maxiter = 200
    nprint = 1

    diag = None

    nocovar = False
    fastnorm = False
    rescale = False
    autoderivative = True
    quiet = False
    debugCalls = False
    debugJac = False

    
    def __init__ (self, func=None, npar=None, nout=None, solclass=Solution):
        if func is not None:
            self.setFunc (func, npar, nout)

        if not issubclass (solclass, Solution):
            raise ValueError ('solclass')

        self.solclass = solclass


    def setFunc (self, func, npar, nout):
        if not callable (func):
            raise ValueError ('func')
        
        try:
            npar = int (npar)
            assert npar > 0
        except:
            raise ValueError ('npar')

        try:
            nout = int (nout)
            assert nout > 0
            # Do not check that nout >= npar here, since
            # the user may wish to fix parameters, which
            # could make the problem tractable after all.
        except:
            raise ValueError ('nout')

        realloc = self._npar is None or self._npar != npar
        
        self._func = func
        self._npar = npar
        self._nout = nout
        self.nfev = 0

        # Initialize parameter info arrays. Avoid doing so if it seems
        # that we've been called before and npar is the same, in case
        # the problem is largely the same and the stored parameter
        # info should be preserved.

        if realloc:
            self._pinfof = p = N.ndarray ((PI_NUM_F, npar), dtype=N.float)
            p[PI_F_VALUE] = N.nan
            p[PI_F_LLIMIT] = -N.inf
            p[PI_F_ULIMIT] = N.inf
            p[PI_F_STEP] = 0.
            p[PI_F_MAXSTEP] = N.inf
            
            self._pinfob = p = N.ndarray (npar, dtype=N.int)
            p[:] = 0
        
            self._pinfoo = p = N.ndarray ((PI_NUM_O, npar), dtype=N.object)
            p[PI_O_NAME] = None
            p[PI_O_TIED] = None

        # Return self for easy chaining of calls.
        return self
    

    def _fixupCheck (self):
        if self._func is None:
            raise ValueError ('No function yet.')

        # Coerce parameters to desired types

        self.ftol = float (self.ftol)
        self.xtol = float (self.xtol)
        self.gtol = float (self.gtol)
        self.damp = float (self.damp)
        self.factor = float (self.factor)

        if self.epsfunc is not None:
            self.epsfunc = float (self.epsfunc)

        self.maxiter = int (self.maxiter)
        self.nprint = int (self.nprint)

        self.nocovar = bool (self.nocovar)
        self.fastnorm = bool (self.fastnorm)
        self.rescale = bool (self.rescale)
        self.autoderivative = bool (self.autoderivative)
        self.quiet = bool (self.quiet)
        self.debugCalls = bool (self.debugCalls)
        self.debugJac = bool (self.debugJac)

        if self.diag is not None:
            self.diag = N.asarray (self.diag, dtype=N.float)
        
        # Bounds and type checks

        if not issubclass (self.solclass, Solution):
            raise ValueError ('solclass')

        if self.ftol <= 0.:
            raise ValueError ('ftol')

        if self.xtol <= 0.:
            raise ValueError ('xtol')

        if self.gtol <= 0.:
            raise ValueError ('gtol')

        if self.damp < 0.:
            raise ValueError ('damp')

        if self.maxiter < 1:
            raise ValueError ('maxiter')

        if self.factor <= 0.:
            raise ValueError ('factor')

        # Consistency checks

        if not ((self.damp > 0.) ^ self.autoderivative):
            raise ValueError ('Damping factor and autoderivative '
                              'are mutually exclusive.')

        if self.rescale:
            if diag is None or diag.shape != (self.npar, ):
                raise ValueError ('diag')
            if N.any (diag <= 0.):
                raise ValueError ('diag')

        p = self._pinfof

        if N.any (N.isinf (p[PI_F_VALUE])):
            raise ValueError ('Some specified initial values infinite.')
        
        if N.any (N.isinf (p[PI_F_STEP])):
            raise ValueError ('Some specified parameter steps infinite.')
        
        if N.any (p[PI_F_STEP] > p[PI_F_MAXSTEP]):
            raise ValueError ('Some specified steps bigger than specified maxsteps.')

        if N.any (p[PI_F_LLIMIT] > p[PI_F_ULIMIT]):
            raise ValueError ('Some param lower limits > upper limits.')

        if N.any (p[PI_F_VALUE] < p[PI_F_LLIMIT]):
            raise ValueError ('Some param values < lower limits.')

        if N.any (p[PI_F_VALUE] > p[PI_F_ULIMIT]):
            raise ValueError ('Some param values < lower limits.')

        p = self._pinfoo

        if not N.all ([x is None or callable (x) for x in p[PI_O_TIED]]):
            raise ValueError ('Some tied values not None or callable.')

        nfix = N.where (N.logical_or ([x is not None for x in p[PI_O_TIED]],
                                      self._getBits (PI_M_FIXED)))[0].size

        if self._nout < self._npar - nfix:
            raise RuntimeError ('Too many free parameters.')

        # Finally, compute useful arrays.

        qtied = N.asarray ([x is not None for x in self._pinfoo[PI_O_TIED]])
        self._qanytied = N.any (qtied)

        # A tied parameter is effectively fixed.
        qfixed = self._getBits (PI_M_FIXED) | qtied
        self._ifree = N.where (-qfixed)[0]

    def copy (self):
        n = Problem (self._func, self._npar, self._nout, self.solclass)

        if self._pinfof is not None:
            n._pinfof = self._pinfof.copy ()
            n._pinfob = self._pinfob.copy ()
            n._pinfoo = self._pinfoo.copy ()

        if self.diag is not None:
            n.diag = self.diag.copy ()

        n.ftol = self.ftol
        n.xtol = self.xtol
        n.gtol = self.gtol
        n.damp = self.damp
        n.factor = self.factor
        n.epsfunc = self.epsfunc
        n.maxiter = self.maxiter
        n.nprint = self.nprint
        n.nocovar = self.nocovar
        n.fastnorm = self.fastnorm
        n.rescale = self.rescale
        n.autoderivative = self.autoderivative
        n.quiet = self.quiet
        n.debugCalls = self.debugCalls
        n.debugJac = self.debugJac

        return n


    def _setBit (self, idx, mask, cond):
        p = self._pinfob
        p[idx] = (p[idx] & ~mask) | N.where (cond, mask, 0x0)


    def _getBits (self, mask):
        return N.where (self._pinfob & mask, True, False)


    def pValue (self, idx, value, fixed=False):
        if N.any (N.isinf (value)):
            raise ValueError ('value')
        
        self._pinfof[PI_F_VALUE,idx] = value
        self._setBit (idx, PI_M_FIXED, fixed)
        return self


    def pLimit (self, idx, lower=-N.inf, upper=N.inf):
        if N.any (lower > upper):
            raise ValueError ('lower/upper')

        self._pinfof[PI_F_LLIMIT,idx] = lower
        self._pinfof[PI_F_ULIMIT,idx] = upper

        # Try to be clever here.
        w = N.where (lower == upper)
        self.pValue (w, lower[w], True)

        return self


    def pStep (self, idx, step, maxstep=N.inf, isrel=False):
        if N.any (N.isinf (step)):
            raise ValueError ('step')
        if N.any (step > maxstep):
            raise ValueError ('step > maxstep')

        self._pinfof[PI_F_STEP,idx] = step
        self._pinfof[PI_F_MAXSTEP,idx] = maxstep
        self._setBit (idx, PI_M_RELSTEP, isrel)
        return self


    def pSide (self, idx, mode):
        if N.any (mode < 0 or mode > 3):
            raise ValueError ('mode')
    
        p = self._pinfob
        p[idx] = (p[idx] & ~PI_M_SIDE) | mode
        return self
        

    def pPrint (self, idx, doprint):
        self._setBit (idx, PI_M_PRINT, doprint)
        return self


    def pTie (self, idx, tiefunc):
        t1 = N.atleast_1d (tiefunc)
        if not N.all ([x is None or callable (x) for x in t1]):
            raise ValueError ('tiefunc')

        self._pinfoo[PI_O_TIED,idx] = tiefunc
        return self


    def pName (self, idx, name):
        self._pinfoo[PI_O_NAME,idx] = name
        return self


    def pNames (self, *names):
        if len (names) != self.npar:
            raise ValueError ('names')

        self._pinfoo[PI_O_NAME] = names
        return self

    
    def _call (self, x, vec, jac):
        if self._qanytied:
            self._doTies (x)

        self.nfev += 1

        if self.debugCalls:
            print 'Call: #%4d f(%s) ->' % (self.nfev, x),
        self._func (x, vec, jac)
        if self.debugCalls:
            print vec, jac

        if self.damp > 0:
            N.tanh (vec / self.damp, vec)


    def solve (self, x0=None, dtype=N.float):
        if x0 is not None:
            x0 = N.asarray (x0, dtype=dtype)

        finfo = N.finfo (dtype)

        self._fixupCheck ()
        ifree = self._ifree
        self.fnorm = fnorm1 = -1.

        soln = self.solclass (self)

        # Steps for numerical derivatives
        isrel = self._getBits (PI_M_RELSTEP)
        dside = self._getBits (PI_M_SIDE)
        maxstep = self._pinfof[PI_F_MAXSTEP]
        qmax = N.isfinite (maxstep)
        qminmax = N.any (qmax)

        # Which parameters are actually free?
        nfree = ifree.size

        if nfree == 0:
            raise ValueError ('No free parameters in problem specification')

        self.params = x0.copy ()
        x = x0[ifree]

        # Which parameters have limits?

        qulim = N.where (N.isfinite (self._pinfof[PI_F_ULIMIT,ifree]))
        ulim = self._pinfof[PI_F_ULIMIT,ifree]
        qllim = N.where (N.isfinite (self._pinfof[PI_F_LLIMIT,ifree]))
        llim = self._pinfof[PI_F_LLIMIT,ifree]
        qanylim = len (qulim[0]) + len (qllim[0]) > 0

        # Init fnorm

        if self.fastnorm:
            _enorm = _enorm_fast
        else:
            _enorm = _enorm_careful

        self._enorm = _enorm
        n = nfree
        fvec = N.ndarray (self._nout, x0.dtype)
        call = self._call

        call (self.params, fvec, None)

        self.fnorm = _enorm (fvec, finfo)

        # Initialize Levenberg-Marquardt parameter and
        # iteration counter.

        par = 0.
        self.niter = 1
        qtf = x * 0.
        status = 0
        
        # Outer loop top.

        while True:
            self.params[ifree] = x

            if self._qanytied:
                self._doTies (self.params)

            # Print out during this iteration?

            if self.nprint > 0: # and iterfunct is not None
                # Blah ...
                pass

            # Calculate the Jacobian

            fjac = self._fdjac2 (x, fvec, ulim, dside, x0, isrel, finfo)

            if qanylim:
                # Check for parameters pegged at limits
                whlpeg = N.where (qllim & (x == llim))
                nlpeg = len (whlpeg[0])
                whupeg = N.where (qulim & (x == ulim))
                nupeg = len (whupeg[0])

                if nlpeg > 0:
                    # Check total derivative of sum wrt lower-pegged params
                    for i in xrange (nlpeg):
                        if N.dot (fvec, fjac[:,whlpeg[0][i]]) > 0:
                            fjac[:,whlpeg[i]] = 0
                if nupeg > 0:
                    for i in xrange (nupeg):
                        if N.dot (fvec, fjac[:,whupeg[0][i]]) < 0:
                            fjac[:,whupeg[i]] = 0

            # Compute QR factorization of the Jacobian

            fjac, ipvt, wa1, wa2 = self.qrfac (fjac, finfo)

            if self.niter == 1:
                # If "diag" unspecified, scale according to norms of columns
                # of the initial jacobian
                if not self.rescale or len (diag) < n:
                    diag = wa2.copy ()
                    diag[N.where (diag == 0)] = 1.

                # Calculate norm of scaled x, initialize step bound delta
                wa3 = diag * x
                xnorm = _enorm (wa3, finfo)
                delta = self.factor * xnorm
                if delta == 0.:
                    delta = self.factor

            # Compute (q.T) * fvec, store the first n components in qtf

            wa4 = fvec.copy ()

            for j in xrange (n):
                lj = ipvt[j]
                temp3 = fjac[j,lj]
                if temp3 != 0:
                    fj = fjac[j:,lj]
                    wj = wa4[j:len (wa4)]
                    wa4[j:len (wa4)] = wj - fj * N.dot (fj, wj) / temp3
                fjac[j,lj] = wa1[j]
                qtf[j] = wa4[j]

            # "From this point on, only the square matrix consisting of
            # the triangle of R is needed."

            fjac = fjac[:n,:n]
            temp = fjac.copy ()
            for i in xrange (n):
                temp[:,i] = fjac[:,ipvt[i]]
            fjac = temp.copy ()

            # "Check for overflow. This should be a cheap test here
            # since fjac has been reduced to a small square matrix."

            if N.any (-N.isfinite (fjac)):
                raise RuntimeError ('Nonfinite terms in Jacobian matrix!')

            # Calculate the norm of the scaled gradient

            gnorm = 0.
            if self.fnorm != 0:
                for j in xrange (n):
                    l = ipvt[j]
                    if wa2[l] != 0:
                        s = N.dot (fjac[:j+1,j], qtf[:j+1]) / self.fnorm
                        gnorm = max (gnorm, abs (s / wa2[l]))

            # Test for convergence of gradient norm

            if gnorm <= self.gtol:
                status = 4
                break

            if not self.rescale:
                diag = N.where (diag > wa2, diag, wa2)

            # Inner loop
            while True:
                # Get Levenberg-Marquardt parameter
                fjac, par, wa1, wa2 = self.lmpar (fjac, ipvt, diag, qtf, delta,
                                                  wa1, wa2, par, finfo)
                # "Store the direction p and x+p. Calculate the norm of p"
                wa1 = -wa1

                if not qanylim and not qminmax:
                    # No limits applied, so just move to new position
                    alpha = 1.
                    wa2 = x + wa1
                else:
                    # We have to respect parameter limits.
                    alpha = 1.

                    if qanylim:
                        if nlpeg > 0:
                            wa1[whlpeg] = N.clip (wa1[whlpeg], 0., max (wa1))
                        if nupeg > 0:
                            wa1[whupeg] = N.clip (wa1[whupeg], min (wa1), 0.)

                        dwa1 = abs (wa1) > finfo.eps
                        whl = N.where ((dwa1 != 0.) & qllim & ((x + wa1) < llim))

                        if len (whl[0]) > 0:
                            t = (llim[whl] - x[whl]) / wa1[whl]
                            alpha = min (alpha, t.min ())

                        whu = N.where ((dwa1 != 0.) & qulim & ((x + wa1) > ulim))

                        if len (whu[0]) > 0:
                            t = (ulim[whu] - x[whu]) / wa1[whu]
                            alpha = min (alpha, t.min ())

                    # Obey max step values
                    if qminmax:
                        nwa1 = wa1 * alpha
                        whmax = N.where (qmax)
                        if len (whmax[0]) > 0:
                            mrat = (nwa1[whmax] / maxstep[whmax]).max ()
                            if mrat > 1:
                                alpha /= mrat

                    # Scale resulting vector
                    wa1 = wa1 * alpha
                    wa2 = x + wa1

                    # Adjust final output values: if we're supposed to be
                    # exactly on a boundary, make it exact.
                    wh = N.where (qulim & (wa2 >= ulim * (1 - finfo.eps)))
                    if len (wh[0]) > 0:
                        wa2[wh] = ulim[wh]
                    wh = N.where (qllim & (wa2 <= llim * (1 + finfo.eps)))
                    if len (wh[0]) > 0:
                        wa2[wh] = llim[wh]

                wa3 = diag * wa1
                pnorm = _enorm (wa3, finfo)

                # On first iter, also adjust initial step bound
                if self.niter == 1:
                    delta = min (delta, pnorm)

                self.params[ifree] = wa2

                # Evaluate func at x + p and calculate norm

                mperr = 0
                call (self.params, wa4, None)
                fnorm1 = _enorm (wa4, finfo)

                # Compute scaled actual reductions

                actred = -1.
                if 0.1 * fnorm1 < self.fnorm:
                    actred = -(fnorm1 / self.fnorm)**2 + 1

                # Compute scaled predicted reduction and scaled directional
                # derivative

                for j in xrange (n):
                    wa3[j] = 0
                    wa3[0:j+1] = wa3[0:j+1] + fjac[0:j+1,j] * wa1[ipvt[j]]

                # "Remember, alpha is the fraction of the full LM step actually
                # taken."

                temp1 = _enorm (alpha * wa3, finfo) / self.fnorm
                temp2 = N.sqrt (alpha * par) * pnorm / self.fnorm
                prered = temp1**2 + 0.5 * temp2**2
                dirder = -(temp1**2 + temp2**2)

                # Compute ratio of the actual to the predicted reduction.
                ratio = 0.
                if prered != 0:
                    ratio = actred / prered

                # Update the step bound

                if ratio <= 0.25:
                    if actred >= 0:
                        temp = 0.5
                    else:
                        temp = 0.5 * dirder / (dider + 0.5 * actred)

                    if 0.1 * fnorm1 >= self.fnorm or temp < 0.1:
                        temp = 0.1

                    delta = temp * min (delta, pnorm / 0.1)
                    par /= temp
                elif par == 0 or ratio >= 0.75:
                    delta = pnorm / 0.5
                    par *= 0.5

                if ratio >= 0.0001:
                    # Successful iteration.
                    x = wa2
                    wa2 = diag * x
                    fvec = wa4
                    xnorm = _enorm (wa2, finfo)
                    self.fnorm = fnorm1
                    self.niter += 1

                # Check for convergence

                if abs (actred) <= self.ftol and prered <= self.ftol and 0.5 * ratio <= 1:
                    status = 1
                    break
                if delta <= self.xtol * xnorm:
                    status = 2
                    break
                # If both, status = 3

                # Check for termination, "stringent tolerances"
                if self.niter >= self.maxiter:
                    status = 5
                    break
                if abs (actred) <= finfo.eps and prered <= finfo.eps and 0.5 * ratio <= 1:
                    status = 6
                    break
                if delta <= finfo.eps * xnorm:
                    status = 7
                    break
                if gnorm <= finfo.eps:
                    status = 8
                    break

                # Repeat loop if iteration unsuccessful
                if ratio >= 0.0001:
                    break

            if status != 0:
                break

            # Check for overflow
            if N.any (-N.isfinite (wa1) | -N.isfinite (wa2) | -N.isfinite (x)):
                raise RuntimeError ('Overflow in wa1, wa2, or x!')

        # End outer loop.

        if len (self.params) == 0:
            return -1

        if nfree == 0:
            self.params = x0.copy ()
        else:
            self.params[ifree] = x

        if self.nprint > 0: # and self.status > 0
            call (self.params, fvec, None)
            self.fnorm = _enorm (fvec, finfo)

        if self.fnorm is not None and fnorm1 is not None:
            self.fnorm = max (self.fnorm, fnorm1)
            self.fnorm **= 2

        self.covar = self.perror = None

        # "(very carefully) set the covariance matrix covar"

        if (not self.nocovar and n is not None and fjac is not None and
            ipvt is not None): # and status > 0
            sz = fjac.shape

            if n > 0 and sz[0] >= n and sz[1] >= n and len (ipvt) >= n:
                cv = self.calc_covar (fjac[:n,:n], ipvt[:n])
                cv.shape = (n, n)
                nn = len (x0)

                # Fill in actual matrix, accounting for fixed params
                self.covar = N.zeros ((nn, nn), dtype)
                for i in xrange (n):
                    self.covar[ifree[i],ifree] = cv[i]
                ##    indices = ifree[0] + ifree[0][i] * n
                ##    self.covar[indices] = cv[:,i]

                # Compute errors in parameters
                self.perror = N.zeros (nn, dtype)
                d = self.covar.diagonal ()
                wh = N.where (d >= 0)
                self.perror[wh] = N.sqrt (d[wh])

        soln.status = status
        soln.params = self.params
        soln.covar = self.covar
        soln.perror = self.perror
        soln.fnorm = self.fnorm
        soln.fvec = fvec
        soln.fjac = fjac

        return soln

    def _fdjac2 (self, x, fvec, ulimit, dside, xall, isrel, finfo):
        ifree = self._ifree
        debug = self.debugJac
        machep = finfo.eps
        nall = len (xall)

        if self.epsfunc is None:
            eps = machep
        else:
            eps = self.epsfunc
        eps = N.sqrt (max (eps, machep))
        m = len (fvec)
        n = len (x)

        if not self.autoderivative:
            # Easy, analytic-derivative case.
            fjac = N.zeros (nall, finfo.dtype)
            fjac[ifree] = 1.0
            self._call (xall, fp, fjac)

            # "This definition is consistent with CURVEFIT."
            assert fjac.shape == (m, nall)
            fjac = -fjac

            if len (ifree) < nall:
                fjac = fjac[:,ifree]
                return fjac

        fjac = N.zeros ((m, n), finfo.dtype)
        h = eps * N.abs (x)

        # Apply any fixed steps, absolute and relative.
        stepi = self._pinfof[PI_F_STEP,ifree]
        wh = N.where (stepi > 0)
        h[wh] = stepi[wh] * N.where (isrel[ifree[wh]], x[wh], 1.)

        # Make sure no zero step values
        h[N.where (h == 0)] = eps

        # Reverse sign of step if against a parameter limit or if
        # backwards-sided derivative

        mask = dside == -1
        if ulimit is not None:
            mask |= x > ulimit - h
            wh = N.where (mask)
            h[wh] = -h[wh]

        if debug:
            print 'Jac-:', h

        # Compute derivative for each parameter

        for j in xrange (n):
            xp = xall.copy ()
            xp[ifree[j]] += h[j]
            fp = N.empty (self._nout, dtype=finfo.dtype)
            self._call (xp, fp, None)

            if abs (dside[j]) <= 1:
                # One-sided derivative
                fjac[:,j] = (fp - fvec) / h[j]
            else:
                # Two-sided ... extra func call
                xp[ifree[j]] = xall[ifree[j]] - h[j]
                fm = N.empty (self._nout, dtype=finfo.dtype)
                self._call (xp, fm, None)
                fjac[:,j] = (fp - fm) / (2 * h[j])

        if debug:
            for i in xrange (m):
                print 'Jac :', fjac[i]
        return fjac

    def _manual_fdjac2 (self, xall, dtype=N.float):
        self._fixupCheck ()

        ifree = self._ifree
        
        xall = N.atleast_1d (N.asarray (xall, dtype))
        x = xall[ifree]
        fvec = N.empty (self._nout, dtype)
        ulimit = self._pinfof[PI_F_ULIMIT,ifree]
        dside = self._getBits (PI_M_SIDE)
        isrel = self._getBits (PI_M_RELSTEP)
        finfo = N.finfo (dtype)

        # Before we can evaluate the Jacobian, we need
        # to get the initial value of the function at
        # the specified position.

        self._call (x, fvec, None)
        return self._fdjac2 (x, fvec, ulimit, dside, xall, isrel, finfo)
        
    def qrfac (self, a, finfo):
        # Hardwired to pivot=True since it always is in this code
        machep = finfo.eps
        m, n = a.shape

        acnorm = N.zeros (n, finfo.dtype)
        for j in xrange (n):
            acnorm[j] = self._enorm (a[:,j], finfo)
        rdiag = acnorm.copy ()
        wa = rdiag.copy ()
        ipvt = N.arange (n)

        # "Reduce a to r with Householder transformations."
        minmn = min (m, n)
        for j in xrange (minmn):
            # "Bring the column of the largest norm into the pivot position."
            rmax = rdiag[j:len(rdiag)].max ()
            kmax = N.where (rdiag[j:len(rdiag)] == rmax)
            ct = len (kmax[0])
            kmax[0][:] += j
            if ct > 0:
                kmax = kmax[0]
                    
                # "Exchange rows via the pivot only.  Avoid actually exchanging
                # the rows, in case there is lots of memory transfer.  The
                # exchange occurs later, within the body of MPFIT, after the
                # extraneous columns of the matrix have been shed."
                
                if kmax != j:
                    temp = ipvt[j]
                    ipvt[j] = ipvt[kmax]
                    ipvt[kmax] = temp
                    rdiag[kmax] = rdiag[j]
                    wa[kmax] = wa[j]

            # "Compute the Householder transformation to reduce the jth
            # column of A to a multiple of the jth unit vector."
            lj = ipvt[j]
            ajj = a[j:,lj]
            ajnorm = self._enorm (ajj, finfo)

            if ajnorm == 0:
                break
            if a[j,j] < 0:
                ajnorm = -ajnorm

            ajj /= ajnorm
            ajj[0] += 1
            a[j:,lj] = ajj

            # "Apply the transformation to the remaining columns and
            # update the norms."

            if j + 1 < n:
                for k in xrange (j + 1, n):
                    lk = ipvt[k]
                    ajk = a[j:,lk]
                    if a[j,lj] != 0:
                        a[j:,lk] = ajk - ajj * N.dot (ajk, ajj) / a[j,lj]
                        if rdiag[k] != 0:
                            temp = a[j,lk] / rdiag[k]
                            rdiag[k] *= N.sqrt (max (1 - temp**2, 0))
                            temp = rdiag[k] / wa[k]

                            if 0.05 * temp**2 <= machep:
                                rdiag[k] = self._enorm (a[j+1:,lk], finfo)
                                wa[k] = rdiag[k]

            rdiag[j] = -ajnorm

        return a, ipvt, rdiag, acnorm


    def qrsolv (self, r, ipvt, diag, qtb, sdiag):
        m, n = r.shape

        # "Copy r and (q.T)*b to preserve input and initialize s.
        # In particular, save the diagonal elements of r in x.

        for j in xrange (n):
            r[j:n,j] = r[j,j:n]
        x = r.diagonal ()
        wa = qtb.copy ()

        # "Eliminate the diagonal matrix d using a Givens rotation."

        for j in xrange (n):
            l = ipvt[j]
            if diag[l] == 0:
                break
            sdiag[j:len(sdiag)] = 0
            sdiag[j] = diag[l]

            # "The transformations to eliminate the row of d modify only a
            # single element of (q transpose)*b beyond the first n, which
            # is initially zero."

            qtbpj = 0.

            for k in xrange (j, n):
                if sdiag[k] == 0:
                    break

                if abs (r[k,k]) < abs (sdiag[k]):
                    cotan = r[k,k] / sdiag[k]
                    sine = 0.5 / N.sqrt (0.25 + 0.25 * cotan**2)
                    cosine = sine * cotan
                else:
                    tang = sdiag[k] / r[k,k]
                    cosine = 0.5 / N.sqrt (0.25 + 0.25 * tang**2)
                    sine = cosine * tang

                # "Compute the modified diagonal element of r and the
                # modified element of ((q transpose)*b,0)."
                r[k,k] = cosine * r[k,k] + sine * sdiag[k]
                temp = cosine * wa[k] + sine * qtbpj
                qtbpj = -sine * wa[k] + cosine * qtbpj
                wa[k] = temp

                # Accumulate the transformation in the row of s
                if n > k + 1:
                    temp = cosine * r[k+1:n,k] + sine * sdiag[k+1:n]
                    sdiag[k+1:n] = -sine * r[k+1:n,k] + cosine * sdiag[k+1:n]
                    r[k+1:n,k] = temp

            sdiag[j] = r[j,j]
            r[j,j] = x[j]

        # "Solve the triangular system for z.  If the system is singular
        # then obtain a least squares solution."

        nsing = n
        wh = N.where (sdiag == 0)
        if len (wh[0]) > 0:
            nsing = wh[0][0]
            wa[nsing:] = 0
            
        if nsing >= 1:
            wa[nsing-1] /= sdiag[nsing-1] # Degenerate c ase
            # "Reverse loop"
            for j in xrange (nsing - 2, -1, -1):
                s = N.dot (r[j+1:nsing,j], wa[j+1:nsing])
                wa[j] = (wa[j] - s) / sdiag[j]

        # "Permute the components of z back to components of x
        x[ipvt] = wa
        return r, x, sdiag


    def lmpar (self, r, ipvt, diag, qtb, delta, x, sdiag, par, finfo):
        dwarf = finfo.tiny
        m, n = r.shape

        # "Compute and store x in the Gauss-Newton direction. If
        # the Jacobian is rank-deficient, obtain a least-squares
        # solution.

        nsing = n
        wa1 = qtb.copy ()
        wh = N.where (r.diagonal () == 0)
        if len (wh[0]) > 0:
            nsing = wh[0][0]
            wa1[wh[0][0]:] = 0
        if nsing > 1:
            # "Reverse loop"
            for j in xrange (nsing - 1, -1, -1):
                wa1[j] /= r[j,j]
                if j - 1 >= 0:
                    wa1[:j] -= r[:j,j] * wa1[j]

        # "Note: ipvt here is a permutation array."
        x[ipvt] = wa1

        # "Initialize the iteration counter.  Evaluate the function at the
        # origin, and test for acceptance of the gauss-newton direction"
        iterct = 0
        wa2 = diag * x
        dxnorm = self._enorm (wa2, finfo)
        fp = dxnorm - delta
        if fp <= 0.1 * delta:
            return r, 0, x, sdiag

        # "If the Jacobian is not rank deficient, the Newton step provides a
        # lower bound, parl, for the zero of the function.  Otherwise set
        # this bound to zero."
      
        parl = 0.
        
        if nsing >= n:
            wa1 = diag[ipvt] * wa2[ipvt] / dxnorm
            wa1[0] /= r[0,0] # Degenerate case 
            for j in xrange (1, n):
                s = N.dot (r[:j,j], wa1[:j])
                wa1[j] = (wa1[j] - s) / r[j,j]

            temp = self._enorm (wa1, finfo)
            parl = fp / delta / temp**2

        # "Calculate an upper bound, paru, for the zero of the function."

        for j in xrange (n):
            s = N.dot (r[:j+1,j], qtb[:j+1])
            wa1[j] = s / diag[ipvt[j]]
        gnorm = self._enorm (wa1, finfo)
        paru = gnorm / delta
        if paru == 0:
            paru = dwarf / min (delta, 0.1)

        par = N.clip (par, parl, paru)
        if par == 0:
            par = gnorm / dxnorm

        # Begin iteration
        while True:
            iterct += 1

            # Evaluate at current value of par.
            if par == 0:
                par = max (dwarf, paru * 0.001)

            temp = N.sqrt (par)
            wa1 = temp * diag
            r, x, sdiag = self.qrsolv (r, ipvt, wa1, qtb, sdiag)
            wa2 = diag * x
            dxnorm = self._enorm (wa2, finfo)
            temp = fp
            fp = dxnorm - delta

            if (abs (fp) < 0.1 * delta or (parl == 0 and fp <= temp and temp < 0) or
                iter == 10):
                break

            # "Compute the Newton correction."
            wa1 = diag[ipvt] * wa2[ipvt] / dxnorm

            for j in xrange (n - 1):
                wa1[j] /= sdiag[j]
                wa1[j+1:n] -= r[j+1:n,j] * wa1[j]
            wa1[n-1] /= siag[n-1] # degenerate case

            temp = self._enorm (wa1, finfo)
            parc = fp / delta / temp**2

            if fp > 0: parl = max (parl, par)
            elif fp < 0: paru = min (paru, par)

            # Improve estimate of par

            par = max (parl, par + parc)

        # All done
        return r, par, x, diag


    def _doTies (self, p):
        funcs = self._pinfoo[PI_O_TIED]
        
        for i in xrange (self.npar):
            if funcs[i] is not None:
                p[i] = funcs[i] (p)


    def calc_covar (self, rr, ipvt, tol=1e-14):
        n = rr.shape[0]
        assert rr.shape[1] == n

        r = rr.copy ()

        # "For the inverse of r in the full upper triangle of r"
        l = -1
        tolr = tol * abs(r[0,0])
        for k in xrange (n):
            if abs (r[k,k]) <= tolr:
                break
            r[k,k] = 1. / r[k,k]
            
            for j in xrange (k):
                temp = r[k,k] * r[j,k]
                r[j,k] = 0.
                r[0:j+1,k] -= temp * r[0:j+1,j]

            l = k

        # "Form the full upper triangle of the inverse of (r transpose)*r
        # in the full upper triangle of r"

        if l >= 0:
            for k in xrange (l + 1):
                for j in xrange (k):
                    temp = r[j,k]
                    r[0:j+1,j] += temp * r[0:j+1,k]
                temp = r[k,k]
                r[0:k+1,k] *= temp

        # "For the full lower triangle of the covariance matrix
        # in the strict lower triangle or and in wa"
        
        wa = N.repeat ([r[0,0]], n)
        
        for j in xrange (n):
            jj = ipvt[j]
            sing = j > l
            for i in xrange (j + 1):
                if sing:
                    r[i,j] = 0.
                ii = ipvt[i]
                if ii > jj: r[ii,jj] = r[i,j]
                elif ii < jj: r[jj,ii] = r[i,j]
            wa[jj] = r[j,j]

        # "Symmetrize the covariance matrix in r"
        
        for j in xrange (n):
            r[:j+1,j] = r[j,:j+1]
            r[j,j] = wa[j]

        return r

def ResidualProblem (func, npar, x, yobs, err, solclass=Solution):
    from numpy import subtract, multiply

    errinv = 1. / err

    # FIXME: handle x.ndim != 1, yobs.ndim != 1

    def wrap (pars, nresids, jac):
        func (pars, x, nresids) # model Y values => nresids
        subtract (yobs, nresids, nresids) # abs. residuals => nresids
        multiply (nresids, errinv, nresids)

    return Problem (wrap, npar, x.size, solclass)


# Test!

@test
def _solve_linear ():
    x = N.asarray ([1, 2, 3])
    y = 2 * x + 1

    from numpy import multiply, add
    
    def f (pars, x, ymodel):
        multiply (x, pars[0], ymodel)
        add (ymodel, pars[1], ymodel)

    p = ResidualProblem (f, 2, x, y, 0.01)
    return p.solve ([2.5, 1.5])

@test
def _simple_automatic_jac ():
    from numpy.testing import assert_array_almost_equal as aaae

    def f (pars, vec, jac):
        N.exp (pars, vec)

    p = Problem (f, 1, 1)
    j = p._manual_fdjac2 (0) 
    aaae (j, [[1.]])
    j = p._manual_fdjac2 (1) 
    aaae (j, [[N.e]])

    p = Problem (f, 3, 3)
    x = N.asarray ([0, 1, 2])
    j = p._manual_fdjac2 (x) 
    aaae (j, N.diag (N.exp (x)))

# Finally ...

if __name__ == '__main__':
    _runtests ()

