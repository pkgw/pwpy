# -*- mode: python; coding: utf-8 -*-

"""
astutil - miscellaneous astronomical utilities
"""

import numpy as N

pi = N.pi
twopi = 2 * pi
halfpi = 0.5 * pi

R2A = 3600 * 180 / N.pi
A2R = N.pi / (3600 * 180)
R2D = 180 / N.pi
D2R = N.pi / 180
R2H = 12 / N.pi
H2R = N.pi / 12
F2S = 1 / N.sqrt (8 * N.log (2)) # FWHM to sigma
S2F = N.sqrt (8 * N.log (2))

__all__ = 'N pi twopi halfpi R2A A2R R2D D2R R2H H2R F2S S2F'.split ()


# Angle and orientation (PA) normalization
#
# PA's seem to usually be given in the range [-90, 90]

angcen = lambda a: (((a + pi) % twopi) - pi)

orientcen = lambda a: (((a + halfpi) % pi) - halfpi)

__all__ += 'angcen orientcen'.split ()


# Formatting/parsing of lat/long/etc

def _fmtsexagesimal (base, norm, basemax, precision=3):
    if norm == 'none':
        pass
    elif norm == 'raise':
        if base > basemax or base < 0:
            raise ValueError ('illegal coordinate of %f' % base)
    elif norm == 'wrap':
        base = base % basemax
    else:
        raise ValueError ('unrecognized normalization type "%s"' % norm)

    precision = max (int (precision), 0)
    if precision == 0:
        width = 2
    else:
        width = precision + 3

    basewidth = len (str (basemax))

    bs = int (N.floor (base))
    min = int (N.floor ((base - bs) * 60))
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

    return '%0*d:%02d:%0*.*f' % \
        (basewidth, bs, min, width, precision, sec)


def fmthours (radians, norm='wrap', precision=3):
    """(radians, norm=wrap, precision=3) -> string

norm[alization] can be one of 'none', 'raise', or 'wrap'
"""
    return _fmtsexagesimal (radians * R2H, norm, 24, precision=precision)


def fmtdeglon (radians, norm='wrap', precision=2):
    """(radians, norm=wrap, precision=2) -> string

norm[alization] can be one of 'none', 'raise', or 'wrap'
"""
    return _fmtsexagesimal (radians * R2D, norm, 360, precision=precision)


def fmtdeglat (radians, norm='raise', precision=2):
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

    deg = int (N.floor (degrees))
    amin = int (N.floor ((degrees - deg) * 60))
    asec = round (3600 * (degrees - deg - amin / 60.), precision)

    if asec >= 60:
        # Can happen if we round up
        asec -= 60
        amin += 1

        if amin >= 60:
            amin -= 60
            deg += 1

    return '%s%02d:%02d:%0*.*f' % \
        (sgn, deg, amin, width, precision, asec)


def fmtradec (rarad, decrad, precision=2):
    return fmthours (rarad, precision=precision + 1) + ' ' \
        + fmtdeglat (decrad, precision=precision)


__all__ += 'fmthours fmtdeglon fmtdeglat fmtradec'.split ()


# Parsing routines are currently very lame.

def parsehours (hrstr):
    try:
        hr, mn, sec = hrstr.split (':')
        hr = int (hr)
        mn = int (mn)
        sec = float (sec)
    except Exception:
        raise ValueError ('unable to parse as hours: ' + hrstr)

    if hr < 0 or hr > 23 or mn < 0 or mn > 59 or sec < 0 or sec >= 60.:
        raise ValueError ('illegal hour specification: ' + hrstr)

    return (hr + mn / 60. + sec / 3600.) * N.pi / 12


def parsedeglat (latstr):
    if latstr[0] != '-':
        sgn = 1
    else:
        sgn = -1
        latstr = latstr[1:]

    try:
        deg, mn, sec = latstr.split (':')
        deg = int (deg)
        mn = int (mn)
        sec = float (sec)
    except Exception:
        raise ValueError ('unable to parse as latitude: ' + latstr)

    if deg < 0 or deg > 90 or mn < 0 or mn > 59 or sec < 0 or sec >= 60.:
        raise ValueError ('illegal latitude specification: ' + latstr)

    return sgn * (deg + mn / 60. + sec / 3600.) * N.pi / 180


__all__ += 'parsehours parsedeglat'.split ()


# Spherical trig

def sphdist (lat1, lon1, lat2, lon2):
    """Args are: lat1, lon1, lat2, lon2 -- consistent with 
    the usual coordinates in images, but note that this maps
    to (Dec, RA) or (Y, X), so be careful with this.
    """
    # "specialized Vincenty formula"
    # faster but more error-prone formula are possible; see Wikipedia
    # on Great-circle Distance

    cd = N.cos (lon2 - lon1)
    sd = N.sin (lon2 - lon1)
    c2 = N.cos (lat2)
    c1 = N.cos (lat1)
    s2 = N.sin (lat2)
    s1 = N.sin (lat1)

    a = N.sqrt ((c2 * sd)**2 + (c1 * s2 - s1 * c2 * cd)**2)
    b = s1 * s2 + c1 * c2 * cd
    return N.arctan2 (a, b)

__all__ += 'sphdist'.split ()


# 2D Gaussian (de)convolution

def gaussianConvolve (maj1, min1, pa1, maj2, min2, pa2):
    """Args are maj1, min1, pa1, maj2, min2, pa2
PAs are in radians, axes can be in anything so long as they're consistent.
"""
    # copied from miriad/src/subs/gaupar.for:gaufac()
    c1 = N.cos (pa1)
    s1 = N.sin (pa1)
    c2 = N.cos (pa2)
    s2 = N.sin (pa2)

    a = (maj1*c1)**2 + (min1*s1)**2 + (maj2*c2)**2 + (min2*s2)**2
    b = (maj1*s1)**2 + (min1*c1)**2 + (maj2*s2)**2 + (min2*c2)**2
    g = 2 * ((min1**2 - maj1**2) * s1 * c1 + (min2**2 - maj2**2) * s2 * c2)

    s = a + b
    t = N.sqrt ((a - b)**2 + g**2)
    maj3 = N.sqrt (0.5 * (s + t))
    min3 = N.sqrt (0.5 * (s - t))

    if abs (g) + abs (a - b) == 0:
        pa3 = 0.
    else:
        pa3 = 0.5 * N.arctan2 (-g, a - b)

    # "Amplitude of the resulting Gaussian":
    # f = N.pi / (4 * N.log (2)) * maj1 * min1 * maj2 * min2 \
    #    / N.sqrt (a * b - 0.25 * g**2)

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
