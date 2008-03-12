# Routines for doing basic fits with numpy

import numpy as _numpy

def linear (x, y, weights = None):
    """Perform a linear fit through the points given in x, y.
    If specified, 'weights' gives the weight that is assigned to each
    point; if not specified, each point is weighted equally. (Suggested
    weights: 1 / err). Thus x, y, and weights should all have the same
    length.

    Returns: (A, B), where A is the slope of the best-fit line, and
    B is the y-intercept of that line. So 'A * x + B' yields the best-fit
    points.
    """

    from scipy.linalg import lstsq
    
    x = _numpy.asarray (x)
    y = _numpy.asarray (y)

    if weights is None:
        weights = _numpy.ones (len (x))
    else:
        weights = _numpy.asarray (weights)

    # lstsq finds x that minimizes A * x = B, with all
    # of the above being matrices.
    
    fitA = _numpy.vstack ((x * weights, weights)).T
    fitB = (y * weights).T

    res = lstsq (fitA, fitB)[0]
    return (res[0], res[1])

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

    x = _numpy.asarray (x)
    y = _numpy.asarray (y)

    if weights is None:
        weights = _numpy.ones (len (x))
    else:
        weights = _numpy.asarray (weights)

    A = (x - x0) * weights
    B = (y - y0) * weights

    # Upgrade precision in case all of our arrays were ints.
    # FIXME: is there a function to upgrade something to at least
    # a float? If all the inputs are float32's, we should also
    # return a float32.
    
    return _numpy.float64 (_numpy.dot (A, B)) / _numpy.dot (A, A)

_exp = _numpy.exp

def makeGaussian (params):
    """Return a lambda function that evaluates a Gaussian
    corresponding to the given parameters.

    Parameters: Gaussian fit tuple. Decomposes into (height,
      xmid, width).
    """

    height, xmid, width = params
    return lambda x: height * _exp (-0.5 * ((x - xmid)/width)**2)

def guessGaussianParams (x, y):
    """Guess initial Gaussian parameters using the moments of the
    given data."""

    from numpy import asarray, abs, sqrt
    
    x = asarray (x)
    y = asarray (y)
    
    height = y.max ()

    ytotal = y.sum ()
    byx = y * x
    xmid = byx.sum () / ytotal

    # Not at all sure if this is a good algorithm. Seems to
    # work OK.
    width = sqrt (abs ((x - xmid)**2 * y).sum () / ytotal)

    return (height, xmid, width)
    
def gaussian (x, y, params=None):
    """Fit a Gaussian to the data in x and y, optionally starting
    with the parameters given in params. Params is a tuple of
    (height, xmid, width) ; if unspecified, the initial guess
    is taken from the moments of the data.

    Returns: a parameter tuple after performing a fit. Has the
    same form of (height, xmid, width)."""

    from numpy import asarray, ravel
    from scipy import optimize

    x = asarray (x)
    y = asarray (y)
    
    if params is None: params = guessGaussianParams (x, y)

    def error (p):
        return ravel (makeGaussian (p)(x) - y)

    pfit, xx, xx, msg, success = optimize.leastsq (error, params,
                                                   full_output=True)

    if success != 1:
        raise Exception ('Least square fit failed: ' + msg)

    return pfit

def generic (model, x, y, params, **kwargs):
    """Generic least-squares fitting algorithm. Parameters are:

    model    - A function of N+1 variables: an ndarray of X values,
               then N tunable parameters.
    x        - The data X values.
    y        - The data Y values.
    params   - A tuple of N values that are the initial guesses for
               the parameters to model().
    **kwargs - Optional extra parameters to pass to the fitting
               function, scipy.optimize.leastsq().

    Returns: a tuple of N parameters that minimize the least-squares
    difference between the model function and the data.
    """

    from numpy import asarray, ravel
    from scipy import optimize

    x = asarray (x)
    y = asarray (y)
    
    def error (p):
        return ravel (model (x, *p) - y)

    pfit, xx, xx, msg, success = optimize.leastsq (error, params,
                                                   full_output=True, **kwargs)

    if success < 1 or success > 4:
        raise Exception ('Least square fit failed: ' + msg)

    return pfit

def _gausslinModel (x, y0, m, height, xmid, width):
    return (y0 + x * m) + height * _exp (-0.5 * ((x - xmid)/width)**2)

def gausslin (x, y, params=None):
    """Least-squares fit of a Gaussian plus a linear offset. The parameter
    tuple is of the form (y0, m, height, xmid, width)."""
    
    if params is None:
        params = (0, 0) + guessGaussianParams (x, y)

    return generic (_gausslinModel, x, y, params)

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
        model = makeGauss2dFunc (*params)(*_numpy.indices (data.shape))
        return _numpy.ravel (model - data)

    pfit, xx, xx, msg, success = optimize.leastsq (err, guess,
                                                   full_output=True, **kwargs)

    if success < 1 or success > 4:
        raise Exception ('Least square fit failed: ' + msg)

    if not getResid: return pfit

    model = makeGauss2dFunc (*pfit)(*_numpy.indices (data.shape))
    return pfit, data - model

def power (x, y, params=None, **kwargs):
    """Least-squares fit of a power law: y = q * x**alpha.

    Returns: q, alpha.
    """
    
    l = _numpy.log
    
    def model (x, q, alpha):
        return q * x **alpha

    if params is None:
        dlogx = l (x.max ()) - l (x.min ())
        dlogy = l (y.max ()) - l (y.min ())
        alpha = dlogy / dlogx

        mlogx = l (x).mean ()
        mlogy = l (y).mean ()
        q = _numpy.exp (- mlogy / alpha / mlogx)

        params = (q, alpha)

    return generic (model, x, y, params, **kwargs)
