"""ellutil - utilities for manipulating 2D Gaussians and ellipses

Useful for sources and bivariate error distributions. We can express
the shape of the function in several ways, which have different strengths
and weaknesses:

* "biv", as in Gaussian bivariate: sigma x, sigma y, cov(x,y)
* "ell", as in ellipse: major, minor, PA [*]
* "abc": coefficients such that z = exp (ax^2 + bxy + cy^2)
* "nf": EXPERIMENTAL, "numerically friendly", params named u, v, w

[*] Any slice through a 2D Gaussian is an ellipse. Ours is defined such it
is the same as a Gaussian bivariate when major = minor.

Note that when considering astronomical position angles,
conventionally defined as East from North, the Dec/lat axis should be
considered the X axis and the RA/long axis should be considered the Y
axis.

TODO: figure out if nf is actually helpful; improve it, remove it, or
document it.

Possible TODO: make more array-friendly. All of the bounds-checking
becomes a pain (e.g. need to wrap in np.any()) to make array-friendly
while still providing useful debug output.
"""

import numpy as np

__all__ = ('F2S S2F sigmascale clscale '
           'bivell bivnorm bivabc bivnf databiv bivplot '
           'ellnorm ellpoint elld2 ellabc ellplot '
           'nfabc nfell nfd2 nfplot '
           'abcell abcd2 abcnf abcplot').split ()


# Some utilities for scaling ellipse axis lengths

F2S = 1 / np.sqrt (8 * np.log (2)) # FWHM to sigma; redundant w/ astutil
S2F = np.sqrt (8 * np.log (2))


def sigmascale (nsigma):
    """Say we take a Gaussian bivariate and convert the parameters of
the distribution to an ellipse (major, minor, PA). By what factor
should we scale those axes to make the area of the ellipse correspond
to the n-sigma confidence interval?"""
    from scipy.special import erfc
    if nsigma <= 0:
        raise ValueError ('nsigma must be positive (%.10e)' % nsigma)
    return np.sqrt (-2 * np.log (erfc (nsigma / np.sqrt (2))))


def clscale (cl):
    """Say we take a Gaussian bivariate and convert the parameters of
the distribution to an ellipse (major, minor, PA). By what factor
should we scale those axes to make the area of the ellipse correspond
to the confidence interval CL? (I.e. 0 < CL < 1)"""
    if cl <= 0 or cl >= 1:
        raise ValueError ('must have 0 < cl < 1 (%.10e)' % cl)
    return np.sqrt (-2 * np.log (1 - cl))


# Bivariate form: sigma x, sigma y, cov(x,y)

def _bivcheck (sx, sy, cxy):
    if sx <= 0:
        raise ValueError ('negative sx (%.10e)' % sx)
    if sy <= 0:
        raise ValueError ('negative sy (%.10e)' % sy)
    if abs (cxy) >= sx * sy:
        raise ValueError ('illegal covariance (sx=%.10e, sy=%.10e, cxy=%.10e, '
                          'cxy/sxsy=%.16f)' % (sx, sy, cxy, cxy / (sx * sy)))
    return sx, sy, cxy # convenience


def bivell (sx, sy, cxy):
    """Given the parameters of a Gaussian bivariate distribution,
compute the parameters for the equivalent 2D Gaussian in ellipse form
(major, minor, pa).

Inputs:

* sx: standard deviation (not variance) of x var
* sy: standard deviation (not variance) of y var
* cxy: covariance (not correlation coefficient) of x and y

Outputs:

* maj: major axis of equivalent 2D Gaussian (sigma, not FWHM)
* min: minor axis
* pa: position angle, rotating from +x to +y

Lots of sanity-checking because it's obnoxiously easy to have
numerics that just barely blow up on you.
"""
    # See CfA notebook #1 pp. 129-133.
    _bivcheck (sx, sy, cxy)
    from numpy import arctan2, sqrt

    sx2, sy2, cxy2 = sx**2, sy**2, cxy**2

    pa = 0.5 * arctan2 (2 * cxy, sx2 - sy2)
    h = sqrt ((sx2 - sy2)**2 + 4*cxy2)

    t = 2 * (sx2 * sy2 - cxy2) / (sx2 + sy2 - h)
    if t < 0:
        raise ValueError ('covariance just barely out of bounds [1] '
                          '(sx=%.10e, sy=%.10e, cxy=%.10e, cxy/sxsy=%.16f)' %
                          (sx, sy, cxy, cxy / (sx * sy)))
    maj = sqrt (t)

    t = 2 * (sx2 * sy2 - cxy2) / (sx2 + sy2 + h)
    if t < 0: # if we got this far, shouldn't happen, but ...
        raise ValueError ('covariance just barely out of bounds [2] '
                          '(sx=%.10e, sy=%.10e, cxy=%.10e, cxy/sxsy=%.16f)' %
                          (sx, sy, cxy, cxy / (sx * sy)))
    min = sqrt (t)

    return ellnorm (maj, min, pa)


def bivnorm (sx, sy, cxy):
    """Given the parameters of a Gaussian bivariate distribution,
compute the correct normalization for the equivalent 2D Gaussian.
It's 1 / (2 pi sqrt (sx**2 sy**2 - cxy**2). This function adds a lot
of sanity checking.

Inputs:

* sx: standard deviation (not variance) of x var
* sy: standard deviation (not variance) of y var
* cxy: covariance (not correlation coefficient) of x and y

Returns: the scalar normalization
"""
    _bivcheck (sx, sy, cxy)
    from numpy import pi, sqrt

    t = (sx * sy)**2 - cxy**2
    if t <= 0:
        raise ValueError ('covariance just barely out of bounds '
                          '(sx=%.10e, sy=%.10e, cxy=%.10e, cxy/sxsy=%.16f)' %
                          (sx, sy, cxy, cxy / (sx * sy)))
    return (2 * pi * sqrt (t))**-1


def bivabc (sx, sy, cxy):
    """Compute nontrivial parameters for evaluating a bivariate distribution
as a 2D Gaussian. Inputs:

* sx: standard deviation (not variance) of x var
* sy: standard deviation (not variance) of y var
* cxy: covariance (not correlation coefficient) of x and y

Returns: (a, b, c), where z = k exp (ax^2 + bxy + cy^2)

The proper value for k can be obtained from bivnorm().
"""
    _bivcheck (sx, sy, cxy)

    sx2, sy2, cxy2 = sx**2, sy**2, cxy**2
    t = 1. / (sx2 * sy2 - cxy2)
    if t <= 0:
        raise ValueError ('covariance just barely out of bounds '
                          '(sx=%.10e, sy=%.10e, cxy=%.10e, cxy/sxsy=%.16f)' %
                          (sx, sy, cxy, cxy / (sx * sy)))

    a = -0.5 * sy2 * t
    c = -0.5 * sx2 * t
    b = cxy * t
    return _abccheck (a, b, c)


def bivnf (sx, sy, cxy):
    # NOTE: indirect; bad for precision
    _bivcheck (sx, sy, cxy)
    return abcnf (*bivabc (sx, sy, cxy))


def databiv (xy, coordouter=False, **kwargs):
    """Compute the main parameters of a bivariate distribution from data.
The parameters are returned in the same format as used in the rest of
this module.

* xy: a 2D data array of shape (2, nsamp) or (nsamp, 2)
* coordouter: if True, the coordinate axis is the outer axis; i.e.
    the shape is (2, nsamp). Otherwise, the coordinate axis is the
    inner axis; i.e. shape is (nsamp, 2).

Returns: (sx, sy, cxy)

In both cases, the first slice along the coordinate axis gives the X
data (i.e., xy[0] or xy[:,0]) and the second slice gives the Y data
(xy[1] or xy[:,1]).
"""
    xy = np.asarray (xy)
    if xy.ndim != 2:
        raise ValueError ('"xy" must be a 2D array')

    if coordouter:
        if xy.shape[0] != 2:
            raise ValueError ('if "coordouter" is True, first axis of "xy" must have size 2')
    else:
        if xy.shape[1] != 2:
            raise ValueError ('if "coordouter" is False, second axis of "xy" must have size 2')

    cov = np.cov (xy, rowvar=coordouter, **kwargs)
    sx, sy = np.sqrt (np.diag (cov))
    cxy = cov[0,1]
    return _bivcheck (sx, sy, cxy)


def bivplot (sx, sy, cxy, **kwargs):
    _bivcheck (sx, sy, cxy)
    return ellplot (*bivell (sx, sy, cxy), **kwargs)


# Ellipse form: major, minor, pa

def _ellcheck (maj, min, pa):
    if maj <= 0:
        raise ValueError ('maj must be positive (%.10e)' % maj)
    if min <= 0:
        raise ValueError ('min must be positive (%.10e)' % min)
    if min > maj:
        raise ValueError ('min must be less than maj (min=%.10e, maj=%.10e)' % (min, maj))
    return maj, min, pa


def ellnorm (maj, min, pa):
    if maj <= 0:
        raise ValueError ('maj must be positive (%.10e)' % maj)
    if min <= 0:
        raise ValueError ('min must be positive (%.10e)' % min)

    from numpy import pi
    hp = 0.5 * pi

    if min > maj:
        maj, min = min, maj
        pa += hp

    while pa < -hp:
        pa += pi
    while pa >= hp:
        pa -= pi

    return maj, min, pa


def ellpoint (maj, min, pa, th):
    """Compute a point on an ellipse parametrically. Inputs:

* maj: major axis (sigma not FWHM) of the ellipse
* min: minor axis (sigma not FWHM) of the ellipse
* pa: position angle (from +x to +y) of the ellipse, radians
* th: the parameter, 0 <= th < 2pi: the eccentric anomaly

Returns: (x, y)

th may be a vector, in which case x and y will be as well.
"""
    _ellcheck (maj, min, pa)
    from numpy import cos, sin
    ct, st = cos (th), sin (th)
    cp, sp = cos (pa), sin (pa)
    x = maj * cp * ct - min * sp * st
    y = maj * sp * ct + min * cp * st
    return x, y


def elld2 (x0, y0, maj, min, pa, x, y):
    """Given an 2D Gaussian expressed as an ellipse (major, minor,
pa), compute a "squared distance parameter" such that

   z = exp (-0.5 * d2)

Inputs:

* x0: position of Gaussian center on x axis
* y0: position of Gaussian center on y axis
* maj: major axis (sigma not FWHM) of the Gaussian
* min: minor axis (sigma not FWHM) of the Gaussian
* pa: position angle (from +x to +y) of the Gaussian, radians
* x: x coordinates of the locations for which to evaluate d2
* y: y coordinates of the locations for which to evaluate d2

Returns: d2, distance parameter defined as above.

x0, y0, maj, and min may be in any units so long as they're
consistent.  x and y may be arrays (of the same shape), in which case
d2 will be an array as well.
"""
    _ellcheck (maj, min, pa)

    dx, dy = x - x0, y - y0
    c, s = np.cos (pa), np.sin (pa)
    a = c * dx + s * dy
    b = -s * dx + c * dy
    return (a / maj)**2 + (b / min)**2


def ellabc (maj, min, pa):
    """Given a 2D Gaussian expressed as an ellipse (major, minor, pa),
compute the nontrivial parameters for its evaluation.

* maj: major axis (sigma not FWHM) of the Gaussian
* min: minor axis (sigma not FWHM) of the Gaussian
* pa: position angle (from +x to +y) of the Gaussian, radians

Returns: (a, b, c), where z = exp (ax^2 + bxy + cy^2)
"""
    _ellcheck (maj, min, pa)

    cpa, spa = np.cos (pa), np.sin (pa)
    majm2, minm2 = maj**-2, min**-2

    a = -0.5 * (cpa**2 * majm2 + spa**2 * minm2)
    c = -0.5 * (spa**2 * majm2 + cpa**2 * minm2)
    b = cpa * spa * (minm2 - majm2)

    return _abccheck (a, b, c)


def ellplot (maj, min, pa):
    """Utility for debugging."""
    _ellcheck (maj, min, pa)
    import omega as om

    th = np.linspace (0, 2 * np.pi, 200)
    x, y = ellpoint (maj, min, pa, th)
    return om.quickXY (x, y, 'maj=%f min=%f pa=%f' % (maj, min, pa * 180 / np.pi))


# "ABC" form (maybe better called polynomial form): exp (Ax^2 + Bxy + Cy^2)

def _abccheck (a, b, c):
    if a >= 0:
        raise ValueError ('a must be negative (%.10e)' % a)
    if c >= 0:
        raise ValueError ('c must be negative (%.10e)' % c)
    if b**2 >= 4 * a * c:
        raise ValueError ('must have b^2 < 4ac (a=%.10e, c=%.10e, '
                          'b=%.10e, b^2/4ac=%.10e)' % (a, c, b, b**2/(4*a*c)))

    return a, b, c



def abcell (a, b, c):
    """Given the nontrivial parameters for evaluation a 2D Gaussian
as a polynomial, compute the equivalent ellipse parameters (major, minor, pa)

Inputs: (a, b, c), where z = exp (ax^2 + bxy + cy^2)

Returns:

* maj: major axis (sigma not FWHM) of the Gaussian
* min: minor axis (sigma not FWHM) of the Gaussian
* pa: position angle (from +x to +y) of the Gaussian, radians
"""
    _abccheck (a, b, c)

    from numpy import arctan2, sqrt

    pa = 0.5 * arctan2 (b, a - c)

    t1 = np.sqrt ((a - c)**2 + b**2)
    t2 = -t1 - a - c
    if t2 <= 0:
        raise ValueError ('abc parameters just barely illegal [1] '
                          '(a=%.10e, c=%.10e, b=%.10e, b^2/4ac=%.10e)'
                          % (a, c, b, b**2/(4*a*c)))
    maj = t2**-0.5

    t2 = t1 - a - c
    if t2 <= 0: # should never be a problem but ...
        raise ValueError ('abc parameters just barely illegal [1] '
                          '(a=%.10e, c=%.10e, b=%.10e, b^2/4ac=%.10e)'
                          % (a, c, b, b**2/(4*a*c)))
    min = t2**-0.5

    return ellnorm (maj, min, pa)



def abcd2 (x0, y0, a, b, c, x, y):
    """Given an 2D Gaussian expressed as the ABC polynomial
coefficients, compute a "squared distance parameter" such that

   z = exp (-0.5 * d2)

Inputs:

* x0: position of Gaussian center on x axis
* y0: position of Gaussian center on y axis
* a: such that z = exp (ax^2 + bxy + cy^2)
* b: see above
* c: see above
* x: x coordinates of the locations for which to evaluate d2
* y: y coordinates of the locations for which to evaluate d2

Returns: d2, distance parameter defined as above.

This is pretty trivial. Mainly for testing.
"""
    _abccheck (a, b, c)
    dx, dy = x - x0, y - y0
    return -2 * (a * dx**2 + b * dx * dy + c * dy**2)


def abcnf (a, b, c):
    _abccheck (a, b, c)
    u = np.log (-a)
    v = np.log (-c)
    w = 1 + np.arctanh (b / (2 * np.sqrt (a * c)))
    return u, v, w


def abcplot (a, b, c, **kwargs):
    _abccheck (a, b, c)
    return ellplot (*abcell (a, b, c), **kwargs)


# PROTOTYPE numerically friendly

def nfabc (u, v, w):
    a = -np.exp (u)
    c = -np.exp (v)
    b = 2 * np.tanh (w - 1) * np.exp (0.5 * (u + v))
    return _abccheck (a, b, c)


def nfell (u, v, w):
    # NOTE: indirect; bad for precision
    return abcell (*nfabc (u, v, w))


def nfd2 (x0, y0, u, v, w, x, y):
    # TODO: compute directly if the nf parametrization turns out to be useful.
    a, b, c = nfabc (u, v, w)
    return abcd2 (x0, y0, a, b, c, x, y)


def nfplot (u, v, w, **kwargs):
    return ellplot (*nfell (u, v, w), **kwargs)
