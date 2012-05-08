# Copyright 2012 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""
astimage -- generic loading of (radio) astronomical images

Use `astimage.open (path, mode)` to open an astronomical image,
regardless of its file format.
"""

# Developer notes:
"""
Note that pyrap.images allegedly supports casacore, HDF5, FITS, and
MIRIAD format images transparently. Frankly, I don't trust it, I don't
like the pyrap.images API, and I'd rather not require that casacore
and pyrap be installed. pyrap.images doesn't support masks in MIRIAD
images.

TODO: make sure restfreq semantics are right (probably aren't)

TODO: axis types (ugh standardizing these would be a bear)
      Some kind of way to get generic formatting of RA/Dec, glat/glon,
      etc would be nice.

TODO: obs date (MJD? that's native system used by CASA)

TODO: image units (ie, "set units to Jy/px"; standardization also a pain)
"""

import numpy as np

from numpy import pi
D2R = pi / 180 # if end up needing more of these, start using astutil.py
R2D = 180 / pi

__all__ = ('UnsupportedError AstroImage MIRIADImage CASAImage '
           'FITSImage SimpleImage open').split ()


class UnsupportedError (RuntimeError):
    def __init__ (self, fmt, *args):
        if not len (args):
            self._message = str (fmt)
        else:
            self._message = fmt % args

    def __str__ (self):
        return self._message


class AstroImage (object):
    path = None
    mode = None
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

    pclat = None
    "Latitude of the pointing center in radians"

    pclon = None
    "Longitude of the pointing center in radians"

    restfreq = None
    "Mean rest frequency of the image in GHz"

    axdescs = None
    """If not None, list of strings describing the axis types;
    no standard format."""

    def __init__ (self, path, mode):
        self.path = path
        self.mode = mode


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


    def _checkWriteable (self):
        if self.mode == 'r':
            raise UnsupportedError ('this operation cannot be performed on the '
                                    'read-only image at "%s"', self.path)


    @property
    def size (self):
        return np.prod (self.shape)


    def read (self, squeeze=False, flip=False):
        raise NotImplementedError ()


    def write (self, data):
        raise NotImplementedError ()


    def toworld (self, pixel):
        raise NotImplementedError ()


    def topixel (self, world):
        raise NotImplementedError ()


    def simple (self):
        lat, lon = self._latlonaxes ()

        if lat < 0 or lon < 0 or lat == lon:
            raise UnsupportedError ('the image "%s" does not have both latitude '
                                    'and longitude axes', self.path)

        if lat == 0 and lon == 1 and self.shape.size == 2:
            return self # noop

        return SimpleImage (self, lat, lon)


    def saveCopy (self, path, overwrite=False, openmode=None):
        raise NotImplementedError ()


    def saveAsFITS (self, path, overwrite=False, openmode=None):
        raise NotImplementedError ()


    def delete (self):
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
    wcscale = np.ones (naxis)

    for i in xrange (naxis):
        q = wcscale.size - 1 - i
        text = wcs.wcs.cunit[q].strip ()

        try:
            uc = pywcs.UnitConverter (text, 'rad')
            wcscale[i] = uc.scale
        except SyntaxError: # !! pywcs 1.10
            pass # not an angle unit; don't futz.
        except ValueError: # pywcs 1.11
            pass

    return wcscale


def _wcs_toworld (wcs, pixel, wcscale, naxis):
    # TODO: we don't allow the usage of "SIP" or "Paper IV"
    # transformations, let alone a concatenation of these, because
    # they're not invertible.

    pixel = np.asarray (pixel)
    if pixel.shape != (naxis, ):
        raise ValueError ('pixel coordinate must be a %d-element vector', naxis)

    pixel = pixel.reshape ((1, naxis))[:,::-1]
    world = wcs.wcs_pix2sky (pixel, 0)
    return world[0,::-1] * wcscale


def _wcs_topixel (wcs, world, wcscale, naxis):
    world = np.asarray (world)
    if world.shape != (naxis, ):
        raise ValueError ('world coordinate must be a %d-element vector', naxis)

    world = (world / wcscale)[::-1].reshape ((1, naxis))
    pixel = wcs.wcs_sky2pix (world, 0)
    return pixel[0,::-1]


def _wcs_latlonaxes (wcs, naxis):
    lat = lon = -1

    if wcs.wcs.lat >= 0:
        lat = naxis - 1 - wcs.wcs.lat
    if wcs.wcs.lng >= 0:
        lon = naxis - 1 - wcs.wcs.lng

    return lat, lon


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
        self.shape = np.empty (naxis, dtype=np.int)
        self.axdescs = []

        for i in xrange (naxis):
            q = naxis - i
            self.shape[i] = h.getScalarItem ('naxis%d' % q, 1)
            self.axdescs.append (h.getScalarItem ('ctype%d' % q, '???'))

        self.units = maybelower (h.getScalarItem ('bunit'))

        self.bmaj = h.getScalarItem ('bmaj')
        if self.bmaj is not None:
            self.bmin = h.getScalarItem ('bmin', self.bmaj)
            self.bpa = h.getScalarItem ('bpa', 0) * D2R

        self.pclat = h.getScalarItem ('obsdec')
        if self.pclat is not None:
            self.pclon = h.getScalarItem ('obsra')
        else:
            try:
                import mirtask.mostable
                mt = mirtask.mostable.readDataSet (h)[0] # ignore WCS warnings here
                if mt.radec.shape[0] == 1:
                    self.pclat = mt.radec[0,1]
                    self.pclon = mt.radec[0,0]
            except Exception:
                pass

        self._wcscale = _get_wcs_scale (self._wcs, self.shape.size)

        # FIXME: assuming that spectral axis exists and is in units of Hz
        s = naxis - self._wcs.wcs.spec - 1
        self.restfreq = self.toworld (np.zeros (naxis))[s] * 1e-9


    def _closeImpl (self):
        self._handle.close ()


    def read (self, squeeze=False, flip=False):
        self._checkOpen ()
        nonplane = self.shape[:-2]

        if nonplane.size == 0:
            data = self._handle.readPlane ([], topIsZero=flip)
        else:
            data = np.ma.empty (self.shape, dtype=np.float32)
            data.mask = np.zeros (self.shape, dtype=np.bool)
            n = np.prod (nonplane)
            fdata = data.reshape ((n, self.shape[-2], self.shape[-1]))

            for i in xrange (n):
                axes = np.unravel_index (i, nonplane)
                self._handle.readPlane (axes, fdata[i], topIsZero=flip)

        if squeeze:
            data = data.squeeze ()

        return data


    def write (self, data):
        data = np.ma.asarray (data)

        if data.shape != tuple (self.shape):
            raise ValueError ('data is wrong shape: got %s, want %s' \
                                  % (data.shape, tuple (self.shape)))

        self._checkOpen ()
        self._checkWriteable ()
        nonplane = self.shape[:-2]

        if nonplane.size == 0:
            self._handle.writePlane (data, [])
        else:
            n = np.prod (nonplane)
            fdata = data.reshape ((n, self.shape[-2], self.shape[-1]))

            for i in xrange (n):
                axes = np.unravel_index (i, nonplane)
                self._handle.writePlane (fdata[i], axes)

        return self


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


    def _latlonaxes (self):
        if self._wcs is None:
            raise UnsupportedError ('world coordinate information is required '
                                    'but not present in "%s"', self.path)
        return _wcs_latlonaxes (self._wcs, self.shape.size)


    def saveCopy (self, path, overwrite=False, openmode=None):
        import shutil, os.path

        # FIXME: race conditions and such in overwrite checks.
        # Too lazy to do a better job.

        if os.path.exists (path):
            if overwrite:
                if os.path.isdir (path):
                    shutil.rmtree (path)
                else:
                    os.unlink (path)
            else:
                raise UnsupportedError ('refusing to copy "%s" to "%s": '
                                        'destination already exists' % (self.path, path))

        shutil.copytree (self.path, path, symlinks=False)

        if openmode is None:
            return None
        return open (path, openmode)


    def saveAsFITS (self, path, overwrite=False, openmode=None):
        from mirexec import TaskFits
        import os.path

        if os.path.exists (path):
            if overwrite:
                os.unlink (path)
            else:
                raise UnsupportedError ('refusing to export "%s" to "%s": '
                                        'destination already exists' % (self.path, path))

        TaskFits (op='xyout', in_=self.path, out=path).runsilent ()

        if openmode is None:
            return None
        return FITSImage (path, openmode)


    def delete (self):
        if self._handle is not None:
            raise UnsupportedError ('cannot delete the image at "%s" without '
                                    'first closing it', self.path)
        self._checkWriteable ()

        import shutil, os.path

        if os.path.isdir (self.path):
            shutil.rmtree (self.path)
        else:
            os.unlink (self.path) # may be a symlink; rmtree rejects this


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
        self.shape = np.asarray (self._handle.shape (), dtype=np.int)
        self.axdescs = []

        if 'coordinates' in allinfo:
            pc = allinfo['coordinates'].get ('pointingcenter')
            # initial=True signifies that the pointing center information
            # hasn't actually been initialized.
            if pc is not None and not pc['initial']:
                # This bit of info doesn't have any metadata about units or
                # whatever; appears to be fixed as RA/Dec in radians.
                self.pclat = pc['value'][1]
                self.pclon = pc['value'][0]

        ii = self._handle.imageinfo ()

        if 'restoringbeam' in ii:
            self.bmaj = _casa_convert (ii['restoringbeam']['major'], 'rad')
            self.bmin = _casa_convert (ii['restoringbeam']['minor'], 'rad')
            self.bpa = _casa_convert (ii['restoringbeam']['positionangle'], 'rad')

        # Make sure that angular units are always measured in radians,
        # because anything else is ridiculous.

        from pyrap.quanta import quantity
        self._wcscale = wcscale = np.ones (self.shape.size)
        c = self._handle.coordinates ()
        radian = quantity (1., 'rad')

        for item in c.get_axes ():
            if isinstance (item, basestring):
                self.axdescs.append (item.replace (' ', '_'))
            else:
                for subitem in item:
                    self.axdescs.append (subitem.replace (' ', '_'))

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

        # TODO: is this always in Hz?
        self.restfreq = c.get_coordinate ('spectral').get_restfrequency () * 1e-9


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


    def write (self, data):
        data = np.ma.asarray (data)

        if data.shape != tuple (self.shape):
            raise ValueError ('data is wrong shape: got %s, want %s' \
                                  % (data.shape, tuple (self.shape)))

        self._checkOpen ()
        self._checkWriteable ()
        self._handle.put (data)
        return self


    def toworld (self, pixel):
        self._checkOpen ()
        pixel = np.asarray (pixel)
        return self._wcscale * np.asarray (self._handle.toworld (pixel))


    def topixel (self, world):
        self._checkOpen ()
        world = np.asarray (world)
        return np.asarray (self._handle.topixel (world / self._wcscale))


    def _latlonaxes (self):
        self._checkOpen ()

        lat = lon = -1
        flat = []

        for item in self._handle.coordinates ().get_axes ():
            if isinstance (item, basestring):
                flat.append (item)
            else:
                for subitem in item:
                    flat.append (subitem)

        for i, name in enumerate (flat):
            # These symbolic names obtained from
            # casacore/coordinates/Coordinates/DirectionCoordinate.cc
            # Would be nice to have a better system for determining
            # this a la what wcslib provides.
            if name in ('Right Ascension', 'Hour Angle', 'Longitude'):
                if lon == -1:
                    lon = i
                else:
                    lon = -2
            elif name in ('Declination', 'Latitude'):
                if lat == -1:
                    lat = i
                else:
                    lat = -2

        return lat, lon


    def saveCopy (self, path, overwrite=False, openmode=None):
        self._checkOpen ()
        self._handle.saveas (path, overwrite=overwrite)

        if openmode is None:
            return None
        return open (path, openmode)


    def saveAsFITS (self, path, overwrite=False, openmode=None):
        self._checkOpen ()
        self._handle.tofits (path, overwrite=overwrite)

        if openmode is None:
            return None
        return FITSImage (path, openmode)


    def delete (self):
        if self._handle is not None:
            raise UnsupportedError ('cannot delete the image at "%s" without '
                                    'first closing it', self.path)
        self._checkWriteable ()

        import shutil, os.path

        if os.path.isdir (self.path):
            shutil.rmtree (self.path)
        else:
            os.unlink (self.path) # may be a symlink; rmtree rejects this


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
        self._wcs.wcs.set ()

        self.units = maybelower (header.get ('bunit'))

        naxis = header.get ('naxis', 0)
        self.shape = np.empty (naxis, dtype=np.int)
        self.axdescs = []

        for i in xrange (naxis):
            q = naxis - i
            self.shape[i] = header.get ('naxis%d' % q, 1)
            self.axdescs.append (header.get ('ctype%d' % q, '???'))

        self.bmaj = maybescale (header.get ('bmaj'), D2R)
        if self.bmaj is None:
            bmindefault = None
        else:
            bmindefault = self.bmaj * R2D
        self.bmin = maybescale (header.get ('bmin', bmindefault), D2R)
        self.bpa = maybescale (header.get ('bpa', 0), D2R)

        self.pclat = maybescale (header.get ('obsdec'), D2R)
        self.pclon = maybescale (header.get ('obsra'), D2R)

        self._wcscale = _get_wcs_scale (self._wcs, self.shape.size)

        # FIXME: assuming that spectral axis exists and is in units of Hz
        s = naxis - self._wcs.wcs.spec - 1
        self.restfreq = self.toworld (np.zeros (naxis))[s] * 1e-9


    def _closeImpl (self):
        self._handle.close ()


    def read (self, squeeze=False, flip=False):
        self._checkOpen ()
        data = np.ma.asarray (self._handle[0].data)
        # Are there other standards for expressing masking in FITS?
        data.mask = -np.isfinite (data.data)

        if flip:
            data = data[...,::-1,:]
        if squeeze:
            data = data.squeeze ()
        return data


    def write (self, data):
        data = np.ma.asarray (data)

        if data.shape != tuple (self.shape):
            raise ValueError ('data is wrong shape: got %s, want %s' \
                                  % (data.shape, tuple (self.shape)))

        self._checkOpen ()
        self._checkWriteable ()
        self._handle[0].data[:] = data
        self._handle.flush ()
        return self


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


    def _latlonaxes (self):
        if self._wcs is None:
            raise UnsupportedError ('world coordinate information is required '
                                    'but not present in "%s"', self.path)
        return _wcs_latlonaxes (self._wcs, self.shape.size)


    def saveCopy (self, path, overwrite=False, openmode=None):
        self._checkOpen ()
        self._handle.writeto (path, output_verify='fix', clobber=overwrite)

        if openmode is None:
            return None
        return open (path, openmode)


    def saveAsFITS (self, path, overwrite=False, openmode=None):
        return self.saveCopy (path, overwrite=overwrite, openmode=openmode)


    def delete (self):
        if self._handle is not None:
            raise UnsupportedError ('cannot delete the image at "%s" without '
                                    'first closing it', self.path)
        self._checkWriteable ()

        os.unlink (self.path)


class SimpleImage (AstroImage):
    def __init__ (self, parent, latax, lonax):
        self._handle = parent
        self._latax = latax
        self._lonax = lonax

        checkworld1 = parent.toworld (parent.shape * 0.) # need float!
        checkworld2 = parent.toworld (parent.shape - 1.) # (for pyrap)
        self._topixelok = True

        for i in xrange (parent.shape.size):
            # Two things to check. Firstly, that all non-lat/lon
            # axes have only one pixel; this limitation can be relaxed
            # if we add a mechanism for choosing which non-spatial
            # pixels to work with.
            #
            # Secondly, check that non-lat/lon world coordinates
            # don't vary over the image; otherwise topixel() will
            # be broken.
            if i in (latax, lonax):
                continue
            if parent.shape[i] != 1:
                raise UnsupportedError ('cannot simplify an image with '
                                        'nondegenerate nonspatial axes')
            if np.abs (1 - checkworld1[i] / checkworld2[i]) > 1e-6:
                self._topixelok = False

        self.path = '<subimage of %s>' % parent.path
        self.shape = np.asarray ([parent.shape[latax], parent.shape[lonax]])
        self.axdescs = [parent.axdescs[latax], parent.axdescs[lonax]]
        self.bmaj = parent.bmaj
        self.bmin = parent.bmin
        self.bpa = parent.bpa
        self.units = parent.units
        self.pclat = parent.pclat
        self.pclon = parent.pclon
        self.restfreq = parent.restfreq

        self._pctmpl = np.zeros (parent.shape.size)
        self._wctmpl = parent.toworld (self._pctmpl)


    def _closeImpl (self):
        pass


    def read (self, squeeze=False, flip=False):
        self._checkOpen ()
        data = self._handle.read (flip=flip)
        idx = list (self._pctmpl)
        idx[self._latax] = slice (None)
        idx[self._lonax] = slice (None)
        data = data[tuple (idx)]

        if self._latax > self._lonax:
            # Ensure that order is (lat, lon). Note that unlike the
            # above operations, this forces a copy of data.
            data = data.T

        if squeeze:
            data = data.squeeze () # could be 1-by-N ...

        return data


    def write (self, data):
        data = np.ma.asarray (data)

        if data.shape != tuple (self.shape):
            raise ValueError ('data is wrong shape: got %s, want %s' \
                                  % (data.shape, tuple (self.shape)))

        self._checkOpen ()
        self._checkWriteable ()

        fulldata = np.ma.empty (self._handle.shape, dtype=data.dtype)
        idx = list (self._pctmpl)
        idx[self._latax] = slice (None)
        idx[self._lonax] = slice (None)

        if self._latax > self._lonax:
            fulldata[tuple (idx)] = data.T
        else:
            fulldata[tuple (idx)] = data

        self._handle.write (fulldata)
        return self


    def toworld (self, pixel):
        self._checkOpen ()
        p = self._pctmpl.copy ()
        p[self._latax] = pixel[0]
        p[self._lonax] = pixel[1]
        w = self._handle.toworld (p)
        world = np.empty (2)
        world[0] = w[self._latax]
        world[1] = w[self._lonax]
        return world


    def topixel (self, world):
        self._checkOpen ()
        if not self._topixelok:
            raise UnsupportedError ('mixing in the coordinate system of '
                                    'this subimage prevents mapping from '
                                    'world to pixel coordinates')

        w = self._wctmpl.copy ()
        w[self._latax] = world[0]
        w[self._lonax] = world[1]
        p = self._handle.topixel (w)
        pixel = np.empty (2)
        pixel[0] = p[self._latax]
        pixel[1] = p[self._lonax]
        return pixel


    def simple (self):
        return self


    def saveCopy (self, path, overwrite=False, openmode=None):
        raise UnsupportedError ('cannot save a copy of a subimage')


    def saveAsFITS (self, path, overwrite=False, openmode=None):
        raise UnsupportedError ('cannot save subimage as FITS')


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
