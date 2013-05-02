# -*- mode: python; coding: utf-8 -*-
# Copyright 2012-2013 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""
astutil - miscellaneous astronomical utilities
"""

import numpy as np

pi = np.pi
twopi = 2 * pi
halfpi = 0.5 * pi

R2A = 3600 * 180 / pi
A2R = pi / (3600 * 180)
R2D = 180 / pi
D2R = pi / 180
R2H = 12 / pi
H2R = pi / 12
F2S = 1 / np.sqrt (8 * np.log (2)) # FWHM to sigma
S2F = np.sqrt (8 * np.log (2))

__all__ = 'np pi twopi halfpi R2A A2R R2D D2R R2H H2R F2S S2F'.split ()


# Angle and orientation (PA) normalization
#
# PA's seem to usually be given in the range [-90, 90]

angcen = lambda a: (((a + pi) % twopi) - pi)

orientcen = lambda a: (((a + halfpi) % pi) - halfpi)

__all__ += 'angcen orientcen'.split ()


# Formatting/parsing of lat/long/etc

def _fmtsexagesimal (base, norm, basemax, seps, precision=3):
    if norm == 'none':
        pass
    elif norm == 'raise':
        if base > basemax or base < 0:
            raise ValueError ('illegal coordinate of %f' % base)
    elif norm == 'wrap':
        base = base % basemax
    else:
        raise ValueError ('unrecognized normalization type "%s"' % norm)

    if len (seps) < 2:
        # To ponder: we accept len(seps) > 3; seems OK.
        raise ValueError ('there must be at least two sexagesimal separators; '
                          'got value "%s"' % seps)

    precision = max (int (precision), 0)
    if precision == 0:
        width = 2
    else:
        width = precision + 3

    basewidth = len (str (basemax))

    bs = int (np.floor (base))
    min = int (np.floor ((base - bs) * 60))
    sec = round (3600 * (base - bs - min / 60.), precision)

    if sec >= 60:
        # Can happen if we round up
        sec -= 60
        min += 1

        if min >= 60:
            min -= 60
            bs += 1

            if bs >= basemax:
                bs -= basemax

    if len (seps) > 2:
        sep2 = seps[2]
    else:
        sep2 = ''

    return '%0*d%s%02d%s%0*.*f%s' % \
        (basewidth, bs, seps[0], min, seps[1], width, precision, sec, sep2)


def fmthours (radians, norm='wrap', precision=3, seps='::'):
    """(radians, norm=wrap, precision=3) -> string

norm[alization] can be one of 'none', 'raise', or 'wrap'
"""
    return _fmtsexagesimal (radians * R2H, norm, 24, seps, precision=precision)


def fmtdeglon (radians, norm='wrap', precision=2, seps='::'):
    """(radians, norm=wrap, precision=2) -> string

norm[alization] can be one of 'none', 'raise', or 'wrap'
"""
    return _fmtsexagesimal (radians * R2D, norm, 360, seps, precision=precision)


def fmtdeglat (radians, norm='raise', precision=2, seps='::'):
    """(radians, norm=raise, precision=2) -> string

norm[alization] can be one of 'none', 'raise', or 'wrap'
"""

    if norm == 'none':
        pass
    elif norm == 'raise':
        if radians > halfpi or radians < -halfpi:
            raise ValueError ('illegal latitude of %f radians' % radians)
    elif norm == 'wrap':
        radians = angcen (radians)
        if radians > halfpi:
            radians = pi - radians
        elif radians < -halfpi:
            radians = -pi - radians
    else:
        raise ValueError ('unrecognized normalization type "%s"' % norm)

    if len (seps) < 2:
        # To ponder: we accept len(seps) > 3; seems OK.
        raise ValueError ('there must be at least two sexagesimal separators; '
                          'got value "%s"' % seps)

    precision = max (int (precision), 0)
    if precision == 0:
        width = 2
    else:
        width = precision + 3

    degrees = radians * R2D

    if degrees >= 0:
        sgn = '+'
    else:
        sgn = '-'
        degrees = -degrees

    deg = int (np.floor (degrees))
    amin = int (np.floor ((degrees - deg) * 60))
    asec = round (3600 * (degrees - deg - amin / 60.), precision)

    if asec >= 60:
        # Can happen if we round up
        asec -= 60
        amin += 1

        if amin >= 60:
            amin -= 60
            deg += 1

    if len (seps) > 2:
        sep2 = seps[2]
    else:
        sep2 = ''

    return '%s%02d%s%02d%s%0*.*f%s' % \
        (sgn, deg, seps[0], amin, seps[1], width, precision, asec, sep2)


def fmtradec (rarad, decrad, precision=2, raseps='::', decseps='::', intersep=' '):
    return fmthours (rarad, precision=precision + 1, seps=raseps) + str (intersep) \
        + fmtdeglat (decrad, precision=precision, seps=decseps)


__all__ += 'fmthours fmtdeglon fmtdeglat fmtradec'.split ()


# Parsing routines are currently very lame.

def _parsesexagesimal (sxgstr, desc, negok):
    sxgstr_orig = sxgstr
    sgn = 1

    if sxgstr[0] == '-':
        if negok:
            sgn = -1
            sxgstr = sxgstr[1:]
        else:
            raise ValueError ('illegal negative %s expression: %s' % (desc, sxgstr_orig))

    try:
        # TODO: other separators ...
        bs, mn, sec = sxgstr.split (':')
        bs = int (bs)
        mn = int (mn)
        sec = float (sec)
    except Exception:
        raise ValueError ('unable to parse as %s: %s' % (desc, sxgstr_orig))

    if mn < 0 or mn > 59 or sec < 0 or sec >= 60.:
        raise ValueError ('illegal sexagesimal %s expression: ' % (desc, sxgstr_orig))
    if bs < 0: # two minus signs, or something
        raise ValueError ('illegal negative %s expression: %s' % (desc, sxgstr_orig))

    return sgn * (bs + mn / 60. + sec / 3600.)


def parsehours (hrstr):
    hr = _parsesexagesimal (hrstr, 'hours', False)
    if hr >= 24:
        raise ValueError ('illegal hour specification: ' + hrstr)
    return hr * H2R


def parsedeglat (latstr):
    deg = _parsesexagesimal (latstr, 'latitude', True)
    if abs (deg) > 90:
        raise ValueError ('illegal latitude specification: ' + latstr)
    return deg * D2R


def parsedeglon (lonstr):
    return _parsesexagesimal (lonstr, 'longitude', True) * D2R


__all__ += 'parsehours parsedeglat parsedeglon'.split ()


# Spherical trig

def sphdist (lat1, lon1, lat2, lon2):
    """Args are: lat1, lon1, lat2, lon2 -- consistent with
    the usual coordinates in images, but note that this maps
    to (Dec, RA) or (Y, X), so be careful with this.
    """
    # "specialized Vincenty formula"
    # faster but more error-prone formula are possible; see Wikipedia
    # on Great-circle Distance

    cd = np.cos (lon2 - lon1)
    sd = np.sin (lon2 - lon1)
    c2 = np.cos (lat2)
    c1 = np.cos (lat1)
    s2 = np.sin (lat2)
    s1 = np.sin (lat1)

    a = np.sqrt ((c2 * sd)**2 + (c1 * s2 - s1 * c2 * cd)**2)
    b = s1 * s2 + c1 * c2 * cd
    return np.arctan2 (a, b)


def sphbear (lat1, lon1, lat2, lon2, erronpole=True, tol=1e-15):
    """Args are (lat1, lon1, lat2, lon2, erronpole=True, tol=1e-15) --
    consistent with the usual coordinates in images, but note that
    this maps to (Dec, RA) or (Y, X). All in radians. Returns the
    bearing (AKA position angle, PA) of point 2 with regards to point
    1.

    The sign convention is astronomical: bearing ranges from -pi to pi,
    with negative values if point 2 is in the western hemisphere w.r.t.
    point 1, positive if it is in the eastern.

    If point1 is very near the pole, the bearing is undefined and an
    exception is raised. If erronpole is set to False, 0 is returned
    instead.

    tol is used for checking pole nearness and for rounding the bearing
    to precisely zero if it's extremely small.

    Derived from bear() in angles.py from Prasanth Nair,
    https://github.com/phn/angles . His version is BSD licensed. This
    one is sufficiently different that I think it counts as a separate
    implementation.
    """

    v1 = np.asarray ([np.cos (lat1) * np.cos (lon1),
                      np.cos (lat1) * np.sin (lon1),
                      np.sin (lat1)])

    if v1[0]**2 + v1[1]**2 < tol:
        if erronpole:
            raise ValueError ('trying to compute undefined bearing from the pole')
        return 0.

    v2 = np.asarray ([np.cos (lat2) * np.cos (lon2),
                      np.cos (lat2) * np.sin (lon2),
                      np.sin (lat2)])

    p12 = np.cross (v1, v2) # ~"perpendicular to great circle containing points"
    p1z = np.asarray ([v1[1], -v1[0], 0.]) # ~"perp to base and Z axis"

    # ~"angle between these vectors"
    cm = np.sqrt ((np.cross (p12, p1z)**2).sum ())
    bearing = np.arctan2 (cm, np.dot (p12, p1z))

    if p12[2] < 0:
        bearing = -bearing

    if abs (bearing) < tol:
        return 0.
    return bearing


def sphofs (lat1, lon1, r, pa, tol=1e-2, rmax=None):
    """Args are: lat1, lon1, r, pa -- consistent with
    the usual coordinates in images, but note that this maps
    to (Dec, RA) or (Y, X). PA is East from North. Returns
    lat2, lon2.

    Error checking can be done in two ways. If tol is not
    None, sphdist() is used to calculate the actual distance
    between the two locations, and if the magnitude of the
    fractional difference between that and *r* is larger than
    tol, an exception is raised. This will add an overhead
    to the computation that may be significant if you're
    going to be calling this function a whole lot.

    If rmax is not None, magnitudes of *r* greater than that
    value are rejected. For reference, an *r* of 0.2 (~11 deg)
    gives a maximum fractional distance error of ~3%.
    """

    if rmax is not None and np.abs (r) > rmax:
        raise ValueError ('sphofs radius value %f is too big for '
                          'our approximation' % r)

    lat2 = lat1 + r * np.cos (pa)
    lon2 = lon1 + r * np.sin (pa) / np.cos (lat2)

    if tol is not None:
        s = sphdist (lat1, lon1, lat2, lon2)
        if np.any (np.abs ((s - r) / s) > tol):
            raise ValueError ('sphofs approximation broke down '
                              '(%s %s %s %s %s %s %s)' % (lat1, lon1,
                                                          lat2, lon2,
                                                          r, s, pa))

    return lat2, lon2


__all__ += 'sphdist sphbear sphofs'.split ()


# 2D Gaussian (de)convolution

def gaussianConvolve (maj1, min1, pa1, maj2, min2, pa2):
    """Args are maj1, min1, pa1, maj2, min2, pa2
PAs are in radians, axes can be in anything so long as they're consistent.
"""
    # copied from miriad/src/subs/gaupar.for:gaufac()
    c1 = np.cos (pa1)
    s1 = np.sin (pa1)
    c2 = np.cos (pa2)
    s2 = np.sin (pa2)

    a = (maj1*c1)**2 + (min1*s1)**2 + (maj2*c2)**2 + (min2*s2)**2
    b = (maj1*s1)**2 + (min1*c1)**2 + (maj2*s2)**2 + (min2*c2)**2
    g = 2 * ((min1**2 - maj1**2) * s1 * c1 + (min2**2 - maj2**2) * s2 * c2)

    s = a + b
    t = np.sqrt ((a - b)**2 + g**2)
    maj3 = np.sqrt (0.5 * (s + t))
    min3 = np.sqrt (0.5 * (s - t))

    if abs (g) + abs (a - b) == 0:
        pa3 = 0.
    else:
        pa3 = 0.5 * np.arctan2 (-g, a - b)

    # "Amplitude of the resulting Gaussian":
    # f = pi / (4 * np.log (2)) * maj1 * min1 * maj2 * min2 \
    #    / np.sqrt (a * b - 0.25 * g**2)

    return maj3, min3, pa3


def gaussianDeconvolve (smaj, smin, spa, bmaj, bmin, bpa):
    """'s' as in 'source', 'b' as in 'beam'. All arguments in
    radians. (Well, major and minor axes can be in any units, so long
    as they're consistent.)

    Returns dmaj, dmin, dpa, status
    Return units are consistent with the inputs.
    status is one of 'ok', 'pointlike', 'fail'

    Derived from miriad gaupar.for:GauDfac()

    We currently don't do a great job of dealing with pointlike
    sources. I've added extra code ensure smaj >= bmaj, smin >= bmin,
    and increased coefficient in front of "limit" from 0.1 to
    0.5. Feel a little wary about that first change.
    """

    from numpy import cos, sin, sqrt, min, abs, arctan2

    if smaj < bmaj:
        smaj = bmaj
    if smin < bmin:
        smin = bmin

    alpha = ((smaj * cos (spa))**2 + (smin * sin (spa))**2 -
             (bmaj * cos (bpa))**2 - (bmin * sin (bpa))**2)
    beta = ((smaj * sin (spa))**2 + (smin * cos (spa))**2 -
            (bmaj * sin (bpa))**2 - (bmin * cos (bpa))**2)
    gamma = 2 * ((smin**2 - smaj**2) * sin (spa) * cos (spa) -
                 (bmin**2 - bmaj**2) * sin (bpa) * cos (bpa))

    s = alpha + beta
    t = sqrt ((alpha - beta)**2 + gamma**2)
    limit = 0.5 * min ([smaj, smin, bmaj, bmin])**2
    #limit = 0.1 * min ([smaj, smin, bmaj, bmin])**2
    status = 'ok'

    if alpha < 0 or beta < 0 or s < t:
        dmaj = dmin = dpa = 0

        if 0.5 * (s - t) < limit and alpha > -limit and beta > -limit:
            status = 'pointlike'
        else:
            status = 'fail'
    else:
        dmaj = sqrt (0.5 * (s + t))
        dmin = sqrt (0.5 * (s - t))

        if abs (gamma) + abs (alpha - beta) == 0:
            dpa = 0
        else:
            dpa = 0.5 * arctan2 (-gamma, alpha - beta)

    return dmaj, dmin, dpa, status


__all__ += 'gaussianConvolve gaussianDeconvolve'.split ()


# Smooth a timeseries with uncertainties

def smooth (window, x, y, u=None, k=None):
    if k is None:
        k = window.size

    conv = lambda q, r: np.convolve (q, r, mode='valid')

    norm = conv (np.ones_like (x), window)
    cx = conv (x, window) / norm

    if u is None:
        cy = conv (y, window) / norm
        return cx[::k], cy[::k]

    w = u**-2
    cw = conv (w, window)
    cy = conv (w * y, window) / cw
    cu = np.sqrt (conv (w, window**2)) / cw
    return cx[::k], cy[::k], cu[::k]


__all__ += ['smooth']
