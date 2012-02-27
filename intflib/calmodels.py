#! /usr/bin/env python

models = {}
spindexes = {}

def CasA (freqInMHz, year):
    """Return the flux of Cas A given a frequency and the year of
    observation. Based on the formula given in Baars et al., 1977.
    
    Parameters:

    freq - Observation frequency in MHz.
    year - Year of observation. May be floating-point.

    Returns: s, flux in Jy.
    """
    from math import log10

    # The snu rule is right out of Baars et al. The dnu is corrected
    # for the frequency being measured in MHz, not GHz.
    
    snu = 10. ** (5.745 - 0.770 * log10 (freqInMHz)) # Jy
    dnu = 0.01 * (0.07 - 0.30 * log10 (freqInMHz)) # percent per yr.
    loss = (1 - dnu) ** (year - 1980.)

    return snu * loss

def initCasA (year):
    """Insert an entry for Cas A into the table of models. Need to
    specify the year of the observations to account for the time
    variation of Cas A's emission."""

    year = float (year)
    models['CasA'] = lambda f: CasA (f, year)


# Other models from Baars et al. 1977
# Data from Table 5 in that paper
# Some of these will be overwritten by VLA models below.

def _makeGenericBaars (a, b, c, fmin, fmax):
    from numpy import log10, any

    def f (freqInMHz):
        if any (freqInMHz < fmin) or any (freqInMHz > fmax):
            raise Exception ('Going beyond frequency limits of model!')
        
        lf = log10 (freqInMHz)
        return 10.**(a + b * lf + c * lf**2)

    return f

def _makeGenericBaarsSpindex (a, b, c, fmin, fmax):
    from numpy import log10, any

    def f (freqInMHz):
        if any (freqInMHz < fmin) or any (freqInMHz > fmax):
            raise Exception ('Going beyond frequency limits of model!')
        
        return b + 2 * c * log10 (freqInMHz)

    return f


def _addGenericBaars (src, a, b, c, fmin, fmax):
    models[src] = _makeGenericBaars (a, b, c, fmin, fmax)
    spindexes[src] = _makeGenericBaarsSpindex (a, b, c, fmin, fmax)


baarsParameters = {
    '3c48': (2.345, 0.071, -0.138, 405., 15000.),
    '3c123': (2.921, -0.002, -0.124, 405., 15000.),
    '3c147': (1.766, 0.447, -0.184, 405., 15000.),
    '3c161': (1.633, 0.498, -0.194, 405., 10700.),
    '3c218': (4.497, -0.910, 0.0, 405., 10700.),
    '3c227': (3.460, -0.827, 0.0, 405, 15000.),
    '3c249.1': (1.230, 0.288, -0.176, 405., 15000.),
    '3c286': (1.480, 0.292, -0.124, 405., 15000.),
    '3c295': (1.485, 0.759, -0.255, 405., 15000.),
    '3c348': (4.963, -1.052, 0., 405., 10700.),
    '3c353': (2.944, -0.034, -0.109, 405., 10700.),
    'DR21': (1.81, -0.122, 0., 7000., 31000.),
    'NGC7027': (1.32, -0.127, 0., 10000., 31000.)
}

for src, info in baarsParameters.iteritems ():
    _addGenericBaars (src, *info)

# VLA models of calibrators:
# see http://www.vla.nrao.edu/astro/calib/manual/baars.html
# These are the 1999.2 values. This makes them pretty out
# of date, but still a lot more recent than Baars.

def _makeVLAModel (a, b, c, d):
    from numpy import log10, any

    def f (freqInMHz):
        if any (freqInMHz < 300) or any (freqInMHz > 50000):
            raise StandardError ('Going beyond frequency limits of model!')
        
        lghz = log10 (freqInMHz) - 3
        return 10.**(a + b * lghz + c * lghz**2 + d * lghz**3)

    return f

def _makeVLASpindex (a, b, c, d):
    from numpy import log10, any

    def f (freqInMHz):
        if any (freqInMHz < 300) or any (freqInMHz > 50000):
            raise StandardError ('Going beyond frequency limits of model!')
        
        lghz = log10 (freqInMHz) - 3
        return b + 2 * c * lghz + 3 * d * lghz**2

    return f


def _addVLAModel (src, a, b, c, d):
    models[src] = _makeVLAModel (a, b, c, d)
    spindexes[src] = _makeVLASpindex (a, b, c, d)


vlaParameters = {
    # These are the "1999.2" model parameters. These seem to
    # be the most recent available.
    '3c48': (1.31752, -0.74090, -0.16708, +0.01525),
    '3c138': (1.00761, -0.55629, -0.11134, -0.01460),
    '3c147': (1.44856, -0.67252, -0.21124, +0.04077),
    '3c286': (1.23734, -0.43276, -0.14223, +0.00345),
    '3c295': (1.46744, -0.77350, -0.25912, +0.00752)
}

for src, info in vlaParameters.iteritems ():
    _addVLAModel (src, *info)

# Crappier power-law models based on VLA Calibrator Manual
# catalog. It is not clear whether values in the catalog
# should be taken to supersede those given in the analytic
# models above, for those five sources that have analytic
# models. The catalog entries do not seem to necessarily
# be more recent than the analytic models.

def modelFromVLAObs (Lband, Cband):
    """Generate spectral model parameters from VLA calibrator
    table data. Lband is the L-band (20 cm) flux in Jy, Cband
    is the C-band (6 cm) flux in Jy.

    Returns (A, B), where the spectral model is

       log10 (Flux in Jy) = A * log10 (Freq in MHz) + B
    """

    import cgs
    from math import log10
    
    fL = log10 (1425)
    fC = log10 (4860)

    lL = log10 (Lband)
    lC = log10 (Cband)

    m = (lL - lC) / (fL - fC)

    return m, lL - m * fL

def funcFromVLAObs (Lband, Cband):
    A, B = modelFromVLAObs (Lband, Cband)
    from numpy import log10
    
    def f (freqInMHz):
        return 10.**(A * log10 (freqInMHz) + B)

    return f


def spindexFromVLAObs (Lband, Cband):
    A, B = modelFromVLAObs (Lband, Cband)
    
    def f (freqInMHz):
        return A

    return f


def addFromVLAObs (src, Lband, Cband):
    """Add an entry into the models table for a source based on the
    Lband and Cband entries from the VLA catalog."""

    if src in models: raise Exception ('Already have a model for ' + src)
    models[src] = funcFromVLAObs (Lband, Cband)
    spindexes[src] = spindexFromVLAObs (Lband, Cband)

# addFromVLA ('3c48', 16.50, 5.48)
addFromVLAObs ('3c84', 23.9, 23.3)
# addFromVLA ('3c138', 8.47, 3.78)

# If we're executed as a program, print out a flux given a source
# name

def _usage ():
    from sys import stderr, argv
    
    print >>stderr, """Usage: %s [-f] <source> <freq> [year]

Where:
  <source> is the source name (e.g., 3c348)
  <freq> is the observing frequency in MHz (e.g., 1420)
  [year] is the decimal year of the observation (e.g., 2007.8).
     Only needed if <source> is CasA.
  [-f] is "flux" mode, which prints out a three-item string
     that can be passed to MIRIAD tasks that accept a model flux
     and spectral index argument.

Prints the flux in Jy of the specified calibrator at the
specified frequency.""" % argv[0]
    return 0
    
def _interactive (args):
    from sys import stderr

    if len (args) < 1: return _usage ()

    fluxMode = (args[0] == '-f')
    if fluxMode: del args[0]

    source = args[0]

    if source == 'CasA':
        if len (args) != 3: return _usage ()

        try:
            year = float (args[2])
            initCasA (year)
        except Exception, e:
            print >>stderr, 'Unable to parse year \"%s\":' % args[2], e
            return 1
    elif len (args) != 2: return _usage ()

    try:
        freq = float (args[1])
    except Exception, e:
        print >>stderr, 'Unable to parse frequency \"%s\":' % args[1], e
        return 1
        
    if source not in models:
        print >>stderr, 'Unknown source \"%s\". Known sources are:' % source
        print >>stderr, '   ', ', '.join (sorted (models.keys ()))
        return 1

    try:
        flux = models[source](freq)
    except Exception, e:
        # Catch, e.g, going beyond frequency limits.
        print >>stderr, 'Error finding flux of %s at %f MHz:' % (source, freq), e
        return 1

    if not fluxMode:
        print '%g' % (flux, )
        return 0

    try:
        spindex = spindexes[source](freq)
    except Exception, e:
        print >>stderr, 'WARNING: error finding spectral index of %s at %f MHz:' \
            % (source, freq), e
        spindex = 0

    print '%g,%g,%g' % (flux, freq * 1e-3, spindex)
    return 0


if __name__ == '__main__':
    from sys import argv, exit
    exit (_interactive (argv[1:]))
