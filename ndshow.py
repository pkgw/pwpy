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


class Viewport (gtk.DrawingArea):
    getshape = None
    getsurface = None

    centerx = 0
    centery = 0
    # The data pixel coordinate of the central pixel of the displayed
    # window

    scale = None
    # From data space to viewer space: e.g., scale = 2 means that
    # each data pixel occupies 2 pixels on-screen.

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


    def setShapeGetter (self, getshape):
        if getshape is not None and not callable (getshape):
            raise ValueError ()
        self.getshape = getshape
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

        w = self.allocation.width
        seendatawidth = w / self.scale
        xoffset = 0.5 * seendatawidth - self.centerx
        h = self.allocation.height
        seendataheight = h / self.scale
        yoffset = 0.5 * seendataheight - self.centery

        surface, xoffset, yoffset = self.getsurface (xoffset, yoffset,
                                                     seendatawidth, seendataheight)

        ctxt = self.window.cairo_create ()
        ctxt.scale (self.scale, self.scale)
        ctxt.set_source_surface (surface, xoffset, yoffset)
        pat = ctxt.get_source ()
        pat.set_extend (cairo.EXTEND_NONE)
        pat.set_filter (cairo.FILTER_NEAREST)
        ctxt.paint ()

        return True


    def _on_scroll (self, alsoself, event):
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


    def _on_button_press (self, alsoself, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
            self.grab_add ()
            self.drag_win_x0 = event.x
            self.drag_win_y0 = event.y
            self.drag_dc_x0 = self.centerx
            self.drag_dc_y0 = self.centery
            return True

        if event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:
            dx = event.x - 0.5 * self.allocation.width
            dy = event.y - 0.5 * self.allocation.height
            self.centerx += dx / self.scale
            self.centery += dy / self.scale
            self.queue_draw ()
            # Prevent the drag-release code from running. (Double-click events
            # are preceded by single-click events.)
            self.grab_remove ()
            self.drag_win_x0 = None
            return True

        return False


    def _on_button_release (self, alsoself, event):
        if event.type == gtk.gdk.BUTTON_RELEASE and event.button == 1:
            if self.drag_win_x0 is None:
                return False

            self.grab_remove ()
            self.centerx = self.drag_dc_x0 + (self.drag_win_x0 - event.x) / self.scale
            self.centery = self.drag_dc_y0 + (self.drag_win_y0 - event.y) / self.scale
            self.drag_win_x0 = self.drag_win_y0 = None
            self.drag_dc_x0 = self.drag_dc_y0 = None
            self.queue_draw ()
            return True

        return False

    def _on_motion_notify (self, alsoself, event):
        if self.drag_win_x0 is None:
            return False

        self.centerx = self.drag_dc_x0 + (self.drag_win_x0 - event.x) / self.scale
        self.centery = self.drag_dc_y0 + (self.drag_win_y0 - event.y) / self.scale
        self.queue_draw ()
        return True


DEFAULT_WIN_WIDTH = 600
DEFAULT_WIN_HEIGHT = 400


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
    stride = cairo.ImageSurface.format_stride_for_width (cairo.FORMAT_ARGB32, w)
    # stride is in bytes:
    assert stride % 4 == 0
    imgdata = N.empty ((h, stride // 4), dtype=N.uint32)
    imagesurface = cairo.ImageSurface.create_for_data (imgdata, cairo.FORMAT_ARGB32,
                                                       w, h, stride)

    imgdata.fill (0xFF000000) # 100% alpha
    amin, amax = array.min (), array.max ()
    imgdata += (array - amin) * (255. / (amax - amin))
    if N.ma.is_masked (array):
        imgdata -= 0xFF000000 * array.mask

    def getshape ():
        return w, h

    def getsurface (xoffset, yoffset, width, height):
        return imagesurface, xoffset, yoffset

    viewer = Viewer ()
    viewer.setShapeGetter (getshape)
    viewer.setSurfaceGetter (getsurface)
    viewer.win.show_all ()
    viewer.win.connect ('destroy', gtk.main_quit)
    gtk.main ()
