#! /usr/bin/env python

"""blflag - Baseline-based bad data flagger.

Presents a graphical interface for identifying and flagging bad baselines
in a dataset.

This documentation is wildly insufficient.

This can be used as a standalone script, or interactively as a module
via IPython."""

import omega, pickle
from os import listdir, mkdir
from os.path import basename, join, isdir, exists, dirname
from mirexec import TaskSelfCal, TaskUVPlot, TaskUVFlag
from mirtask.util import decodeBaseline
from numutils import *
import cairo, gtk, gobject, numpy as N

def _makeGladeFile ():
    import os
    f = os.path.dirname (__file__)
    return os.path.join (f, 'blmapper.glade')

_gladefile = _makeGladeFile ()
from gtk import glade

class BLData (object):
    def __init__ (self):
        self.clear ()

    def clear (self):
        self.ants = set ()
        self.values = {}
        
    def add (self, bl, value):
        a1, a2 = bl

        if a1 > a2: raise ValueError ()
        
        self.ants.add (a1)
        self.ants.add (a2)
        
        self.values[bl] = value

class BLDrawer (gtk.DrawingArea):
    margin = 2
    spacing = 4
    textColor = (0, 0, 0)
    grayColor = (0.8, 0.8, 0.8)
    selColor = (0.5, 0, 0.8)

    logMode = False
    scaleToMin = False
    
    def __init__ (self, data):
        gtk.DrawingArea.__init__ (self)

        self.data = data
        self.hidden = set ()
        self.selected = set ()
        
        self.connect ('expose_event', self._expose)

    def resetSels (self):
        self.hidden = set ()
        self.selected = set ()
        self.queue_draw ()
    
    def _expose (self, widget, event):
        ctxt = widget.window.cairo_create ()
        ctxt.rectangle (event.area.x, event.area.y,
                        event.area.width, event.area.height)
        ctxt.clip ()

        w, h = self.allocation.width, self.allocation.height

        self.paint (ctxt, w, h)
        return False

    def toggleVisibility (self, bl):
        if bl in self.hidden:
            self.hidden.remove (bl)
        else:
            self.hidden.add (bl)
    
    def toggleSelection (self, bl):
        if bl in self.selected:
            self.selected.remove (bl)
        else:
            self.selected.add (bl)
    
    antColXMin = None
    antColXMax = None
    antRowYMin = None
    antRowYMax = None
    blXMin = None
    blXMax = None
    blYMin = None
    blYMax = None
    blWidth = None
    blHeight = None
    srtAnts = None

    blOfMax = None
    blOfMin = None

    def isHidden (self, bl):
        if bl in self.hidden: return True
        if (bl[0], None) in self.hidden: return True
        if (bl[1], None) in self.hidden: return True
        return False
        
    def paint (self, ctxt, w, h):
        from math import ceil, floor

        nants = len (self.data.ants)

        if nants < 1: return

        # Apply margins

        ctxt.translate (self.margin, self.margin)
        w -= 2 * self.margin
        h -= 2 * self.margin

        self.antColXMin = self.margin
        self.antRowYMin = self.margin
        
        # Calculate text extents to know how much space we have for tiles
        
        r = xrange (0, nants)
        srtAnts = sorted (self.data.ants)
        extents = {}
        maxtw, maxth = 0, 0
        
        for ant in srtAnts:
            extents[ant] = e = ctxt.text_extents ('%d' % ant)
            
            if e[2] > maxtw:
                maxtw = int (ceil (e[2]))

            if e[3] > maxth:
                maxth = int (ceil (e[3]))

        draww, drawh = w - maxtw, h - maxth

        antw = int (floor (1.0 * (draww - nants * self.spacing) / nants))
        anth = int (floor (1.0 * (drawh - nants * self.spacing) / nants))

        self.antColXMax = self.antColXMin + maxtw
        self.antRowYMax = self.antRowYMin + maxth
        self.blXMin = self.antColXMax + self.spacing
        self.blYMin = self.antRowYMax + self.spacing
        self.blWidth = antw + self.spacing
        self.blHeight = anth + self.spacing
        self.blXMax = self.blXMin + self.blWidth * nants
        self.blYMax = self.blYMin + self.blHeight * nants
        self.srtAnts = srtAnts
        
        # Draw side labels

        for i in r:
            ant = srtAnts[i]
            e = extents[ant]

            yTop = maxth + self.spacing + i * (anth + self.spacing)
            yText = yTop + 0.5 * (anth - e[3])

            ctxt.move_to (-e[0], yText - e[1])
            ctxt.set_source_rgb (*self.textColor)
            ctxt.show_text ('%d' % ant)

            if (ant, None) in self.selected:
                ctxt.rectangle (0, yTop, maxtw, anth)
                ctxt.set_source_rgb (*self.selColor)
                ctxt.set_line_width (self.spacing)
                ctxt.stroke ()

        # Draw top labels

        for i in r:
            ant = srtAnts[i]
            e = extents[ant]

            xLeft = maxtw + self.spacing + i * (antw + self.spacing)
            xText = xLeft + 0.5 * (antw - e[2])

            ctxt.move_to (xText - e[0], -e[1])
            ctxt.set_source_rgb (*self.textColor)
            ctxt.show_text ('%d' % ant)

            if (ant, None) in self.selected:
                ctxt.rectangle (xLeft, 0, antw, maxth)
                ctxt.set_source_rgb (*self.selColor)
                ctxt.set_line_width (self.spacing)
                ctxt.stroke ()
        
        # Draw boxes

        dmax = 0.0
        dmin = 1e40
        
        for (bl, val) in self.data.values.iteritems ():
            if self.isHidden (bl): continue
            
            if val > dmax:
                dmax = val
                self.blOfMax = bl
            if val < dmin:
                dmin = val
                self.blOfMin = bl

        from numpy import log10 as l10
        
        for i1 in r:
            for i2 in r:
                a1 = srtAnts[i1]
                a2 = srtAnts[i2]

                xLeft = maxtw + self.spacing + i1 * (antw + self.spacing)
                yTop = maxth + self.spacing + i2 * (anth + self.spacing)
                ctxt.rectangle (xLeft, yTop, antw, anth)

                if a1 > a2: bl = (a2, a1)
                else: bl = (a1, a2)
                
                val = self.data.values.get (bl)

                if bl in self.selected:
                    ctxt.set_source_rgb (*self.selColor)
                    ctxt.set_line_width (self.spacing)
                    ctxt.stroke_preserve ()
                
                if val is None or self.isHidden (bl):
                    ctxt.set_source_rgb (*self.grayColor)
                elif self.logMode:
                    v = (l10 (val) - l10 (dmin)) / (l10 (dmax) - l10 (dmin))
                    ctxt.set_source_rgb (0., 0., v)
                elif self.scaleToMin:
                    ctxt.set_source_rgb ((val - dmin) / (dmax - dmin), 0., 0.)
                else:
                    ctxt.set_source_rgb (val / dmax, 0., 0.)

                ctxt.fill ()

    def decodePoint (self, x, y):
        if self.blWidth is None:
            raise Exception ('Haven\'t painted yet!')

        from math import floor
        
        xValid = x >= self.blXMin and x <= self.blXMax
        yValid = y >= self.blYMin and y <= self.blYMax

        inAntRow = y >= self.antRowYMin and y <= self.antRowYMax
        inAntCol = x >= self.antColXMin and x <= self.antColXMax

        if xValid:
            xNum = int (floor ((x - self.blXMin) / self.blWidth))

            if x - self.blXMin - xNum * self.blWidth > self.blWidth - self.spacing:
                # we hit the gutter
                xValid = False
            else:
                xAnt = self.srtAnts[xNum]

        if yValid:
            yNum = int (floor ((y - self.blYMin) / self.blHeight))

            if y - self.blYMin - yNum * self.blHeight > self.blHeight - self.spacing:
                # we hit the gutter
                yValid = False
            else:
                yAnt = self.srtAnts[yNum]

        if xValid and yValid:
            if xAnt > yAnt: return (yAnt, xAnt)
            return (xAnt, yAnt)

        if xValid and inAntRow:
            return (xAnt, None)

        if yValid and inAntCol:
            return (yAnt, None)

        return None
    
class BLWindow (object):
    def __init__ (self, workflow, parent=None, title=None):
        self.workflow = workflow
        self.data = BLData ()
        self.drawer = drawer = BLDrawer (self.data)

        self.xml = xml = glade.XML (_gladefile)
        xml.signal_autoconnect (self)
        
        # Window setup
        
        self.win = win = xml.get_widget ('blmapper')
        if title is not None: win.set_title (str (title))
        if parent is not None: win.set_transient_for (parent)

        # Drawer setup

        xml.get_widget ('vbox1').add_with_properties (drawer, 'position', 0)
        drawer.add_events (gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK)
        drawer.connect ('button_press_event', self.onButtonPress)
        drawer.connect ('button_release_event', self.onButtonRelease)
        drawer.connect_after ('expose_event', self.onExpose)
        
        # Mode selector

        xml.get_widget ('rb_both').set_active (True)
        self.clickMode = self.CM_VISIBILITY | self.CM_SELECTION

        # Extremum indicator

        self.l_extrema = xml.get_widget ('l_extrema')

    def run (self):
        if not self.workflow.next ():
            print 'Nothing to do at all???'
            return
        
        self.workflow.amStdExport (self.data)
        
        self.win.connect ('destroy', gtk.main_quit)
        self.win.show_all ()
        gtk.main ()
    
    CM_VISIBILITY = 1
    CM_SELECTION = 2
    
    def onVisibilityToggled (self, rb):
        if not rb.get_active (): return
        self.clickMode = self.CM_VISIBILITY
        
    def onSelectionToggled (self, rb):
        if not rb.get_active (): return
        self.clickMode = self.CM_SELECTION
        
    def onBothToggled (self, rb):
        if not rb.get_active (): return
        self.clickMode = self.CM_VISIBILITY | self.CM_SELECTION

    def onScaleMinToggled (self, cb):
        self.drawer.scaleToMin = cb.get_active ()
        self.drawer.queue_draw ()

    def onExpose (self, drawer, event):
        def upd ():
            t = '<b>Maximum:</b> %d-%d ; <b>Minimum:</b> %d-%d' % \
                (drawer.blOfMax + drawer.blOfMin)
            self.l_extrema.set_markup (t)
            return False
        
        gobject.idle_add (upd)
    
    def onButtonPress (self, drawer, event):
        # Is this something we care about?
        return event.button == 1
        
    def onButtonRelease (self, drawer, event):
        if event.button != 1:
            return False

        x, y = event.get_coords ()
        ret = drawer.decodePoint (x, y)

        if ret is None: return True

        #elif ret[1] is None:
        #    print 'hit row or col for', ret[0]
        #else:
        #    print 'hit baseline %d-%d' % ret

        if self.clickMode & self.CM_VISIBILITY:
            drawer.toggleVisibility (ret)
            drawer.queue_draw ()
            
        if self.clickMode & self.CM_SELECTION:
            drawer.toggleSelection (ret)
            drawer.queue_draw ()
            
        return True

    def onRegen (self, button):
        self.workflow.applySels (self.drawer.selected)
        self.workflow.regen ()
        self.workflow.amStdExport (self.data)
        self.drawer.resetSels ()
        self.drawer.queue_draw ()

    def onShowAmStds (self, button):
        self.workflow.amStdExport (self.data)
        self.drawer.queue_draw ()

    def onShowAmps (self, button):
        self.workflow.ampExport (self.data)
        self.drawer.queue_draw ()

    def onShowPhStds (self, button):
        self.workflow.phStdExport (self.data)
        self.drawer.queue_draw ()

    def onShowPhs (self, button):
        self.workflow.phExport (self.data)
        self.drawer.queue_draw ()

    def onShowUVds (self, button):
        self.workflow.uvdExport (self.data)
        self.drawer.queue_draw ()

    def onSaveNext (self, button):
        self.workflow.applySels (self.drawer.selected)
        self.workflow.save ()

        if not self.workflow.next ():
            print 'All done!'
            gtk.main_quit ()
            
        self.workflow.amStdExport (self.data)
        self.drawer.resetSels ()
        self.drawer.queue_draw ()

    def onSkipNext (self, button):
        if not self.workflow.next ():
            print 'All done!'
            gtk.main_quit ()
        
        self.workflow.amStdExport (self.data)
        self.drawer.resetSels ()
        self.drawer.queue_draw ()

class IterFlagWorkFlow (object):
    vis = None
    work = None
    
    def startFile (self, vis, pol, flagfile):
        if self.work is not None: self.work.delete ()

        print
        print 'Working on', vis
        print
        
        if exists (flagfile):
            print
            print '!!! Flag file %s exists!' % flagfile
            print

        self.vis = vis
        self.pol = pol
        self.flagfile = flagfile
        
        self.work = vis.vvis ('blflag')
        self.bls = set ()
        self.ants = set ()

        self.astats = self.uvstats = self.phstats = None
        self.regen ()
    
    def regen (self):
        # Create untouched work file
        
        self.work.delete ()
        #self.vis.averTo (self.work, 100, select='-auto')
        self.vis.catTo (self.work, select='-auto,pol(%s)' % self.pol)

        # Apply flags
        
        if len (self.ants) > 0:
            TaskUVFlag (vis=self.work, flagval='f',
                        select='ant(%s)' % ','.join (str (a) for a in sorted (self.ants))).run ()
        
        for bl in self.bls:
            self.work.fBL (self.pol, bl[0], bl[1])

        # Selfcal
        
        TaskSelfCal (vis=self.work, noscale=True, amplitude=True,
                     flux=1.0, interval=30).xrun ()

        # Make MIRIAD plots
        
        TaskUVPlot (vis=self.work, axis='uvdist,amp', nobase=True,
                    yrange='0,2', device='1/xs').run ()
        TaskUVPlot (vis=self.work, axis='uvdist,ph', nobase=True,
                    device='2/xs').run ()
        
        # Read in information
        
        self.astats = AccDict (StatsAccumulator, lambda a, v: a.add (v))
        self.uvstats = AccDict (StatsAccumulator, lambda a, v: a.add (v))
        self.phstats = AccDict (StatsAccumulator, lambda a, v: a.add (v))
        
        print 'Reading', self.work, '...'
        ngot = 0
        iter = self.work.readLowlevel (False, line='chan,1,1,512')
        
        for inp, preamble, data, flags, nread in iter:
            assert (nread == 1)
            if flags[0] == 0: continue
            ngot += 1
            bl = decodeBaseline (preamble[4])
            uvd = N.sqrt (preamble[0]**2 + preamble[1]**2) * 1e-3
            self.astats.accum (bl, abs (data[0]))
            self.phstats.accum (bl, N.arctan2 (data[0].imag, data[0].real))
            self.uvstats.accum (bl, uvd)

        if ngot == 0: print 'Read no data??!'
        else: print 'Read %d points' % ngot

    def amStdExport (self, data):
        data.clear ()
        
        for bl, acc in self.astats.iteritems ():
            data.add (bl, acc.std ())

    def ampExport (self, data):
        data.clear ()
        
        for bl, acc in self.astats.iteritems ():
            data.add (bl, acc.mean ())

    def phStdExport (self, data):
        data.clear ()
        
        for bl, acc in self.phstats.iteritems ():
            data.add (bl, acc.std ())

    def phExport (self, data):
        data.clear ()
        
        for bl, acc in self.phstats.iteritems ():
            data.add (bl, acc.mean ())

    def uvdExport (self, data):
        data.clear ()
        
        for bl, acc in self.uvstats.iteritems ():
            data.add (bl, acc.mean ())

    def applySels (self, selected):
        for a1, a2 in selected:
            if a2 is None:
                self.ants.add (a1)
            else:
                self.bls.add ((a1, a2))

        toremove = []
        
        for a1, a2 in self.bls:
            if a1 in self.ants or a2 in self.ants:
                toremove.append ((a1, a2))

        for bl in toremove: self.bls.remove (bl)

        print 'Flagged antennas:', ' '.join (str (x) for x in self.ants)
        print 'Flagged baselines:', ' '.join ('%d-%d' % x for x in self.bls)
    
    def save (self):
        if len (self.ants) == 0 and len (self.bls) == 0:
            print 'Nothing to write, not saving.'
            return
        
        f = file (self.flagfile, 'w')
        print 'Writing %s ...' % self.flagfile

        if len (self.ants) > 0:
            print >>f, 'pol=%s ant=%s' % (self.pol, ','.join(str (a) for a in sorted (self.ants)))

        if len (self.bls) > 0:
            print >>f, 'pol=%s bl=%s' % (self.pol, ','.join ('%d-%d' % t for t in self.bls))
        f.close ()


class SingleWorkFlow (IterFlagWorkFlow):
    def __init__ (self, vis, pol, flagfile):
        self.thevis = vis
        self.thepol = pol
        self.theflag = flagfile
    
    def next (self):
        if self.thevis is None: return False

        self.startFile (self.thevis, self.thepol, self.theflag)
        self.thevis = None
        return True

if __name__ == '__main__':
    if len (sys.argv) == 4:
        wf = SingleWorkFlow (VisData (sys.argv[1]), sys.argv[2], sys.argv[3])
    else:
        print 'Usage: %s vis pol flagfile' % sys.argv[0]
        sys.exit (1)
    
    blw = BLWindow (wf)
    blw.run ()
    blw.workflow.work.delete ()
