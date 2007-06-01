# physical constants

# make e the electron charge
from numpy import pi, e as euler, exp

# erg = esu**2 / cm -> esu = m^1/2 cm^3/2 s^-1
# erg / cm^3 = (E|B)^2 -> [field] = m^1/2 cm^-1/2 s^-1
# esu * field = dyne

c = 2.99792458e10 # cm / s
h = 6.6260755e-27 # erg s
me = 9.1093897e-28 # g
mp = 1.6726231e-24 # g
e = 4.802e-10 # esu
G = 6.67259e-8 # cm^3 g^-1 s^-2
k = 1.3806505e-16 # erg / K
hbar = h / 2 / pi
alpha = e**2  / hbar / c # dimensionless
sigma = pi**2 * k ** 4 * hbar**-3 * c**-2 / 60 # g s^-3 K^-4
a0 = hbar**2 / (me * e**2) # cm
re = e**2 / (me * c**2) # cm
Ryd1 = e**2 / (2 * a0) # erg
mue = e * hbar / (2 * me * c) # magnetic moment units, whatever those are
sigmaT = 8 * pi * re**2 / 3 # cm^2
ergpereV = 1.60e-12 # erg / eV [dimensionless]
eVpererg = 1. / ergpereV
cmperpc = 3.08568025e18 # cm / pc [dimensionless]
pcpercm = 1. / cmperpc
cmperAU = 1.49598e13 # cm / AU [dimensionless]
AUpercm = 1. / cmperAU
spersyr = 31558150. # s / sidereal yr [dimensionless]
syrpers = 1. / spersyr

# Astro
mSun = 1.989e33 # g
rSun = 6.9599e10 # cm

bnu = lambda nu, T: 2 * h * nu**3 * c**-2 / (exp (h * nu / k / T) - 1)
