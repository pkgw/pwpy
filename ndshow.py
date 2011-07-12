"""
UI features of the viewport:

click-drag to pan
scrollwheel to zoom in/out
double-click to recenter

Added by the toplevel window viewer:

Ctrl-A to autoscale data to fit window
Ctrl-E to center the data in the window
Ctrl-W to close the window
Ctrl-1 to set scale to unity

"""

import numpy as N
import cairo
import gtk
import sys # tmp for stdout flush

DRAG_TYPE_NONE = 0
DRAG_TYPE_PAN = 1
DRAG_TYPE_TUNER = 2


class Viewport (gtk.DrawingArea):
    bgpattern = None

    getshape = None
    settuning = None
    getsurface = None

    centerx = 0
    centery = 0
    # The data pixel coordinate of the central pixel of the displayed
    # window

    scale = None
    # From data space to viewer space: e.g., scale = 2 means that
    # each data pixel occupies 2 pixels on-screen.

    needtune = True
    tunerx = 0
    tunery = 1.
    tunerscale = 200

    drag_type = DRAG_TYPE_NONE
    drag_win_x0 = drag_win_y0 = None
    drag_dc_x0 = drag_dc_y0 = None


    def __init__ (self):
        super (Viewport, self).__init__ ()
        self.add_events (gtk.gdk.POINTER_MOTION_MASK |
                         gtk.gdk.BUTTON_PRESS_MASK |
                         gtk.gdk.BUTTON_RELEASE_MASK |
                         gtk.gdk.SCROLL_MASK)
        self.connect ('expose-event', self._on_expose)
        self.connect ('scroll-event', self._on_scroll)
        self.connect ('button-press-event', self._on_button_press)
        self.connect ('button-release-event', self._on_button_release)
        self.connect ('motion-notify-event', self._on_motion_notify)

        self.bgpattern = cairo.SolidPattern (0.1, 0.1, 0.1)


    def setShapeGetter (self, getshape):
        if getshape is not None and not callable (getshape):
            raise ValueError ()
        self.getshape = getshape
        return self


    def setTuningSetter (self, settuning):
        if settuning is not None and not callable (settuning):
            raise ValueError ()
        self.settuning = settuning
        self.needtune = True
        return self


    def setSurfaceGetter (self, getsurface):
        if getsurface is not None and not callable (getsurface):
            raise ValueError ()
        self.getsurface = getsurface
        return self


    def autoscale (self):
        if self.allocation is None:
            raise Exception ('Must be called after allocation')
        if self.getshape is None:
            raise Exception ('Must be called after setting shape-getter')

        aw = self.allocation.width
        ah = self.allocation.height

        dw, dh = self.getshape ()

        wratio = float (aw) / dw
        hratio = float (ah) / dh

        self.scale = min (wratio, hratio)
        self.centerx = 0.5 * dw
        self.centery = 0.5 * dh
        self.queue_draw ()
        return self


    def center (self):
        if self.getshape is None:
            raise Exception ('Must be called after setting shape-getter')

        dw, dh = self.getshape ()
        self.centerx = 0.5 * dw
        self.centery = 0.5 * dh
        self.queue_draw ()
        return self


    def _on_expose (self, alsoself, event):
        if self.getshape is None or self.getsurface is None:
            return False

        if self.scale is None:
            self.autoscale ()
        if self.needtune:
            self.settuning (self.tunerx, self.tunery)
            self.needtune = False

        w = self.allocation.width
        seendatawidth = w / self.scale
        xoffset = 0.5 * seendatawidth - self.centerx
        h = self.allocation.height
        seendataheight = h / self.scale
        yoffset = 0.5 * seendataheight - self.centery

        surface, xoffset, yoffset = self.getsurface (xoffset, yoffset,
                                                     seendatawidth, seendataheight)

        ctxt = self.window.cairo_create ()
        ctxt.set_source (self.bgpattern)
        ctxt.paint ()

        ctxt.scale (self.scale, self.scale)
        ctxt.set_source_surface (surface, xoffset, yoffset)
        pat = ctxt.get_source ()
        pat.set_extend (cairo.EXTEND_NONE)
        pat.set_filter (cairo.FILTER_NEAREST)
        ctxt.paint ()

        return True


    def _on_scroll (self, alsoself, event):
        modmask = gtk.accelerator_get_default_mod_mask ()

        if (event.state & modmask) == 0:
            oldscale = self.scale
            newscale = self.scale

            if event.direction == gtk.gdk.SCROLL_UP:
                newscale *= 1.05

            if event.direction == gtk.gdk.SCROLL_DOWN:
                newscale /= 1.05

            if newscale == oldscale:
                return False

            self.scale = newscale
            self.queue_draw ()
            return True

        if (event.state & modmask) == gtk.gdk.SHIFT_MASK:
            oldscale = self.tunerscale
            newscale = self.tunerscale

            if event.direction == gtk.gdk.SCROLL_UP:
                newscale *= 1.05

            if event.direction == gtk.gdk.SCROLL_DOWN:
                newscale /= 1.05

            if newscale == oldscale:
                return False

            self.tunerscale = newscale
            return True

        return False


    def _on_button_press (self, alsoself, event):
        modmask = gtk.accelerator_get_default_mod_mask ()

        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
            self.grab_add ()
            self.drag_win_x0 = event.x
            self.drag_win_y0 = event.y

            if (event.state & modmask) == 0:
                self.drag_type = DRAG_TYPE_PAN
                self.drag_dc_x0 = self.centerx
                self.drag_dc_y0 = self.centery
                return True

            if (event.state & modmask) == gtk.gdk.SHIFT_MASK:
                self.drag_type = DRAG_TYPE_TUNER
                self.drag_dc_x0 = self.tunerx
                self.drag_dc_y0 = self.tunery
                return True

            return False

        if event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:
            dx = event.x - 0.5 * self.allocation.width
            dy = event.y - 0.5 * self.allocation.height

            if (event.state & modmask) == 0:
                self.centerx += dx / self.scale
                self.centery += dy / self.scale
            elif (event.state & modmask) == gtk.gdk.SHIFT_MASK:
                self.tunerx += dx / self.tunerscale
                self.tunery += dy / self.tunerscale
                self.needtune = True
            else:
                return False

            self.queue_draw ()
            # Prevent the drag-release code from running. (Double-click events
            # are preceded by single-click events.)
            self.grab_remove ()
            self.drag_type = DRAG_TYPE_NONE
            return True

        return False


    def _on_button_release (self, alsoself, event):
        if event.type == gtk.gdk.BUTTON_RELEASE and event.button == 1:
            if self.drag_type == DRAG_TYPE_NONE:
                return False

            self.grab_remove ()

            if self.drag_type == DRAG_TYPE_PAN:
                self.centerx = self.drag_dc_x0 + (self.drag_win_x0 - event.x) / self.scale
                self.centery = self.drag_dc_y0 + (self.drag_win_y0 - event.y) / self.scale
            elif self.drag_type == DRAG_TYPE_TUNER:
                self.tunerx = self.drag_dc_x0 + (event.x - self.drag_win_x0) / self.tunerscale
                self.tunery = self.drag_dc_y0 + (event.y - self.drag_win_y0) / self.tunerscale
                self.needtune = True
            else:
                return False

            self.drag_win_x0 = self.drag_win_y0 = None
            self.drag_dc_x0 = self.drag_dc_y0 = None
            self.drag_type = DRAG_TYPE_NONE
            self.queue_draw ()
            return True

        return False

    def _on_motion_notify (self, alsoself, event):
        if self.drag_type == DRAG_TYPE_NONE:
            return False
        elif self.drag_type == DRAG_TYPE_PAN:
            self.centerx = self.drag_dc_x0 + (self.drag_win_x0 - event.x) / self.scale
            self.centery = self.drag_dc_y0 + (self.drag_win_y0 - event.y) / self.scale
        elif self.drag_type == DRAG_TYPE_TUNER:
            self.tunerx = self.drag_dc_x0 + (event.x - self.drag_win_x0) / self.tunerscale
            self.tunery = self.drag_dc_y0 + (event.y - self.drag_win_y0) / self.tunerscale
            self.needtune = True

        self.queue_draw ()
        return True


DEFAULT_WIN_WIDTH = 800
DEFAULT_WIN_HEIGHT = 600


class Viewer (object):
    def __init__ (self, title='Array Viewer', default_width=DEFAULT_WIN_WIDTH,
                  default_height=DEFAULT_WIN_HEIGHT):
        self.viewport = Viewport ()
        self.win = gtk.Window (gtk.WINDOW_TOPLEVEL)
        self.win.set_title (title)
        self.win.set_default_size (default_width, default_height)
        self.win.add (self.viewport)
        self.win.connect ('key-press-event', self._on_key_press)


    def setShapeGetter (self, getshape):
        self.viewport.setShapeGetter (getshape)
        return self


    def setTuningSetter (self, settuning):
        self.viewport.setTuningSetter (settuning)
        return self


    def setSurfaceGetter (self, getsurface):
        self.viewport.setSurfaceGetter (getsurface)
        return self


    def _on_key_press (self, widget, event):
        kn = gtk.gdk.keyval_name (event.keyval)
        modmask = gtk.accelerator_get_default_mod_mask ()
        isctrl = (event.state & modmask) == gtk.gdk.CONTROL_MASK

        if kn == 'a' and isctrl:
            self.viewport.autoscale ()
            return True

        if kn == 'e' and isctrl:
            self.viewport.center ()
            return True

        if kn == 'w' and isctrl:
            self.win.destroy ()
            return True

        if kn == '1' and isctrl:
            self.viewport.scale = 1.
            self.viewport.queue_draw ()
            return True

        return False


def view (array):
    h, w = array.shape
    amin, amax = array.min (), array.max ()
    if not N.isfinite (amin):
        amin = array[N.where (N.isfinite (array))].min ()
    if not N.isfinite (amax):
        amax = array[N.where (N.isfinite (array))].max ()

    stride = cairo.ImageSurface.format_stride_for_width (cairo.FORMAT_ARGB32, w)
    # stride is in bytes:
    assert stride % 4 == 0
    imgdata = N.empty ((h, stride // 4), dtype=N.uint32)
    imagesurface = cairo.ImageSurface.create_for_data (imgdata, cairo.FORMAT_ARGB32,
                                                       w, h, stride)

    imgdata.fill (0xFF000000)

    if N.ma.is_masked (array):
        filled = array.filled (amin)
        antimask = ~array.mask
    else:
        filled = array
        antimask = None

    # Translate to 32-bit signed fixed-point. 0 is data min and
    # 0x0FFFFFF0 is data max; this gives a dynamic range of ~1.67e7
    # within the data, 4 bits of dynamic range for fractional values,
    # and 3 bits of dynamic range for out-of-scale values. The
    # smallest value we can represent is min - 8 * (max - min) and
    # the largest is 8 * (max - min) + min.

    fixed = (filled - amin) * (0x0FFFFFF0 / (amax - amin)).astype (N.int32)
    clipped = N.zeros ((h, w), dtype=N.int32)

    def getshape ():
        return w, h

    def settuning (tunerx, tunery):
        # TODO: could have different clipping behaviors. Regular clipping,
        # mark with some crazy color, flag (ie alpha -> 0)
        N.bitwise_and (imgdata, 0xFF000000, imgdata)

        fmin = int (0x0FFFFFF0 * tunerx)
        fmax = int (0x0FFFFFF0 * tunery)

        if fmin == fmax:
            # Can't use += because then Python thinks imgdata is a
            # function-local variable.
            N.add (imgdata, 255 * (fixed > fmin), imgdata)
        else:
            N.clip (fixed, fmin, fmax, clipped)
            N.subtract (clipped, fmin, clipped)
            N.multiply (clipped, 255. / (fmax - fmin), clipped)
            N.add (imgdata, clipped, imgdata)

        if antimask is not None:
            N.multiply (imgdata, antimask, imgdata)

    def getsurface (xoffset, yoffset, width, height):
        return imagesurface, xoffset, yoffset

    viewer = Viewer ()
    viewer.setShapeGetter (getshape)
    viewer.setTuningSetter (settuning)
    viewer.setSurfaceGetter (getsurface)
    viewer.win.show_all ()
    viewer.win.connect ('destroy', gtk.main_quit)
    gtk.main ()


def blink (arrays, cadence=0.6):
    import time, glib

    n = len (arrays)
    amin = amax = h = w = None

    for array in arrays:
        thish, thisw = array.shape
        thismin, thismax = array.min (), array.max ()

        if not N.isfinite (thismin):
            thismin = array[N.where (N.isfinite (array))].min ()
        if not N.isfinite (thismax):
            thismax = array[N.where (N.isfinite (array))].max ()

        if amin is None:
            w, h, amin, amax = thisw, thish, thismin, thismax
        else:
            if thisw != w:
                raise ValueError ('array widths not all equal')
            if thish != h:
                raise ValueError ('array heights not all equal')

            amin = min (amin, thismin)
            amax = max (amax, thismax)

    stride = cairo.ImageSurface.format_stride_for_width (cairo.FORMAT_ARGB32, w)
    # stride is in bytes:
    assert stride % 4 == 0
    imgdata = N.empty ((n, h, stride // 4), dtype=N.uint32)

    surfaces = [None] * n

    for i in xrange (n):
        array = arrays[i]
        surfaces[i] = cairo.ImageSurface.create_for_data (imgdata[i], cairo.FORMAT_ARGB32,
                                                          w, h, stride)

        clipped = N.clip (array, amin, amax)

        # Premultiplied alpha: if alpha = 0, entire uint32 should be zero.

        imgdata[i].fill (0xFF000000)
        N.bitwise_or (imgdata[i],
                      ((clipped - amin) * 0xFF / (amax - amin)).astype (N.uint32),
                      imgdata[i])

        if N.ma.is_masked (array):
            N.multiply (imgdata[i], ~array.mask, imgdata[i])

    t0 = time.time ()

    def getshape ():
        return w, h

    def settuning (tunerx, tunery):
        pass

    def getsurface (xoffset, yoffset, width, height):
        i = int (N.floor (((time.time () - t0) / cadence) % n))
        return surfaces[i], xoffset, yoffset

    viewer = Viewer ()
    viewer.setShapeGetter (getshape)
    viewer.setTuningSetter (settuning)
    viewer.setSurfaceGetter (getsurface)
    viewer.win.show_all ()
    viewer.win.connect ('destroy', gtk.main_quit)

    def refresh ():
        viewer.viewport.queue_draw ()
        return True

    sid = glib.timeout_add (int (cadence * 1000), refresh)
    gtk.main ()
    glib.source_remove (sid)
