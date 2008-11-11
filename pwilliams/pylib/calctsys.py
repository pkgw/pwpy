#! /usr/bin/env python
# -*- python -*-

"""= calctsys - Compute TSys values from data noise properties
& pkgw
: Calibration
+
 CALCTSYS computes the system temperatures of a group of antennas
 based on the noise properties of a dataset. It prints out the
 derived temperatures and can optionally generate a copy of the
 input dataset with the computed values inserted into the 'systemp'
 UV variable.

 The system temperatures are computed from the variance in the real
 and imaginary parts across the spectral window of a visibility. The
 data for each baseline are averaged in time (see the "interval"
 keyword) before the variances are computed. The effective system
 temperature for a baseline is computed as:

 TSys = G * (SRe + SIm)/2 * etaQ * sqrt(2 * SDF * tau) / jyperk .

 Here, SRe and SIm are the standard deviations of the real and imaginary
 parts, respectively, of the averaged spectral window. etaQ is the
 quantization efficiency of the correlator (see the keyword "quant").
 SDF is the width of the spectral window. tau is the mean integration
 time of data feeding into the computation. (This will be different than
 "interval" if data are flagged or there are no observations for part of
 the interval.) jyperk is the current value of the "jyperk" UV variable.

 G is a "gain" parameter used to convert SRe and SIm from their native
 units into Janskys. By default, G is 1, which is appropriate for
 datasets with accurate absolute antenna gains. However, if the "flux"
 keyword is given, the data are assumed to not be amplitude calibrated,
 and then

 G = flux / sqrt (MRe^2 + MIm^2)

 where MRe and MIm are the mean value across the time-averaged spectral
 window of the real and imaginary parts, respectively. (This expression
 will only produce realistic results if the observations are of
 something similar to a point source at phase center.) The TSyses
 computed in this way will be less reliable than ones computed from a
 properly-calibrated dataset. If the antenna gains in a dataset have
 the correct relative calibration but an incorrect absolute
 calibration, using the "gain" keyword will give you results essentially
 as good as those obtained from a dataset with correct absolute
 calibration. (Such datasets might come from running MFCAL with an
 unknown source or SELFCAL without the "noscale" option.)

 Once TSys values are computed for an ensemble of baselines, TSys values
 are computed for their contributing antennas by minimizing the
 chi-squared parameter derived from the model

 TSys_ij = sqrt (TSys_i * TSys_j) .

 Very bad antennas will give poor fits to the baseline-based system
 temperatures. CALCTSYS will fit iteratively, flagging out antennas
 with excessively high TSys values. (See the "maxtsys" keyword.) The
 removal of such antennas generally improves the quality of the fit.

 CALCTSYS will print out its progress as it iteratively solves for the
 antenna TSys values and then print out the values that it computes as
 well as the baselines with the worst residuals to the fit. The
 "Pseudo-RCHiSq" value that is printed is the chi-squared value divided
 by the number of degrees of freedom; it's not a true reduced chi
 squared because the uncertainties of the baseline-based TSys
 computations are unknown. The number in parentheses after each antenna
 TSys is the RMS residual to the fit of all the baselines involving
 that antenna.

 If the "out" keyword is given, the input dataset will be copied to a
 new dataset with the computed TSys values written into the "systemp"
 UV variable. Any preexisting "systemp" values are destroyed. Any
 antennas for which no solution was found (by virtue of being either
 absent or having a computed TSys above "maxtsys") will be given a
 system temperature of 9999 K. Baselines involving such antennas will
 written into the new dataset, but be completely flagged.
 
 LIMITATIONS: Currently CALCTSYS can only handle data with a single
 spectral window and no wide channels. CALCTSYS will only process data
 of a single polarization -- it is capable of handling multiple
 polarizations internally, but the author is unclear how best to write
 out TSys values for multiple feeds on the same antenna. (There are the
 UV variables "xtsys" and "ytsys" but they don't seem to be hooked up
 the UVIO code in the same way that "systemp" is.) CALCTSYS doesn't
 write very useful history entries.

< vis
 Only a single input file is supported by CALCTSYS.
 
@ flux
 The assumed flux of the source in Janskys, if the antenna gains in
 the input dataset are uncalibrated or are only relatively calibrated.
 Do not specify this keyword if the dataset has correct absolute
 antenna gains. See the discussion of the gain parameter G above.
 
@ out
 The name of the output dataset. If given, the input dataset is
 copied with the computed TSys values inserted into it. If
 unspecified, no output dataset is created.

@ interval
 The UV data averaging interval in minutes. Default is 5. The UV data
 are time-averaged before baseline-based TSys values are computed.

@ maxtsys
 The maximum allowed TSys for an antenna, in Kelvin. If the TSys
 computed for an antenna is higher than this number, the antenna is
 flagged out in the internal data structures and TSys values are
 recomputed. If an output dataset is being created, visibilities
 involving any such antenna will be flagged. Default is 350. The
 input dataset is never modified.

@ quant
 The nature of the quantization in the correlator. Two integer values
 can be given: the first is the number of quantization levels and
 the second is the sampling rate in terms of the Nyquist sampling rate.
 (E.g., if the second value is 2, the correlator samples at twice the
 Nyquist rate.) If the second integer is unspecified it is assumed to
 be 1. The two numbers are used to look up the quantization efficiency
 in a table. (The table is a copy of Thompson, Moran, & Swenson,
 Table 8.1) The table contains entries for 2- to 4-bit correlators
 and 3-level quantization at 1 or 2 times the Nyquist rate. If
 unspecified or an unsupported bits-rate pair is given, a
 quantization efficiency of unity is used.

@ options
 Multiple options can be specified, separated by commas. Minimum-match
 is used.

 'showpre'   Plot the baseline-based TSys values before a fit is
             attempted. One plot for each antenna is shown. Requires the
             Python module 'omega'.
 'showfinal' Plot the baseline-based TSys values and model results after
             the fitting process completes. Same requirements and
             behavior as 'showpre'.
 'showall'   Plot values and model results after each iteration of the
             fitting process. Same requirements and behavior as
             'showpre'.
--
"""

import sys, numpy as N
from numutils import *
from miriad import *
from mirtask import keys, util, uvdat

SVNID = '$Id$'
# here is a demo change

# Tables

# These values come from Thompson, Moran, & Swenson, table 8.1.
# The 4-bit value comes from later in the section, citing a
# private communication from D. T. Emerson

etaQs = { (2, 1): 0.64, (2, 2): 0.74,
          (3, 1): 0.81, (3, 2): 0.89,
          (4, 1): 0.88, (4, 2): 0.94,
          (16, 1): 0.97 }

SECOND = 1. / 24 / 3600

reallyBadTSys = 9999

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
        from mirtask.util import linLeastSquares

        idxs = self.idxs
        ants = self.ants
        tsyses = self.tsyses

        # T_ij = sqrt (T_i T_j)
        # square and take logarithm:
        # 2 * log (T_ij) = log (T_i) + log (T_j)
        #
        # transform problem into log space and populate
        # the data matrices for the solver.
        
        coeffs = N.zeros ((self.nap, self.nbp))
        
        for i in idxs:
            a1, a2 = ants[i]
            coeffs[a1,i] = 1
            coeffs[a2,i] = 1

        vals = 2 * N.log (tsyses)

        logTs = linLeastSquares (coeffs, vals)
        
        self.soln = soln = N.exp (logTs)

        # Populate useful arrays.

        self.model = model = N.ndarray (self.nbp)

        for i in idxs:
            a1, a2 = ants[i]
            model[i] = soln[a1] * soln[a2]

        N.sqrt (model, model)

        self.resid = tsyses - model
        self.rchisq = (self.resid**2).sum () / (self.nbp - self.nap)
        print '   Pseudo-RChiSq:', self.rchisq

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
        import omega
        
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
            #self._solve_miriad ()
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
            self.toTrack = toTrack
            
            tmin = tmax = tprev = time

        if self.t.updated ():
            nants = inp.getVarInt ('nants')
            assert nants > 0
            if 'nspect' in self.toTrack:
                nspect = inp.getVarInt ('nspect')
            if 'nwide' in self.toTrack:
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
    flaggedAps = None
    
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

            dOut.openHistory ()
            dOut.writeHistory (banner)
            dOut.logInvocation ('CALCTSYS')

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

            if flaggedAps is not None:
                dOut.writeHistory ('CALCTSYS: in previous solution, '
                                   'flagged %d antpols' % len (flaggedAps))
                for ap in flaggedAps:
                    dOut.writeHistory ('CALCTSYS:   flagged ' + util.fmtAP (ap))
            
            systemps = N.zeros (nants, dtype=N.float32) + reallyBadTSys
            goodAps = set ()

            jd = util.jdToFull (solutions[nextSolnIdx][0])
            dOut.writeHistory ('CALCTSYS: soln %s: temps for %d antpols' % (jd, len (solns)))
        
            for ap, tsys in sorted (solns.iteritems (), key=lambda x: x[0]):
                goodAps.add (ap)
                ant = util.apAnt (ap)
                systemps[ant-1] = tsys
                dOut.writeHistory ('CALCTSYS:  %5s %f' % (util.fmtAP (ap), tsys))

            dOut.writeVarFloat ('systemp', systemps)

            nextSolnIdx += 1
            thePol = None
            flaggedAps = set ()

        bad = False
        
        if bp[0] not in goodAps:
            # No TSys solution for one of the antpols. Flag the record.
            flaggedAps.add (bp[0])
            bad = True
        if bp[1] not in goodAps:
            flaggedAps.add (bp[1])
            bad = True

        if bad:
            flags.fill (0)

        # Convert UVW coordinates from wavelengths back to nanoseconds
        # (readLowlevel automatically has Miriad do the conversion to
        # wavelengths when reading data)
        preamble[0:3] /= inp.getVarDouble ('sfreq')
        
        inp.copyLineVars (dOut)
        dOut.writeVarInt ('pol', pol)
        dOut.write (preamble, data, flags, nread)

    # All done. 

    if flaggedAps is not None:
        dOut.writeHistory ('CALCTSYS: in previous solution, '
                           'flagged %d antpols' % len (flaggedAps))
        for ap in flaggedAps:
            dOut.writeHistory ('CALCTSYS:   flagged ' + util.fmtAP (ap))
    
    dOut.closeHistory ()
    dOut.close ()

# Task implementation.

def task ():
    banner = util.printBannerSvn ('calctsys',
                                  'compute TSys values from data noise properties', SVNID)
    
    # Keywords and argument checking

    keys.keyword ('interval', 'd', 5.)
    keys.keyword ('flux', 'd', -1)
    keys.keyword ('maxtsys', 'd', 350.)
    keys.keyword ('vis', 'f', ' ')
    keys.keyword ('out', 'f', ' ')
    keys.keyword ('quant', 'i', None, 2)
    keys.option ('showpre', 'showfinal', 'showall')

    args = keys.process ()

    # Verify arguments that can be invalid
    
    if args.vis == ' ':
        print >>sys.stderr, 'Error: no UV input specified.'
        sys.exit (1)

    if args.showpre or args.showfinal or args.showall:
        try: import omega, omega.gtkUtil
        except ImportError, e:
            print >>sys.stderr, 'Unable to load module omega:', e
            print >>sys.stderr, 'Error: unable to plot solutions'
            sys.exit (1)
    
    if args.maxtsys <= 0:
        print >>sys.stderr, 'Error: invalid maximum TSys', maxtsys
        sys.exit (1)

    interval = args.interval / 60. / 24.
    if interval <= 0:
        print >>sys.stderr, 'Error: invalid interval', interval
        sys.exit (1)

    # Print out summary of config
    
    print 'Configuration:'
    rewrite = args.out != ' '
    if not rewrite:
        print '  Computing gains only, not writing new dataset.'

    if args.flux < 0:
        print '  Assuming data are calibrated to Jansky units.'
        args.flux = None
    else:
        print '  Assuming data are uncalibrated, using source flux %3g' % args.flux

    print '  Flagging TSyses above %g' % args.maxtsys

    vis = VisData (args.vis)

    print '  Averaging interval: %#4g minutes' % args.interval

    q = args.quant

    if len (q) == 0:
        etaQ = 1
    else:
        levels = q[0]

        if len (q) > 1:
            beta = q[1]
        else:
            beta = 1

        if (levels, beta) in etaQs:
            print ('  Using quantization efficiency for %d levels '
                   'and %d times Nyquist sampling' % (levels, beta))
            etaQ = etaQs[(levels, beta)]
        else:
            print >>sys.stderr, 'Warning: no tabulated quantization efficiency for %d levels and' % levels
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
