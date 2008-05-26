#! /usr/bin/env python

"""Routines for doing useful things with calibrator sources."""

# 'cals' is a table of:
#
#   catalog ident
#   RA in decimal hours
#   Dec in decimal degrees
#   flux @ 20 cm in Jy from VLA table.
#
# Coordinates are from the output of 'atacheck', zero-padded
# to align the columns (we shouldn't use these coordinates
# for anything important; just for guessing what's up, etc.
# The catalog software should be the canonical source of
# coordinates.)
#
# Try to keep the table sorted by RA.

cals = [ (    '3c48', 1.628055556,  33.15972222, 16.5),
         (    '3c84', 3.329888889,  41.51166667, 24.),
         (   '3c119', 4.543473100,  41.64123060, 8.6),
         (   '3c123', 4.617833333,  29.67111111, 20.),
         (   '3c138', 5.352751100,  16.63947670, 8.5),
         (   '3c147', 5.710055556,  49.85194444, 22.5),
         ('0744-064', 7.739350300,  -6.49330220, 8.5),
         ('0834+555', 8.581917500,  55.57251920, 8.8),
         ('1130-148', 11.50195920, -14.82427500, 5.3),
         (   '3c273', 12.50019444,   2.05250000, 32.),
         (   '3c274', 12.51372890,  12.39112330, 0.0),
         (   '3c279', 12.93643530,  -5.78931310, 0.0),
         (   '3c286', 13.51877778,  30.50888889, 15),
         ('1347+122', 13.79260000,  12.29005580, 5.2),
         (   '3c345', 16.71633610,  39.81027580, 8.),
         ('1733-130', 17.55075170, -13.08042940, 5.2),
         (   '3c380', 18.49214970,  48.74638080, 14.2),
         (   '3c395', 19.04887170,  31.99490780, 3.0),
         ('2038+513', 20.64362080,  51.32018470, 5.8),
         (   'BLLac', 22.04535860,  42.27777280, 6.1),
         ('2206-185', 22.10289310, -18.59410060, 6.4),
         (    'CasA', 23.39077778,  58.80777778, 1200.)
]

max_elevation = 84.0
min_elevation = 18.0

import ataprobe

def suggestCals (lst=None, cutoffHA = 5.0):
    """Return a list of calibrators that may be useful for observations
    taking place at the given LST. If no arguments are supplied, the
    current LAST is used, and 'atacheck' is used to get more detailed
    information about the calibrators. Otherwise, 'az', 'el', and
    'setsIn' below are set to None.

    See also rankCals, which uses an ad-hoc formula to rank the
    desirability of the available calibrators.
    
    Returns a list of (ident, RA, Dec, flux20cm, az, el, setsIn) where
    the tuple elements are:

    ident    - Identifier of the source
    ra       - Its approximate RA in decimal hours
    dec      - Its approximate dec in decimal degrees
    flux20cm - Its approximate flux at 20 cm according to the VLA
    az       - Its current azimuth
    el       - Its current elevation
    setsIn   - The number of hours until the source sets below 18 deg elevation.
    """

    usingNow = lst is None
    if usingNow: lst = ataprobe.getLAST ()
    
    poss = []

    for (ident, ra, dec, flux20cm) in cals:
        ha = lst - ra

        if abs (ha) > cutoffHA: continue

        # Note that check() will return perfectly valid az, el,
        # and setsIn values for a source that isn't up, but that
        # those values won't be at all meaningful in evaluating
        # the suitability of the source as a calibrator. So we
        # don't provide them.
        
        if usingNow:
            (isUp, az, el, risesIn, setsIn) = ataprobe.check (ident)

            if not isUp: continue
        else:
            az = el = setsIn = None
        
        poss.append ((ident, ra, dec, flux20cm, az, el, setsIn))

    return poss

def rankCals (lst=None, **kwargs):
    """Return a list of calibrators ranked by how useful they might be.
    Uses an ad-hoc ranking formula; see the source code for exactly
    how it works. If 'lst' is not specified, much more detailed
    information can be derived via atacheck. Otherwise, az, el, and
    setsIn below are set to None.

    Returns a list of (ident, score, RA, Dec, flux20cm, az, el, setsIn)
    where the tuple elements are:

    ident    - Identifier of the source
    score    - This source's score according to the ranking formula;
               higher is better.
    ra       - Its approximate RA in decimal hours
    dec      - Its approximate dec in decimal degrees
    flux20cm - Its approximate flux at 20 cm according to the VLA
    az       - Its current azimuth
    el       - Its current elevation
    setsIn   - The number of hours until the source sets below 18 deg elevation.
    """


    poss = suggestCals (lst, **kwargs)

    newposs = []

    for (ident, ra, dec, flux20cm, az, el, setsIn) in poss:
        if flux20cm > 1000: eff_flux = 25.
        else: eff_flux = flux20cm

        if az is None:
            ha = lst - ra
            score = eff_flux * 10. + (12 - abs (ha)) * 20.
        else:
            if el > max_elevation: eff_el = 15.
            else: eff_el = el
        
            score = eff_el + setsIn * 20. + eff_flux * 10.

            if az > 330.0: # going to transit north soon, maybe?
                score -= 150.

        newposs.append ((ident, score, ra, dec, flux20cm, az, el, setsIn))

    newposs.sort (key = lambda tup: tup[1], reverse=True)
    return newposs

def printRanked (cals):
    """Print a list of ranked calibrators as returned from rankCals."""

    print '%20s %8s %8s %8s %8s %8s %8s %8s' % \
              ('Ident', 'Score', 'Flux20cm', 'RA', 'Dec', 'CurAz', 'CurEl', 'SetsIn')
    print
    
    for (id, sc, ra, de, fl, az, el, si) in cals:
        if az is None:
            az = -1.
            el = -1.
            si = -1.
        
        print '%20s %8.0f %8.1f %8.4f %+8.4f %8.3f %8.4f %8.2f' % \
              (id, sc, fl, ra, de, az, el, si)

if __name__ == '__main__':
    import sys

    try:
        if len (sys.argv) == 1: lst = None
        elif len (sys.argv) != 2: raise Exception ()
        else: lst = float (sys.argv[1])
        printRanked (rankCals (lst))
    except:
        print >>sys.stderr, 'Usage: %s [LST to check]' % sys.argv[0]

