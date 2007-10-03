"""Utility class for rendering 2-D numpy arrays
graphically as images."""

# TODO: zooming, color, slices, histogram

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

class ArrayViewerTmp (object):
    SCALING_LINEAR = 0
    SCALING_LOG = 1
    SCALING_SQRT = 2

    CLAMPING_MYMEDIAN = 0
    CLAMPING_MINMAX = 1
    CLAMPING_NONE = 2
    
    def __init__ (self, array, parent=None, title=None,
                  clamping=None, scaling=None, enlarge=1):
        if array.ndim != 2:
            raise Exception ('Can only show 2-dimensional arrays as images.')

        self.orig_data = array
        self.orig_nrow, self.orig_ncol = array.shape
        self.orig_min, self.orig_max = N.min (array), N.max (array)
        self.orig_med = N.median (array.ravel ())

        # Initial rendering settings
        
        if clamping is None: clamping = self.CLAMPING_MYMEDIAN
        if scaling is None: scaling = self.SCALING_LINEAR
        
        self.scaling = scaling
        self.invertScale = False
        self.clamping = clamping
        self.enlargement = enlarge
        
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

        # Scaling combo setup

        cb = xml.get_widget ('cb_clamping')
        cb.set_active (self.clamping)

        # Scaling combo setup

        cb = xml.get_widget ('cb_scaling')
        cb.set_active (self.scaling)

        # Enlargement setup

        xml.get_widget ('sb_enlargement').set_value (self.enlargement)
        
        # Statusbar setup
        
        self.statusbar = xml.get_widget ('statusbar')
        self.sbctxt = self.statusbar.get_context_id ('Position')

        # All one. Draw the thing. self.clamped and self.scaled will
        # already have been set from the set_actives above.

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
            max = self.orig_med + (self.orig_med - self.orig_min) * 10
            clamped = N.minimum (self.orig_data, max) - omin
            cmax = max - omin
        else:
            raise Exception ('Unknown clamping mode %d' % self.clamping)

        self.clamped = clamped
        self.clamped_max = cmax
        
    def doScaling (self):
        ncol, nrow = self.orig_ncol, self.orig_nrow
        scaled = N.ndarray ((nrow, ncol), N.uint8)

        cmax = self.clamped_max

        # These are all slicewise assignments to set the array contents,
        # not just the array variable. Otherwise we lose the uint8 datatype,
        # and the arrayness altogether when cmax = 0.
        
        if cmax == 0:
            scaled[:,:] = 0
        elif self.scaling == self.SCALING_LINEAR:
            scale = 255. / cmax
            scaled[:,:] = self.clamped * scale
        elif self.scaling == self.SCALING_LOG:
            scale = 255. / N.log (cmax + 1.0)
            scaled[:,:] = N.log (self.clamped + 1.0) * scale
        elif self.scaling == self.SCALING_SQRT:
            scale = 255. / N.sqrt (cmax + 1.0)
            scaled[:,:] = N.sqrt (self.clamped + 1.0) * scale
        else:
            raise Exception ('Unknown image scale %d' % self.scaling)

        if self.invertScale:
            scaled = -scaled + 255
        
        self.scaled = scaled

    def makePixbuf (self):
        ncol, nrow = self.orig_ncol, self.orig_nrow
        e = self.enlargement
        
        a2 = Numeric.zeros ((nrow, ncol, 3), 'b')
        
        a2[:,:,0] = self.scaled
        a2[:,:,1] = self.scaled
        a2[:,:,2] = self.scaled

        pb = gdk.pixbuf_new_from_array (a2, gdk.COLORSPACE_RGB, 8)

        if e != 1:
            pb = pb.scale_simple (ncol * e, nrow * e, gdk.INTERP_NEAREST)

        return pb

    def update (self, reclamp, rescale):
        if reclamp:
            self.doClamping ()
        if rescale:
            self.doScaling ()
            
        pb = self.makePixbuf ()
        self.img.set_from_pixbuf (pb)
    
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

    def onScalingChanged (self, combo):
        self.scaling = combo.get_active ()
        self.update (False, True)

    def onInvertToggled (self, toggle):
        self.invertScale = toggle.get_active ()
        self.update (False, True)
        
    def onClampingChanged (self, combo):
        self.clamping = combo.get_active ()
        self.update (True, True)
        
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
            self.viewer = ArrayViewerTmp (array, parent, **kwargs)
            self.lock.release ()
            self.viewer.win.connect ('destroy', clear)
            self.viewer.win.show_all ()

        gtkThread.send (init)

    def __del__ (self):
        if self.viewer == None: return
        if gtkThread == None: return # this can get GC'd before us!

        # See omega/gtkUtil:LiveDisplay.__del__ ()

        def doit ():
            self.lock.acquire ()
            if self.viewer != None:
                self.viewer.win.destroy ()
                self.viewer = None
            self.lock.release ()

        gtkThread.send (doit)

    lingerInterval = 250
    
    def linger (self):
        """Block the caller until the ArrayViewer window has been
        closed by the user. Useful for semi-interactive programs to pause
        while the user examines a plot."""

        from Queue import Queue, Empty

        q = Queue ()

        def check_done ():
            self.lock.acquire ()
            haswin = self.viewer is not None
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
