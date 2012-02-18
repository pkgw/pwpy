"""
Tools for color mapping -- converting arrays of real-valued data to
other formats (usually, RGB24) for visualization.

TODO: "heated body" map

The generic interface is the *factory_map* variable, which is a
dictionary from colormap names to factory functions. The factory
functions return another function, the "mapper". Each mapper takes a
single argument, an array of values between 0 and 1, and returns
the mapped colors. If the input array has shape S, the returned value
has a shape (S + (3, )), with mapped[...,0] being the R values,
between 0 and 1, etc.

The basic colormap names are:

  moreland_bluered
    Divergent colormap from intense blue (at 0) to intense red (at 1),
    passing through white

  cubehelix_dagreen
    From black to white through rainbow colors

  cubehelix_blue
    From black to white, with blue hues

  pkgw
    From black to red, through purplish

  black_to_white, black_to_red, black_to_green, black_to_blue
    From black to the named colors.

  white_to_black, white_to_red, white_to_green, white_to_blue
    From white to the named colors.

The mappers can also take keyword arguments, including at least
"transform", which specifies simple transforms that can be applied to
the colormaps. These are (in terms of symbolic constants and literal
string values):

  TRANSFORM_NONE - 'none'
    No transform (the default)

  TRANSFORM_REVERSE - 'reverse'
    x -> 1 - x (reverses the colormap)

  TRANSFORM_SQRT - 'sqrt'
    x -> sqrt (x)

For each transform other than "none", *factory_map* contains an entry
with an underscore and the transform name applied (e.g.,
"pkgw_reverse") that has that transform applied.

The initial inspiration was an implementation of the ideas in
"Diverging Color Maps for Scientific Visualization (Expanded)",
Kenneth Moreland,

http://www.cs.unm.edu/~kmorel/documents/ColorMaps/index.html

I've realized that I'm not too fond of the white mid-values
in these color maps in many cases. So I also added an implementation
of the "cube helix" color map, described by D. A. Green in

"A colour scheme for the display of astronomical intensity images"
http://adsabs.harvard.edu/abs/2011BASI...39..289G
(D. A. Green, 2011 Bull. Ast. Soc. of India, 39 289)

I made up the pkgw map myself (who'd have guessed?).
"""

import numpy as N

base_factory_names = ('moreland_bluered cubehelix_dagreen cubehelix_blue '
                      'pkgw black_to_white black_to_red '
                      'black_to_green black_to_blue '
                      'white_to_black white_to_red '
                      'white_to_green white_to_blue').split ()

R, G, B = range (3)
X, Y, Z = range (3)
L, A, B = range (3) # fortunately this B and RGB's B agree...
M, S, H = range (3)

DEFAULT_SAMPLE_POINTS = 512

TRANSFORM_NONE = 'none'
TRANSFORM_REVERSE = 'reverse'
TRANSFORM_SQRT = 'sqrt'

# I don't quite understand where this value comes from, given the
# various Wikipedia values for D65, but this works.
CIELAB_D65 = N.asarray ([0.9505, 1., 1.0890])

# from Moreland:
_linsrgb_to_xyz = N.asarray ([[0.4124, 0.2126, 0.0193],
                              [0.3576, 0.7152, 0.1192],
                              [0.1805, 0.0722, 0.9505]])

# from Wikipedia, SRGB:
_xyz_to_linsrgb = N.asarray ([[3.2406, -0.9689, 0.0557],
                              [-1.5372, 1.8758, -0.2040],
                              [-0.4986, 0.0415, 1.0570]])



# Interpolation utilities. Given a colormap sampled at various values,
# compute splines that interpolate in R, G, and B (separately) for
# fast evaluation of the colormap for arbitrary float values. We have
# primitive support for some transformations, though these are
# generally best done upstream of the color mapping code.


def approx_colormap (samples, transform=TRANSFORM_NONE, fitfactor=1.):
    """
*samples* is of shape (4, n)
samples[0,:] are the normalized values at which the map is
  sampled, hopefully ranging uniformly between 0 and 1
samples[1:4,:] are the RGB values of the colormap. (They
  don't need to actually be RGB, but there need to be three
  of them.)

*transform* can be one of the TRANSFORM_* constants

Returns a function that maps an array of shape S into
an array of shape (S + (3,)), following a spline interpolation
from the sampled values.
"""
    import scipy.interpolate as SI

    values = samples[0]
    if transform == TRANSFORM_NONE:
        pass
    elif transform == TRANSFORM_REVERSE:
        samples = samples[:,::-1]
    elif transform == TRANSFORM_SQRT:
        values = N.sqrt (values)
    else:
        raise ValueError ('unknown transformation: ' + str (transform))

    nsamp = samples.shape[1]
    rspline = SI.splrep (values, samples[R+1], s=fitfactor/nsamp)
    gspline = SI.splrep (values, samples[G+1], s=fitfactor/nsamp)
    bspline = SI.splrep (values, samples[B+1], s=fitfactor/nsamp)

    def colormap (values):
        values = N.asarray (values)
        mapped = N.empty (values.shape + (3,))

        flatvalues = values.flatten ()
        flatmapped = mapped.reshape (flatvalues.shape + (3,))

        flatmapped[:,R] = SI.splev (flatvalues, rspline)
        flatmapped[:,G] = SI.splev (flatvalues, gspline)
        flatmapped[:,B] = SI.splev (flatvalues, bspline)

        return mapped

    return colormap


# Colorspace utilities based on the Moreland paper.

def srgb_to_linsrgb (srgb):
    """Convert sRGB values to physically linear
ones. The transformation is uniform in RGB, so
*srgb* can be of any shape.

*srgb* values should range between 0 and 1, inclusively.
"""

    gamma = ((srgb + 0.055) / 1.055)**2.4
    scale = srgb / 12.92
    return N.where (srgb > 0.04045, gamma, scale)


def linsrgb_to_srgb (linsrgb):
    """Convert physically linear RGB values into
sRGB ones. The transform is uniform in the components,
so *linsrgb* can be of any shape.

*linsrgb* values should range between 0 and 1, inclusively.
"""

    # From Wikipedia, but easy analogue to the above.
    gamma = 1.055 * linsrgb**(1./2.4) - 0.055
    scale = linsrgb * 12.92
    return N.where (linsrgb > 0.0031308, gamma, scale)


def linsrgb_to_xyz (linsrgb):
    """Convert linearized sRGB values (cf srgb_to_linsrgb)
to CIE XYZ values.

*linsrgb* should be of shape (*, 3). Values should range
  between 0 and 1 inclusively.
Return value will be of same shape.

Returned XYZ values range between [0, 0, 0] and
[0.9505, 1., 1.089].
"""

    return N.dot (linsrgb, _linsrgb_to_xyz)


def xyz_to_linsrgb (xyz):
    """Convert CIE XYZ values to linearized sRGB values (cf
srgb_to_linsrgb).

*xyz* should be of shape (*, 3)
Return value will be of same shape."""

    return N.dot (xyz, _xyz_to_linsrgb)


def xyz_to_cielab (xyz, refwhite):
    """Convert CIE XYZ color values to CIE L*a*b*.

*xyz* should be of shape (*, 3)
*refwhite* is the reference white value, of shape (3, )
Return value will have same shape as *xyz*, but be
in CIE L*a*b* coordinates.
"""

    norm = xyz / refwhite
    pow = norm**0.333333333333333
    scale = 7.787037 * norm + 16./116
    mapped = N.where (norm > 0.008856, pow, scale)

    cielab = N.empty_like (xyz)
    cielab[...,L] = 116 * mapped[...,Y] - 16
    cielab[...,A] = 500 * (mapped[...,X] - mapped[...,Y])
    cielab[...,B] = 200 * (mapped[...,Y] - mapped[...,Z])

    return cielab


def cielab_to_xyz (cielab, refwhite):
    """Convert CIE L*a*b* color values to CIE XYZ,

*cielab* should be of shape (*, 3)
*refwhite* is the reference white value in the L*a*b*
color space, of shape (3, )
Return value has same shape as *cielab*
"""
    def func (t):
        pow = t**3
        scale = 0.128419 * t - 0.0177129
        return N.where (t > 0.206897, pow, scale)

    xyz = N.empty_like (cielab)
    lscale = 1./116 * (cielab[...,L] + 16)
    xyz[...,X] = func (lscale + 0.002 * cielab[...,A])
    xyz[...,Y] = func (lscale)
    xyz[...,Z] = func (lscale - 0.005 * cielab[...,B])
    xyz *= refwhite
    return xyz


def cielab_to_msh (cielab):
    """Convert CIE L*a*b* to Moreland's Msh colorspace.

*cielab* should be of shape (*, 3)
Return value will have same shape.
"""
    msh = N.empty_like (cielab)
    msh[...,M] = N.sqrt ((cielab**2).sum (axis=-1))
    msh[...,S] = N.arccos (cielab[...,L] / msh[...,M])
    msh[...,H] = N.arctan2 (cielab[...,B], cielab[...,A])
    return msh


def msh_to_cielab (msh):
    """Convert Moreland's Msh colorspace to CIE L*a*b*.

*msh* should be of shape (*, 3)
Return value will have same shape.
"""
    cielab = N.empty_like (msh)
    cielab[...,L] = msh[...,M] * N.cos (msh[...,S])
    cielab[...,A] = msh[...,M] * N.sin (msh[...,S]) * N.cos (msh[...,H])
    cielab[...,B] = msh[...,M] * N.sin (msh[...,S]) * N.sin (msh[...,H])
    return cielab


def srgb_to_msh (srgb, refwhite):
    """Convert sRGB to Moreland's Msh color space, via
XYZ and CIE L*a*b*.

*srgb* should be of shape (*, 3)
*refwhite* is the CIE L*a*b* reference white color, of shape (3, )
Return value will have same shape.
"""
    return cielab_to_msh (xyz_to_cielab (linsrgb_to_xyz (srgb_to_linsrgb (srgb)),
                                         refwhite))


def msh_to_srgb (msh, refwhite):
    """Convert Moreland's Msh color space to sRGB, via
XYZ and CIE L*a*b*.

*msh* should be of shape (*, 3)
*refwhite* is the CIE L*a*b* reference white color, of shape (3, )
Return value will have same shape.
"""
    return linsrgb_to_srgb (xyz_to_linsrgb (cielab_to_xyz (msh_to_cielab (msh),
                                                           refwhite)))


# The Moreland divergent colormap generation algorithm

def moreland_adjusthue (msh, m_unsat):
    """Moreland's AdjustHue procedure to adjust the hue
value of an Msh color based on ... some criterion.

*msh* should be of of shape (3, )
*m_unsat* is a scalar
Return value is the adjusted h (hue) value
"""

    if msh[M] >= m_unsat:
        return msh[H] # "Best we can do"

    hspin = (msh[S] * N.sqrt (m_unsat**2 - msh[M]**2) /
             (msh[M] * N.sin (msh[S])))

    if msh[H] > -N.pi / 3: # "Spin away from purple"
        return msh[H] + hspin
    return msh[H] - hspin


def moreland_interpolate_sampled (srgb1, srgb2, refwhite=CIELAB_D65,
                                  nsamples=DEFAULT_SAMPLE_POINTS):
    # Adapted from Moreland's InterpolateColor. This uses the
    # full transformations to compute a color mapping at a set
    # of sampled points.

    msh1, msh2 = srgb_to_msh (N.asarray ([srgb1, srgb2],
                                         dtype=N.float), refwhite)

    raddiff = msh1[H] - msh2[H]
    while raddiff > N.pi:
        raddiff -= 2 * N.pi
    while raddiff < -N.pi:
        raddiff += 2 * N.pi
    raddiff = N.abs (raddiff)

    x = N.linspace (0, 1, nsamples).reshape ((nsamples, 1))
    x = N.repeat (x, 3, 1)

    if msh1[S] <= 0.05 or msh2[S] <= 0.05 or raddiff < N.pi/3:
        # Colors are too close together to comfortably put white in
        # between. Our interpolation won't have a control point, and
        # won't actually be divergent.

        if msh1[S] < 0.05 and msh2[S] > 0.05:
            msh1[H] = moreland_adjusthue (msh1, msh1[M])
        elif msh2[S] < 0.05 and msh1[S] > 0.05:
            msh2[H] = moreland_adjusthue (msh2, msh2[M])

        samples = N.empty ((4, nsamples))

        msh = (1 - x) * msh1 + x * msh2
        samples[0] = x[:,0]
        samples[1:4] = msh_to_srgb (msh, refwhite).T
    else:
        # Colors are not too close together -- we can add a white
        # control point in the middle, and do two interpolations
        # joined piecewise.  We then use 2*nsamples-1 (not actually
        # nsamples -- shhh) samples for the spline fit

        msh3 = msh2
        msh2a = N.asarray ([N.max ([msh1[M], msh3[M], 88]), 0, 0])
        msh2b = msh2a.copy ()

        if msh1[S] < 0.05 and msh2a[S] > 0.05:
            msh1[H] = moreland_adjusthue (msh2a, msh1[M])
        elif msh2a[S] < 0.05 and msh1[S] > 0.05:
            msh2a[H] = moreland_adjusthue (msh1, msh2a[M])

        if msh2b[S] < 0.05 and msh3[S] > 0.05:
            msh2b[H] = moreland_adjusthue (msh3, msh2b[M])
        elif msh3[S] < 0.05 and msh2b[S] > 0.05:
            msh3[H] = moreland_adjusthue (msh2b, msh3[M])

        samples = N.empty ((4, 2*nsamples-1))

        msh = (1 - x) * msh1 + x * msh2a
        samples[0,:nsamples] = 0.5 * x[:,0]
        samples[1:4,:nsamples] = msh_to_srgb (msh, refwhite).T

        msh = (1 - x) * msh2b + x * msh3
        samples[0,nsamples-1:] = 0.5 * x[:,0] + 0.5
        samples[1:4,nsamples-1:] = msh_to_srgb (msh, refwhite).T

    return samples


def moreland_bluered (transform=TRANSFORM_NONE):
    samples = moreland_interpolate_sampled ([0.2305, 0.2969, 0.7500],
                                            [0.7031, 0.0156, 0.1484])
    return approx_colormap (samples, transform=transform)


# D. A. Green's "cube helix" colormap

def cubehelix_create (start, rotations, hue, gamma):
    def colormap (values):
        values = N.asarray (values)
        mapped = N.empty (values.shape + (3,))

        flatvalues = values.flatten ()
        flatmapped = mapped.reshape (flatvalues.shape + (3,))

        gv = flatvalues ** gamma
        a = 0.5 * hue * gv * (1 - gv)
        phi = 2 * N.pi * (0.3333333 * start + rotations * flatvalues)
        c = N.cos (phi)
        s = N.sin (phi)

        flatmapped[:,R] = gv + a * (-0.14861 * c + 1.78277 * s)
        flatmapped[:,G] = gv + a * (-0.29227 * c - 0.90649 * s)
        flatmapped[:,B] = gv + a * 1.97294 * c

        return mapped
    return colormap


def cubehelix_sample (start, rotations, hue, gamma,
                      nsamples=DEFAULT_SAMPLE_POINTS):
    samples = N.empty ((4, nsamples,))
    samples[0] = N.linspace (0, 1, nsamples)
    samples[1:] = cubehelix_create (start, rotations, hue, gamma) (samples[0]).T
    return samples


def cubehelix_dagreen (transform=TRANSFORM_NONE):
    samples = cubehelix_sample (0.5, -1.5, 1.0, 1)
    return approx_colormap (samples, transform=transform)


def cubehelix_blue (transform=TRANSFORM_NONE):
    samples = cubehelix_sample (0.5, -0.6, 1.2, 1)
    return approx_colormap (samples, transform=transform)


# Something quick I came up with based on the Moreland work, scaling from
# black to a bright-ish red.

def pkgw (transform=TRANSFORM_NONE, nsamples=DEFAULT_SAMPLE_POINTS):
    samples = N.empty ((4, nsamples))
    samples[0] = N.linspace (0, 1, nsamples)

    msh = N.empty ((nsamples, 3))
    msh[:,M] = 1. + 85 * samples[0]
    msh[:,S] = 0.3 * samples[0] + 0.7
    msh[:,H] = 2.9 * samples[0] - 2.1

    samples[1:4] = msh_to_srgb (msh, CIELAB_D65).T

    return approx_colormap (samples, transform=transform)


# Simple maps linear in RGB

def rgblinear_create (factor_r, factor_g, factor_b,
                      zero_r, zero_g, zero_b,
                      transform=TRANSFORM_NONE):
    if transform == TRANSFORM_NONE:
        valmap = lambda x: x
    elif transform == TRANSFORM_REVERSE:
        valmap = lambda x: 1 - x
    elif transform == TRANSFORM_SQRT:
        valmap = N.sqrt
    else:
        raise ValueError ('unknown transformation: ' + str (transform))

    def colormap (values):
        values = valmap (N.asarray (values))
        mapped = N.empty (values.shape + (3,))
        flatvalues = values.flatten ()
        flatmapped = mapped.reshape (flatvalues.shape + (3,))
        flatmapped[:,R] = flatvalues * factor_r + zero_r
        flatmapped[:,G] = flatvalues * factor_g + zero_g
        flatmapped[:,B] = flatvalues * factor_b + zero_b
        return mapped

    return colormap


def black_to_white (transform=TRANSFORM_NONE):
    return rgblinear_create (1, 1, 1, 0, 0, 0, transform)

def black_to_red (transform=TRANSFORM_NONE):
    return rgblinear_create (1, 0, 0, 0, 0, 0, transform)

def black_to_green (transform=TRANSFORM_NONE):
    return rgblinear_create (0, 1, 0, 0, 0, 0, transform)

def black_to_blue (transform=TRANSFORM_NONE):
    return rgblinear_create (0, 0, 1, 0, 0, 0, transform)

def white_to_black (transform=TRANSFORM_NONE):
    return rgblinear_create (-1, -1, -1, 1, 1, 1, transform)

def white_to_red (transform=TRANSFORM_NONE):
    return rgblinear_create (0, -1, -1, 1, 1, 1, transform)

def white_to_green (transform=TRANSFORM_NONE):
    return rgblinear_create (-1, 0, -1, 1, 1, 1, transform)

def white_to_blue (transform=TRANSFORM_NONE):
    return rgblinear_create (-1, -1, 0, 1, 1, 1, transform)



# Useful for introspection
#
# Factories return a function that maps values between 0 and 1 into
# RGB values between 0 and 1, and accept a keyword argument
# 'transform' that can perform primitive transforms on the direction
# and scaling of the colormap.

factory_map = dict ((n, globals()[n]) for n in base_factory_names)

def _make_transformed (factory, transform):
    # We have to create these helper functions in a separate function
    # because otherwise some all of the new dict entries end up
    # referencing the finally-created subfunction.
    def newfactory ():
        return factory (transform=transform)
    return newfactory

def _fill_transforms ():
    for transform in (TRANSFORM_REVERSE, TRANSFORM_SQRT):
        for n in base_factory_names:
            factory = globals()[n]
            factory_map[n + '_' + transform] = \
                _make_transformed (factory, transform)

_fill_transforms ()


# Infrastructure for quickly rendering color maps.

def showdemo (factoryname, **kwargs):
    import gtk, cairo
    W, H = 512, 100

    colormap = factory_map[factoryname] (**kwargs)

    array = N.linspace (0, 1, W)
    array = array.reshape ((W, 1))
    array = N.repeat (array, H, 1).T

    mapped = colormap (array)
    argb = N.empty ((H, W), dtype=N.uint32)
    argb.fill (0xFF000000)
    argb |= (mapped[:,:,0] * 0xFF).astype (N.uint32) << 16
    argb |= (mapped[:,:,1] * 0xFF).astype (N.uint32) << 8
    argb |= (mapped[:,:,2] * 0xFF).astype (N.uint32)

    surf = cairo.ImageSurface.create_for_data (argb, cairo.FORMAT_ARGB32,
                                               W, H, W * 4)

    def expose (widget, event):
        ctxt = widget.window.cairo_create ()
        ctxt.set_source_surface (surf, 0, 0)
        pat = ctxt.get_source ()
        pat.set_extend (cairo.EXTEND_NONE)
        pat.set_filter (cairo.FILTER_NEAREST)
        ctxt.paint ()
        return True

    da = gtk.DrawingArea ()
    da.connect ('expose-event', expose)

    win = gtk.Window (gtk.WINDOW_TOPLEVEL)
    win.set_title ('Colormap Demo - ' + factoryname)
    win.set_default_size (W, H)
    win.connect ('destroy', gtk.main_quit)
    win.add (da)
    win.show_all ()
    gtk.main ()


def printmaps ():
    print 'Available color maps:'

    for m in sorted (factory_map.iterkeys ()):
        print '\t' + m


if __name__ == '__main__':
    import sys
    if len (sys.argv) < 2:
        printmaps ()
    else:
        showdemo (sys.argv[1])
