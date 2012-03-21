"""pwmpfit - Pythonic, Numpy-based port of MPFIT.
"""

from __future__ import division
import numpy as np


# Quickie testing infrastructure

_testfuncs = []

def test (f):
    """A decorator for functions to be run as part of
    the test suite."""
    _testfuncs.append (f)
    return f

def _runtests (namefilt=None):
    for f in _testfuncs:
        if namefilt is not None and f.__name__ != namefilt:
            continue
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

_enorm_fast = lambda v, finfo: np.sqrt (np.dot (v, v))

def _enorm_careful (v, finfo):
    # "This is hopefully a compromise between speed and robustness.
    # Need to do this because of the possibility of over- or under-
    # flow."

    mx = max (abs (v.max ()), abs (v.min ()))

    if mx == 0:
        return v[0] * 0. # preserve type (?)
    if not np.isfinite (mx):
        raise ValueError ('computed nonfinite vector norm')
    if mx > finfo.max / v.size or mx < finfo.tiny * v.size:
        return mx * np.sqrt (np.dot (v / mx, v / mx))

    return np.sqrt (np.dot (v, v))


def _enorm_minpack (v, finfo):
    rdwarf = 3.834e-20
    rgiant = 1.304e19
    agiant = rgiant / v.size

    s1 = s2 = s3 = x1max = x3max = 0.

    for i in xrange (v.size):
        xabs = abs (v[i])

        if xabs > rdwarf and xabs < agiant:
            s2 += xabs**2
        elif xabs <= rdwarf:
            if xabs <= x3max:
                if xabs != 0.:
                    s3 += (xabs / x3max)**2
            else:
                s3 = 1 + s3 * (x3max / xabs)**2
                x3max = xabs
        else:
            if xabs <= x1max:
                s1 += (xabs / x1max)**2
            else:
                s1 = 1. + s1 * (x1max / xabs)**2
                x1max = xabs

    if s1 != 0.:
        return x1max * np.sqrt (s1 + (s2 / x1max) / x1max)

    if s2 == 0.:
        return x3max * np.sqrt (s3)

    if s2 >= x3max:
        return np.sqrt (s2 * (1 + (x3max / s2) * (x3max * s3)))

    return np.sqrt (x3max * ((s2 / x3max) + (x3max * s3)))


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

  np.dot (q, r) = a[:,pmut]

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

    acnorm = np.empty (n, finfo.dtype)
    for j in xrange (n):
        acnorm[j] = enorm (a[:,j], finfo)

    rdiag = acnorm.copy ()
    wa = rdiag.copy ()

    pmut = np.arange (n)

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

            temp = a[:,i].copy ()
            a[:,i] = a[:,kmax]
            a[:,kmax] = temp

        # "Compute the Householder transformation to reduce the i'th
        # column of A to a multiple of the i'th unit vector."

        ainorm = enorm (a[i:,i], finfo)

        if ainorm == 0:
            rdiag[i] = 0
            continue

        if a[i,i] < 0:
            # Doing this apparently improves FP precision somehow.
            ainorm = -ainorm

        a[i:,i] /= ainorm
        a[i,i] += 1

        # "Apply the transformation to the remaining columns and
        # update the norms."

        for j in xrange (i + 1, n):
            s = np.dot (a[i:,j], a[i:,i])
            temp = s / a[i,i]
            a[i:,j] -= a[i:,i] * temp

            if rdiag[j] != 0:
                temp = a[i,j] / rdiag[j]
                rdiag[j] *= np.sqrt (max (1 - temp**2, 0))
                temp = rdiag[j] / wa[j]

                if 0.05 * temp**2 <= machep:
                    # What does this do???
                    wa[j] = rdiag[j] = enorm (a[i+1:,j], finfo)

        rdiag[i] = -ainorm

    return pmut, rdiag, acnorm


def _manual_qr_factor_packed (a, dtype=np.float):
    # This testing function gives sensible defaults to _qr_factor_packed
    # and makes a copy of its input to make comparisons easier.

    a = np.array (a, dtype)
    pmut, rdiag, acnorm = _qr_factor_packed (a, _enorm_careful, np.finfo (dtype))
    return a, pmut, rdiag, acnorm


def _qr_factor_full (a, dtype=np.float):
    """Compute the QR factorization of a matrix, with pivoting.

Parameters:
a     - An m-by-n arraylike, m >= n.
dtype - (optional) The data type to use for computations.
        Default is np.float.

Returns:
q    - An m-by-m orthogonal matrix (q q^T = ident)
r    - An m-by-n upper triangular matrix
pmut - An n-element permutation vector

The returned values will satisfy the equation

np.dot (q, r) = a[:,pmut]

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

    r = np.zeros ((m, n))

    for i in xrange (n):
        r[:i,i] = packed[:i,i]
        r[i,i] = rdiag[i]

    # Now the Q matrix. It is the concatenation of n Householder
    # transformations, each of which is defined by a column in the
    # lower trapezoidal portion of 'a'. We extract the appropriate
    # vector, construct the matrix for the Householder transform,
    # and build up the Q matrix.

    q = np.eye (m)
    v = np.empty (m)

    for i in xrange (n):
        v[:] = packed[:,i]
        v[:i] = 0

        hhm = np.eye (m) - 2 * np.outer (v, v) / np.dot (v, v)
        q = np.dot (q, hhm)

    return q, r, pmut


@test
def _qr_examples ():
    # This is the sample given in the comments of Craig Markwardt's
    # IDL MPFIT implementation.

    a = np.asarray ([[9., 4], [2, 8], [6, 7]])
    packed, pmut, rdiag, acnorm = _manual_qr_factor_packed (a)

    Taaae (packed, [[1.35218036, -8.27623852],
                    [0.70436073,  1.96596229],
                    [0.61631563,  0.25868293]])
    assert pmut[0] == 1
    assert pmut[1] == 0
    Taaae (rdiag, [-11.35781669, 7.24595584])
    Taaae (acnorm, [11.0, 11.35781669])

    q, r, pmut = _qr_factor_full (a)
    Taaae (np.dot (q, r), a[:,pmut])

    # This is the sample given in Wikipedia. I know, shameful!

    a = np.asarray ([[12., -51, 4],
                     [6, 167, -68],
                     [-4, 24, -41]])
    packed, pmut, rdiag, acnorm = _manual_qr_factor_packed (a)
    Taaae (packed, [[ 1.28935268, -71.16941178,  1.66803309],
                    [-0.94748818,   1.36009392, -2.18085468],
                    [-0.13616597,   0.93291606,  2.]])
    assert pmut[0] == 1
    assert pmut[1] == 2
    assert pmut[2] == 0
    Taaae (rdiag, [176.25549637, 35.43888862, 13.72812946])
    Taaae (acnorm, [14., 176.25549637, 79.50471684])

    q, r, pmut = _qr_factor_full (a)
    Taaae (np.dot (q, r), a[:,pmut])

    # A sample I constructed myself analytically. I made the Q
    # from rotation matrices and chose R pretty dumbly to get a
    # nice-ish matrix following the columnar norm constraint.

    r3 = np.sqrt (3)
    a = np.asarray ([[-3 * r3, 3 * r3],
                     [7, 9],
                     [-2, -6]])
    q, r, pmut = _qr_factor_full (a)

    r *= np.sign (q[0,0])
    for i in xrange (3):
        # Normalize signs.
        q[:,i] *= (-1)**i * np.sign (q[0,i])

    assert pmut[0] == 1
    assert pmut[1] == 0

    Taaae (q, 0.25 * np.asarray ([[r3, -2 * r3, 1],
                                  [3, 2, r3],
                                  [-2, 0, 2 * r3]]))
    Taaae (r, np.asarray ([[12, 4],
                           [0, 8],
                           [0, 0]]))
    Taaae (np.dot (q, r), a[:,pmut])


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
                sin = 0.5 / np.sqrt (0.25 + 0.25 * cot**2)
                cos = sin * cot
            else:
                tan = sdiag[j] / r[j,j]
                cos = 0.5 / np.sqrt (0.25 + 0.25 * tan**2)
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
            s = np.dot (r[i+1:nsing,i], zwork[i+1:nsing])
            zwork[i] = (zwork[i] - s) / sdiag[i]

    # "Permute the components of z back to components of x."
    x[pmut] = zwork
    return x


def _manual_qrd_solve (r, pmut, ddiag, qtb, dtype=np.float, build_s=False):
    r = np.asarray (r, dtype)
    pmut = np.asarray (pmut, np.int)
    ddiag = np.asarray (ddiag, dtype)
    qtb = np.asarray (qtb, dtype)

    swork = r.copy ()
    sdiag = np.empty (r.shape[0], r.dtype)

    x = _qrd_solve (swork, pmut, ddiag, qtb, sdiag)

    if not build_s:
        return x, swork, sdiag

    # Rebuild s.

    swork = swork.T
    for i in xrange (r.shape[0]):
        swork[i:,i] = 0
        swork[i,i] = sdiag[i]

    return x, swork


def _qrd_solve_full (a, b, ddiag, dtype=np.float):
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

    a = np.asarray (a, dtype)
    b = np.asarray (b, dtype)
    ddiag = np.asarray (ddiag, dtype)

    m, n = a.shape
    assert m >= n
    assert b.shape == (m, )
    assert ddiag.shape == (n, )

    # The computation is straightforward.

    q, r, pmut = _qr_factor_full (a)
    qtb = np.dot (q.T, b)
    x, s = _manual_qrd_solve (r[:n], pmut, ddiag, qtb,
                              dtype=dtype, build_s=True)

    return x, s, pmut


@test
def _qrd_solve_alone ():
    # Testing out just the QR solution function without
    # also the QR factorization bits.

    # The very simplest case.
    r = np.eye (2)
    pmut = np.asarray ([0, 1])
    diag = np.asarray ([0., 0])
    qtb = np.asarray ([3., 5])
    x, s = _manual_qrd_solve (r, pmut, diag, qtb, build_s=True)
    Taaae (x, [3., 5])
    Taaae (s, np.eye (2))

    # Now throw in a diagonal matrix ...
    diag = np.asarray ([2., 3.])
    x, s = _manual_qrd_solve (r, pmut, diag, qtb, build_s=True)
    Taaae (x, [0.6, 0.5])
    Taaae (s, np.sqrt (np.diag ([5, 10])))

    # And a permutation. We permute A but maintain
    # B, effectively saying x1 = 5, x2 = 3, so
    # we need to permute diag as well to scale them
    # by the amounts that yield nice X values.
    pmut = np.asarray ([1, 0])
    diag = np.asarray ([3., 2.])
    x, s = _manual_qrd_solve (r, pmut, diag, qtb, build_s=True)
    Taaae (x, [0.5, 0.6])
    Taaae (s, np.sqrt (np.diag ([5, 10])))


# Calculation of the Levenberg-Marquardt parameter

def _lmpar (r, ipvt, diag, qtb, delta, x, sdiag, par, enorm, finfo):
    dwarf = finfo.tiny
    m, n = r.shape

    # "Compute and store x in the Gauss-Newton direction. If
    # the Jacobian is rank-deficient, obtain a least-squares
    # solution.

    nsing = n
    wa1 = qtb.copy ()
    wh = np.where (r.diagonal () == 0)
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
            s = np.dot (r[:j,j], wa1[:j])
            wa1[j] = (wa1[j] - s) / r[j,j]

        temp = enorm (wa1, finfo)
        parl = fp / delta / temp**2

    # "Calculate an upper bound, paru, for the zero of the function."

    for j in xrange (n):
        s = np.dot (r[:j+1,j], qtb[:j+1])
        wa1[j] = s / diag[ipvt[j]]
    gnorm = enorm (wa1, finfo)
    paru = gnorm / delta
    if paru == 0:
        paru = dwarf / min (delta, 0.1)

    par = np.clip (par, parl, paru)
    if par == 0:
        par = gnorm / dxnorm

    # Begin iteration
    while True:
        iterct += 1

        # Evaluate at current value of par.
        if par == 0:
            par = max (dwarf, paru * 0.001)

        temp = np.sqrt (par)
        wa1 = temp * diag
        x = _qrd_solve (r, ipvt, wa1, qtb, sdiag)
        wa2 = diag * x
        dxnorm = enorm (wa2, finfo)
        temp = fp
        fp = dxnorm - delta

        if (abs (fp) < 0.1 * delta or (parl == 0 and fp <= temp and temp < 0) or
            iterct == 10):
            break

        # "Compute the Newton correction."
        wa1 = diag[ipvt] * wa2[ipvt] / dxnorm

        for j in xrange (n - 1):
            wa1[j] /= sdiag[j]
            wa1[j+1:n] -= r[j+1:n,j] * wa1[j]
        wa1[n-1] /= sdiag[n-1] # degenerate case

        temp = enorm (wa1, finfo)
        parc = fp / delta / temp**2

        if fp > 0:
            parl = max (parl, par)
        elif fp < 0:
            paru = min (paru, par)

        # Improve estimate of par

        par = max (parl, par + parc)

    # All done
    return r, par, x, diag


def _calc_covar (rr, ipvt, tol=1e-14):
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
            r[:j+1,k] -= temp * r[:j+1,j]

        l = k

    # "Form the full upper triangle of the inverse of (r transpose)*r
    # in the full upper triangle of r"

    if l >= 0:
        for k in xrange (l + 1):
            for j in xrange (k):
                temp = r[j,k]
                r[:j+1,j] += temp * r[:j+1,k]
            temp = r[k,k]
            r[:k+1,k] *= temp

    # "For the full lower triangle of the covariance matrix
    # in the strict lower triangle or and in wa"

    wa = np.repeat ([r[0,0]], n)

    for j in xrange (n):
        jj = ipvt[j]
        sing = j > l
        for i in xrange (j + 1):
            if sing:
                r[i,j] = 0.
            ii = ipvt[i]
            if ii > jj:
                r[ii,jj] = r[i,j]
            elif ii < jj:
                r[jj,ii] = r[i,j]
        wa[jj] = r[j,j]

    # "Symmetrize the covariance matrix in r"

    for j in xrange (n):
        r[:j+1,j] = r[j,:j+1]
        r[j,j] = wa[j]

    return r


# The actual user interface to the problem-solving machinery:

class Solution (object):
    ndof = None
    prob = None
    status = None
    niter = None
    perror = None
    params = None
    covar = None
    fnorm = None
    fvec = None
    fjac = None
    nfev = -1
    njev = -1

    def __init__ (self, prob):
        self.prob = prob

"""
solve() status codes:
status is a set of strings. The presence of a string in the set means that
the specified condition was active when the iteration terminated. Multiple
conditions may contribute to ending the iteration.

'ftol' (MPFIT equiv: 1, 3)
  "Termination occurs when both the actual and predicted relative
  reductions in the sum of squares are at most FTOL. Therefore, FTOL
  measures the relative error desired in the sum of squares."

'xtol' (MPFIT equiv: 2, 3)
  "Termination occurs when the relative error between two consecutive
  iterates is at most XTOL. Therefore, XTOL measures the relative
  error desired in the approximate solution."

'gtol' (MPFIT equiv: 4)
  "Termination occurs when the cosine of the angle between fvec and
  any column of the jacobian is at most GTOL in absolute
  value. Therefore, GTOL measures the orthogonality desired between
  the function vector and the columns of the jacobian."

'maxiter' (MPFIT equiv: 5)
  Number of iterations exceeds maxiter.

'feps' (MPFIT equiv: 6)
  "ftol is too small. no further reduction in the sum of squares is
  possible."

'xeps' (MPFIT equiv: 7)
  "xtol is too small. no further improvement in the approximate
  solution x is possible."

'geps' (MPFIT equiv: 8)
  "gtol is too small. fvec is orthogonal to the columns of the jacobian
  to machine precision."

"""

class Problem (object):
    _yfunc = None
    _jfunc = None
    _npar = None
    _nout = None

    _pinfof = None
    _pinfoo = None
    _pinfob = None

    # These ones are set in _fixupCheck
    _ifree = None
    _anytied = None

    # Public fields, settable by user at will

    solclass = None

    ftol = 1e-10
    xtol = 1e-10
    gtol = 1e-10
    damp = 0.
    factor = 100.
    epsfunc = None

    maxiter = 200

    diag = None

    fastnorm = False
    debugCalls = False
    debugJac = False


    def __init__ (self, npar=None, nout=None, yfunc=None, jfunc=None,
                  solclass=Solution):
        if npar is not None:
            self.setNPar (npar)
        if yfunc is not None:
            self.setFunc (nout, yfunc, jfunc)

        if not issubclass (solclass, Solution):
            raise ValueError ('solclass')

        self.solclass = solclass


    # The parameters and their metadata -- can be configured without
    # setting nout or the functions.

    def setNPar (self, npar):
        try:
            npar = int (npar)
            assert npar > 0
        except Exception:
            raise ValueError ('npar must be a positive integer')

        if self._npar is not None and self._npar == npar:
            return self

        newinfof = p = np.ndarray ((PI_NUM_F, npar), dtype=np.float)
        p[PI_F_VALUE] = np.nan
        p[PI_F_LLIMIT] = -np.inf
        p[PI_F_ULIMIT] = np.inf
        p[PI_F_STEP] = 0.
        p[PI_F_MAXSTEP] = np.inf

        newinfoo = p = np.ndarray ((PI_NUM_O, npar), dtype=np.object)
        p[PI_O_NAME] = None
        p[PI_O_TIED] = None

        newinfob = p = np.ndarray (npar, dtype=np.int)
        p[:] = 0

        if self._npar is not None:
            overlap = min (self._npar, npar)
            newinfof[:,:overlap] = self._pinfof[:,:overlap]
            newinfoo[:,:overlap] = self._pinfoo[:,:overlap]
            newinfob[:overlap] = self._pinfob[:overlap]

        self._pinfof = newinfof
        self._pinfoo = newinfoo
        self._pinfob = newinfob
        # Return self for easy chaining of calls.
        self._npar = npar
        return self


    def _setBit (self, idx, mask, cond):
        p = self._pinfob
        p[idx] = (p[idx] & ~mask) | np.where (cond, mask, 0x0)


    def _getBits (self, mask):
        return np.where (self._pinfob & mask, True, False)


    def pValue (self, idx, value, fixed=False):
        if np.any (-np.isfinite (value)):
            raise ValueError ('value')

        self._pinfof[PI_F_VALUE,idx] = value
        self._setBit (idx, PI_M_FIXED, fixed)
        return self


    def pLimit (self, idx, lower=-np.inf, upper=np.inf):
        if np.any (lower > upper):
            raise ValueError ('lower/upper')

        self._pinfof[PI_F_LLIMIT,idx] = lower
        self._pinfof[PI_F_ULIMIT,idx] = upper

        # Try to be clever here -- setting lower = upper
        # marks the parameter as fixed.

        w = np.where (lower == upper)
        if len (w) > 0 and w[0].size > 0:
            self.pValue (w, np.atleast_1d (lower)[w], True)

        return self


    def pStep (self, idx, step, maxstep=np.inf, isrel=False):
        if np.any (np.isinf (step)):
            raise ValueError ('step')
        if np.any ((step > maxstep) & ~isrel):
            raise ValueError ('step > maxstep')

        self._pinfof[PI_F_STEP,idx] = step
        self._pinfof[PI_F_MAXSTEP,idx] = maxstep
        self._setBit (idx, PI_M_RELSTEP, isrel)
        return self


    def pSide (self, idx, mode):
        if np.any (mode < 0 or mode > 3):
            raise ValueError ('mode')

        p = self._pinfob
        p[idx] = (p[idx] & ~PI_M_SIDE) | mode
        return self


    def pPrint (self, idx, doprint):
        self._setBit (idx, PI_M_PRINT, doprint)
        return self


    def pTie (self, idx, tiefunc):
        t1 = np.atleast_1d (tiefunc)
        if not np.all ([x is None or callable (x) for x in t1]):
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


    def _checkParamConfig (self):
        if self._npar is None:
            raise ValueError ('no npar yet')

        p = self._pinfof

        if np.any (np.isinf (p[PI_F_VALUE])):
            # note: this allows NaN param values, in which case we'll
            # check in solve() that it's been given valid parameters
            # as arguments.
            raise ValueError ('some specified initial values infinite')

        if np.any (np.isinf (p[PI_F_STEP])):
            raise ValueError ('some specified parameter steps infinite')

        if np.any ((p[PI_F_STEP] > p[PI_F_MAXSTEP]) & ~self._getBits (PI_M_RELSTEP)):
            raise ValueError ('some specified steps bigger than specified maxsteps')

        if np.any (p[PI_F_LLIMIT] > p[PI_F_ULIMIT]):
            raise ValueError ('some param lower limits > upper limits')

        if np.any (p[PI_F_VALUE] < p[PI_F_LLIMIT]):
            raise ValueError ('some param values < lower limits')

        if np.any (p[PI_F_VALUE] > p[PI_F_ULIMIT]):
            raise ValueError ('some param values < lower limits')

        p = self._pinfoo

        if not np.all ([x is None or callable (x) for x in p[PI_O_TIED]]):
            raise ValueError ('some tied values not None or callable')

        # And compute some useful arrays. A tied parameter counts as fixed.

        tied = np.asarray ([x is not None for x in self._pinfoo[PI_O_TIED]])
        self._anytied = np.any (tied)
        self._ifree = np.where (-(self._getBits (PI_M_FIXED) | tied))[0]


    def getNFree (self):
        self._checkParamConfig ()
        return self._ifree.size


    # Now, the function and the constraint values

    def setFunc (self, nout, yfunc, jfunc):
        try:
            nout = int (nout)
            assert nout > 0
            # Do not check that nout >= npar here, since
            # the user may wish to fix parameters, which
            # could make the problem tractable after all.
        except:
            raise ValueError ('nout')

        if not callable (yfunc):
            raise ValueError ('yfunc')

        if jfunc is None:
            self._get_jacobian = self._get_jacobian_automatic
        else:
            if not callable (jfunc):
                raise ValueError ('jfunc')
            self._get_jacobian = self._get_jacobian_explicit

        self._nout = nout
        self._yfunc = yfunc
        self._jfunc = jfunc
        self._nfev = 0
        self._njev = 0
        return self


    def setResidualFunc (self, yobs, errinv, yfunc, jfunc, reckless=False):
        from numpy import subtract, multiply

        self._checkParamConfig ()
        npar = self._npar

        if not np.all (np.isfinite (errinv)):
            raise ValueError ('some uncertainties are zero or nonfinite')

        # FIXME: handle yobs.ndim != 1 and/or yops being complex

        if reckless:
            def ywrap (pars, nresids):
                yfunc (pars, nresids) # model Y values => nresids
                subtract (yobs, nresids, nresids) # abs. residuals => nresids
                multiply (nresids, errinv, nresids)
            def jwrap (pars, jac):
                jfunc (pars, jac)
                multiply (jac, -1, jac)
                for i in xrange (npar):
                    multiply (jac[:,i], errinv, jac[:,i])
        else:
            def ywrap (pars, nresids):
                yfunc (pars, nresids)
                if not np.all (np.isfinite (nresids)):
                    raise RuntimeError ('function returned nonfinite values')
                subtract (yobs, nresids, nresids)
                multiply (nresids, errinv, nresids)
                #print 'N:', (nresids**2).sum ()
            def jwrap (pars, jac):
                jfunc (pars, jac)
                if not np.all (np.isfinite (jac)):
                    raise RuntimeError ('jacobian returned nonfinite values')
                multiply (jac, -1, jac)
                for i in xrange (npar):
                    multiply (jac[:,i], errinv, jac[:,i])

        if jfunc is None:
            jwrap = None

        return self.setFunc (yobs.size, ywrap, jwrap)


    def _fixupCheck (self):
        self._checkParamConfig ()

        if self._nout is None:
            raise ValueError ('no nout yet')

        if self._nout < self._npar - self._ifree.size:
            raise RuntimeError ('too many free parameters')

        # Coerce parameters to desired types

        self.ftol = float (self.ftol)
        self.xtol = float (self.xtol)
        self.gtol = float (self.gtol)
        self.damp = float (self.damp)
        self.factor = float (self.factor)

        if self.epsfunc is not None:
            self.epsfunc = float (self.epsfunc)

        self.maxiter = int (self.maxiter)

        self.fastnorm = bool (self.fastnorm)
        self.debugCalls = bool (self.debugCalls)
        self.debugJac = bool (self.debugJac)

        if self.diag is not None:
            self.diag = np.atleast_1d (np.asarray (self.diag, dtype=np.float))

            if self.diag.shape != (self._npar, ):
                raise ValueError ('diag')
            if np.any (self.diag <= 0.):
                raise ValueError ('diag')

        # Bounds and type checks

        if not issubclass (self.solclass, Solution):
            raise ValueError ('solclass')

        if self.ftol < 0.:
            raise ValueError ('ftol')

        if self.xtol < 0.:
            raise ValueError ('xtol')

        if self.gtol < 0.:
            raise ValueError ('gtol')

        if self.damp < 0.:
            raise ValueError ('damp')

        if self.maxiter < 1:
            raise ValueError ('maxiter')

        if self.factor <= 0.:
            raise ValueError ('factor')

        # Consistency checks

        if self._jfunc is not None and self.damp > 0:
            raise ValueError ('damping factor not allowed when using '
                              'explicit derivatives')


    def getNDOF (self):
        self._fixupCheck ()
        return self._nout - self._ifree.size


    def copy (self):
        n = Problem (self._npar, self._nout, self._yfunc, self._jfunc,
                     self.solclass)

        if self._pinfof is not None:
            n._pinfof = self._pinfof.copy ()
            n._pinfoo = self._pinfoo.copy ()
            n._pinfob = self._pinfob.copy ()

        if self.diag is not None:
            n.diag = self.diag.copy ()

        n.ftol = self.ftol
        n.xtol = self.xtol
        n.gtol = self.gtol
        n.damp = self.damp
        n.factor = self.factor
        n.epsfunc = self.epsfunc
        n.maxiter = self.maxiter
        n.fastnorm = self.fastnorm
        n.debugCalls = self.debugCalls
        n.debugJac = self.debugJac

        return n


    # Actual implementation code!

    def _ycall (self, params, vec):
        if self._anytied:
            self._apply_ties (params)

        self._nfev += 1

        if self.debugCalls:
            print 'Call: #%4d f(%s) ->' % (self._nfev, params),
        self._yfunc (params, vec)
        if self.debugCalls:
            print vec

        if self.damp > 0:
            np.tanh (vec / self.damp, vec)


    def solve (self, initial_params=None, dtype=np.float):
        from numpy import any, clip, dot, isfinite, sqrt, where

        self._fixupCheck ()
        ifree = self._ifree
        ycall = self._ycall
        n = ifree.size # number of free params; we try to allow n = 0

        # Set up initial values. These can either be specified via the
        # arguments to this function, or set implicitly with calls to
        # pValue() and pLimit (). Former overrides the latter.

        if initial_params is not None:
            initial_params = np.atleast_1d (np.asarray (initial_params, dtype=dtype))
        else:
            initial_params = self._pinfof[PI_F_VALUE]

        if initial_params.size != self._npar:
            raise ValueError ('expected exactly %d parameters, got %d'
                              % (self._npar, initial_params.size))

        if any (-isfinite (initial_params)):
            raise ValueError ('some nonfinite initial parameter values')

        dtype = initial_params.dtype
        finfo = np.finfo (dtype)
        params = initial_params.copy ()
        x = params[ifree] # x is the free subset of our parameters

        # Steps for numerical derivatives
        isrel = self._getBits (PI_M_RELSTEP)
        dside = self._pinfob & PI_M_SIDE
        maxstep = self._pinfof[PI_F_MAXSTEP,ifree]
        qmax = isfinite (maxstep)
        anymaxsteps = any (qmax)

        # Which parameters have limits?

        qulim = isfinite (self._pinfof[PI_F_ULIMIT,ifree])
        ulim = self._pinfof[PI_F_ULIMIT,ifree]
        qllim = isfinite (self._pinfof[PI_F_LLIMIT,ifree])
        llim = self._pinfof[PI_F_LLIMIT,ifree]
        anylimits = any (qulim) or any (qllim)

        # Init fnorm

        if self.fastnorm:
            enorm = _enorm_fast
        else:
            enorm = _enorm_careful

        fnorm1 = -1.
        fvec = np.ndarray (self._nout, dtype)
        ycall (params, fvec)
        fnorm = enorm (fvec, finfo)

        # Initialize Levenberg-Marquardt parameter and
        # iteration counter.

        par = 0.
        niter = 1
        qtf = x * 0.
        status = set ()

        # Outer loop top.

        while True:
            params[ifree] = x

            if self._anytied:
                self._apply_ties (params)

            fjac = self._get_jacobian (params, fvec, ulim, dside, maxstep, isrel, finfo)

            if anylimits:
                # Check for parameters pegged at limits
                whlpeg = where (qllim & (x == llim))
                nlpeg = len (whlpeg[0])
                whupeg = where (qulim & (x == ulim))
                nupeg = len (whupeg[0])

                if nlpeg > 0:
                    # Check total derivative of sum wrt lower-pegged params
                    for i in xrange (nlpeg):
                        if dot (fvec, fjac[:,whlpeg[0][i]]) > 0:
                            fjac[:,whlpeg[i]] = 0
                if nupeg > 0:
                    for i in xrange (nupeg):
                        if dot (fvec, fjac[:,whupeg[0][i]]) < 0:
                            fjac[:,whupeg[i]] = 0

            # Compute QR factorization of the Jacobian
            # wa1: "rdiag", diagonal part of R matrix, pivoting applied
            # wa2: "acnorm", unpermuted column norms of fjac
            # fjac: overwritten with Q and R matrix info, pivoted
            ipvt, wa1, wa2 = _qr_factor_packed (fjac, enorm, finfo)

            if niter == 1:
                # If "diag" unspecified, scale according to norms of columns
                # of the initial jacobian
                if self.diag is not None:
                    diag = self.diag.copy ()
                else:
                    diag = wa2.copy ()
                    diag[where (diag == 0)] = 1.

                # Calculate norm of scaled x, initialize step bound delta
                xnorm = enorm (diag * x, finfo)
                delta = self.factor * xnorm
                if delta == 0.:
                    delta = self.factor

            # Compute (q.T) * fvec, store the first n components in qtf

            wa4 = fvec.copy ()

            for j in xrange (n):
                temp3 = fjac[j,j]
                if temp3 != 0:
                    fj = fjac[j:,j]
                    wj = wa4[j:]
                    wa4[j:] = wj - fj * dot (fj, wj) / temp3
                fjac[j,j] = wa1[j]
                qtf[j] = wa4[j]

            # "From this point on, only the square matrix consisting
            # of the triangle of R is needed." ...  "Check for
            # overflow. This should be a cheap test here since fjac
            # has been reduced to a small square matrix."

            fjac = fjac[:n,:n]

            if any (-isfinite (fjac)):
                raise RuntimeError ('nonfinite terms in Jacobian matrix')

            # Calculate the norm of the scaled gradient

            gnorm = 0.
            if fnorm != 0:
                for j in xrange (n):
                    l = ipvt[j]
                    if wa2[l] != 0:
                        s = dot (fjac[:j+1,j], qtf[:j+1]) / fnorm
                        gnorm = max (gnorm, abs (s / wa2[l]))

            # Test for convergence of gradient norm

            if gnorm <= self.gtol:
                status.add ('gtol')
                break

            if self.diag is None:
                diag = np.maximum (diag, wa2)

            # Inner loop
            while True:
                # Get Levenberg-Marquardt parameter
                fjac, par, wa1, wa2 = _lmpar (fjac, ipvt, diag, qtf, delta,
                                              wa1, wa2, par, enorm, finfo)
                # "Store the direction p and x+p. Calculate the norm of p"
                wa1 *= -1
                alpha = 1.

                if not anylimits and not anymaxsteps:
                    # No limits applied, so just move to new position
                    wa2 = x + wa1
                else:
                    if anylimits:
                        if nlpeg > 0:
                            wa1[whlpeg] = clip (wa1[whlpeg], 0., max (wa1))
                        if nupeg > 0:
                            wa1[whupeg] = clip (wa1[whupeg], min (wa1), 0.)

                        dwa1 = abs (wa1) > finfo.eps
                        whl = where ((dwa1 != 0.) & qllim & ((x + wa1) < llim))

                        if len (whl[0]) > 0:
                            t = (llim[whl] - x[whl]) / wa1[whl]
                            alpha = min (alpha, t.min ())

                        whu = where ((dwa1 != 0.) & qulim & ((x + wa1) > ulim))

                        if len (whu[0]) > 0:
                            t = (ulim[whu] - x[whu]) / wa1[whu]
                            alpha = min (alpha, t.min ())

                    if anymaxsteps:
                        nwa1 = wa1 * alpha
                        whmax = where (qmax)
                        if len (whmax[0]) > 0:
                            mrat = np.abs (nwa1[whmax] / maxstep[whmax]).max ()
                            if mrat > 1:
                                alpha /= mrat

                    # Scale resulting vector
                    wa1 *= alpha
                    wa2 = x + wa1

                    # Adjust final output values: if we're supposed to be
                    # exactly on a boundary, make it exact.
                    wh = where (qulim & (wa2 >= ulim * (1 - finfo.eps)))
                    if len (wh[0]) > 0:
                        wa2[wh] = ulim[wh]
                    wh = where (qllim & (wa2 <= llim * (1 + finfo.eps)))
                    if len (wh[0]) > 0:
                        wa2[wh] = llim[wh]

                wa3 = diag * wa1
                pnorm = enorm (wa3, finfo)

                # On first iter, also adjust initial step bound
                if niter == 1:
                    delta = min (delta, pnorm)

                params[ifree] = wa2

                # Evaluate func at x + p and calculate norm

                ycall (params, wa4)
                fnorm1 = enorm (wa4, finfo)

                # Compute scaled actual reductions

                actred = -1.
                if 0.1 * fnorm1 < fnorm:
                    actred = 1 - (fnorm1 / fnorm)**2

                # Compute scaled predicted reduction and scaled directional
                # derivative

                for j in xrange (n):
                    wa3[j] = 0
                    wa3[:j+1] = wa3[:j+1] + fjac[:j+1,j] * wa1[ipvt[j]]

                # "Remember, alpha is the fraction of the full LM step actually
                # taken."

                temp1 = enorm (alpha * wa3, finfo) / fnorm
                temp2 = sqrt (alpha * par) * pnorm / fnorm
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

                    if 0.1 * fnorm1 >= fnorm or temp < 0.1:
                        temp = 0.1

                    delta = temp * min (delta, 10 * pnorm)
                    par /= temp
                elif par == 0 or ratio >= 0.75:
                    delta = 2 * pnorm
                    par *= 0.5

                if ratio >= 0.0001:
                    # Successful iteration.
                    x = wa2
                    wa2 = diag * x
                    fvec = wa4
                    xnorm = enorm (wa2, finfo)
                    fnorm = fnorm1
                    niter += 1

                # Check for convergence

                if abs (actred) <= self.ftol and prered <= self.ftol and ratio <= 2:
                    status.add ('ftol')

                if delta <= self.xtol * xnorm:
                    status.add ('xtol')

                # Check for termination, "stringent tolerances"

                if niter >= self.maxiter:
                    status.add ('maxiter')

                if abs (actred) <= finfo.eps and prered <= finfo.eps and ratio <= 2:
                    status.add ('feps')

                if delta <= finfo.eps * xnorm:
                    status.add ('xeps')

                if gnorm <= finfo.eps:
                    status.add ('geps')

                # Repeat loop if iteration unsuccessful (that is,
                # ratio < 1e-4 and not stopping criteria met)
                if ratio >= 0.0001 or len (status):
                    break

            if len (status):
                break

            # Check for overflow
            if any (-isfinite (wa1) | -isfinite (wa2) | -isfinite (x)):
                raise RuntimeError ('overflow in wa1, wa2, or x')

        # End outer loop. Finalize params, fvec, and fnorm

        if n == 0:
            params = initial_params.copy ()
        else:
            params[ifree] = x

        ycall (params, fvec)
        fnorm = enorm (fvec, finfo)
        fnorm = max (fnorm, fnorm1)
        fnorm **= 2

        # Covariance matrix. Nonfree parameters get zeros. Fill in
        # everything else if possible. TODO: I don't understand the
        # "covar = None" branch

        covar = np.zeros ((self._npar, self._npar), dtype)

        if n > 0:
            sz = fjac.shape

            if sz[0] < n or sz[1] < n or len (ipvt) < n:
                covar = None
            else:
                cv = _calc_covar (fjac[:n,:n], ipvt[:n])
                cv.shape = (n, n)

                for i in xrange (n): # can't do 2D fancy indexing
                    covar[ifree[i],ifree] = cv[i]

        # Errors in parameters from the diagonal of covar.

        perror = None

        if covar is not None:
            perror = np.zeros (self._npar, dtype)
            d = covar.diagonal ()
            wh = where (d >= 0)
            perror[wh] = sqrt (d[wh])

        # Export results and we're done.

        soln = self.solclass (self)
        soln.ndof = self.getNDOF ()
        soln.status = status
        soln.niter = niter
        soln.params = params
        soln.covar = covar
        soln.perror = perror
        soln.fnorm = fnorm
        soln.fvec = fvec
        soln.fjac = fjac
        soln.nfev = self._nfev
        soln.njev = self._njev
        return soln


    def moronsolve (self, initial_params=None, dtype=np.float, maxiter=20):
        soln = self.solve (initial_params, dtype)
        prevfnorm = soln.fnorm
        params = soln.params

        for i in xrange (maxiter):
            soln = self.solve (params, dtype)

            if soln.fnorm > prevfnorm:
                raise RuntimeError ('lame iteration gave worse results')

            if (prevfnorm - soln.fnorm) / prevfnorm < 1e-3:
                return soln

            params = soln.params
            prevfnorm = soln.fnorm

        raise RuntimeError ('lame iteration didn\'t converge (%d iters)' % maxiter)


    def _get_jacobian_explicit (self, params, fvec, ulimit, dside, maxstep, isrel, finfo):
        fjac = np.zeros ((self._nout, self._npar), finfo.dtype)

        self._njev += 1

        if self.debugCalls:
            print 'Call: #%4d j(%s) ->' % (self._njev, params),
        self._jfunc (params, fjac)
        if self.debugCalls:
            print fjac

        if self._ifree.size < self._npar:
            fjac = fjac[:,self._ifree]

        return fjac


    def _get_jacobian_automatic (self, params, fvec, ulimit, dside, maxstep, isrel, finfo):
        ifree = self._ifree
        debug = self.debugJac
        machep = finfo.eps

        x = params[ifree]

        if self.epsfunc is None:
            eps = machep
        else:
            eps = self.epsfunc
        eps = np.sqrt (max (eps, machep))
        m = len (fvec)
        n = len (x)

        fjac = np.zeros ((m, n), finfo.dtype)
        h = eps * np.abs (x)

        # Apply any fixed steps, absolute and relative.
        stepi = self._pinfof[PI_F_STEP,ifree]
        wh = np.where (stepi > 0)
        h[wh] = stepi[wh] * np.where (isrel[ifree[wh]], x[wh], 1.)

        # Clamp stepsizes to maxstep.
        np.minimum (h, maxstep, h)

        # Make sure no zero step values
        h[np.where (h == 0)] = eps

        # Reverse sign of step if against a parameter limit or if
        # backwards-sided derivative

        mask = (dside == DSIDE_NEG)[ifree]
        if ulimit is not None:
            mask |= x > ulimit - h
            wh = np.where (mask)
            h[wh] = -h[wh]

        if debug:
            print 'Jac-:', h

        # Compute derivative for each parameter

        for j in xrange (n):
            xp = params.copy ()
            xp[ifree[j]] += h[j]
            fp = np.empty (self._nout, dtype=finfo.dtype)
            self._ycall (xp, fp)

            if dside[j] != DSIDE_TWO:
                # One-sided derivative
                fjac[:,j] = (fp - fvec) / h[j]
            else:
                # Two-sided ... extra func call
                xp[ifree[j]] = params[ifree[j]] - h[j]
                fm = np.empty (self._nout, dtype=finfo.dtype)
                self._ycall (xp, fm)
                fjac[:,j] = (fp - fm) / (2 * h[j])

        if debug:
            for i in xrange (m):
                print 'Jac :', fjac[i]
        return fjac


    def _manual_jacobian (self, params, dtype=np.float):
        self._fixupCheck ()

        ifree = self._ifree

        params = np.atleast_1d (np.asarray (params, dtype))
        fvec = np.empty (self._nout, dtype)
        ulimit = self._pinfof[PI_F_ULIMIT,ifree]
        dside = self._pinfob & PI_M_SIDE
        maxstep = self._pinfof[PI_F_MAXSTEP,ifree]
        isrel = self._getBits (PI_M_RELSTEP)
        finfo = np.finfo (dtype)

        # Before we can evaluate the Jacobian, we need to get the
        # initial value of the function at the specified position.
        # Note that in the real algorithm, _apply_ties is always
        # called before _get_jacobian.

        self._ycall (params, fvec)
        return self._get_jacobian (params, fvec, ulimit, dside, maxstep, isrel, finfo)


    def _apply_ties (self, params):
        funcs = self._pinfoo[PI_O_TIED]

        for i in xrange (self._npar):
            if funcs[i] is not None:
                params[i] = funcs[i] (params)


def checkDerivative (npar, nout, yfunc, jfunc, guess):
    explicit = np.empty ((nout, npar))
    jfunc (guess, explicit)

    p = Problem (npar, nout, yfunc, None)
    auto = p._manual_jacobian (guess)

    return explicit, auto


def ResidualProblem (npar, yobs, errinv, yfunc, jfunc,
                     solclass=Solution, reckless=False):
    p = Problem (solclass=solclass)
    p.setNPar (npar)
    p.setResidualFunc (yobs, errinv, yfunc, jfunc, reckless=reckless)
    return p


# Test!


@test
def _solve_linear ():
    x = np.asarray ([1, 2, 3])
    y = 2 * x + 1

    from numpy import multiply, add

    def f (pars, ymodel):
        multiply (x, pars[0], ymodel)
        add (ymodel, pars[1], ymodel)

    p = ResidualProblem (2, y, 100, f, None)
    return p.solve ([2.5, 1.5])

@test
def _simple_automatic_jac ():
    def f (pars, vec):
        np.exp (pars, vec)

    p = Problem (1, 1, f, None)
    j = p._manual_jacobian (0)
    Taaae (j, [[1.]])
    j = p._manual_jacobian (1)
    Taaae (j, [[np.e]])

    p = Problem (3, 3, f, None)
    x = np.asarray ([0, 1, 2])
    j = p._manual_jacobian (x)
    Taaae (j, np.diag (np.exp (x)))

@test
def _jac_sidedness ():
    # Make a function with a derivative discontinuity so we can test
    # the sidedness settings.

    def f (pars, vec):
        p = pars[0]

        if p >= 0:
            vec[:] = p
        else:
            vec[:] = -p

    p = Problem (1, 1, f, None)

    # Default: positive unless against upper limit.
    Taaae (p._manual_jacobian (0), [[1.]])

    # DSIDE_AUTO should be the default.
    p.pSide (0, DSIDE_AUTO)
    Taaae (p._manual_jacobian (0), [[1.]])

    # DSIDE_POS should be equivalent here.
    p.pSide (0, DSIDE_POS)
    Taaae (p._manual_jacobian (0), [[1.]])

    # DSIDE_NEG should get the other side of the discont.
    p.pSide (0, DSIDE_NEG)
    Taaae (p._manual_jacobian (0), [[-1.]])

    # DSIDE_AUTO should react to an upper limit and take
    # a negative-step derivative.
    p.pSide (0, DSIDE_AUTO)
    p.pLimit (0, upper=0)
    Taaae (p._manual_jacobian (0), [[-1.]])

@test
def _jac_stepsizes ():
    def f (expstep, pars, vec):
        p = pars[0]

        if p != 1.:
            Taae (p, expstep)

        vec[:] = 1

    # Fixed stepsize of 1.
    p = Problem (1, 1, lambda p, v: f (2., p, v), None)
    p.pStep (0, 1.)
    p._manual_jacobian (1)

    # Relative stepsize of 0.1
    p = Problem (1, 1, lambda p, v: f (1.1, p, v), None)
    p.pStep (0, 0.1, isrel=True)
    p._manual_jacobian (1)

    # Fixed stepsize must be less than max stepsize.
    try:
        p = Problem (2, 2, f, None)
        p.pStep ((0, 1), (1, 1), (1, 0.5))
        assert False, 'Invalid arguments accepted'
    except ValueError:
        pass

    # Maximum stepsize, made extremely small to be enforced
    # in default circumstances.
    p = Problem (1, 1, lambda p, v: f (1 + 1e-11, p, v), None)
    p.pStep (0, 0.0, 1e-11)
    p._manual_jacobian (1)

    # Maximum stepsize and a relative stepsize
    p = Problem (1, 1, lambda p, v: f (1.1, p, v), None)
    p.pStep (0, 0.5, 0.1, True)
    p._manual_jacobian (1)


# lmder1 / lmdif1 test cases

def _lmder1_test (nout, func, jac, guess):
    finfo = np.finfo (np.float)
    tol = np.sqrt (finfo.eps)
    guess = np.asfarray (guess)

    y = np.empty (nout)
    func (guess, y)
    fnorm1 = _enorm_careful (y, finfo)
    p = Problem (guess.size, nout, func, jac)
    p.xtol = p.ftol = tol
    p.gtol = 0
    p.maxiter = 100 * (guess.size + 1)
    s = p.solve (guess)
    func (s.params, y)
    fnorm2 = _enorm_careful (y, finfo)

    print '  n, m:', guess.size, nout
    print '  fnorm1:', fnorm1
    print '  fnorm2:', fnorm2
    print '  nfev, njev:', s.nfev, s.njev
    print '  status:', s.status
    print '  params:', s.params


def _lmder1_driver (nout, func, jac, guess, target_fnorm1,
                    target_fnorm2, target_params):
    finfo = np.finfo (np.float)
    tol = np.sqrt (finfo.eps)
    guess = np.asfarray (guess)

    y = np.empty (nout)
    func (guess, y)
    fnorm1 = _enorm_careful (y, finfo)
    Taae (fnorm1, target_fnorm1)

    p = Problem (guess.size, nout, func, jac)
    p.xtol = p.ftol = tol
    p.gtol = 0
    p.maxiter = 100 * (guess.size + 1)
    s = p.solve (guess)

    # assert_array_almost_equal goes to a fixed number of decimal
    # places regardless of the scale of the number, so it breaks
    # when we work with very large values.
    from numpy.testing import assert_array_almost_equal as aaae
    scale = np.maximum (np.abs (target_params), 1)
    aaae (s.params / scale, target_params / scale, decimal=10)

    func (s.params, y)
    fnorm2 = _enorm_careful (y, finfo)
    Taae (fnorm2, target_fnorm2)


def _lmder1_linear_full_rank (n, m, factor, target_fnorm1, target_fnorm2):
    def func (params, vec):
        s = params.sum ()
        temp = 2. * s / m + 1
        vec[:] = -temp
        vec[:params.size] += params

    def jac (params, jac):
        # jac.shape = (m, n) by LMDER standards
        temp = 2. / m
        jac[:,:] = -temp
        for i in xrange (n):
            jac[i,i] += 1

    guess = np.ones (n) * factor

    #_lmder1_test (m, func, jac, guess)
    _lmder1_driver (m, func, jac, guess,
                    target_fnorm1, target_fnorm2,
                    [-1] * n)

@test
def _lmder1_linear_full_rank_1 ():
    _lmder1_linear_full_rank (5, 10, 1, 5., 0.2236068e+01)

@test
def _lmder1_linear_full_rank_2 ():
    _lmder1_linear_full_rank (5, 50, 1, 0.806225774e+01, 0.670820393e+01)


def _lmder1_linear_rank1 (n, m, factor, target_fnorm1, target_fnorm2, target_params):
    def func (params, vec):
        s = 0
        for j in xrange (n):
            s += (j + 1) * params[j]
        for i in xrange (m):
            vec[i] = (i + 1) * s - 1

    def jac (params, jac):
        for i in xrange (m):
            for j in xrange (n):
                jac[i,j] = (i + 1) * (j + 1)

    guess = np.ones (n) * factor

    #_lmder1_test (m, func, jac, guess)
    _lmder1_driver (m, func, jac, guess,
                    target_fnorm1, target_fnorm2, target_params)

@test
def _lmder1_linear_rank1_1 ():
    _lmder1_linear_rank1 (5, 10, 1,
                          0.2915218688e+03, 0.1463850109e+01,
                          [-0.167796818e+03, -0.8339840901e+02, 0.2211100431e+03, -0.4119920451e+02, -0.327593636e+02])

@test
def _lmder1_linear_rank1_2 ():
    _lmder1_linear_rank1 (5, 50, 1,
                          0.310160039334e+04, 0.34826301657e+01,
                          [-0.2029999900022674e+02, -0.9649999500113370e+01, -0.1652451975264496e+03,
                            -0.4324999750056676e+01,  0.1105330585100652e+03])


def _lmder1_linear_r1zcr (n, m, factor, target_fnorm1, target_fnorm2, target_params):
    """linear function - rank 1 with zero columns and rows"""

    def func (params, vec):
        s = 0
        for j in xrange (1, n - 1):
            s += (j + 1) * params[j]
        for i in xrange (m):
            vec[i] = i * s - 1
        vec[m-1] = -1

    def jac (params, jac):
        jac.fill (0)

        for i in xrange (1, m - 1):
            for j in xrange (1, n - 1):
                jac[i,j] = i * (j + 1)

    guess = np.ones (n) * factor

    #_lmder1_test (m, func, jac, guess)
    _lmder1_driver (m, func, jac, guess,
                    target_fnorm1, target_fnorm2, target_params)

@test
def _lmder1_linear_r1zcr_1 ():
    _lmder1_linear_r1zcr (5, 10, 1,
                          0.1260396763e+03, 0.1909727421e+01,
                          [0.1000000000e+01, -0.2103615324e+03, 0.3212042081e+02,
                           0.8113456825e+02, 0.1000000000e+01])

@test
def _lmder1_linear_r1zcr_2 ():
    _lmder1_linear_r1zcr (5, 50, 1,
                          0.17489499707e+04, 0.3691729402e+01,
                          [0.1000000000e+01, 0.3321494859e+03, -0.4396851914e+03,
                           0.1636968826e+03, 0.1000000000e+01])

@test
def _lmder1_rosenbrock ():
    def func (params, vec):
        vec[0] = 10 * (params[1] - params[0]**2)
        vec[1] = 1 - params[0]

    def jac (params, jac):
        jac[0,0] = -20 * params[0]
        jac[0,1] = 10
        jac[1,0] = -1
        jac[1,1] = 0

    guess = np.asfarray ([-1.2, 1])
    norm1s = [0.491934955050e+01, 0.134006305822e+04, 0.1430000511923e+06]

    for i in xrange (3):
        _lmder1_driver (2, func, jac, guess * 10**i,
                        norm1s[i], 0, [1, 1])


@test
def _lmder1_helical_valley ():
    tpi = 2 * np.pi

    def func (params, vec):
        if params[0] == 0:
            tmp1 = np.copysign (0.25, params[1])
        elif params[0] > 0:
            tmp1 = np.arctan (params[1] / params[0]) / tpi
        else:
            tmp1 = np.arctan (params[1] / params[0]) / tpi + 0.5

        tmp2 = np.sqrt (params[0]**2 + params[1]**2)

        vec[0] = 10 * (params[2] - 10 * tmp1)
        vec[1] = 10 * (tmp2 - 1)
        vec[2] = params[2]

    def jac (params, jac):
        temp = params[0]**2 + params[1]**2
        tmp1 = tpi * temp
        tmp2 = np.sqrt (temp)
        jac[0,0] = 100 * params[1] / tmp1
        jac[0,1] = -100 * params[0] / tmp1
        jac[0,2] = 10
        jac[1,0] = 10 * params[0] / tmp2
        jac[1,1] = 10 * params[1] / tmp2
        jac[1,2] = 0
        jac[2,0] = 0
        jac[2,1] = 0
        jac[2,2] = 1

    guess = np.asfarray ([-1, 0, 0])

    _lmder1_driver (3, func, jac, guess,
                    50., 0.993652310343e-16,
                    [0.100000000000e+01, -0.624330159679e-17, 0.000000000000e+00])
    _lmder1_driver (3, func, jac, guess * 10,
                    0.102956301410e+03, 0.104467885065e-18,
                    [0.100000000000e+01, 0.656391080516e-20, 0.000000000000e+00])
    _lmder1_driver (3, func, jac, guess * 100,
                    0.991261822124e+03, 0.313877781195e-28,
                    [0.100000000000e+01, -0.197215226305e-29, 0.000000000000e+00])


def _lmder1_powell_singular ():
    """Don't run this as a test, since it just zooms to zero
    parameters.  The precise results depend a lot on nitty-gritty
    rounding and tolerances and things."""

    def func (params, vec):
        vec[0] = params[0] + 10 * params[1]
        vec[1] = np.sqrt (5) * (params[2] - params[3])
        vec[2] = (params[1] - 2 * params[2])**2
        vec[3] = np.sqrt (10) * (params[0] - params[3])**2

    def jac (params, jac):
        jac.fill (0)
        jac[0,0] = 1
        jac[0,1] = 10
        jac[1,2] = np.sqrt (5)
        jac[1,3] = -np.sqrt (5)
        jac[2,1] = 2 * (params[1] - 2 * params[2])
        jac[2,2] = -2 * jac[2,1]
        jac[3,0] = 2 * np.sqrt (10) * (params[0] - params[3])
        jac[3,3] = -jac[3,0]

    guess = np.asfarray ([3, -1, 0, 1])

    _lmder1_test (4, func, jac, guess)
    _lmder1_test (4, func, jac, guess * 10)
    _lmder1_test (4, func, jac, guess * 100)


@test
def _lmder1_freudenstein_roth ():
    """Freudenstein and Roth function (lmder1 test #7)"""

    def func (params, vec):
        vec[0] = -13 + params[0] + ((5 - params[1]) * params[1] - 2) * params[1]
        vec[1] = -29 + params[0] + ((1 + params[1]) * params[1] - 14) * params[1]

    def jac (params, jac):
        jac[0,0] = jac[1,0] = 1
        jac[0,1] = params[1] * (10 - 3 * params[1]) - 2
        jac[1,1] = params[1] * (2 + 3 * params[1]) - 14

    guess = np.asfarray ([0.5, -2])

    _lmder1_driver (2, func, jac, guess,
                    0.200124960962e+02, 0.699887517585e+01,
                    [0.114124844655e+02, -0.896827913732e+00])
    _lmder1_driver (2, func, jac, guess * 10,
                    0.124328339489e+05, 0.699887517449e+01,
                    [0.114130046615e+02, -0.896796038686e+00])
    _lmder1_driver (2, func, jac, guess * 100,
                    0.11426454595762e+08, 0.699887517243e+01,
                    [0.114127817858e+02, -0.896805107492e+00])


@test
def _lmder1_bard ():
    """Bard function (lmder1 test #8)"""

    y1 = np.asfarray ([0.14, 0.18, 0.22, 0.25, 0.29,
                       0.32, 0.35, 0.39, 0.37, 0.58,
                       0.73, 0.96, 1.34, 2.10, 4.39])

    def func (params, vec):
        for i in xrange (15):
            tmp2 = 15 - i

            if i > 7:
                tmp3 = tmp2
            else:
                tmp3 = i + 1

            vec[i] = y1[i] - (params[0] + (i + 1) / (params[1] * tmp2 + params[2] * tmp3))

    def jac (params, jac):
        for i in xrange (15):
            tmp2 = 15 - i

            if i > 7:
                tmp3 = tmp2
            else:
                tmp3 = i + 1

            tmp4 = (params[1] * tmp2 + params[2] * tmp3)**2
            jac[i,0] = -1
            jac[i,1] = (i + 1) * tmp2 / tmp4
            jac[i,2] = (i + 1) * tmp3 / tmp4

    guess = np.asfarray ([1, 1, 1])

    _lmder1_driver (15, func, jac, guess,
                    0.6456136295159668e+01, 0.9063596033904667e-01,
                    [0.8241057657583339e-01, 0.1133036653471504e+01, 0.2343694638941154e+01])
    _lmder1_driver (15, func, jac, guess * 10,
                    0.3614185315967845e+02, 0.4174768701385386e+01,
                    [0.8406666738183293e+00, -0.1588480332595655e+09, -0.1643786716535352e+09])
    _lmder1_driver (15, func, jac, guess * 100,
                    0.3841146786373992e+03, 0.4174768701359691e+01,
                    [0.8406666738676455e+00, -0.1589461672055184e+09, -0.1644649068577712e+09])


@test
def _lmder1_kowalik_osborne ():
    """Kowalik & Osborne function (lmder1 test #9)"""
    v = np.asfarray ([4, 2, 1, 0.5, 0.25, 0.167, 0.125, 0.1, 0.0833, 0.0714, 0.0625])
    y2 = np.asfarray ([0.1957, 0.1947, 0.1735, 0.16, 0.0844, 0.0627, 0.0456,
                       0.0342, 0.0323, 0.0235, 0.0246])

    def func (params, vec):
        for i in xrange (11):
            tmp1 = v[i] * (v[i] + params[1])
            tmp2 = v[i] * (v[i] + params[2]) + params[3]
            vec[i] = y2[i] - params[0] * tmp1 / tmp2

    def jac (params, jac):
        for i in xrange (11):
            tmp1 = v[i] * (v[i] + params[1])
            tmp2 = v[i] * (v[i] + params[2]) + params[3]
            jac[i,0] = -tmp1 / tmp2
            jac[i,1] = -v[i] * params[0] / tmp2
            jac[i,2] = jac[i,0] * jac[i,1]
            jac[i,3] = jac[i,2] / v[i]

    guess = np.asfarray ([0.25, 0.39, 0.415, 0.39])

    _lmder1_driver (11, func, jac, guess,
                    0.7289151028829448e-01, 0.1753583772112895e-01,
                    [0.1928078104762493e+00, 0.1912626533540709e+00,
                     0.1230528010469309e+00, 0.1360532211505167e+00])
    _lmder1_driver (11, func, jac, guess * 10,
                    0.2979370075552020e+01, 0.3205219291793696e-01,
                    [0.7286754737686598e+06, -0.1407588031293926e+02,
                     -0.3297779778419661e+08, -0.2057159419780170e+08])

    # This last test seems to rely on hitting maxfev in the solver.
    # Our stopping criterion is a bit different, so we go a bit farther.
    # I'm going to hope that's why our results are different.
    #_lmder1_driver (11, func, jac, guess * 100,
    #                0.2995906170160365e+02, 0.1753583967605901e-01,
    #                [0.1927984063846549e+00, 0.1914736844615448e+00,
    #                 0.1230924753714115e+00, 0.1361509629062244e+00])


# Finally ...

if __name__ == '__main__':
    _runtests ()
