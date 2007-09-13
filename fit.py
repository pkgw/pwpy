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

    from numpy import exp, asarray, ravel
    from scipy import optimize

    x = asarray (x)
    y = asarray (y)
    
    if params is None: params = guessGaussianParams (x, y)

    def makeGaussian (height, xmid, width):
        return lambda x: height * exp (-0.5 * ((x - xmid)/width)**2)

    def error (p):
        return ravel (makeGaussian (*p)(x) - y)

    pfit, success = optimize.leastsq (error, params)

    if success != 1: raise Exception ('Least square fit failed.')

    return pfit
