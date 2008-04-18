"""An interactive tweakable plot thingy."""

import gtk
import omega, omega.gtkUtil
import numpy as N

class TweakyPlot (omega.ToplevelPaintParent):
    def __init__ (self, params):
        self.params = params
        self.style = omega.styles.WhiteOnBlackBitmap ()
        self._adjs = {}
        self.p = self._setup ()

        # UI
        
        self.win = gtk.Window ()
        self.win.set_title ('TweakyPlot!')
        self.win.set_default_size (640, 480)
        
        self.vbox = vbox = gtk.VBox (len (params) + 1)
        vbox.set_homogeneous (False)
        self.win.add (vbox)

        self.oa = omega.gtkUtil.OmegaArea (self.p, omega.styles.WhiteOnBlackBitmap (), False)
        self.oa.connect ('expose_event', self.onExpose)
        vbox.pack_start (self.oa, True, True, 4)
            
        for (name, pmin, pmax, digits) in params:
            hb = gtk.HBox (2)
            hb.set_homogeneous (False)

            l = gtk.Label ('<b>%s:</b>' % name)
            l.set_use_markup (True)
            l.set_alignment (0.5, 1.0)
            hb.pack_start (l, False, False, 2)

            s = gtk.HScale ()
            s.set_value_pos (gtk.POS_RIGHT)
            s.set_update_policy (gtk.UPDATE_CONTINUOUS)
            s.set_digits (digits)
            s.connect ('value-changed', self.onChanged)
            
            self._adjs[name] = s.get_adjustment ()
            self._adjs[name].lower = pmin
            self._adjs[name].upper = pmax
            self._adjs[name].value = (pmin + pmax) / 2
            hb.pack_start (s, True, True, 2)

            vbox.pack_start (hb, False, True, 2)

        self.win.show_all ()

        # Load in first batch of data
        
        self.onExpose (None, None)

    def onExpose (self, widget, event):
        # Export params
        
        for (name, pmin, pmax, digits) in self.params:
            setattr (self, name, self._adjs[name].value)

        # Update data
        
        self._updatePainter ()
        return False

    def onChanged (self, widget):
        self.oa.queue_draw ()
    
    def _getPainter (self):
        raise NotImplementedError ()

    def showBlocking (self):
        self.win.connect ('destroy', gtk.main_quit)
        gtk.main ()

class DemoTweaky (TweakyPlot):
    def __init__ (self):
        TweakyPlot.__init__ (self, [('xmid', -5., 5, 1),
                                    ('ht', 0., 10., 1),
                                    ('w', 0., 5., 1)])

    def _setup (self):
        self.dp = omega.rect.XYDataPainter ()

        self.x = N.linspace (-10, 10, 100, True)

        p = omega.RectPlot ()
        p.add (self.dp, rebound=False)
        return p

    def _updatePainter (self):
        y = self.ht * N.exp (-(self.x - self.xmid)**2 / (2 * self.w**2))
        self.dp.setFloats (self.x, y)
        
        self.p.rebound ()
