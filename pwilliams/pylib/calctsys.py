#! /usr/bin/env python
# -*- python -*-

"""= calctsys - 
& pkgw
: Calibration
+
 CALCTSYS ...

< vis

--
"""

import sys, omega, numpy as N
from numutils import *
from miriad import *
from mirtask import keys, util, uvdat
import fit
from scipy.stats.distributions import norm
from scipy.stats import kstest
from scipy.special import erf, erfc
from scipy.optimize import fmin_l_bfgs_b

SVNID = '$Id$'

# Tables

# These values come from Thompson, Moran, & Swenson, table 8.1.
etaQs = { (2, 1): 0.64, (2, 2): 0.74,
          (3, 1): 0.81, (3, 2): 0.89,
          (4, 1): 0.88, (4, 2): 0.94 }

SECOND = 1. / 24 / 3600

# Iterative averaging TSys computer

class SysTemps (object):
    def __init__ (self, flux, etaQ, maxtsys, showall, showfinal):
        self.integData = {}
        self.tmin = None
        self.flux = flux
        self.etaQ = etaQ
        self.maxtsys = maxtsys
        self.showall = showall
        self.showfinal = showfinal

    def accumulate (self, time, bl, data, flags, inttime):
        if self.tmin is None:
            self.tmin = time
        else:
            self.tmin = min (self.tmin, time)
        
        times = flags * inttime
        dt = data * times

        tup = self.integData.get (bl)

        if tup is not None:
            d0, t0 = tup
            times += t0
            dt += d0

        self.integData[bl] = dt, times

    def _flatten (self):
        # Flatten out data into arrays of values we'll need

        seenAnts = set ()
        gai = GrowingArray (N.double, 7)
        gaa = GrowingArray (N.int, 2)

        for bl, (dt, times) in self.integData.iteritems ():
            w = N.where (times > 0)
            if len (w[0]) < 2: continue # if only 1 item, can't calc meaningful std
            tw = times[w]
            dt = dt[w] / tw

            mreal = dt.real.mean ()
            sreal = dt.real.std ()
            mimag = dt.imag.mean ()
            simag = dt.imag.std ()
            
            gaa.add (bl[0], bl[1])
            gai.add (mreal, sreal, mimag, simag, tw.mean (), 0., 0.)
            seenAnts.add (bl[0])
            seenAnts.add (bl[1])

        gaa.doneAdding ()
        gai.doneAdding ()

        assert len (gaa) > 0, 'No data accepted!'
        
        del self.integData
        
        self.ants = sorted (seenAnts)
        self.gaa = gaa
        self.gai = gai
        self.tsyses = gai.col (6)

        self.nbl = len (gaa)
        self.nant = len (seenAnts)
        self.idxs = xrange (0, self.nbl)

        self._flattenAnts ()

    def _flattenAnts (self):
        get = self.gaa.get
        index = self.ants.index
        
        for i in self.idxs:
            row = get (i)
            row[0] = index (row[0])
            row[1] = index (row[1])

        self.a1s = self.gaa.col (0)
        self.a2s = self.gaa.col (1)

    def _computeBLSysTemps (self, jyperk, sdf):
        # Compute per-baseline tsyses
        flux = self.flux
        etaQ = self.etaQ
        tsyses = self.tsyses
        get = self.gai.get
        
        for i in self.idxs:
            mreal, sreal, mimag, simag, meantime, tmp1, tmp2 = get (i)
            s = (sreal + simag) / 2

            if flux is None:
                gain = 1
            else:
                gain = flux / N.sqrt (mreal**2 + mimag**2)
            
            tsys = gain * s * etaQ * N.sqrt (2 * sdf * 1e9 * meantime) / jyperk

            #if tsys > 300: 
                #    print '  Crappy %d-%d: TSys = %g' % (bl[0], bl[1], tsys)
                #    print '    real: s, D, p:', sreal, Dr, pr
                #    print '    imag: s, D, p:', simag, Di, pi
                #    continue
        
            tsyses[i] = tsys

    def _reflattenFiltered (self, skipAnts):
        # prefix: o = old, n = new

        seenAnts = set ()
        nGaa = GrowingArray (N.int, 2)
        nGai = GrowingArray (N.double, 7)
        oA1s = self.a1s
        oA2s = self.a2s
        oAnts = self.ants
        ogaaGet = self.gaa.get
        ogaiGet = self.gai.get

        # Copy old data

        for i in self.idxs:
            a1, a2 = oAnts[oA1s[i]], oAnts[oA2s[i]]
            if a1 in skipAnts or a2 in skipAnts: continue

            nGai.addLine (ogaiGet (i))
            nGaa.add (a1, a2)
            seenAnts.add (a1)
            seenAnts.add (a2)

        nGaa.doneAdding ()
        nGai.doneAdding ()

        assert len (nGaa) > 0, 'Skipped all antennas!'
        
        self.ants = ants = sorted (seenAnts)
        self.nbl = len (nGaa)
        self.nant = len (seenAnts)
        self.idxs = idxs = xrange (0, self.nbl)
        self.gaa = nGaa
        self.gai = nGai
        self.a1s = nGaa.col (0)
        self.a2s = nGaa.col (1)
        self.tsyses = nGai.col (6)

        self._flattenAnts ()
    
    def _solve (self):
        # Solve for per-ant tsyses
        from numpy import sqrt, subtract, square, ndarray, zeros
        idxs = self.idxs
        a1s = self.a1s
        a2s = self.a2s
        tsyses = self.tsyses
        
        chiwork = ndarray (self.nbl)
        model = ndarray (self.nbl)
        resid = ndarray (self.nbl)

        def chisq (g):
            for i in idxs:
                chiwork[i] = g[a1s[i]] * g[a2s[i]]

            sqrt (chiwork, model)
            subtract (model, tsyses, resid)
            square (resid, chiwork)
            return chiwork.sum ()

        gradwork = ndarray (self.nant)

        def grad (g):
            gradwork.fill (0.)

            for i in idxs:
                a1, a2, tsys = a1s[i], a2s[i], tsyses[i]
                model[i] = sqrt (g[a1] * g[a2])
            
                # chi element = (sqrt(g1 g2) - t12)**2
                # d(elt)/dg1 = 2 (sqrt(g1 g2) - t12) * / 2 / sqrt(g1 g2) * g2
                #  = g2 * (1 - t1/sqrt(g1 g2))

                v = 1 - tsys / model[i]
                gradwork[a1] += v * g[a2]
                gradwork[a2] += v * g[a1]

            #print ' Grad:', gradwork
            return gradwork

        guess = zeros (self.nant)
        n = zeros (self.nant, dtype=N.int)

        for i in idxs:
            a1, a2, tsys = a1s[i], a2s[i], tsyses[i]

            guess[a1] += tsys
            guess[a2] += tsys
            n[a1] += 1
            n[a2] += 1

        guess /= n
        #print 'guess:', guess
        bounds = [(1., None)] * self.nant
        soln, chisq, info = fmin_l_bfgs_b (chisq, guess, grad, bounds=bounds, factr=1e9)
        rchisq = chisq / (self.nbl - self.nant)
        print '   Pseudo-RChiSq:', rchisq

        if info['warnflag'] != 0:
            print >>sys.stderr, 'Error: Failed to find a solution!'
            print >>sys.stderr, 'soln, chisq:', soln, chisq
            print >>sys.stderr, 'info:', info
            raise Exception ('Failed to find a solution')

        self.soln = soln
        self.rchisq = rchisq
        self.model = model
        self.resid = resid

    def _print (self):
        ants = self.ants
        tsyses = self.tsyses
        model = self.model
        soln = self.soln
        resid = self.resid
        a1s = self.a1s
        a2s = self.a2s
        
        print 'Systemp solutions:'

        col = 0
        sa = StatsAccumulator ()
        
        for i in xrange (0, self.nant):
            # Compute RMS residual for this ant
            sa.clear ()
            for j in self.idxs:
                if a1s[j] != i and a2s[j] != i: continue
                sa.add (resid[j])
            rms = sa.rms ()
            
            if col == 0: print ' ',
            if col < 3:
                print ' %3d %#6g (%#4g)' % (ants[i], soln[i], rms),
                col += 1
            else:
                print ' %3d %#6g (%#4g)' % (ants[i], soln[i], rms)
                col = 0

        # Make sure we end with a newline
        print
        print 'Worst residuals:'

        idxs = N.abs (resid).argsort ()
        col = 0
        lb = max (-10, -len (idxs))
        
        for i in xrange (lb, 0):
            idx = idxs[i]
            bl = ('%d-%d' % (ants[a1s[idx]], ants[a2s[idx]])).rjust (6)
            
            if col == 0: print ' ',
            if col < 4:
                print '%s % #6g' % (bl, resid[idx]),
                col += 1
            else:
                print '%s % #6g' % (bl, resid[idx])
                col = 0

        # Make sure we end with a newline
        print

    def _show (self):
        ants = self.ants
        tsyses = self.tsyses
        model = self.model
        soln = self.soln
        a1s = self.a1s
        a2s = self.a2s
        
        for i in xrange (0, self.nant):
            x = []
            yobs = []
            ymod = []
            
            for j in self.idxs:
                if a1s[j] == i:
                    x.append (ants[a2s[j]])
                elif a2s[j] == i:
                    x.append (ants[a1s[j]])
                else: continue

                yobs.append (tsyses[j])
                ymod.append (model[j])

            # print x, yobs, ymod
            p = omega.quickXY (x, yobs, 'Observed', lines=False)
            p.addXY (x, ymod, 'Model', lines=False)
            p.addXY ((0, ants[-1]), (soln[i], soln[i]), 'TSys %d' % ants[i])
            p.setBounds (0, ants[-1], 0)
            p.showBlocking ()

    def flush (self, jyperk, sdf):
        self._flatten ()
        self._computeBLSysTemps (jyperk, sdf)

        print 'Iteratively flagging ...'
        
        while True:
            self._solve ()
            #self._print ()

            if self.showall: self._show ()
            
            badAnts = []
            for i in xrange (0, self.nant):
                if self.soln[i] > self.maxtsys:
                    badAnts.append ((self.ants[i], self.soln[i]))

            if len (badAnts) == 0: break

            # Let's not flag too many at once here
            badAnts.sort (key = lambda t: t[1], reverse=True)
            badAnts = badAnts[0:3]
            
            for ant, soln in badAnts:
                print '      Flagging antenna %2d: TSys %#4g > %#4g' % \
                      (ant, soln, self.maxtsys)

            self._reflattenFiltered ([t[0] for t in badAnts])

        print
        self._print ()
        
        # If showall, we already showed this solution up above.
        if self.showfinal and not self.showall: self._show ()
        
        tmin = self.tmin
        
        self.integData = {}
        self.tmin = None

        return tmin, dict (zip (self.ants, self.soln))

# Hooks up the SysTemp calculator to the reading of a dataset

class DataProcessor (object):
    def __init__ (self, interval, flux, etaQ, maxtsys, showall=False, showfinal=False):
        self.interval = interval
        
        self.sts = SysTemps (flux, etaQ, maxtsys, showall, showfinal)
        self.first = True
        self.thePol = None
        self.solutions = []

    def process (self, inp, preamble, data, flags, nread):
        time = preamble[3]

        if not self.first:
            tmin, tmax, tprev = self.tmin, self.tmax, self.tprev
            jyperk, inttime, sdf = self.jyperk, self.inttime, self.sdf
        else:
            self.first = False

            toTrack = ['nants', 'jyperk', 'inttime']        

            nants = inp.getVarFirstInt ('nants', 0)
            assert nants > 0
            nspect = inp.getVarFirstInt ('nspect', 0)
            nwide = inp.getVarFirstInt ('nwide', 0)
            # assert nspect > 0 or nwide > 0 FIXME: support all this
            assert nspect == 1 and nwide == 0
            jyperk = inp.getVarFirstFloat ('jyperk', 0.0)
            assert jyperk > 0
            inttime = inp.getVarFirstFloat ('inttime', 10.0)
            assert inttime > 0.
        
            if nspect > 0:
                sdf = inp.getVarDouble ('sdf', nspect)
                toTrack.append ('sdf')
                toTrack.append ('nspect')
            if nwide > 0:
                toTrack.append ('nwide')
        
            self.t = inp.makeVarTracker ()
            self.t.track (*toTrack)

            tmin = tmax = tprev = time

        if self.t.updated ():
            nants = inp.getVarInt ('nants')
            assert nants > 0
            if 'nspect' in toTrack:
                nspect = inp.getVarInt ('nspect')
            if 'nwide' in toTrack:
                nwide = inp.getVarInt ('nwide')
            assert nspect > 0 or nwide > 0
            jyperk = inp.getVarFloat ('jyperk')
            assert jyperk > 0
            inttime = inp.getVarFloat ('inttime')
            assert inttime > 0.

            if nspect > 0:
                sdf = inp.getVarDouble ('sdf', nspect)
        
        data = data[0:nread]
        flags = flags[0:nread]

        bl = util.decodeBaseline (preamble[4])

        if bl[0] == bl[1]: return # skip autos
    
        pol = uvdat.getPol ()

        if not util.polarizationIsInten (pol): return
    
        if self.thePol is None:
            self.thePol = pol
        else:
            if pol != self.thePol:
                raise Exception ('Single-pol data only, sorry')

        if (time - tmin) > self.interval or (tmax - time) > self.interval:
            self.solutions.append (self.sts.flush (jyperk, sdf))
            tmin = tmax = time

        self.sts.accumulate (time, bl, data, flags, inttime)

        self.tmin, self.tmax, self.tprev = tmin, tmax, tprev
        self.jyperk, self.inttime, self.sdf = jyperk, inttime, sdf

    def finish (self):
        self.solutions.append (self.sts.flush (self.jyperk, self.sdf))
        self.solutions.sort (key = lambda t: t[0])

        # Sentinel entry to make rewriteData algorithm simpler.
        self.solutions.append ((self.solutions[-1][0] + self.interval, None))

# Rewrite a dataset with new TSys solutions embedded

def rewriteData (banner, vis, out, solutions):
    dOut = out.open ('w')
    dOut.setPreambleType ('uvw', 'time', 'baseline')

    first = True
    nextSolnIdx = 0

    for inp, preamble, data, flags, nread in vis.readLowlevel (False):
        if first:
            first = False

            toTrack = ['nants', 'jyperk', 'inttime']        

            nants = inp.getVarFirstInt ('nants', 0)
            assert nants > 0
            nspect = inp.getVarFirstInt ('nspect', 0)
            nwide = inp.getVarFirstInt ('nwide', 0)
            assert nspect > 0 or nwide > 0
            jyperk = inp.getVarFirstFloat ('jyperk', 0.0)
            assert jyperk > 0
            inttime = inp.getVarFirstFloat ('inttime', 10.0)
            assert inttime > 0.
        
            if nspect > 0:
                sdf = inp.getVarDouble ('sdf', nspect)
                toTrack.append ('sdf')
                toTrack.append ('nspect')
            if nwide > 0:
                toTrack.append ('nwide')
        
            t = inp.makeVarTracker ()
            t.track (*toTrack)

            corrType, corrLen, corrUpd = inp.probeVar ('corr')

            if corrType != 'r' and corrType != 'j' and corrType != 'c':
                raise Exception ('No channels to copy')

            dOut.setCorrelationType (corrType)
            inp.copyHeader (dOut, 'history')
            inp.initVarsAsInput (' ') # ???
        
        if t.updated ():
            nants = inp.getVarInt ('nants')
            assert nants > 0
            if 'nspect' in toTrack:
                nspect = inp.getVarInt ('nspect')
            if 'nwide' in toTrack:
                nwide = inp.getVarInt ('nwide')
            # assert nspect > 0 or nwide > 0 FIXME: implement all this
            assert nspect == 1 and nwide == 0
            jyperk = inp.getVarFloat ('jyperk')
            assert jyperk > 0
            inttime = inp.getVarFloat ('inttime')
            assert inttime > 0.

            if nspect > 0:
                sdf = inp.getVarDouble ('sdf', nspect)

            dOut.writeVarInt ('nants', nants)
            dOut.writeVarFloat ('jyperk', jyperk)
            dOut.writeVarFloat ('inttime', inttime)

            if nspect > 0:
                dOut.writeVarInt ('nspect', nspect)
                dOut.writeVarInt ('nschan', inp.getVarInt ('nschan', nspect))
                dOut.writeVarInt ('ischan', inp.getVarInt ('ischan', nspect))
                dOut.writeVarDouble ('sdf', sdf)
                dOut.writeVarDouble ('sfreq', inp.getVarDouble ('sfreq', nspect))
                dOut.writeVarDouble ('restfreq', inp.getVarDouble ('restfreq', nspect))
            
            if nwide > 0:
                dOut.writeVarInt ('nwide', nwide)
                dOut.writeVarDouble ('wfreq', inp.getVarDouble ('wfreq', nwide))
                
            tup = inp.probeVar ('xyphase')
            if tup is not None:
                dOut.writeVarFloat ('xyphase', inp.getVarFloat ('xyphase', tup[1]))

        time = preamble[3]
        bl = util.decodeBaseline (preamble[4])
        pol = uvdat.getPol ()

        # Write a new systemp entry?

        if time >= solutions[nextSolnIdx][0]:
            solns = solutions[nextSolnIdx][1]
            assert solns is not None, 'Bizarre interval calculation issues?'
        
            systemps = N.zeros (nants, dtype=N.float32)
            skipAnts = set ()
        
            for i in xrange (0, nants):
                ant = i + 1 # stupid indexing differences

                if ant in solns:
                    systemps[i] = solns[ant]
                else:
                    skipAnts.add (ant)

            dOut.writeVarFloat ('systemp', systemps)
            nextSolnIdx += 1

        if bl[0] in skipAnts or bl[1] in skipAnts:
            # No TSys solution for one of the ants. Flag the record.
            flags.fill (0)
    
        inp.copyLineVars (dOut)
        dOut.writeVarInt ('pol', pol)
        dOut.write (preamble, data, flags, nread)

    # All done. 

    dOut.openHistory ()
    dOut.writeHistory (banner)
    dOut.logInvocation ('CALCTSYS')
    dOut.closeHistory ()
    dOut.close ()

# Task implementation.

def task ():
    banner = util.printBannerSvn ('calctsys', 'magic!', SVNID)
    
    # Keywords and argument checking

    keys.keyword ('interval', 'd', 5.)
    keys.keyword ('flux', 'd', -1)
    keys.keyword ('maxtsys', 'd', 350.)
    keys.keyword ('vis', 'f', ' ')
    keys.keyword ('out', 'f', ' ')
    keys.keyword ('quant', 'i', None, 2)
    keys.option ('showfinal', 'showall')

    args = keys.process ()
    print 'Configuration:'

    if args.vis == ' ':
        print >>sys.stderr, 'Error: no UV input specified.'
        sys.exit (1)

    rewrite = args.out != ' '
    if not rewrite:
        print '  Computing gains only, not writing new dataset.'

    if args.flux < 0:
        print '  Assuming data are calibrated to Jansky units.'
        args.flux = None
    else:
        print '  Assuming data are uncalibrated, using source flux %3g' % args.flux

    if args.maxtsys <= 0:
        print >>sys.stderr, 'Error: invalid maximum TSys', maxtsys

    print '  Flagging TSyses above %g' % args.maxtsys

    vis = VisData (args.vis)

    interval = args.interval / 60. / 24.
    if interval <= 0:
        print >>sys.stderr, 'Error: invalid interval', interval
    print '  Averaging interval: %#4g minutes' % args.interval

    q = args.quant

    if len (q) == 0:
        etaQ = 1
    else:
        bits = q[0]

        if len (q) > 1:
            beta = q[1]
        else:
            beta = 1

        if (bits, beta) in etaQs:
            print '  Using quantization efficiency for %d bits and %d times Nyquist sampling' % (bits, beta)
            etaQ = etaQs[(bits, beta)]
        else:
            print >>sys.stderr, 'Warning: no tabulated quantization efficiency for %d bits and' % bits
            print >>sys.stderr, '  %d times Nyquist sampling. Defaulting to unity.' % beta
            etaQ = 1

    print '  Quantization efficiency: %g' % etaQ

    # Let's go!

    dp = DataProcessor (interval, args.flux, etaQ, args.maxtsys, args.showall, args.showfinal)

    for tup in vis.readLowlevel (False):
        dp.process (*tup)

    dp.finish ()
    
    if not rewrite:
        # All done in this case.
        return 0
    
    # Now write the new dataset with TSys data embedded.

    out = VisData (args.out)
    rewriteData (banner, vis, out, dp.solutions)
    return 0

if __name__ == '__main__':
    sys.exit (task ())
