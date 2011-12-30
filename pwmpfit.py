"""pwmpfit - Pythonic, Numpy-based port of MPFIT.
"""

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
        print f.__name__, '...'
        f ()

from numpy.testing import assert_array_almost_equal as Taaae
from numpy.testing import assert_almost_equal as Taae


# Public constants

DSIDE_AUTO = 0x0
DSIDE_POS  = 0x1
DSIDE_NEG  = 0x2
DSIDE_TWO  = 0x3


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


# Euclidean norm-calculating functions. Apparently the "careful" norm
# calculator can be slow, while the "fast" version can be susceptible
# to under- or overflows.

_enorm_fast = lambda v, finfo: N.sqrt (N.dot (v, v))

def _enorm_careful (v, finfo):
    #if v.size == 0:
    #    return 0.

    agiant = finfo.max / v.size
    adwarf = finfo.tiny * v.size

    # "This is hopefully a compromise between speed and robustness.
    # Need to do this because of the possibility of over- or under-
    # flow.
    
    mx = max (abs (v.max ()), abs (v.min ()))
    
    if mx == 0:
        return v[0] * 0. # preserve type (?)
    if mx > agiant or mx < adwarf:
        return mx * N.sqrt (N.dot (v / mx, v / mx))
    
    return N.sqrt (N.dot (v, v))


# Q-R factorization.

def _qr_factor_packed (a, enorm, finfo):
    """Compute the packed pivoting Q-R factorization of a matrix.

Parameters:
a     - An m-by-n matrix, m >= n. This will be *overwritten* 
        by this function as described below!
enorm - A Euclidian-norm-computing function.
finfo - A Numpy finfo object.

Returns:
pmut   - An n-element permutation vector
rdiag  - An n-element vector of the diagonal of R
acnorm - An n-element vector of the norms of the columns
         of the input matrix 'a'.

Computes the Q-R factorization of the matrix 'a', with pivoting, in a
packed form, in-place. The packed information can be used to construct
matrices q and r such that

  N.dot (q, r) = a[:,pmut]

where q is m-by-m and q q^T = ident and r is m-by-n and is upper
triangular.  The function _qr_factor_full can compute these
matrices. The packed form of output is all that is used by the main LM
fitting algorithm.

"Pivoting" refers to permuting the columns of 'a' to have their norms
in nonincreasing order. The return value 'pmut' maps the unpermuted
columns of 'a' to permuted columns. That is, the norms of the columns
of a[:,pmut] are in nonincreasing order.

The parameter 'a' is overwritten by this function. Its new value
should still be interpreted as an m-by-n array. It comes in two
parts. Its strict upper triangular part contains the strict upper
triangular part of R. (The diagonal of R is returned in 'rdiag' and
the strict lower trapezoidal part of R is zero.) The lower trapezoidal
part of 'a' contains Q as factorized into a series of Householder
transformation vectors. Q can be reconstructed as the matrix product
of n Householder matrices, where the i'th Householder matrix is
defined by

H_i = I - 2 (v^T v) / (v v^T)

where 'v' is the pmut[i]'th column of 'a' with its strict upper
triangular part set to zero. See _qr_factor_full for more information.

'rdiag' contains the diagonal part of the R matrix, taking into
account the permutation of 'a'. The strict upper triangular part of R
is stored in 'a' *with permutation*, so that the i'th column of R has
rdiag[i] as its diagonal and a[:i,pmut[i]] as its upper part. See
_qr_factor_full for more information.

'acnorm' contains the norms of the columns of the original input
matrix 'a' without permutation.

The form of this transformation and the method of pivoting first
appeared in Linpack."""

    machep = finfo.eps
    m, n = a.shape

    if m < n:
        raise ValueError ('a must be at least as tall as it is wide')

    # Initialize our various arrays.

    acnorm = N.empty (n, finfo.dtype)
    for j in xrange (n):
        acnorm[j] = enorm (a[:,j], finfo)

    rdiag = acnorm.copy ()
    wa = rdiag.copy ()

    pmut = N.arange (n)

    # Start the computation.

    for i in xrange (n):
        # Find the column of a with the i'th largest norm,
        # and note it in the pivot vector.

        kmax = rdiag[i:].argmax () + i

        if kmax != i:
            temp = pmut[i]
            pmut[i] = pmut[kmax]
            pmut[kmax] = temp
            rdiag[kmax] = rdiag[i]
            wa[kmax] = wa[i]

        # "Compute the Householder transformation to reduce the i'th
        # column of A to a multiple of the i'th unit vector."

        li = pmut[i]
        aii = a[i:,li] # note that modifying aii modifies a
        ainorm = enorm (aii, finfo)

        if ainorm == 0:
            rdiag[i] = 0
            continue

        if a[i,li] < 0:
            # Doing this apparently improves FP precision somehow.
            ainorm = -ainorm

        aii /= ainorm
        aii[0] += 1

        # "Apply the transformation to the remaining columns and
        # update the norms."

        for j in xrange (i + 1, n):
            lj = pmut[j]
            aij = a[i:,lj] # modifying aij modifies a as well.

            if a[i,li] != 0:
                aij -= aii * N.dot (aij, aii) / a[i,li]

            if rdiag[j] != 0:
                temp = a[i,lj] / rdiag[j]
                rdiag[j] *= N.sqrt (max (1 - temp**2, 0))
                temp = rdiag[j] / wa[j]

                if 0.05 * temp**2 <= machep:
                    # What does this do???
                    wa[j] = rdiag[j] = enorm (a[i+1:,lj], finfo)

        rdiag[i] = -ainorm

    return pmut, rdiag, acnorm


def _manual_qr_factor_packed (a, dtype=N.float):
    # This testing function gives sensible defaults to _qr_factor_packed
    # and makes a copy of its input to make comparisons easier.

    a = N.array (a, dtype)
    pmut, rdiag, acnorm = _qr_factor_packed (a, _enorm_careful, N.finfo (dtype))
    return a, pmut, rdiag, acnorm


def _qr_factor_full (a, dtype=N.float):
    """Compute the QR factorization of a matrix, with pivoting.

Parameters:
a     - An m-by-n arraylike, m >= n.
dtype - (optional) The data type to use for computations.
        Default is N.float.

Returns:
q    - An m-by-m orthogonal matrix (q q^T = ident)
r    - An m-by-n upper triangular matrix
pmut - An n-element permutation vector

The returned values will satisfy the equation

N.dot (q, r) = a[:,pmut]

The outputs are computed indirectly via the function
_qr_factor_packed. If you need to compute q and r matrices in
production code, there are faster ways to do it. This function is for
testing _qr_factor_packed.

The permutation vector pmut is a vector of the integers 0 through
n-1. It sorts the columns of 'a' by their norms, so that the
pmut[i]'th column of 'a' has the i'th biggest norm."""

    m, n = a.shape

    # Compute the packed Q and R matrix information.

    packed, pmut, rdiag, acnorm = \
        _manual_qr_factor_packed (a, dtype)

    # Now we unpack. Start with the R matrix, which is easy:
    # we just have to piece it together from the strict
    # upper triangle of 'a' and the diagonal in 'rdiag'.
    # We're working in the "permuted frame", as it were, so
    # we need to permute indices when accessing 'a', which is
    # in the "unpermuted" frame.

    r = N.zeros ((m, n))

    for i in xrange (n):
        r[:i,i] = packed[:i,pmut[i]]
        r[i,i] = rdiag[i]

    # Now the Q matrix. It is the concatenation of n Householder
    # transformations, each of which is defined by a column in the
    # lower trapezoidal portion of 'a'. We extract the appropriate
    # vector, construct the matrix for the Householder transform,
    # and build up the Q matrix.

    q = N.eye (m)
    v = N.empty (m)

    for i in xrange (n):
        v[:] = packed[:,pmut[i]]
        v[0:i] = 0
        
        hhm = N.eye (m) - 2 * N.outer (v, v) / N.dot (v, v)
        q = N.dot (q, hhm)

    return q, r, pmut


@test
def _qr_examples ():
    # This is the sample given in the comments of Craig Markwardt's
    # IDL MPFIT implementation. Our results differ because we always
    # use pivoting whereas his example didn't. But the results become
    # the same if you remove the pivoting bits.

    a = N.asarray ([[9., 4], [2, 8], [6, 7]])
    packed, pmut, rdiag, acnorm = _manual_qr_factor_packed (a)
    
    Taaae (packed, [[-8.27623852, 1.35218036],
                    [ 1.96596229, 0.70436073],
                    [ 0.25868293, 0.61631563]])
    assert pmut[0] == 1
    assert pmut[1] == 0
    Taaae (rdiag, [-11.35781669, 7.24595584])
    Taaae (acnorm, [11.0, 11.35781669])

    q, r, pmut = _qr_factor_full (a)
    Taaae (N.dot (q, r), a[:,pmut])

    # This is the sample given in Wikipedia. I know, shameful!  Once
    # again, the Wikipedia example doesn't include pivoting, but the
    # numbers work out.

    a = N.asarray ([[12., -51, 4],
                    [6, 167, -68],
                    [-4, 24, -41]])
    packed, pmut, rdiag, acnorm = _manual_qr_factor_packed (a)
    Taaae (packed, [[ 1.66803309,  1.28935268, -71.16941178],
                    [-2.18085468, -0.94748818,   1.36009392],
                    [ 2.        , -0.13616597,   0.93291606]])
    assert pmut[0] == 1
    assert pmut[1] == 2
    assert pmut[2] == 0
    Taaae (rdiag, [176.25549637, 35.43888862, 13.72812946])
    Taaae (acnorm, [14., 176.25549637, 79.50471684])

    # A sample I constructed myself analytically. I made the Q
    # from rotation matrices and chose R pretty dumbly to get a
    # nice-ish matrix following the columnar norm constraint.

    r3 = N.sqrt (3)
    a = N.asarray ([[-3 * r3, 3 * r3],
                    [7, 9],
                    [-2, -6]])
    q, r, pmut = _qr_factor_full (a)

    r *= N.sign (q[0,0])
    for i in xrange (3):
        # Normalize signs.
        q[:,i] *= (-1)**i * N.sign (q[0,i])

    assert pmut[0] == 1
    assert pmut[1] == 0

    Taaae (q, 0.25 * N.asarray ([[r3, -2 * r3, 1],
                                 [3, 2, r3], 
                                 [-2, 0, 2 * r3]]))
    Taaae (r, N.asarray ([[12, 4],
                          [0, 8],
                          [0, 0]]))
    Taaae (N.dot (q, r), a[:,pmut])


# QR solution.

def _qrd_solve (r, pmut, ddiag, qtb, sdiag):
    """Solve an equation given a QR factored matrix and a diagonal.

Parameters:
r     - n-by-n in-out array. The full upper triangle contains the full
        upper triangle of R. On output, the strict lower triangle
        contains the transpose of the strict upper triangle of
        S.
pmut  - n-vector describing the permutation matrix P.
ddiag - n-vector containing the diagonal of the matrix D in the base 
        problem (see below).
qtb   - n-vector containing the first n elements of Q^T B.
sdiag - output n-vector. It is filled with the diagonal of S. Should
        be preallocated by the caller -- can result in somewhat greater
        efficiency if the vector is reused from one call to the next.

Returns:
x     - n-vector solving the equation.

Compute the n-vector x such that

A x = B, D x = 0

where A is an m-by-n matrix, B is an m-vector, and D is an n-by-n
diagonal matrix. We are given information about pivoted QR
factorization of A with permutation, such that

A P = Q R

where P is a permutation matrix, Q has orthogonal columns, and R is
upper triangular with nonincreasing diagonal elements. Q is m-by-m, R
is m-by-n, and P is n-by-n. If x = P z, then we need to solve

R z = Q^T B, P^T D P z = 0 (why the P^T?)

If the system is rank-deficient, these equations are solved as well as
possible in a least-squares sense. For the purposes of the LM
algorithm we also compute the upper triangular n-by-n matrix S such
that

P^T (A^T A + D D) P = S^T S.
"""

    m, n = r.shape

    # "Copy r and (q.T)*b to preserve input and initialize s.  In
    # particular, save the diagonal elements of r in x."  Recall that
    # on input only the full upper triangle of R is meaningful, so we
    # can mirror that into the lower triangle without issues.

    for i in xrange (n):
        r[i:,i] = r[i,i:]

    x = r.diagonal ()
    zwork = qtb.copy ()

    # "Eliminate the diagonal matrix d using a Givens rotation."
    
    for i in xrange (n):
        # "Prepare the row of D to be eliminated, locating the
        # diagonal element using P from the QR factorization."

        li = pmut[i]
        if ddiag[li] == 0:
            sdiag[i] = r[i,i]
            r[i,i] = x[i]
            continue

        sdiag[i:] = 0
        sdiag[i] = ddiag[li]

        # "The transformations to eliminate the row of d modify only a
        # single element of (q transpose)*b beyond the first n, which
        # is initially zero."

        qtbpi = 0.

        for j in xrange (i, n):
            # "Determine a Givens rotation which eliminates the
            # appropriate element in the current row of D."

            if sdiag[j] == 0:
                continue

            if abs (r[j,j]) < abs (sdiag[j]):
                cot = r[j,j] / sdiag[j]
                sin = 0.5 / N.sqrt (0.25 + 0.25 * cot**2)
                cos = sin * cot
            else:
                tan = sdiag[j] / r[j,j]
                cos = 0.5 / N.sqrt (0.25 + 0.25 * tan**2)
                sin = cos * tan

            # "Compute the modified diagonal element of r and the
            # modified element of ((q transpose)*b,0)."
            r[j,j] = cos * r[j,j] + sin * sdiag[j]
            temp = cos * zwork[j] + sin * qtbpi
            qtbpi = -sin * zwork[j] + cos * qtbpi
            zwork[j] = temp

            # "Accumulate the transformation in the row of s."
            if j + 1 < n:
                temp = cos * r[j+1:,j] + sin * sdiag[j+1:]
                sdiag[j+1:] = -sin * r[j+1:,j] + cos * sdiag[j+1:]
                r[j+1:,j] = temp

        # Save the diagonal of S and restore the diagonal of R
        # from its saved location in x.
        sdiag[i] = r[i,i]
        r[i,i] = x[i]

    # "Solve the triangular system for z.  If the system is singular
    # then obtain a least squares solution."

    nsing = n

    for i in xrange (n):
        if sdiag[i] == 0.:
            nsing = i
            zwork[i:] = 0
            break
            
    if nsing >= 1:
        zwork[nsing-1] /= sdiag[nsing-1] # Degenerate case
        # "Reverse loop"
        for i in xrange (nsing - 2, -1, -1):
            s = N.dot (r[i+1:nsing,i], zwork[i+1:nsing])
            zwork[i] = (zwork[i] - s) / sdiag[i]

    # "Permute the components of z back to components of x."
    x[pmut] = zwork
    return x


def _manual_qrd_solve (r, pmut, ddiag, qtb, dtype=N.float, build_s=False):
    r = N.asarray (r, dtype)
    pmut = N.asarray (pmut, N.int)
    ddiag = N.asarray (ddiag, dtype)
    qtb = N.asarray (qtb, dtype)

    swork = r.copy ()
    sdiag = N.empty (r.shape[0], r.dtype)

    x = _qrd_solve (swork, pmut, ddiag, qtb, sdiag)

    if not build_s:
        return x, swork, sdiag

    # Rebuild s.

    swork = swork.T
    for i in xrange (r.shape[0]):
        swork[i:,i] = 0
        swork[i,i] = sdiag[i]

    return x, swork


def _qrd_solve_full (a, b, ddiag, dtype=N.float):
    """Solve the equation A x = B, D x = 0.

Parameters:
a     - an m-by-n array, m >= n
b     - an m-vector
ddiag - an n-vector giving the diagonal of D. (The rest of D is 0.)

Returns:
x    - n-vector solving the equation.
s    - the n-by-n supplementary matrix s.
pmut - n-element permutation vector defining the permutation matrix P.

The equations are solved in a least-squares sense if the system is
rank-deficient.  D is a diagonal matrix and hence only its diagonal is
in fact supplied as an argument. The matrix s is full upper triangular
and solves the equation

P^T (A^T A + D D) P = S^T S

where P is the permutation matrix defined by the vector pmut; it puts
the columns of 'a' in order of nonincreasing rank, so that a[:,pmut]
has its columns sorted that way.
"""

    a = N.asarray (a, dtype)
    b = N.asarray (b, dtype)
    ddiag = N.asarray (ddiag, dtype)

    m, n = a.shape
    assert m >= n
    assert b.shape == (m, )
    assert ddiag.shape == (n, )

    # The computation is straightforward.

    q, r, pmut = _qr_factor_full (a)
    qtb = N.dot (q.T, b)
    x, s = _manual_qrd_solve (r[:n], pmut, ddiag, qtb, 
                              dtype=dtype, build_s=True)

    return x, s, pmut


@test
def _qrd_solve_alone ():
    # Testing out just the QR solution function without 
    # also the QR factorization bits.

    # The very simplest case.
    r = N.eye (2)
    pmut = N.asarray ([0, 1])
    diag = N.asarray ([0., 0])
    qtb = N.asarray ([3., 5])
    x, s = _manual_qrd_solve (r, pmut, diag, qtb, build_s=True)
    Taaae (x, [3., 5])
    Taaae (s, N.eye (2))

    # Now throw in a diagonal matrix ...
    diag = N.asarray ([2., 3.])
    x, s = _manual_qrd_solve (r, pmut, diag, qtb, build_s=True)
    Taaae (x, [0.6, 0.5])
    Taaae (s, N.sqrt (N.diag ([5, 10])))

    # And a permutation. We permute A but maintain
    # B, effectively saying x1 = 5, x2 = 3, so
    # we need to permute diag as well to scale them
    # by the amounts that yield nice X values.
    pmut = N.asarray ([1, 0])
    diag = N.asarray ([3., 2.])
    x, s = _manual_qrd_solve (r, pmut, diag, qtb, build_s=True)
    Taaae (x, [0.5, 0.6])
    Taaae (s, N.sqrt (N.diag ([5, 10])))


# Calculation of the Levenberg-Marquardt parameter

def _lmpar (r, ipvt, diag, qtb, delta, x, sdiag, par, enorm, finfo):
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
    dxnorm = enorm (wa2, finfo)
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

        temp = enorm (wa1, finfo)
        parl = fp / delta / temp**2

    # "Calculate an upper bound, paru, for the zero of the function."

    for j in xrange (n):
        s = N.dot (r[:j+1,j], qtb[:j+1])
        wa1[j] = s / diag[ipvt[j]]
    gnorm = enorm (wa1, finfo)
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
        x = _qrd_solve (r, ipvt, wa1, qtb, sdiag)
        wa2 = diag * x
        dxnorm = enorm (wa2, finfo)
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
        wa1[n-1] /= sdiag[n-1] # degenerate case

        temp = enorm (wa1, finfo)
        parc = fp / delta / temp**2

        if fp > 0: parl = max (parl, par)
        elif fp < 0: paru = min (paru, par)

        # Improve estimate of par

        par = max (parl, par + parc)

    # All done
    return r, par, x, diag


# The actual user interface to the problem-solving machinery:

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
            if self.diag is None or self.diag.shape != (self._npar, ):
                raise ValueError ('diag')
            if N.any (self.diag <= 0.):
                raise ValueError ('diag')

        p = self._pinfof

        if N.any (N.isinf (p[PI_F_VALUE])):
            raise ValueError ('Some specified initial values infinite.')
        
        if N.any (N.isinf (p[PI_F_STEP])):
            raise ValueError ('Some specified parameter steps infinite.')
        
        if N.any ((p[PI_F_STEP] > p[PI_F_MAXSTEP]) & ~self._getBits (PI_M_RELSTEP)):
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

        # Try to be clever here -- setting lower = upper
        # markes the parameter as fixed.

        w = N.where (lower == upper)
        if len (w) > 0 and w[0].size > 0:
            self.pValue (w, N.atleast_1d (lower)[w], True)

        return self


    def pStep (self, idx, step, maxstep=N.inf, isrel=False):
        if N.any (N.isinf (step)):
            raise ValueError ('step')
        if N.any ((step > maxstep) & ~isrel):
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
        if len (names) != self._npar:
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
        dside = self._pinfob & PI_M_SIDE
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

        qulim = N.isfinite (self._pinfof[PI_F_ULIMIT,ifree])
        ulim = self._pinfof[PI_F_ULIMIT,ifree]
        qllim = N.isfinite (self._pinfof[PI_F_LLIMIT,ifree])
        llim = self._pinfof[PI_F_LLIMIT,ifree]
        qanylim = N.any (qulim) or N.any (qllim)

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

            fjac = self._fdjac2 (x, fvec, ulim, dside, x0, maxstep, isrel, finfo)

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

            ipvt, wa1, wa2 = _qr_factor_packed (fjac, self._enorm, finfo)

            if self.niter == 1:
                # If "diag" unspecified, scale according to norms of columns
                # of the initial jacobian
                if self.rescale:
                    diag = self.diag.copy ()
                else:
                    diag = wa2.copy ()
                    diag[N.where (diag == 0)] = 1.

                # Calculate norm of scaled x, initialize step bound delta
                xnorm = _enorm (diag * x, finfo)
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
                fjac, par, wa1, wa2 = _lmpar (fjac, ipvt, diag, qtf, delta,
                                              wa1, wa2, par, _enorm, finfo)
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
                prered = temp1**2 + 2 * temp2**2
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
                        temp = 0.5 * dirder / (dirder + 0.5 * actred)

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
        soln.niter = self.niter
        soln.params = self.params
        soln.covar = self.covar
        soln.perror = self.perror
        soln.fnorm = self.fnorm
        soln.fvec = fvec
        soln.fjac = fjac

        return soln

    def _fdjac2 (self, x, fvec, ulimit, dside, xall, maxstep, isrel, finfo):
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
            if len (ifree) < nall:
                fjac = fjac[:,ifree]
            return fjac

        fjac = N.zeros ((m, n), finfo.dtype)
        h = eps * N.abs (x)

        # Apply any fixed steps, absolute and relative.
        stepi = self._pinfof[PI_F_STEP,ifree]
        wh = N.where (stepi > 0)
        h[wh] = stepi[wh] * N.where (isrel[ifree[wh]], x[wh], 1.)

        # Clamp stepsizes to maxstep.
        N.minimum (h, maxstep, h)

        # Make sure no zero step values
        h[N.where (h == 0)] = eps

        # Reverse sign of step if against a parameter limit or if
        # backwards-sided derivative

        mask = (dside == DSIDE_NEG)[ifree]
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

            if dside[j] != DSIDE_TWO:
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
        dside = self._pinfob & PI_M_SIDE
        maxstep = self._pinfof[PI_F_MAXSTEP]
        isrel = self._getBits (PI_M_RELSTEP)
        finfo = N.finfo (dtype)

        # Before we can evaluate the Jacobian, we need
        # to get the initial value of the function at
        # the specified position.

        self._call (x, fvec, None)
        return self._fdjac2 (x, fvec, ulimit, dside, xall, maxstep, isrel, finfo)
        

    def _doTies (self, p):
        funcs = self._pinfoo[PI_O_TIED]
        
        for i in xrange (self._npar):
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

def ResidualProblem (func, npar, x, yobs, err, solclass=Solution, reckless=False):
    from numpy import subtract, multiply

    errinv = 1. / err
    if not N.all (N.isfinite (errinv)):
        raise ValueError ('some uncertainties are zero or nonfinite')

    # FIXME: handle x.ndim != 1, yobs.ndim != 1

    if reckless:
        def wrap (pars, nresids, jac):
            func (pars, x, nresids) # model Y values => nresids
            subtract (yobs, nresids, nresids) # abs. residuals => nresids
            multiply (nresids, errinv, nresids)
    else:
        def wrap (pars, nresids, jac):
            func (pars, x, nresids)
            if not N.all (N.isfinite (nresids)):
                raise RuntimeError ('function returned nonfinite values')
            subtract (yobs, nresids, nresids)
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
    def f (pars, vec, jac):
        N.exp (pars, vec)

    p = Problem (f, 1, 1)
    j = p._manual_fdjac2 (0) 
    Taaae (j, [[1.]])
    j = p._manual_fdjac2 (1) 
    Taaae (j, [[N.e]])

    p = Problem (f, 3, 3)
    x = N.asarray ([0, 1, 2])
    j = p._manual_fdjac2 (x) 
    Taaae (j, N.diag (N.exp (x)))

@test
def _jac_sidedness ():
    # Make a function with a derivative discontinuity so we can test
    # the sidedness settings.

    def f (pars, vec, jac):
        p = pars[0]

        if p >= 0:
            vec[:] = p
        else:
            vec[:] = -p

    p = Problem (f, 1, 1)

    # Default: positive unless against upper limit.
    Taaae (p._manual_fdjac2 (0), [[1.]])

    # DSIDE_AUTO should be the default.
    p.pSide (0, DSIDE_AUTO)
    Taaae (p._manual_fdjac2 (0), [[1.]])

    # DSIDE_POS should be equivalent here.
    p.pSide (0, DSIDE_POS)
    Taaae (p._manual_fdjac2 (0), [[1.]])

    # DSIDE_NEG should get the other side of the discont.
    p.pSide (0, DSIDE_NEG)
    Taaae (p._manual_fdjac2 (0), [[-1.]])

    # DSIDE_AUTO should react to an upper limit and take
    # a negative-step derivative.
    p.pSide (0, DSIDE_AUTO)
    p.pLimit (0, upper=0)
    Taaae (p._manual_fdjac2 (0), [[-1.]])

@test
def _jac_stepsizes ():
    def f (expstep, pars, vec, jac):
        p = pars[0]

        if p != 1.:
            Taae (p, expstep)

        vec[:] = 1

    # Fixed stepsize of 1.
    p = Problem (lambda p, v, j: f (2., p, v, j), 1, 1)
    p.pStep (0, 1.)
    p._manual_fdjac2 (1)

    # Relative stepsize of 0.1
    p = Problem (lambda p, v, j: f (1.1, p, v, j), 1, 1)
    p.pStep (0, 0.1, isrel=True)
    p._manual_fdjac2 (1)

    # Fixed stepsize must be less than max stepsize.
    try:
        p = Problem (f, 2, 2)
        p.pStep ((0, 1), (1, 1), (1, 0.5))
        assert False, 'Invalid arguments accepted'
    except ValueError:
        pass

    # Maximum stepsize, made extremely small to be enforced
    # in default circumstances.
    p = Problem (lambda p, v, j: f (1 + 1e-11, p, v, j), 1, 1)
    p.pStep (0, 0.0, 1e-11)
    p._manual_fdjac2 (1)

    # Maximum stepsize and a relative stepsize
    p = Problem (lambda p, v, j: f (1.1, p, v, j), 1, 1)
    p.pStep (0, 0.5, 0.1, True)
    p._manual_fdjac2 (1)

# Finally ...

if __name__ == '__main__':
    _runtests ()

