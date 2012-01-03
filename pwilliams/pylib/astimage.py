"""
astimage -- generic loading of radio astronomical images

Use `astimage.open (path, mode)` to open an astronomical image,
regardless of its file format.
"""

# Developer notes:
"""
Note that pyrap.images allegedly supports casacore, HDF5, FITS, and
MIRIAD format images transparently. Frankly, I don't trust it, and I'd
rather not require that casacore and pyrap be installed.

TODO: allow writing of data
 (useful in msimgen, msimhack)

TODO: for iminfo, need: axis types, ref freq

TODO: use axis types (e.g., self._wcs.{lat,lon,spec}) to allow some kind of
sanity-checking of image structure and squashing down to "canonical" 2D
form (I'm thinking 2D with axes of [lat,long]).

TODO: standardized celestial axis types for proper generic formatting
of RA/Dec ; glat/glon etc

TODO: subimages
"""

import numpy as N
from numpy import pi

D2R = pi / 180
R2D = 180 / pi
A2R = pi / (180 * 3600)
R2A = 180 * 3600 / pi
F2S = 1 / N.sqrt (8 * N.log (2)) # FWHM to sigma
S2F = N.sqrt (8 * N.log (2))

__all__ = ('UnsupportedError AstroImage MIRIADImage CASAImage '
           'FITSImage open').split ()


class UnsupportedError (RuntimeError):
    def __init__ (self, fmt, *args):
        if not len (args):
            self.message = str (fmt)
        else:
            self.message = fmt % args

    def __str__ (self):
        return self.message


class AstroImage (object):
    path = None
    _handle = None

    shape = None
    "An integer ndarray of the image shape"

    bmaj = None 
    "If not None, the restoring beam FWHM major axis in radians"

    bmin = None 
    "If not None, the restoring beam FWHM minor axis in radians"

    bpa = None 
    """If not None, the restoring beam position angle (east 
    from celestial north) in radians"""

    units = None
    "Lower-case string describing image units (e.g., jy/beam, jy/pixel)"


    def __init__ (self, path, mode):
        self.path = path


    def __del__ (self):
        self.close ()


    def close (self):
        if self._handle is not None:
            self._closeImpl ()
            self._handle = None


    def __enter__ (self):
        return self


    def __exit__ (self, etype, evalue, traceback):
        self.close ()
        return False # raise any exception that may have happened


    def _checkOpen (self):
        if self._handle is None:
            raise UnsupportedError ('this operation cannot be performed on the '
                                    'closed image at "%s"', self.path)


    def read (self, squeeze=False, flip=False):
        raise NotImplementedError ()


    def toworld (self, pixel):
        raise NotImplementedError ()


    def topixel (self, world):
        raise NotImplementedError ()


    def saveAsFITS (self, path, overwrite=False):
        raise NotImplementedError ()


def maybescale (x, a):
    if x is None:
        return None
    return a * x


def maybelower (x):
    if x is None:
        return None
    return x.lower ()


# We use WCSLIB/pywcs for coordinates for both FITS and MIRIAD
# images. It does two things that we don't like. First of all, it
# stores axes in Fortran style, with the first axis being the most
# rapidly varying. Secondly, it does all of its angular work in
# degrees, not radians (why??). We fix these up as best we can.

def _get_wcs_scale (wcs, naxis):
    import pywcs
    wcscale = N.ones (naxis)

    for i in xrange (naxis):
        q = wcscale.size - 1 - i
        text = wcs.wcs.cunit[q].strip ()

        try:
            uc = pywcs.UnitConverter (text, 'rad')
            wcscale[i] = uc.scale
        except SyntaxError: # !!
            pass # not an angle unit; don't futz.

    return wcscale


def _wcs_toworld (wcs, pixel, wcscale, naxis):
    # TODO: we don't allow the usage of "SIP" or "Paper IV"
    # transformations, let alone a concatenation of these, because
    # they're not invertible.

    pixel = N.asarray (pixel)
    if pixel.shape != (naxis, ):
        raise ValueError ('pixel coordinate must be a %d-element vector', naxis)

    pixel = pixel.reshape ((1, naxis))[:,::-1]
    world = wcs.wcs_pix2sky (pixel, 0)
    return world[0,::-1] * wcscale


def _wcs_topixel (wcs, world, wcscale, naxis):
    world = N.asarray (world)
    if world.shape != (naxis, ):
        raise ValueError ('world coordinate must be a %d-element vector', naxis)

    world = (world / wcscale)[::-1].reshape ((1, naxis))
    pixel = wcs.wcs_sky2pix (world, 0)
    return pixel[0,::-1]


class MIRIADImage (AstroImage):
    _modemap = {'r': 'rw', # no true read-only option
                'rw': 'rw'
                }

    def __init__ (self, path, mode):
        try:
            from mirtask import XYDataSet
        except ImportError:
            raise UnsupportedError ('cannot open MIRIAD images without the '
                                    'Python module "mirtask"')

        super (MIRIADImage, self).__init__ (path, mode)

        self._handle = h = XYDataSet (path, self._modemap[mode])
        self._wcs, warnings = h.wcs ()

        for w in warnings:
            # Whatever.
            import sys
            print >>sys.stderr, 'irregularity in coordinates of "%s": %s' % (self.path, w)

        naxis = h.getScalarItem ('naxis', 0)
        self.shape = N.empty (naxis, dtype=N.int)
        for i in xrange (naxis):
            q = naxis - i
            self.shape[i] = h.getScalarItem ('naxis%d' % q, 1)

        self.units = maybelower (h.getScalarItem ('bunit'))

        self.bmaj = h.getScalarItem ('bmaj')
        if self.bmaj is not None:
            self.bmin = h.getScalarItem ('bmin', self.bmaj)
            self.bpa = h.getScalarItem ('bpa', 0) * D2R

        self._wcscale = _get_wcs_scale (self._wcs, self.shape.size)


    def _closeImpl (self):
        self._handle.close ()


    def read (self, squeeze=False, flip=False):
        self._checkOpen ()
        nonplane = self.shape[:-2]

        if nonplane.size == 0:
            data = self._handle.readPlane ([], topIsZero=flip)
        else:
            data = N.ma.empty (self.shape, dtype=N.float32)
            n = N.prod (nonplane)
            fdata = data.reshape ((n, self.shape[-2], self.shape[-1]))

            for i in xrange (n):
                axes = N.unravel_index (i, nonplane)
                self._handle.readPlane (axes, fdata[i], topIsZero=flip)

        if squeeze:
            data = data.squeeze ()

        return data


    def toworld (self, pixel):
        # self._wcs is still valid if we've been closed, so no need
        # to _checkOpen().

        if self._wcs is None:
            raise UnsupportedError ('world coordinate information is required '
                                    'but not present in "%s"', self.path)

        return _wcs_toworld (self._wcs, pixel, self._wcscale, self.shape.size)


    def topixel (self, world):
        if self._wcs is None:
            raise UnsupportedError ('world coordinate information is required '
                                    'but not present in "%s"', self.path)

        return _wcs_topixel (self._wcs, world, self._wcscale, self.shape.size)


    def saveAsFITS (self, path, overwrite=False):
        from mirexec import TaskFits
        import os.path

        if os.path.exists (path):
            if overwrite:
                os.unlink (path)
            else:
                raise UnsupportedError ('refusing to export "%s" to "%s": '
                                        'destination already exists' % (self.path, path))

        TaskFits (op='xyout', in_=self.path, out=path).runsilent ()


def _casa_convert (d, unitstr):
    from pyrap.quanta import quantity
    return quantity (d['value'], d['unit']).get_value (unitstr)


class CASAImage (AstroImage):
    def __init__ (self, path, mode):
        try:
            from pyrap.images import image
        except ImportError:
            raise UnsupportedError ('cannot open CASAcore images without the '
                                    'Python module "pyrap.images"')

        super (CASAImage, self).__init__ (path, mode)

        # no mode specifiable
        self._handle = image (path)

        allinfo = self._handle.info ()
        self.units = maybelower (allinfo.get ('unit'))
        self.shape = N.asarray (self._handle.shape (), dtype=N.int)

        ii = self._handle.imageinfo ()

        if 'restoringbeam' in ii:
            self.bmaj = _casa_convert (ii['restoringbeam']['major'], 'rad')
            self.bmin = _casa_convert (ii['restoringbeam']['minor'], 'rad')
            self.bpa = _casa_convert (ii['restoringbeam']['positionangle'], 'rad')

        # Make sure that angular units are always measured in radians,
        # because anything else is ridiculous.

        from pyrap.quanta import quantity
        self._wcscale = wcscale = N.ones (self.shape.size)
        c = self._handle.coordinates ()
        radian = quantity (1., 'rad')

        def getconversion (text):
            q = quantity (1., text)
            if q.conforms (radian):
                return q.get_value ('rad')
            return 1

        i = 0

        for item in c.get_unit ():
            if isinstance (item, basestring):
                wcscale[i] = getconversion (item)
                i += 1
            elif len (item) == 0:
                wcscale[i] = 1 # null unit
                i += 1
            else:
                for subitem in item:
                    wcscale[i] = getconversion (subitem)
                    i += 1


    def _closeImpl (self):
        # No explicit close method provided here. Annoying.
        del self._handle


    def read (self, squeeze=False, flip=False):
        self._checkOpen ()
        data = self._handle.get ()

        if flip:
            data = data[...,::-1,:]
        if squeeze:
            data = data.squeeze ()
        return data


    def toworld (self, pixel):
        self._checkOpen ()
        pixel = N.asarray (pixel)
        return self._wcscale * N.asarray (self._handle.toworld (pixel))


    def topixel (self, world):
        self._checkOpen ()
        world = N.asarray (world)
        return N.asarray (self._handle.topixel (world / self._wcscale))


    def saveAsFITS (self, path, overwrite=False):
        self._checkOpen ()
        self._handle.tofits (path, overwrite=overwrite)


class FITSImage (AstroImage):
    _modemap = {'r': 'readonly',
                'rw': 'update' # ???
                }

    def __init__ (self, path, mode):
        try:
            import pyfits, pywcs
        except ImportError:
            raise UnsupportedError ('cannot open FITS images without the '
                                    'Python modules "pyfits" and "pywcs"')

        super (FITSImage, self).__init__ (path, mode)

        self._handle = pyfits.open (path, self._modemap[mode])
        header = self._handle[0].header
        self._wcs = pywcs.WCS (header)

        self.units = maybelower (header.get ('bunit'))

        naxis = header.get ('naxis', 0)
        self.shape = N.empty (naxis, dtype=N.int)
        for i in xrange (naxis):
            q = naxis - i
            self.shape[i] = header.get ('naxis%d' % q, 1)

        self.bmaj = maybescale (header.get ('bmaj'), D2R)
        self.bmin = maybescale (header.get ('bmin', self.bmaj * R2D), D2R)
        self.bpa = maybescale (header.get ('bpa', 0), D2R)

        self._wcscale = _get_wcs_scale (self._wcs, self.shape.size)


    def _closeImpl (self):
        self._handle.close ()


    def read (self, squeeze=False, flip=False):
        self._checkOpen ()
        data = N.ma.asarray (self._handle[0].data)
        # Are there other standards for expressing masking in FITS?
        data.mask = -N.isfinite (data.data)

        if flip:
            data = data[...,::-1,:]
        if squeeze:
            data = data.squeeze ()
        return data


    def toworld (self, pixel):
        if self._wcs is None:
            raise UnsupportedError ('world coordinate information is required '
                                    'but not present in "%s"', self.path)
        return _wcs_toworld (self._wcs, pixel, self._wcscale, self.shape.size)


    def topixel (self, world):
        if self._wcs is None:
            raise UnsupportedError ('world coordinate information is required '
                                    'but not present in "%s"', self.path)
        return _wcs_topixel (self._wcs, world, self._wcscale, self.shape.size)


    def saveAsFITS (self, path, overwrite=False):
        self._checkOpen ()
        self._handle.writeto (path, output_verify='fix', clobber=overwrite)


def open (path, mode):
    import __builtin__
    from os.path import exists, join, isdir

    if mode not in ('r', 'rw'):
        raise ValueError ('mode must be "r" or "rw"; got "%s"' % mode)

    if exists (join (path, 'image')):
        return MIRIADImage (path, mode)

    if exists (join (path, 'table.dat')):
        return CASAImage (path, mode)

    if isdir (path):
        raise UnsupportedError ('cannot infer format of image "%s"' % path)

    with __builtin__.open (path, 'rb') as f:
        sniff = f.read (9)

    if sniff.startswith ('SIMPLE  ='):
        return FITSImage (path, mode)

    raise UnsupportedError ('cannot infer format of image "%s"' % path)
