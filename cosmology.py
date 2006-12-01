from numpy import sqrt, abs, sin, sinh
from scipy import integrate
from cgs import c, G, pi, cmperpc, syrpers

H0 = 1e7 / (1e6 * cmperpc) # in s^-1 h^-1
H0_73 = H0 * 0.73 # in s^-1 for h = 0.73
invH0 = 1 / H0 * syrpers / 1e9 # in gyr / h
rhocrit = 3 * H0**2 / 8 / pi / G # in g cm^-3 h^-2
rhocrit_73 = rhocrit * 0.73**2

def calck (oM, oL):
    # must return cm^-2 h^-2
    """Given \Omega_m and \Omega_\Lambda, return the
    curvature parameter, k, in units of cm^-2 h^-2.
    The h in these units refers to the normalization
    of the current value of the Hubble parameter."""

    return H0**2 / c**2 * (oM + oL - 1)

def ksinn (k, x):
    """Return 1/sqrt(|k|) * sinn (sqrt(|k| x), where
    sinn(x) yields x if k == 0, sin(x) if k > 0, and
    sinh(x) if k < 0. This function avoids division
    by zero if k == 0 and returns x in that condition."""

    if k == 0.: return x
    rtabsk = sqrt (abs (k))
    if k > 0.: return sin (rtabsk * x) / rtabsk
    return sinh (rtabsk * x) / rtabsk

def rofz_integral (z, oM, oL):
    def integrand (zp, oM, oL):
    	zp1 = zp + 1
	r = oM * zp1**3 + oL + (1 - oM - oL) * zp1**2
	return 1. / sqrt (r)
    (y, tmp) = integrate.quad (integrand, 0, z, (oM, oL))    
    return y

def rofz (z, oM, oL):
    """Returns the comoving distance in cm h between 
    the observer and a point at redshift z, taking the given 
    cosmological parameters. Here h is the parameter fixing
    the current value of the Hubble parameter."""

    def integrand (zp):
    	zp1 = zp + 1
	r = oM * zp1**3 + oL + (1 - oM - oL) * zp1**2
	return 1. / sqrt (r)
    (I, tmp) = integrate.quad (integrand, 0, z)    
    arg = c / H0 * I
    k = calck (oM, oL)
    return ksinn (k, arg)

def muofz (z, h, oM, oL):
    """Returns the 'distance modulus' for a redshift z,
    taking the given cosmological parameters. The argument
    h specifies the current value of the Hubble parameter
    in the usual way."""

    r = rofz (z, oM, oL)
    return 5 * log10 ((1 + z) * r / h / (10 * cmperpc))

def tofz (z, oM, oL):
	# Return gyr / h ... ? Or gyr * h?
	def integrand (z, oM, oL):
		zp1 = z + 1
		oT = oM + oL
		q = zp1 * sqrt (oM * zp1**3 + oL + (1 - oT) * zp1**2)
		return 1. / q
	(y, nil) = integrate.quad (integrand, z, integrate.Inf, (oM, oL))
	return y * invH0

def age (oM, oL): return tofz (0, oM, oL)

def ang_diam_dist (z, D, oM, oL):
	# assumes D in cm; returns radians
	return (1 + z) * D / rofz (z, oM, oL)
