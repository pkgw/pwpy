# -*- mode: python; coding: utf-8 -*-

"""
UI features of the viewport:

click-drag to pan
scrollwheel to zoom in/out (Ctrl to do so more aggressively)
  (Shift to change color scale adjustment sensitivity)
double-click to recenter
shift-click-drag to adjust color scale (prototype)

Added by the toplevel window viewer:

Ctrl-A to autoscale data to fit window
Ctrl-E to center the data in the window
Ctrl-F to fullscreen the window
Escape to un-fullscreen it
Ctrl-W to close the window
Ctrl-1 to set scale to unity
Ctrl-S to save the data to "data.png" under the current rendering options
  (but not zoomed to the current view of the data).
Ctrl-P to print out data pixel coordinates of current pointer location

Added by cycler:

Ctrl-K to move to next plane
Ctrl-J to move to previous plane
Ctrl-C to toggle automatic cycling

"""

import numpy as N
import cairo
import glib, gtk


DEFAULT_TILESIZE = 128

class LazyComputer (object):
    buffer = None
    tilesize = None
    valid = None


    def setBuffer (self, buffer):
        self.buffer = buffer
        return self


    def allocBuffer (self, template):
        if N.ma.is_masked (template):
            self.buffer = N.ma.empty (template.shape)
            self.buffer.mask = template.mask
        else:
            self.buffer = N.empty (template.shape)
        return self


    def setTileSize (self, tilesize=DEFAULT_TILESIZE):
        self.tilesize = tilesize
        h, w = self.buffer.shape
        nxt = (w + tilesize - 1) // tilesize
        nyt = (h + tilesize - 1) // tilesize
        self.valid = N.zeros ((nyt, nxt))
        return self


    def ensureRegionUpdated (self, data, xoffset, yoffset, width, height):
        ts = self.tilesize
        buf = self.buffer
        valid = self.valid
        func = self._makeFunc (N.ma.is_masked (data))

        tilej = xoffset // ts
        tilei = yoffset // ts
        nxt = (xoffset + width + ts - 1) // ts - tilej
        nyt = (yoffset + height + ts - 1) // ts - tilei

        tyofs = tilei
        pyofs = tilei * ts

        for i in xrange (nyt):
            txofs = tilej
            pxofs = tilej * ts

            for j in xrange (nxt):
                if not valid[tyofs,txofs]:
                    func (data[pyofs:pyofs+ts,pxofs:pxofs+ts],
                          buf[pyofs:pyofs+ts,pxofs:pxofs+ts])
                    valid[tyofs,txofs] = 1

                pxofs += ts
                txofs += 1
            pyofs += ts
            tyofs += 1

        return self


    def ensureAllUpdated (self, data):
        return self.ensureRegionUpdated (data, 0, 0, data.shape[1], data.shape[0])


    def invalidate (self):
        self.valid.fill (0)
        return self


class Clipper (LazyComputer):
    dmin = None
    dmax = None

    def defaultBounds (self, data):
        dmin, dmax = data.min (), data.max ()

        if not N.isfinite (dmin):
            dmin = data[N.where (N.isfinite (data))].min ()
        if not N.isfinite (dmax):
            dmax = data[N.where (N.isfinite (data))].max ()

        self.dmin = dmin
        self.dmax = dmax
        return self


    def _makeFunc (self, ismasked):
        dmin = self.dmin
        scale = 1. / (self.dmax - dmin)

        if not ismasked:
            def func (src, dest):
                N.subtract (src, dmin, dest)
                N.multiply (dest, scale, dest)
                N.clip (dest, 0, 1, dest)
        else:
            def func (src, dest):
                N.subtract (src, dmin, dest)
                N.multiply (dest, scale, dest)
                N.clip (dest, 0, 1, dest)
                dest.mask[:] = src.mask

        return func


class ColorMapper (LazyComputer):
    def __init__ (self, mapname):
        import colormaps
        self.mapper = colormaps.factory_map[mapname]()


    def allocBuffer (self, template):
        self.buffer = N.empty (template.shape, dtype=N.uint32)
        self.buffer.fill (0xFF000000)
        return self


    def _makeFunc (self, ismasked):
        mapper = self.mapper
        # I used to preallocate this scratch array, but doing
        # "N.multiply (mapped[:,:,0], 0xFF, effscratch)" causes
        # segfaults on Fedora 16. So, work around.
        #scratch = N.zeros ((self.tilesize, self.tilesize), dtype=N.uint32)

        if not ismasked:
            def func (src, dest):
                #effscratch = scratch[:dest.shape[0],:dest.shape[1]]
                mapped = mapper (src)
                dest.fill (0xFF000000)
                # New code:
                effscratch = (mapped[:,:,0] * 0xFF).astype (N.uint32)
                # Old code:
                #N.multiply (mapped[:,:,0], 0xFF, effscratch)
                N.left_shift (effscratch, 16, effscratch)
                N.bitwise_or (dest, effscratch, dest)
                effscratch = (mapped[:,:,1] * 0xFF).astype (N.uint32)
                #N.multiply (mapped[:,:,1], 0xFF, effscratch)
                N.left_shift (effscratch, 8, effscratch)
                N.bitwise_or (dest, effscratch, dest)
                effscratch = (mapped[:,:,2] * 0xFF).astype (N.uint32)
                #N.multiply (mapped[:,:,2], 0xFF, effscratch)
                N.bitwise_or (dest, effscratch, dest)
        else:
            scratch2 = N.zeros ((self.tilesize, self.tilesize), dtype=N.uint32)

            def func (src, dest):
                #effscratch = scratch[:dest.shape[0],:dest.shape[1]]
                effscratch2 = scratch2[:dest.shape[0],:dest.shape[1]]
                mapped = mapper (src)

                dest.fill (0xFF000000)
                # New code:
                effscratch = (mapped[:,:,0] * 0xFF).astype (N.uint32)
                # Old code:
                #N.multiply (mapped[:,:,0], 0xFF, effscratch)
                N.left_shift (effscratch, 16, effscratch)
                N.bitwise_or (dest, effscratch, dest)
                effscratch = (mapped[:,:,1] * 0xFF).astype (N.uint32)
                #N.multiply (mapped[:,:,1], 0xFF, effscratch)
                N.left_shift (effscratch, 8, effscratch)
                N.bitwise_or (dest, effscratch, dest)
                effscratch = (mapped[:,:,2] * 0xFF).astype (N.uint32)
                #N.multiply (mapped[:,:,2], 0xFF, effscratch)
                N.bitwise_or (dest, effscratch, dest)

                N.invert (src.mask, effscratch2)
                N.multiply (dest, effscratch2, dest)

        return func


DRAG_TYPE_NONE = 0
DRAG_TYPE_PAN = 1
DRAG_TYPE_TUNER = 2


class Viewport (gtk.DrawingArea):
    bgpattern = None

    getshape = None
    settuning = None
    getsurface = None
    onmotion = None
    hack_doubleshift = None

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


    def setMotionHandler (self, onmotion):
        if onmotion is not None and not callable (onmotion):
            raise ValueError ()
        self.onmotion = onmotion
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


    def writeDataAsPNG (self, filename):
        if self.getshape is None:
            raise Exception ('Must be called after setting shape-getter')
        if self.getsurface is None:
            raise Exception ('Must be called after setting surface-getter')

        if self.needtune:
            self.settuning (self.tunerx, self.tunery)
            self.needtune = False

        dw, dh = self.getshape ()
        surface, xoffset, yoffset = self.getsurface (0, 0, dw, dh)
        surface.write_to_png (filename)


    def writeViewAsPNG (self, filename):
        if self.getshape is None:
            raise Exception ('Must be called after setting shape-getter')
        if self.getsurface is None:
            raise Exception ('Must be called after setting surface-getter')
        if self.allocation is None:
            raise Exception ('Must be called after allocation')

        width = self.allocation.width
        height = self.allocation.height

        stride = cairo.ImageSurface.format_stride_for_width (cairo.FORMAT_ARGB32,
                                                             width)
        assert stride % 4 == 0 # stride is in bytes
        viewdata = N.empty ((height, stride // 4), dtype=N.uint32)
        viewsurface = cairo.ImageSurface.create_for_data (viewdata, cairo.FORMAT_ARGB32,
                                                          width, height, stride)
        ctxt = cairo.Context (viewsurface)
        self._draw_in_context (ctxt, width, height)
        viewsurface.write_to_png (filename)


    def getPointerDataCoords (self):
        if self.allocation is None:
            raise Exception ('Must be called after allocation')
        if self.scale is None:
            self.autoscale ()

        x, y = self.get_pointer ()
        dx = x - 0.5 * self.allocation.width
        dy = y - 0.5 * self.allocation.height
        datax = self.centerx + dx / self.scale
        datay = self.centery + dy / self.scale
        return datax, datay


    def _draw_in_context (self, ctxt, width, height):
        if self.getshape is None or self.getsurface is None:
            raise Exception ('Must be called after setting '
                             'shape-getter and surface-getter')

        if self.scale is None:
            self.autoscale ()
        if self.needtune:
            self.settuning (self.tunerx, self.tunery)
            self.needtune = False

        seendatawidth = width / self.scale
        xoffset = 0.5 * seendatawidth - self.centerx
        seendataheight = height / self.scale
        yoffset = 0.5 * seendataheight - self.centery

        surface, xoffset, yoffset = self.getsurface (xoffset, yoffset,
                                                     seendatawidth, seendataheight)

        ctxt.set_source (self.bgpattern)
        ctxt.paint ()
        ctxt.scale (self.scale, self.scale)
        ctxt.set_source_surface (surface, xoffset, yoffset)
        pat = ctxt.get_source ()
        pat.set_extend (cairo.EXTEND_NONE)
        pat.set_filter (cairo.FILTER_NEAREST)
        ctxt.paint ()


    def _on_expose (self, alsoself, event):
        if self.getshape is None or self.getsurface is None:
            return False

        self._draw_in_context (self.window.cairo_create (),
                               self.allocation.width,
                               self.allocation.height)
        return True


    def _on_scroll (self, alsoself, event):
        modmask = gtk.accelerator_get_default_mod_mask ()

        if (event.state & modmask) in (0, gtk.gdk.CONTROL_MASK):
            oldscale = self.scale
            newscale = self.scale

            if event.state & modmask == gtk.gdk.CONTROL_MASK:
                factor = 1.2
            else:
                factor = 1.05

            if event.direction == gtk.gdk.SCROLL_UP:
                newscale *= factor

            if event.direction == gtk.gdk.SCROLL_DOWN:
                newscale /= factor

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
                if self.hack_doubleshift is not None:
                    self.hack_doubleshift (self, self.centerx + dx / self.scale,
                                           self.centery + dy / self.scale)
                else:
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
            dx = self.drag_win_x0 - event.x
            dy = self.drag_win_y0 - event.y

            if self.drag_type == DRAG_TYPE_PAN:
                self.centerx = self.drag_dc_x0 + dx / self.scale
                self.centery = self.drag_dc_y0 + dy / self.scale
            elif self.drag_type == DRAG_TYPE_TUNER:
                self.tunerx = self.drag_dc_x0 - dx / self.tunerscale
                self.tunery = self.drag_dc_y0 - dy / self.tunerscale
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
        if self.onmotion is not None:
            dx = event.x - 0.5 * self.allocation.width
            dy = event.y - 0.5 * self.allocation.height
            datax = self.centerx + dx / self.scale
            datay = self.centery + dy / self.scale
            self.onmotion (datax, datay)

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
        self.win.connect ('key-press-event', self._on_key_press)

        vb = gtk.VBox ()
        vb.pack_start (self.viewport, True, True, 2)
        hb = gtk.HBox ()
        vb.pack_start (hb, False, True, 2)

        self.status_label = gtk.Label ()
        self.status_label.set_alignment (0, 0.5)
        hb.pack_start (self.status_label, True, True, 2)

        self.status_label.set_markup ('Temp')

        self.win.add (vb)


    def setShapeGetter (self, getshape):
        self.viewport.setShapeGetter (getshape)
        return self


    def setTuningSetter (self, settuning):
        self.viewport.setTuningSetter (settuning)
        return self


    def setSurfaceGetter (self, getsurface):
        self.viewport.setSurfaceGetter (getsurface)
        return self


    def setStatusFormatter (self, fmtstatus):
        def onmotion (x, y):
            self.status_label.set_markup (fmtstatus (x, y))
        self.viewport.setMotionHandler (onmotion)
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

        if kn == 'f' and isctrl:
            self.win.fullscreen ()
            return True

        if kn == 'Escape':
            self.win.unfullscreen ()
            return True

        if kn == 'w' and isctrl:
            self.win.destroy ()
            return True

        if kn == '1' and isctrl:
            self.viewport.scale = 1.
            self.viewport.queue_draw ()
            return True

        if kn == 's' and isctrl:
            import sys
            print 'Writing data.png ...',
            sys.stdout.flush ()
            self.viewport.writeDataAsPNG ('data.png')
            print 'done'
            return True

        if kn == 'p' and isctrl:
            import sys
            print self.viewport.getPointerDataCoords ()
            sys.stdout.flush ()
            return True

        return False


def view (array, title='Array Viewer', colormap='black_to_blue', toworld=None, yflip=False):
    clipper = Clipper ()
    clipper.allocBuffer (array)
    clipper.setTileSize ()
    clipper.defaultBounds (array)
    processed = clipper.buffer

    mapper = ColorMapper (colormap)
    mapper.allocBuffer (array)
    mapper.setTileSize ()

    h, w = array.shape
    stride = cairo.ImageSurface.format_stride_for_width (cairo.FORMAT_ARGB32,
                                                         w)
    assert stride % 4 == 0 # stride is in bytes
    assert stride == 4 * w # size of buffer is set in mapper
    imagesurface = cairo.ImageSurface.create_for_data (mapper.buffer,
                                                       cairo.FORMAT_ARGB32,
                                                       w, h, stride)

    def getshape ():
        return w, h

    orig_min = clipper.dmin
    orig_span = clipper.dmax - orig_min

    def settuning (tunerx, tunery):
        clipper.dmin = orig_span * tunerx + orig_min
        clipper.dmax = orig_span * tunery + orig_min
        clipper.invalidate ()
        mapper.invalidate ()

    def getsurface (xoffset, yoffset, width, height):
        pxofs = max (int (N.floor (-xoffset)), 0)
        pyofs = max (int (N.floor (-yoffset)), 0)
        pw = min (int (N.ceil (width)), w - pxofs)
        ph = min (int (N.ceil (height)), h - pyofs)

        clipper.ensureRegionUpdated (array, pxofs, pyofs, pw, ph)
        mapper.ensureRegionUpdated (processed, pxofs, pyofs, pw, ph)

        return imagesurface, xoffset, yoffset

    if toworld is None:
        def fmtstatus (x, y):
            if yflip:
                y = h - 1 - y
            s = ''
            if x >= 0 and y >= 0 and x < w and y < h:
                s += '%g ' % array[y,x]
            return s + 'x=%d y=%d' % (x, y)
    else:
        from astutil import fmthours, fmtdeglat
        def fmtstatus (x, y):
            if yflip:
                y = h - 1 - y
            s = ''
            if x >= 0 and y >= 0 and x < w and y < h:
                s += '%g ' % array[y,x]
            lat, lon = toworld ([y, x])
            s += 'x=%d y=%d lat=%s lon=%s' % (x, y, fmtdeglat (lat),
                                              fmthours (lon))
            return s

    viewer = Viewer (title=title)
    viewer.setShapeGetter (getshape)
    viewer.setTuningSetter (settuning)
    viewer.setSurfaceGetter (getsurface)
    viewer.setStatusFormatter (fmtstatus)
    viewer.win.show_all ()
    viewer.win.connect ('destroy', gtk.main_quit)
    gtk.main ()


class Cycler (Viewer):
    getn = None
    getshapei = None
    getdesci = None
    settuningi = None
    getsurfacei = None

    i = None
    sourceid = None
    needtune = None

    def __init__ (self, title='Array Cycler', default_width=DEFAULT_WIN_WIDTH,
                  default_height=DEFAULT_WIN_HEIGHT, cadence=0.6):
        self.cadence = cadence

        self.viewport = Viewport ()
        self.win = gtk.Window (gtk.WINDOW_TOPLEVEL)
        self.win.set_title (title)
        self.win.set_default_size (default_width, default_height)
        self.win.connect ('key-press-event', self._on_key_press)
        self.win.connect ('realize', self._on_realize)
        self.win.connect ('unrealize', self._on_unrealize)

        vb = gtk.VBox ()
        vb.pack_start (self.viewport, True, True, 2)
        hb = gtk.HBox ()
        vb.pack_start (hb, False, True, 2)
        self.status_label = gtk.Label ()
        self.status_label.set_alignment (0, 0.5)
        hb.pack_start (self.status_label, True, True, 2)
        self.plane_label = gtk.Label ()
        self.plane_label.set_alignment (0, 0.5)
        hb.pack_start (self.plane_label, True, True, 2)
        self.desc_label = gtk.Label ()
        hb.pack_start (self.desc_label, True, True, 2)
        self.cycle_tbutton = gtk.ToggleButton ('Cycle')
        hb.pack_start (self.cycle_tbutton, False, True, 2)
        self.win.add (vb)

        self.viewport.setShapeGetter (self._get_shape)
        self.viewport.setSurfaceGetter (self._get_surface)
        self.viewport.setTuningSetter (self._set_tuning)

        self.cycle_tbutton.set_active (True)


    def setNGetter (self, getn):
        if not callable (getn):
            raise ValueError ('not callable')
        self.getn = getn
        return self


    def _get_shape (self):
        if self.i is None:
            self.setCurrent (0)
        return self.getshapei (self.i)


    def setShapeGetter (self, getshapei):
        if not callable (getshapei):
            raise ValueError ('not callable')
        self.getshapei = getshapei
        return self


    def setDescGetter (self, getdesci):
        if not callable (getdesci):
            raise ValueError ('not callable')
        self.getdesci = getdesci
        return self


    def _set_tuning (self, tunerx, tunery):
        if self.i is None:
            self.setCurrent (0)
        self.settuningi (self.i, tunerx, tunery)
        self.needtune.fill (True)
        self.needtune[self.i] = False


    def setTuningSetter (self, settuningi):
        if not callable (settuningi):
            raise ValueError ('not callable')
        self.settuningi = settuningi
        self.viewport.setTuningSetter (self._set_tuning) # force retune
        return self


    def _get_surface (self, xoffset, yoffset, width, height):
        if self.i is None:
            self.setCurrent (0)
        return self.getsurfacei (self.i, xoffset, yoffset, width, height)


    def setSurfaceGetter (self, getsurfacei):
        if not callable (getsurfacei):
            raise ValueError ('not callable')
        self.getsurfacei = getsurfacei
        return self


    def setStatusFormatter (self, fmtstatusi):
        def onmotion (x, y):
            self.status_label.set_markup (fmtstatusi (self.i, x, y))
        self.viewport.setMotionHandler (onmotion)
        return self


    def setCurrent (self, index):
        n = self.getn ()
        index = index % n

        if self.needtune is None or self.needtune.size != n:
            self.needtune = N.ones (n, dtype=N.bool_)

        if index == self.i:
            return

        if self.needtune[index]:
            # Force the viewport to call settuning the next time it
            # needs to
            self.viewport.setTuningSetter (self._set_tuning)

        self.i = index
        self.plane_label.set_markup ('<b>Current plane:</b> %d of %d' %
                                     (self.i + 1, n))
        self.desc_label.set_text (self.getdesci (self.i))

        if self.viewport.onmotion is not None:
            datax, datay = self.viewport.getPointerDataCoords ()
            self.viewport.onmotion (datax, datay)

        self.viewport.queue_draw ()


    def _on_realize (self, widget):
        if self.sourceid is not None:
            return
        self.sourceid = glib.timeout_add (int (self.cadence * 1000), self._do_cycle)


    def _on_unrealize (self, widget):
        if self.sourceid is None:
            return
        glib.source_remove (self.sourceid)
        self.sourceid = None


    def _do_cycle (self):
        if self.cycle_tbutton.get_active ():
            self.setCurrent (self.i + 1)
        return True


    def _on_key_press (self, widget, event):
        kn = gtk.gdk.keyval_name (event.keyval)
        modmask = gtk.accelerator_get_default_mod_mask ()
        isctrl = (event.state & modmask) == gtk.gdk.CONTROL_MASK

        if kn == 'j' and isctrl:
            self.setCurrent (self.i - 1)
            return True

        if kn == 'k' and isctrl:
            self.setCurrent (self.i + 1)
            return True

        if kn == 'c' and isctrl:
            self.cycle_tbutton.set_active (not self.cycle_tbutton.get_active ())
            return True

        return super (Cycler, self)._on_key_press (widget, event)


def cycle (arrays, descs=None, cadence=0.6, toworlds=None, yflip=False):
    import time, glib

    n = len (arrays)
    amin = amax = h = w = None

    if descs is None:
        descs = [''] * n

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
    fixed = N.empty ((n, h, w), dtype=N.int32)
    antimask = N.empty ((n, h, w), dtype=N.bool_)
    surfaces = [None] * n

    imgdata.fill (0xFF000000)

    for i, array in enumerate (arrays):
        surfaces[i] = cairo.ImageSurface.create_for_data (imgdata[i], cairo.FORMAT_ARGB32,
                                                          w, h, stride)

        if N.ma.is_masked (array):
            filled = array.filled (amin)
            antimask[i] = ~array.mask
        else:
            filled = array
            antimask[i].fill (True)

        fixed[i] = (filled - amin) * (0x0FFFFFF0 / (amax - amin))

    def getn ():
        return n

    def getshapei (i):
        return w, h

    def getdesci (i):
        return descs[i]

    clipped = N.zeros ((h, w), dtype=N.int32) # scratch array

    def settuningi (i, tunerx, tunery):
        N.bitwise_and (imgdata[i], 0xFF000000, imgdata[i])

        fmin = int (0x0FFFFFF0 * tunerx)
        fmax = int (0x0FFFFFF0 * tunery)

        if fmin == fmax:
            N.add (imgdata[i], 255 * (fixed[i] > fmin), imgdata[i])
        else:
            N.clip (fixed[i], fmin, fmax, clipped)
            N.subtract (clipped, fmin, clipped)
            N.multiply (clipped, 255. / (fmax - fmin), clipped)
            N.add (imgdata[i], clipped, imgdata[i])

        N.multiply (imgdata[i], antimask[i], imgdata[i])

    def getsurfacei (i, xoffset, yoffset, width, height):
        return surfaces[i], xoffset, yoffset

    if toworlds is None:
        def fmtstatusi (i, x, y):
            if yflip:
                y = h - 1 - y
            s = ''
            if x >= 0 and y >= 0 and x < w and y < h:
                s += '%g ' % arrays[i][y,x]
            return s + 'x=%d y=%d' % (x, y)
    else:
        from astutil import fmthours, fmtdeglat
        def fmtstatusi (i, x, y):
            if yflip:
                y = h - 1 - y
            s = ''
            if x >= 0 and y >= 0 and x < w and y < h:
                s += '%g ' % arrays[i][y,x]
            s += 'x=%d y=%d' % (x, y)
            if toworlds[i] is not None:
                lat, lon = toworlds[i] ([y, x])
                s += ' lat=%s lon=%s' % (fmtdeglat (lat),
                                         fmthours (lon))
            return s

    cycler = Cycler ()
    cycler.setNGetter (getn)
    cycler.setShapeGetter (getshapei)
    cycler.setDescGetter (getdesci)
    cycler.setTuningSetter (settuningi)
    cycler.setSurfaceGetter (getsurfacei)
    cycler.setStatusFormatter (fmtstatusi)
    cycler.win.show_all ()
    cycler.win.connect ('destroy', gtk.main_quit)

    gtk.main ()

