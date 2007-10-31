def CasA (freq, year):
    """Return the flux of Cas A given a frequency and the year of
    observation. Based on the formula given in Baars et al., 1977.
    
    Parameters:

    freq - Observation frequency in GHz.
    year - Year of observation. May be floating-point.

    Returns: s, flux in Jy.
    """
    from math import log10
    
    snu = 10. ** (5.745 - 0.770 * log10 (freq * 1000.)) # Jy
    dnu = 0.01 * (0.97 - 0.30 * log10 (freq)) # percent per yr.
    loss = (1 - dnu) ** (year - 1980.)

    return snu * loss

def modelFromVLA (Lband, Cband):
    """Generate spectral model parameters from VLA calibrator
    table data. Lband is the L-band (20 cm) flux in Jy, Cband
    is the C-band (6 cm) flux in Jy.

    Returns (A, B), where the spectral model is

       log10 (Flux in Jy) = A * log10 (Freq in MHz) + B
    """

    import cgs
    from math import log10
    
    fL = log10 (cgs.c / 20 / 1e6)
    fC = log10 (cgs.c / 6 / 1e6)

    lL = log10 (Lband)
    lC = log10 (Cband)

    m = (lL - lC) / (fL - fC)

    return m, lL - m * fL

def funcFromVLA (Lband, Cband):
    A, B = modelFromVLA (Lband, Cband)
    from numpy import log10
    
    def f (freq):
        return 10.**(A * log10 (freq) + B)

    return f
