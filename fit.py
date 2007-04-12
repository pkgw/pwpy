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
