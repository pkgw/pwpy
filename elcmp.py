"""Compare elevations of various sources over time."""

import ralp
import numpy as N
import omega

class ElCmp (object):
    def __init__ (self, yr, mo, dy, horizon=18.0):
        self.tBase = ralp.HPJD ().fromCalendar (yr, mo, dy)

        deltas = N.linspace (-1, 1, 120, True)
        self.times = self.tBase.asLPJD () + deltas
        self.deltahrs = deltas * 24
        
        self.p = omega.quickXY ((-24, 24), (horizon, horizon),
                                'Horizon', rebound=False)
        self.p.setBounds (-24, 24, 0, 90)

    def add (self, name, ra, dec):
        ci = ralp.CatItem ()
        ci.ra, ci.dec = ra, dec
        self.addItem (name, ci)

    def addLookup (self, name):
        import sesame
        self.addItem (name, sesame.makeItem (name))
    
    def addItem (self, name, ci):
        t = ralp.HPJD ()
        
        els = [ci.getHorizon (t.fromLPJD (i))[1] for i in self.times]
        self.p.addXY (self.deltahrs, els, name, rebound=False)

