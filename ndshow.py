"""Utility class for rendering 2-D numpy arrays
graphically as images."""

# TODO: zooming, slices, histogram

import numpy as N
import Numeric # ugh.

import gobject, gtk
gdk = gtk.gdk
from gtk import glade

import omega.gtkThread as gtkThread
import threading

# A lot of this is copied from omega/gtkUtil.py as
# a temp hack. Should be integrated.

def _makeGladeFile ():
    import os
    f = os.path.dirname (__file__)
    return os.path.join (f, 'ndshow.glade')

_gladefile = _makeGladeFile ()

class ArrayWindow (object):
    CLAMPING_MYMEDIAN = 0
    CLAMPING_MINMAX = 1
    CLAMPING_NONE = 2

    SCALING_LINEAR = 0
    SCALING_LOG = 1
    SCALING_SQRT = 2
    SCALING_HISTEQ = 3
    
    COLORING_BLACKTOWHITE = 0
    COLORING_BLUETORED = 1
    COLORING_GREENTOMAGENTA = 2
    
    def __init__ (self, array, parent=None, title=None,
                  clamping=None, scaling=None, coloring=None, enlarge=1):
        if array.ndim != 2:
            raise Exception ('Can only show 2-dimensional arrays as images.')

        self.orig_data = array
        self.orig_nrow, self.orig_ncol = array.shape
        self.orig_min, self.orig_max = N.min (array), N.max (array)
        self.orig_med = N.median (array.ravel ())

        # Initial rendering settings
        
        if clamping is None: clamping = self.CLAMPING_MYMEDIAN
        if scaling is None: scaling = self.SCALING_LINEAR
        if coloring is None: coloring = self.COLORING_BLACKTOWHITE
        
        self.clamping = clamping
        self.scaling = scaling
        self.invertScale = False
        self.coloring = coloring
        self.enlargement = enlarge

        self._initColors ()
        
        # UI.
        
        self.xml = xml = glade.XML (_gladefile)        
        xml.signal_autoconnect (self)

        # Window setup
        
        self.win = win = xml.get_widget ('window')
        if title is not None: win.set_title (str (title))
        if parent is not None: win.set_transient_for (parent)

        # Image setup - do this before UI controls so that
        # their signal callbacks can set the image correctly.
        
        self.img = xml.get_widget ('img')
        self.colorscale_img = xml.get_widget ('colorscale_img')

        # Clamping combo setup

        cb = xml.get_widget ('cb_clamping')
        cb.set_active (self.clamping)

        # Scaling combo setup

        cb = xml.get_widget ('cb_scaling')
        cb.set_active (self.scaling)

        # Scaling combo setup

        cb = xml.get_widget ('cb_coloring')
        cb.set_active (self.coloring)

        # Enlargement setup

        xml.get_widget ('sb_enlargement').set_value (self.enlargement)
        
        # Statusbar setup
        
        self.statusbar = xml.get_widget ('statusbar')
        self.sbctxt = self.statusbar.get_context_id ('Position')

        # All one. Draw the thing. self.clamped and self.scaled will
        # already have been set from the set_actives above.

        self.updateColorscaleImage ()
        self.update (False, False)

    def doClamping (self):
        omin, omax = self.orig_min, self.orig_max
        
        if self.clamping == self.CLAMPING_NONE:
            clamped = self.orig_data
            cmax = omax

            if omin < 0:
                print 'Data minimum less than 0, must have some clamping'
                cb = self.xml.get_widget ('cb_clamping')
                cb.set_active (self.CLAMPING_MINMAX)
        elif self.clamping == self.CLAMPING_MINMAX:
            clamped = self.orig_data - omin
            cmax = omax - omin
        elif self.clamping == self.CLAMPING_MYMEDIAN:
            clamped = self.orig_data * 1.0

            for i in range (0, 5):
                med = N.median (clamped.ravel ())
                quasistd = N.sqrt (((clamped - med)**2).mean ())
                ciel = N.min (med + 5 * quasistd, omax)
                floor = N.max (med - 5 * quasistd, omin)
                
                #nabove = len (N.where (self.orig_data > ciel)[0])
                #nbelow = len (N.where (self.orig_data < floor)[0])
                #
                #print 'med %f, qs %f, ci %f, fl %f, nab %f, nbe %f' \
                #      % (med, quasistd, ciel, floor, nabove, nbelow)

                clamped = N.minimum (self.orig_data, ciel)
                clamped = N.maximum (clamped, floor)
                
            clamped -= floor
            # for some reason this fails for the very highest values
            #cmax = ciel - floor
            cmax = clamped.max ()
        else:
            raise Exception ('Unknown clamping mode %d' % self.clamping)

        self.clamped = clamped
        self.clamped_max = cmax

    def doScaling (self):
        """Map our clamped data, ranging from 0 to clamped_max, into a 24-bit
        space of integers, in preparation for colorization into a 24-bit RGB
        space."""
        
        ncol, nrow = self.orig_ncol, self.orig_nrow
        scaled = N.ndarray ((nrow, ncol), N.uint32)
        smax = 2**24 - 1 # 8 bits of R,G,B = 24 bit color
        
        cmax = self.clamped_max

        # These are all slicewise assignments to set the array contents,
        # not just the array variable. Otherwise we lose the uint32 datatype,
        # and the arrayness altogether when cmax = 0.
        
        if cmax == 0:
            scaled[:,:] = 0
        elif self.scaling == self.SCALING_LINEAR:
            scale = smax / cmax
            scaled[:,:] = self.clamped * scale
        elif self.scaling == self.SCALING_LOG:
            scale = smax / N.log (cmax + 1.0)
            scaled[:,:] = N.log (self.clamped + 1.0) * scale
        elif self.scaling == self.SCALING_SQRT:
            scale = smax / N.sqrt (cmax + 1.0)
            scaled[:,:] = N.sqrt (self.clamped + 1.0) * scale
        elif self.scaling == self.SCALING_HISTEQ:
            # Scale by area under the image histogram -- equivalently, rank
            # by percentile
            # FIXME: we lose precision by taking only a subset of the sorted array,
            # but digitize () gets very slow when its second argument is large.
            # Even a ~512 element maximum is pushing it.
            
            raveled = self.clamped.ravel ()
            
            sorted = raveled * 1.0
            sorted.sort ()

            if sorted.size > 512:
                step = sorted.size / 512
                sorted = sorted[::step]
            
            indexed = N.digitize (raveled, sorted) - 1
            v = 1.0 * smax / len (sorted)
            scaled[:,:] = indexed.reshape (nrow, ncol) * v
        else:
            raise Exception ('Unknown image scale %d' % self.scaling)

        if self.invertScale:
            scaled = -scaled + smax
        
        self.scaled = scaled

    # See http://geography.uoregon.edu/datagraphics/ for some information
    # on good color schemes.
    
    def _colorMakeGauss (self, peak, ctr, width):
        # sqrt (2pi) = 2.50662827463

        def f (work, scaled):
            work[:,:] = N.exp (-(scaled - ctr)**2/(2*width**2)) * \
                        peak / 2.50662827463

        return f
    
    def _colorTruncate (self, work, scaled):
        work[:,:] = scaled // 2**16

    def _initColors (self):
        self._colorschemes = cs = {}

        r = g = b = self._colorTruncate
        cs[self.COLORING_BLACKTOWHITE] = (r, g, b)

        #  These could all use some work.
        
        r = self._colorMakeGauss (255., 2**24 * 0.8, 2**24 * 0.333)
        g = self._colorMakeGauss (255., 2**24 * 0.5, 2**24 * 0.333)
        b = self._colorMakeGauss (255., 2**24 * 0.2, 2**24 * 0.5)
        cs[self.COLORING_BLUETORED] = (r, g, b)
        
        r = self._colorMakeGauss (255., 2**24 * 0.8, 2**24 * 0.25)
        g = self._colorMakeGauss (255., 2**24 * 0.4, 2**24 * 0.3)
        b = self._colorMakeGauss (255., 2**24 * 0.8, 2**24 * 0.25)
        cs[self.COLORING_GREENTOMAGENTA] = (r, g, b)
        
    def makePixbuf (self, scaled, e):
        nrow, ncol = scaled.shape

        a2 = Numeric.zeros ((nrow, ncol, 3), 'b')
        work = N.ndarray ((nrow, ncol), N.uint8)

        if not self.coloring in self._colorschemes:
            raise Exception ('Unknown image colorization %d' % self.coloring)
            
        (r, g, b) = self._colorschemes[self.coloring]

        r (work, scaled)
        a2[:,:,0] = work
        g (work, scaled)
        a2[:,:,1] = work
        b (work, scaled)
        a2[:,:,2] = work

        pb = gdk.pixbuf_new_from_array (a2, gdk.COLORSPACE_RGB, 8)

        if e != 1:
            pb = pb.scale_simple (ncol * e, nrow * e, gdk.INTERP_NEAREST)

        return pb

    def update (self, reclamp, rescale):
        if reclamp:
            self.doClamping ()
        if rescale:
            self.doScaling ()
            
        pb = self.makePixbuf (self.scaled, self.enlargement)
        self.img.set_from_pixbuf (pb)

    # Colorscale demo image

    _lastColorscaleWidth = -1
    
    def updateColorscaleImage (self):
        alloc = self.colorscale_img.get_allocation ()
        ncol = alloc.width
        nrow = 16
        self._lastColorscaleWidth = ncol

        if self.invertScale:
            scale = N.linspace (2**24 - 1, 0, ncol)
        else:
            scale = N.linspace (0, 2**24 - 1, ncol)
            
        scale = N.vstack ((scale, scale, scale, scale))
        scale = N.vstack ((scale, scale, scale, scale))

        pb = self.makePixbuf (scale, 1)
        self.colorscale_img.set_from_pixbuf (pb)

    def onColorscaleAllocate (self, image, allocation):
        if allocation.width == self._lastColorscaleWidth:
            return

        self.updateColorscaleImage ()
        
    # Event handlers.

    sbmid = None
    
    def onMotionNotify (self, ebox, event):
        if self.sbmid != None:
            self.statusbar.remove (self.sbctxt, self.sbmid)

        (x, y) = event.get_coords ()

        # Map to image coordinates. This feels sketchy.
        
        ncol, nrow = self.orig_ncol, self.orig_nrow
        enl = self.enlargement
        alloc = self.img.get_allocation ()
        x -= (alloc.width - ncol * enl) / 2
        y -= (alloc.height - nrow * enl) / 2

        col, row = int (x) // enl, int (y) // enl

        if col < 0 or row < 0 or col >= ncol or row >= nrow:
            return
        
        try:
            val = 'value %g' % self.orig_data[row,col]
        except Exception, e:
            val = 'error getting value: %s' % e
            
        txt = 'Row %d, col %d; %s' % (row, col, val)
        self.sbmid = self.statusbar.push (self.sbctxt, txt)

    def onClampingChanged (self, combo):
        self.clamping = combo.get_active ()
        self.update (True, True)
        
    def onScalingChanged (self, combo):
        self.scaling = combo.get_active ()
        self.update (False, True)

    def onInvertToggled (self, toggle):
        self.invertScale = toggle.get_active ()
        self.updateColorscaleImage ()
        self.update (False, True)
        
    def onColoringChanged (self, combo):
        self.coloring = combo.get_active ()
        self.updateColorscaleImage ()
        self.update (False, False)
        
    def onEnlargementChanged (self, spinbutton):
        self.enlargement = spinbutton.get_value_as_int ()
        self.update (False, False)

class ArrayViewer (object):
    """Instantiating this viewer creates an ArrayWindow object that is
    displayed via a GTK main loop run asynchronously in another thread. This
    means that the window is displayed and kept updated without blocking
    execution of the caller. Deleting the ArrayViewer object destroys
    the ArrayWindow automatically."""
    
    def __init__ (self, array, parent=None, **kwargs):
        self.win = None
        self.lock = threading.Lock ()
        
        # see omega/gtkUtil:LiveDisplay.__init__ ().

        import weakref
        sref = weakref.ref (self)

        def clear (obj):
            instance = sref ()

            if instance != None:
                instance.lock.acquire ()
                instance.win = None
                instance.lock.release ()

        # End obscurity.

        def init ():
            self.lock.acquire ()
            self.window = ArrayWindow (array, parent, **kwargs)
            self.lock.release ()
            self.window.win.connect ('destroy', clear)
            self.window.win.show_all ()

        gtkThread.send (init)

    def __del__ (self):
        if self.window == None: return
        if gtkThread == None: return # this can get GC'd before us!

        # See omega/gtkUtil:LiveDisplay.__del__ ()

        def doit ():
            self.lock.acquire ()
            if self.window != None:
                self.window.win.destroy ()
                self.window = None
            self.lock.release ()

        gtkThread.send (doit)

    lingerInterval = 250
    
    def linger (self):
        """Block the caller until the ArrayWindow window has been
        closed by the user. Useful for semi-interactive programs to pause
        while the user examines a plot."""

        from Queue import Queue, Empty

        q = Queue ()

        def check_done ():
            self.lock.acquire ()
            haswin = self.window is not None
            self.lock.release ()

            if haswin:
                return True
            q.put (True)
            return False

        def doit ():
            gobject.timeout_add (self.lingerInterval, check_done)

        gtkThread.send (doit)
        q.get ()

def showBlocking (array, parent=None, **kwargs):
    """Display an ndarray in a window. This function does not exit
    until the user closes the window! Like the linger () function of
    ArrayViewer, but doesn't involve threads, and so makes debugging
    and such a bit easier."""

    if gtkThread._thread is not None and gtkThread._thread.isAlive ():
        raise Exception ('Can\'t do a showBlocking while the GTK main ' +
                         'loop is running in another thread. Sorry.')
    
    w = ArrayWindow (array, parent, **kwargs)
    w.connect ('destroy', gtk.main_quit)
    w.show_all ()
    gtk.main ()
