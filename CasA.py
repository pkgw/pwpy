def CasAFlux (freq, year):
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
