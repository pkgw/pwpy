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
    def __init__ (self, flux, etaQ, maxtsys, showpre, showall, showfinal):
        self.integData = {}
        self.tmin = None
        self.flux = flux
        self.etaQ = etaQ
        self.maxtsys = maxtsys
        self.showpre = showpre
        self.showall = showall
        self.showfinal = showfinal

    def accumulate (self, time, bp, data, flags, inttime):
        if self.tmin is None:
            self.tmin = time
        else:
            self.tmin = min (self.tmin, time)
        
        times = flags * inttime
        dt = data * times

        tup = self.integData.get (bp)

        if tup is not None:
            d0, t0 = tup
            times += t0
            dt += d0

        self.integData[bp] = dt, times

    def _flatten (self):
        # Flatten out data into arrays of values we'll need

        seenAps = set ()
        aginfo = ArrayGrower (6, N.double)
        agants = ArrayGrower (2, N.int)

        for bp, (dt, times) in self.integData.iteritems ():
            w = N.where (times > 0)
            if len (w[0]) < 2: continue # if only 1 item, can't calc meaningful std
            tw = times[w]
            dt = dt[w] / tw

            mreal = dt.real.mean ()
            sreal = dt.real.std ()
            mimag = dt.imag.mean ()
            simag = dt.imag.std ()
            
            agants.add (bp[0], bp[1])
            aginfo.add (mreal, sreal, mimag, simag, tw.mean (), 0.)
            seenAps.add (bp[0])
            seenAps.add (bp[1])

        del self.integData
        
        self.aps = sorted (seenAps)
        self.info = aginfo.finish ()
        assert len (self.info) > 0, 'No data accepted!'
        self.ants = agants.finish ()
        self.tsyses = self.info[:,5]

        self.nbp = len (self.info)
        self.nap = len (seenAps)
        self.idxs = xrange (0, self.nbp)

        self._flattenAps ()

    def _flattenAps (self):
        index = self.aps.index
        
        for i in self.idxs:
            row = self.ants[i]
            row[0] = index (row[0])
            row[1] = index (row[1])

    def _computeBPSysTemps (self, jyperk, sdf):
        # Compute per-baseline tsyses
        flux = self.flux
        etaQ = self.etaQ
        tsyses = self.tsyses
        
        for i in self.idxs:
            mreal, sreal, mimag, simag, meantime, tmp1 = self.info[i]
            s = (sreal + simag) / 2

            if flux is None:
                gain = 1
            else:
                gain = flux / N.sqrt (mreal**2 + mimag**2)
            
            tsys = gain * s * etaQ * N.sqrt (2 * sdf * 1e9 * meantime) / jyperk

            #if tsys > 300: 
                #    print '  Crappy %s: TSys = %g' % (util.fmtAPs (bp), tsys)
                #    print '    real: s, D, p:', sreal, Dr, pr
                #    print '    imag: s, D, p:', simag, Di, pi
                #    continue
        
            tsyses[i] = tsys

    def _reflattenFiltered (self, skipAps):
        # prefix: o = old, n = new

        seenAps = set ()
        naginfo = ArrayGrower (6, N.double)
        nagants = ArrayGrower (2, N.int)
        oAnts = self.ants
        oAps = self.aps

        # Copy old data

        for i in self.idxs:
            oa1, oa2 = oAnts[i]
            a1, a2 = oAps[oa1], oAps[oa2]
            if a1 in skipAps or a2 in skipAps: continue

            naginfo.addLine (self.info[i])
            nagants.add (a1, a2)
            seenAps.add (a1)
            seenAps.add (a2)

        info = naginfo.finish ()
        ants = nagants.finish ()

        assert len (info) > 0, 'Skipped all antpols!'
        
        self.aps = aps = sorted (seenAps)
        self.nbp = len (info)
        self.nap = len (seenAps)
        self.idxs = idxs = xrange (0, self.nbp)
        self.info = info
        self.ants = ants
        self.tsyses = info[:,5]

        self._flattenAps ()
    
    def _solve (self):
        # Solve for per-antpol tsyses
        from numpy import sqrt, subtract, square, ndarray, zeros
        idxs = self.idxs
        ants = self.ants
        tsyses = self.tsyses
        
        chiwork = ndarray (self.nbp)
        model = ndarray (self.nbp)
        resid = ndarray (self.nbp)

        def chisq (g):
            for i in idxs:
                a1, a2 = ants[i]
                chiwork[i] = g[a1] * g[a2]

            sqrt (chiwork, model)
            subtract (model, tsyses, resid)
            square (resid, chiwork)
            return chiwork.sum ()

        gradwork = ndarray (self.nap)

        def grad (g):
            gradwork.fill (0.)

            for i in idxs:
                a1, a2 = ants[i]
                tsys = tsyses[i]
                model[i] = sqrt (g[a1] * g[a2])
            
                # chi element = (sqrt(g1 g2) - t12)**2
                # d(elt)/dg1 = 2 (sqrt(g1 g2) - t12) * / 2 / sqrt(g1 g2) * g2
                #  = g2 * (1 - t1/sqrt(g1 g2))

                v = 1 - tsys / model[i]
                gradwork[a1] += v * g[a2]
                gradwork[a2] += v * g[a1]

            #print ' Grad:', gradwork
            return gradwork

        guess = zeros (self.nap)
        n = zeros (self.nap, dtype=N.int)

        for i in idxs:
            a1, a2 = ants[i]
            tsys = tsyses[i]
            guess[a1] += tsys
            guess[a2] += tsys
            n[a1] += 1
            n[a2] += 1

        guess /= n
        #print 'guess:', guess
        bounds = [(1., None)] * self.nap
        soln, chisq, info = fmin_l_bfgs_b (chisq, guess, grad, bounds=bounds, factr=1e9)
        rchisq = chisq / (self.nbp - self.nap)
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
        aps = self.aps
        tsyses = self.tsyses
        model = self.model
        soln = self.soln
        resid = self.resid
        ants = self.ants
        
        print 'Systemp solutions:'

        col = 0
        sa = StatsAccumulator ()
        
        for i in xrange (0, self.nap):
            # Compute RMS residual for this antpol
            sa.clear ()
            for j in self.idxs:
                if i not in ants[j]: continue
                sa.add (resid[j])
            rms = sa.rms ()
            
            if col == 0: print ' ',
            if col < 3:
                print ' %3s %#6g (%#4g)' % (util.fmtAP (aps[i]), soln[i], rms),
                col += 1
            else:
                print ' %3s %#6g (%#4g)' % (util.fmtAP (aps[i]), soln[i], rms)
                col = 0

        # Make sure we end with a newline
        print
        print 'Worst residuals:'

        idxs = N.abs (resid).argsort ()
        col = 0
        lb = max (-10, -len (idxs))
        
        for i in xrange (lb, 0):
            idx = idxs[i]
            a1, a2 = ants[idx]
            bp = util.fmtAPs ((aps[a1], aps[a2])).rjust (8)
            
            if col == 0: print ' ',
            if col < 4:
                print '%s % #6g' % (bp, resid[idx]),
                col += 1
            else:
                print '%s % #6g' % (bp, resid[idx])
                col = 0

        # Make sure we end with a newline
        print

    def _show (self, haveModel):
        aps = self.aps
        tsyses = self.tsyses
        ants = self.ants

        if haveModel:
            model = self.model
            soln = self.soln

        for i in xrange (0, self.nap):
            x = []
            yobs = []
            ymod = []
            
            for j in self.idxs:
                a1, a2 = ants[j]
                
                if a1 == i:
                    x.append (aps[a2])
                elif a2 == i:
                    x.append (aps[a1])
                else: continue

                yobs.append (tsyses[j])

                if haveModel:
                    ymod.append (model[j])

            # print x, yobs, ymod
            p = omega.quickXY (x, yobs, 'Observed', lines=False)
            if haveModel:
                p.addXY (x, ymod, 'Model', lines=False)
                p.addXY ((0, aps[-1]), (soln[i], soln[i]), 'TSys ' + util.fmtAP (aps[i]))
            p.setBounds (0, aps[-1], 0)
            p.showBlocking ()

    def flush (self, jyperk, sdf):
        self._flatten ()
        self._computeBPSysTemps (jyperk, sdf)

        if self.showpre: self._show (False)
        
        print 'Iteratively flagging ...'
        
        while True:
            self._solve ()
            #self._print ()

            if self.showall: self._show (True)
            
            badAps = []
            for i in xrange (0, self.nap):
                if self.soln[i] > self.maxtsys:
                    badAps.append ((self.aps[i], self.soln[i]))

            if len (badAps) == 0: break

            # Let's not flag too many at once here
            badAps.sort (key = lambda t: t[1], reverse=True)
            badAps = badAps[0:3]
            
            for ap, soln in badAps:
                print '      Flagging antpol %s: TSys %#4g > %#4g' % \
                      (util.fmtAP (ap), soln, self.maxtsys)

            self._reflattenFiltered ([t[0] for t in badAps])

        print
        self._print ()
        
        # If showall, we already showed this solution up above.
        if self.showfinal and not self.showall: self._show (True)
        
        tmin = self.tmin
        
        self.integData = {}
        self.tmin = None

        return tmin, dict (zip (self.aps, self.soln))

# Hooks up the SysTemp calculator to the reading of a dataset

class DataProcessor (object):
    def __init__ (self, interval, flux, etaQ, maxtsys, showpre=False, showall=False, showfinal=False):
        self.interval = interval
        
        self.sts = SysTemps (flux, etaQ, maxtsys, showpre, showall, showfinal)
        self.first = True
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

        bp = util.mir2aps (inp, preamble)

        if bp[0] != bp[1] and util.apsAreInten (bp):
            # We only consider intensity-type cross-correlations ...

            if (time - tmin) > self.interval or (tmax - time) > self.interval:
                self.solutions.append (self.sts.flush (jyperk, sdf))
                tmin = tmax = time

            self.sts.accumulate (time, bp, data, flags, inttime)

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
    thePol = None
    
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
        bp = util.mir2aps (inp, preamble)
        pol = util.aps2ants (bp)[2]

        if thePol is None:
            thePol = pol
        elif pol != thePol:
            raise Exception ('Can only write meaningful systemp values for one set of polarizations at time.')
        
        # Write a new systemp entry?

        if time >= solutions[nextSolnIdx][0]:
            solns = solutions[nextSolnIdx][1]
            assert solns is not None, 'Bizarre interval calculation issues?'
        
            systemps = N.zeros (nants, dtype=N.float32)
            skipAps = set ()
        
            for i in xrange (0, nants):
                for fpol in xrange (0, 8):
                    ap = util.antpol2ap (i + 1, fpol)

                    if ap in solns:
                        systemps[i] = solns[ap]
                    else:
                        skipAps.add (ap)

            dOut.writeVarFloat ('systemp', systemps)
            nextSolnIdx += 1
            thePol = None

        if bp[0] in skipAps or bp[1] in skipAps:
            # No TSys solution for one of the antpols. Flag the record.
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
    keys.option ('showpre', 'showfinal', 'showall')

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

    dp = DataProcessor (interval, args.flux, etaQ, args.maxtsys, args.showpre,
                        args.showall, args.showfinal)

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
