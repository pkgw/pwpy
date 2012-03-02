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
 UV variable. Temperatures are listed in Kelvin.

 The system temperatures are computed from the variance in the real
 and imaginary parts across the spectral window of a visibility --
 they are thus really expressions of the antenna system equivalent
 flux densities (SEFDs). The data for each baseline are averaged in
 time (see the "interval" keyword) before the variances are computed.
 A smoothed version of the data may also be subtracted off before the
 variances are computed (see the "hann" keyword). The effective
 system temperature for a baseline is computed as:

 TSys = G * (SRe + SIm)/2 * etaQ * sqrt(2 * SDF * tau) / jyperk .

 Here, SRe and SIm are the standard deviations of the real and imaginary
 parts, respectively, of the averaged spectral window. etaQ is the
 quantization efficiency of the correlator (see the keyword "quant").
 SDF is the width of the spectral window. tau is the mean integration
 time of data feeding into the computation. (This will be different than
 "interval" if data are flagged or there are no observations for part of
 the interval.) jyperk is usually the current value of the "jyperk" UV
 variable, but see the "jyperk" keyword.

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
 with excessively high TSys values (see the "maxtsys" keyword) and
 baselines with excessively high residuals to the model fit (see the
 "maxresid" keyword). The removal of such antennas and baselines
 generally improves the quality of the fit.

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
 written into the new dataset, but be completely flagged. Any baselines
 with residuals to the fit above "maxresid" will also be flagged.

 Due to limitations in the MIRIAD handling of system temperatures, by
 default the output dataset can only contain data for antennas with
 one polarization input: that is, the system temperature variable
 can record only one value for each antenna even if the antenna has
 two feeds. (In some feed architectures, the two polarization
 components for one antenna can have significantly different system
 temperatures, in which case this limitation becomes significant. There
 are "xtsys" and "ytsys" UV variables defined in MIRIAD, but they are
 not hooked up to the UV I/O code in the same way that "systemp" is.)
 In normal operation, CALCTSYS will signal an error if it attempts
 to write an output dataset with more than one polarization per
 antenna. The "dualpol" option can circumvent this limitation by
 writing the data in a different format: all antennas are given a
 single semi-arbitrary system temperature, and for each record a
 different "jyperk" value is written out, resulting in a correct
 SEFD for each baseline. This system is a slight abuse of the data
 format and is consumes a bit more disk space, but it works.

 System temperature information can also be stored in a simple
 line-oriented text file via the "textout" keyword. This information
 can then be applied to other datasets using the task APPLYTSYS. The
 format of the text file is designed to be forward-compatible to
 allow the introduction of more data fields if necessary. The
 current format is:

 - The first line contains the string 'nsol', then a space, than an
   integer giving the number of solutions in the file.
 - Lines are ignored until a line starting with the string
   'startsolution' is encountered.
 - Information for the solution is read until a line starting with
   the string 'endsolution' is encountered.
 - The file is read in this way to the end. It is an error if there
   are not the same number of solutions as specified in the first line.
 - Each solution section must contain a line starting with the string
   'tstart', then giving a floating-point number giving the start time
   of the solution as a Julian Date.
 - Each solution section must also contain a line starting with the
   string 'duration', then giving a floating-point number giving the
   length of the solution interval in days.
 - Each solution may contain a line starting with the string 'prchisq',
   then giving a floating-point number giving a pseudo reduced chi
   squared value for the fit of per-antenna SEFDs to the per-baseline
   assessments. Because there is no way to bootstrap the uncertainties
   of the per-baseline measurements, the number is not a true reduced
   chi squared: it gives no absolute sense of how successful the fit
   was.
 - Each solution may contain a line starting with the string 'jyperk',
   then giving a floating-point Jy/K value that may be used to convert
   the SEFDs in this solution interval into TSyses. This value is
   merely advisory.
 - Each solution section may contain any number of lines beginning with
   the string 'sefd', followed by an antpol name (e.g., '12X'), followed
   by the system equivalent flux density (SEFD) of the antpol in that
   solution, in Janskys. The SEFD measurement may be followed by the RMS
   of the contributing baseline SEFD measurements against the antpol
   value and an integer giving the number of baselines used in the
   computation of the RMS.
 - Each solution section may contain any number of lines beginning with
   the string 'badbp', followed by a basepol name (e.g., '3Y-10Y'),
   indicating that the specified basepol should be flagged during this
   solution interval.
 - The order of the above-mentioned entries is unspecified, except that
   later entries override earlier entries.

 LIMITATIONS: Currently CALCTSYS can only handle data with a single
 spectral window and no wide channels.

< vis
 Only a single input file is supported by CALCTSYS.

@ select
 The standard MIRIAD UV-data selection keyword. For more information,
 see "mirhelp select". CALCTSYS processes all selected visibilities
 except same-antenna baselines, where "same-antenna" baselines include
 for example both 6X-6X and 6X-6Y. Non-intensity-type polarizations
 may be relatively more helpful for system temperature computations than
 intensity-type ones since they will generally have a much smaller
 signal (and for the purposes of this task any signal besides system
 noise is undesirable), but see the documentation for the "flux"
 keyword below.

@ flux
 The assumed flux of the source in Janskys, if the antenna gains in
 the input dataset are uncalibrated or are only relatively calibrated.
 Do not specify this keyword if the dataset has correct absolute
 antenna gains. See the discussion of the gain parameter G above. If
 this keyword is specified and the processed data include
 non-intensity-type polarizations, a warning will be printed and
 those data will be ignored -- this keyword specifies the Stokes I
 intensity of the source, and there is no way to indicate the polarized
 flux of the source, so there's no way to correctly scale the
 non-intensity-type baselines in this case.

@ out
 The name of the output dataset. If given, the input dataset is
 copied with the computed TSys values inserted into it. If
 unspecified, no output dataset is created.

@ textout
 The name of a file into which to write a textual table of systemp
 temperature information. The format of this file is described above.

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

@ maxresid
 The maximum allowed residual for a baseline, in Kelvin. If the
 magnitude of the difference between the computed TSys value for the
 baseline and the model value for it is greater than this number, the
 baseline is flagged out in the internal data structures and TSys
 values are recomputed. If an output dataset is being created,
 visibilities involving any such antenna will be flagged. Default is
 50. The input dataset is never modified.

@ hann
 The Hanning smoothing window size. Default is 1, equivalent to no
 smoothing. If specified to be greater than 3, a copy of the
 spectral data is smoothed with a Hanning window of this width and
 then subtracted from the raw spectral data. Values of 2 or 3 remove
 all information and are forbidden. Windows with fewer than (hann + 2)
 channels also lose all information and are discarded.

 Smoothing should yield better calculations of the per-baseline TSys
 values if the bandpass is not quite flat. Larger values are more
 conservative because they vary more slowly across the
 spectrum. Larger values also lose more of your data because (hann/2)
 channels at each edge of the spectral window must be discaded.
 Values that are too small will make your TSys values be smaller than
 they really are; unfortunately, I do not think it is possible to
 quantify just what "too small" is. This smoothing does not compensate
 for flagged channels or different spectral windows, so
 discontinuities in the spectral data will worsen the results of the
 smoothing. Data means are calculated before subtraction of the
 smoothed component, so the "flux" keyword should behave identically
 regardless of the value of this parameter.

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

@ jyperk
 Possibly override the Jy/K setting used in the TSys computation. If
 set to a positive value, that value is use for jyperk. A value of one
 corresponds to computing the SEFD rather than TSys. If set to a
 negative value, the jyperk value embedded in the UV stream is
 multiplied by the absolute value of this argument. Thus -1, which is
 the default value, means that the value of jyperk embedded in the file
 will be used. If jyperk is set to a value significantly different than
 the physically-correct value for the data (especially jyperk=1), you
 will likely need to specify non-default values for the "maxtsys" and
 "maxresid" keywords to prevent all the data from being flagged.

@ options
 Multiple options can be specified, separated by commas. Minimum-match
 is used.

 'dualpol'   Write varying 'jyperk' variables in the output data set
             so that it may contain multiple-polarization data. See
             discussion in the main help text.
 'showpre'   Plot the baseline-based TSys values before a fit is
             attempted. One plot for each antenna is shown. Requires the
             Python module 'omega'.
 'showfinal' Plot the baseline-based TSys values and model results after
             the fitting process completes. Same requirements and
             behavior as 'showpre'.
 'showall'   Plot values and model results after each iteration of the
             fitting process. Same requirements and behavior as
             'showpre'.
 'nocal'     Do not apply calibration corrections when reading or
             writing the data.
 'nopass'    Do not apply bandpass corrections when reading or writing
             the data.
 'nopol'     Do not apply polarization leakage corrections when reading
             or writing the data.
--

FIXME:
 - enable plotting of tsys results.
 - could enable flux keyword and non-intensity pols by allowing user
   to specify an approximate polarized flux?
 - Use SEFDs instead of TSyses in internal computations
 - Clean up solution storage -- full class, not big tuple
 - loadText () is currently broken.
"""

import sys, numpy as np
from miriad import *
from mirtask import keys, util

__version_info__ = (1, 0)
IDENT = '$Id$'

## quickutil: arraygrower statsacc words
#- snippet: arraygrower.py
#- date: 2012 Feb 27
#- SHA1: 8ae43ac24e7ea0fb6ee2cc1047cab1588433a7ec
class ArrayGrower (object):
    __slots__ = 'dtype ncols chunkSize _nextIdx _arr'.split ()

    def __init__ (self, ncols, dtype=None, chunkSize=128):
        if dtype is None:
            import numpy as np
            dtype = np.float

        self.dtype = dtype
        self.ncols = ncols
        self.chunkSize = chunkSize
        self.clear ()


    def clear (self):
        self._nextIdx = 0
        self._arr = None
        return self


    def __len__ (self):
        return self._nextIdx


    def addLine (self, line):
        from numpy import asarray, ndarray

        line = asarray (line, dtype=self.dtype)
        if line.size != self.ncols:
            raise ValueError ('line is wrong size')

        if self._arr is None:
            self._arr = ndarray ((self.chunkSize, self.ncols),
                                 dtype=self.dtype)
        elif self._arr.shape[0] <= self._nextIdx:
            self._arr.resize ((self._arr.shape[0] + self.chunkSize,
                               self.ncols))

        self._arr[self._nextIdx] = line
        self._nextIdx += 1
        return self


    def add (self, *args):
        self.addLine (args)
        return self


    def finish (self):
        if self._arr is None:
            from numpy import ndarray
            ret = ndarray ((0, self.ncols), dtype=self.dtype)
        else:
            self._arr.resize ((self._nextIdx, self.ncols))
            ret = self._arr

        self.clear ()
        return ret
#- snippet: statsacc.py
#- date: 2012 Feb 27
#- SHA1: 37d74dcad853c14a76e2fb627c8f9063d19e9d0c
class StatsAccumulator (object):
    # FIXME: I worry about loss of precision when n gets very large:
    # we'll be adding a tiny number to a large number.  We could
    # periodically rebalance or something. I'll think about it more if
    # it's ever actually a problem.

    __slots__ = 'xtot xsqtot n _shape'.split ()

    def __init__ (self, shape=None):
        self._shape = shape
        self.clear ()

    def clear (self):
        if self._shape is None:
            self.xtot = 0.
            self.xsqtot = 0.
        else:
            from numpy import zeros
            self.xtot = zeros (self.shape)
            self.xsqtot = zeros (self.shape)

        self.n = 0
        return self

    def add (self, x):
        if self._shape is not None:
            from numpy import asarray
            x = asarray (x)
            if x.shape != self._shape:
                raise ValueError ('x has wrong shape')

        self.xtot += x
        self.xsqtot += x**2
        self.n += 1
        return self

    def num (self):
        return self.n

    def mean (self):
        return self.xtot / self.n

    def rms (self):
        if self._shape is None:
            from math import sqrt
        else:
            from numpy import sqrt
        return sqrt (self.xsqtot / self.n)

    def std (self):
        if self._shape is None:
            from math import sqrt
        else:
            from numpy import sqrt
        return sqrt (self.var ())

    def var (self):
        return self.xsqtot/self.n - (self.xtot/self.n)**2
#- snippet: words.py
#- date: 2012 Feb 27
#- SHA1: c571563028e9cc559c27d6acd98d4d35defe7d4e
def words (linegen):
    for line in linegen:
        a = line.split ('#', 1)[0].strip ().split ()
        if not len (a):
            continue
        yield a


def pathwords (path, noexistok=False, **kwargs):
    try:
        with open (path, **kwargs) as f:
            for line in f:
                a = line.split ('#', 1)[0].strip ().split ()
                if not len (a):
                    continue
                yield a
    except IOError as e:
        if e.errno != 2 or not noexistok:
            raise


def pathtext (path, noexistok=False, **kwargs):
    try:
        with open (path, **kwargs) as f:
            for line in f:
                yield line
    except IOError as e:
        if e.errno != 2 or not noexistok:
            raise
## end

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
    def __init__ (self, flux, etaQ, hann, maxtsys, maxresid,
                  showpre, showall, showfinal):
        self.integData = {}
        self.tmin = None
        self.flux = flux
        self.etaQ = etaQ
        self.hann = hann
        self.maxtsys = maxtsys
        self.maxresid = maxresid
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
        aginfo = ArrayGrower (6, np.double)
        agants = ArrayGrower (2, np.int)

        doHann = self.hann > 1
        if doHann:
            window = np.hanning (self.hann) * 2 / (self.hann - 1)

        for bp, (dt, times) in self.integData.iteritems ():
            w = np.where (times > 0)
            if len (w[0]) < self.hann + 2:
                # if only 1 item after smoothing, can't calc meaningful std
                continue
            tw = times[w]
            dt = dt[w] / tw

            r = dt.real
            i = dt.imag

            mreal = r.mean ()
            mimag = i.mean ()

            if doHann:
                r = r[self.hann / 2 : -self.hann / 2 + 1]
                i = i[self.hann / 2 : -self.hann / 2 + 1]
                r -= np.convolve (dt.real, window, mode='valid')
                i -= np.convolve (dt.imag, window, mode='valid')
                tw = np.convolve (tw, window, mode='valid')

            sreal = r.std ()
            simag = i.std ()

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
                gain = flux / np.sqrt (mreal**2 + mimag**2)

            tsys = gain * s * etaQ * np.sqrt (2 * sdf * 1e9 * meantime) / jyperk

            #if tsys > 300:
                #    print '  Crappy %s: TSys = %g' % (util.fmtBP (bp), tsys)
                #    print '    real: s, D, p:', sreal, Dr, pr
                #    print '    imag: s, D, p:', simag, Di, pi
                #    continue

            tsyses[i] = tsys

    def _reflattenFiltered (self, skipAps, skipBps):
        # prefix: o = old, n = new

        seenAps = set ()
        naginfo = ArrayGrower (6, np.double)
        nagants = ArrayGrower (2, np.int)
        oAnts = self.ants
        oAps = self.aps

        # Copy old data

        for i in self.idxs:
            oa1, oa2 = oAnts[i]
            a1, a2 = oAps[oa1], oAps[oa2]
            if (a1, a2) in skipBps: continue
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

        coeffs = np.zeros ((self.nap, self.nbp))

        for i in idxs:
            a1, a2 = ants[i]
            coeffs[a1,i] = 1
            coeffs[a2,i] = 1

        vals = 2 * np.log (tsyses)

        logTs = linLeastSquares (coeffs, vals)

        self.soln = soln = np.exp (logTs)

        # Populate useful arrays.

        self.model = model = np.ndarray (self.nbp)

        for i in idxs:
            a1, a2 = ants[i]
            model[i] = soln[a1] * soln[a2]

        np.sqrt (model, model)

        self.resid = tsyses - model
        self.rchisq = (self.resid**2).sum () / (self.nbp - self.nap)
        print '   Pseudo-RChiSq:', self.rchisq

        self.rms = rms = np.ndarray (self.nap)
        self.ncontrib = ncontrib = np.zeros (self.nap)

        sa = StatsAccumulator ()

        for i in xrange (self.nap):
            sa.clear ()
            for j in self.idxs:
                if i not in ants[j]:
                    continue
                sa.add (self.resid[j])
                ncontrib[i] += 1
            rms[i] = sa.rms ()


    def _print (self):
        aps = self.aps
        tsyses = self.tsyses
        model = self.model
        soln = self.soln
        rms = self.rms
        resid = self.resid
        ants = self.ants

        print 'Solutions:'

        col = 0

        for i in xrange (0, self.nap):
            if col == 0: print ' ',
            if col < 3:
                print ' %3s %#.4g (%#.3g)' % (util.fmtAP (aps[i]), soln[i], rms[i]),
                col += 1
            else:
                print ' %3s %#.4g (%#.3g)' % (util.fmtAP (aps[i]), soln[i], rms[i])
                col = 0

        # Make sure we end with a newline
        print
        print 'Worst residuals:'

        idxs = np.abs (resid).argsort ()
        col = 0
        lb = max (-10, -len (idxs))

        for i in xrange (lb, 0):
            idx = idxs[i]
            a1, a2 = ants[idx]
            bp = util.fmtBP ((aps[a1], aps[a2])).rjust (8)

            if col == 0: print ' ',
            if col < 4:
                print '%s % #6g' % (bp, resid[idx]),
                col += 1
            else:
                print '%s % #6g' % (bp, resid[idx])
                col = 0

        # Make sure we end with a newline
        print
        print 'Best dual-pol antennas:'

        jtsyses = {}
        lastant = None
        lasttsys = None

        for i in xrange (0, self.nap):
            ant = util.apAnt (aps[i])

            if ant == lastant:
                jtsyses[ant] = np.sqrt (lasttsys * soln[i])

            lasttsys = soln[i]
            lastant = ant

        sjtsys = sorted (jtsyses.iteritems (), key=lambda t: t[1])

        print '   ',
        for ant, jtsys in sjtsys[:5]:
            print '%d (%#.4g)' % (ant, jtsys),

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

        pg = omega.makeDisplayPager ()

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
            p.sendTo (pg)

        pg.done ()

    def flush (self, jyperk, sdf):
        self._flatten ()
        self._computeBPSysTemps (jyperk, sdf)

        if self.showpre: self._show (False)

        print 'Iteratively flagging ...'
        allBadBps = set ()

        while True:
            #self._solve_miriad ()
            self._solve ()
            #self._print ()

            if self.showall: self._show (True)

            # First look for bad baselines. Flag antennas after
            # we've gotten all of those -- don't want to let one
            # really bad baseline cause an otherwise good antenna
            # to be flagged.

            badBps = []
            badAps = []

            for i in self.idxs:
                if abs (self.resid[i]) > self.maxresid:
                    a1, a2 = self.ants[i]
                    bp = (self.aps[a1], self.aps[a2])
                    badBps.append ((bp, self.resid[i]))
                    allBadBps.add (bp)

            if len (badBps) == 0:
                for i in xrange (0, self.nap):
                    if self.soln[i] > self.maxtsys:
                        badAps.append ((self.aps[i], self.soln[i]))

                if len (badAps) == 0: break

            # Let's not flag too many at once here
            badBps.sort (key = lambda t: t[1], reverse=True)
            badBps = badBps[0:3]
            badAps.sort (key = lambda t: t[1], reverse=True)
            badAps = badAps[0:3]

            for bp, resid in badBps:
                print '      Flagging basepol %s: resid |%#4g| > %#4g' % \
                      (util.fmtBP (bp), resid, self.maxresid)
            for ap, soln in badAps:
                print '      Flagging antpol %s: TSys %#4g > %#4g' % \
                      (util.fmtAP (ap), soln, self.maxtsys)

            self._reflattenFiltered ([t[0] for t in badAps],
                                     [t[0] for t in badBps])

        print
        self._print ()

        # If showall, we already showed this solution up above.
        if self.showfinal and not self.showall: self._show (True)

        tmin = self.tmin

        self.integData = {}
        self.tmin = None

        return (tmin, self.aps, self.soln, allBadBps, jyperk, self.rms,
                self.ncontrib, self.rchisq)

# Hooks up the SysTemp calculator to the reading of a dataset

class DataProcessor (object):
    def __init__ (self, interval, flux, etaQ, hann, fjyperk, maxtsys,
                  maxresid, showpre=False, showall=False, showfinal=False):
        self.interval = interval
        self.fjyperk = fjyperk

        self.sts = SysTemps (flux, etaQ, hann, maxtsys, maxresid,
                             showpre, showall, showfinal)
        self.first = True
        self.flux = flux
        self.warnedFluxAndCrossPols = False
        self.solutions = []

    def _jyperk (self, rawval):
        if self.fjyperk == 1.:
            print 'Computing SEFDs in Jy.'
            return 1.

        if self.fjyperk > 0:
            print 'Computing temps in Kelvin, using Jy/K =', self.fjyperk, '(from task arguments)'
            return self.fjyperk

        if self.fjyperk == -1.:
            print 'Computing temps in Kelvin, using Jy/K =', rawval, '(from "jyperk" in dataset)'
            return rawval

        v = -self.fjyperk * rawval
        print 'Computing temps in Kelvin, using Jy/K =', v, \
              '(%g * "jyperk" in dataset)' % (-self.fjyperk)
        return v

    def process (self, inp, preamble, data, flags):
        time = preamble[3]

        if not self.first:
            tmin, tmax, tprev = self.tmin, self.tmax, self.tprev
            jyperk, inttime, sdf = self.jyperk, self.inttime, self.sdf
        else:
            self.first = False

            toTrack = ['nants', 'jyperk', 'inttime']

            nants = inp.getScalar ('nants', 0)
            assert nants > 0
            nspect = inp.getScalar ('nspect', 0)
            nwide = inp.getScalar ('nwide', 0)
            # assert nspect > 0 or nwide > 0 FIXME: support all this
            assert nspect == 1 and nwide == 0
            jyperk = inp.getScalar ('jyperk', 0.0)
            assert jyperk > 0
            inttime = inp.getScalar ('inttime', 10.0)
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

        bp = util.mir2bp (inp, preamble)
        ants = util.decodeBaseline (preamble[4])
        fcpdiscard = (self.flux is not None) and (not util.bpIsInten (bp))

        if fcpdiscard and not self.warnedFluxAndCrossPols:
            print >>sys.stderr, 'Warning: flux keyword not compatible with ' \
                'processing non-intensity polarizations; ignoring them.'
            self.warnedFluxAndCrossPols = True

        # drop both (eg) 6X-6X and 6X-6Y baselines.
        if ants[0] != ants[1] and not fcpdiscard:
            if (time - tmin) > self.interval or (tmax - time) > self.interval:
                self.solutions.append (self.sts.flush (self._jyperk (jyperk), sdf))
                tmin = tmax = time

            self.sts.accumulate (time, bp, data, flags, inttime)

        self.tmin, self.tmax, self.tprev = tmin, tmax, tprev
        self.jyperk, self.inttime, self.sdf = jyperk, inttime, sdf

    def finish (self):
        self.solutions.append (self.sts.flush (self._jyperk (self.jyperk), self.sdf))
        self.solutions.sort (key = lambda t: t[0])

        # Sentinel entry to make rewriteData algorithm simpler.
        self.solutions.append ((self.solutions[-1][0] + self.interval, None, None, None,
                                None, None, None, None))


def dumpText (solutions, durDays, outfn):
    """Dump the solution data to a simple textual file format."""

    f = file (outfn, 'w')

    # There's a final sentinel entry to ignore.
    print >>f, 'nsol', len (solutions) - 1

    for tstart, aps, systemps, badbps, jyperk, rms, ncontrib, rchisq in solutions[:-1]:
        print >>f, 'startsolution'
        print >>f, 'tstart', '%.10f' % tstart
        print >>f, 'duration', '%.10f' % durDays
        print >>f, 'prchisq', '%.10f' % rchisq
        print >>f, 'jyperk', '%.10f' % jyperk

        # Write SEFDs since those are really the fundamental
        # piece of information that we've computed.

        for idx, ap in enumerate (aps):
            print >>f, 'sefd', util.fmtAP (ap), '%.3f' % (systemps[idx] * jyperk), \
                '%.3f' % (rms[idx] * jyperk), ncontrib[idx]

        for bp in badbps:
            print >>f, 'badbp', util.fmtBP (bp)

        print >>f, 'endsolution'

    f.close ()


class TextFormatError (StandardError):
    def __init__ (self, *args):
        self.text = ' '.join (str (x) for x in args)
    def __str__ (self):
        return self.text


def loadText (fn):
    """Load solution data from the simple textual file format."""

    first = True

    for a in pathwords (fn):
        if first:
            if a[0] != 'nsol' or len (a) != 2:
                raise TextFormatError ('file', fn, 'does not appear to contain TSys information')

            nsol_expected = int (a[1])
            in_soln = False
            solutions = []
            first = False
            continue

        if not in_soln:
            if a[0] == 'startsolution':
                in_soln = True
                aps = []
                sefds = []
                rms = []
                ncontribs = []
                tstart = None
                durDays = None
                prchisq = None
                badbps = set ()
            continue

        if a[0] == 'endsolution':
            in_soln = False
            if tstart is None:
                raise TextFormatError ('no start time for solution in file', fn)
            if durDays is None:
                raise TextFormatError ('no duration for solution in file', fn)
            if prchisq is None:
                raise TextFormatError ('no pseudo-reduced-chi-squared for solution in file', fn)

            solutions.append ((tstart, aps, sefds, badbps, 1.0, rms, ncontribs, prchisq))
            continue

        if a[0] == 'tstart':
            tstart = float (a[1])
        elif a[0] == 'duration':
            durDays = float (a[1])
        elif a[0] == 'prchisq':
            prchisq = float (a[1])
        elif a[0] == 'sefd':
            aps.append (util.parseAP (a[1]))
            sefds.append (float (a[2]))
            rms.append (float (a[3]))
            ncontribs.append (int (float (a[4])))
        elif a[0] == 'badbp':
            badbps.add (util.parseBP (a[1]))

    if len (solutions) != nsol_expected:
        raise TextFormatError ('missing solutions in file', fn)

    solutions.append ((tstart + durDays, None, None, None))
    return solutions

# Rewrite a dataset with new TSys solutions embedded

def rewriteData (banner, vis, out, solutions, varyJyPerK, **kwargs):
    dOut = out.open ('c')
    dOut.setPreambleType ('uvw', 'time', 'baseline')

    first = True
    nextSolnIdx = 0
    thePol = None
    flaggedAps = None

    # FIXME: we don't write out npol!

    if varyJyPerK:
        theSysTemp = solutions[0][2][0]

    for inp, preamble, data, flags in vis.readLowlevel ('3', False, **kwargs):
        if first:
            first = False

            toTrack = ['nants', 'inttime']

            nants = inp.getScalar ('nants', 0)
            assert nants > 0
            nspect = inp.getScalar ('nspect', 0)
            nwide = inp.getScalar ('nwide', 0)
            assert nspect > 0 or nwide > 0
            inttime = inp.getScalar ('inttime', 10.0)
            assert inttime > 0.

            if not varyJyPerK:
                toTrack.append ('jyperk')
                jyperk = inp.getScalar ('jyperk', 0.0)
                assert jyperk > 0

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
            inp.copyItem (dOut, 'history')
            inp.initVarsAsInput (' ') # ???

            if varyJyPerK:
                systemps = np.zeros (nants, dtype=np.float32) + theSysTemp
                dOut.writeVarFloat ('systemp', systemps)

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
            inttime = inp.getVarFloat ('inttime')
            assert inttime > 0.

            if nspect > 0:
                sdf = inp.getVarDouble ('sdf', nspect)

            dOut.writeVarInt ('nants', nants)
            dOut.writeVarFloat ('inttime', inttime)

            if not varyJyPerK:
                jyperk = inp.getVarFloat ('jyperk')
                assert jyperk > 0
                dOut.writeVarFloat ('jyperk', jyperk)

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
        bp = util.mir2bp (inp, preamble)
        pol = util.bp2aap (bp)[2]

        if thePol is None:
            thePol = pol
        elif pol != thePol and not varyJyPerK:
            raise Exception ('Can only write meaningful systemp values for one set of polarizations at time.')

        # Write a new systemp entry?

        if time >= solutions[nextSolnIdx][0]:
            curSolns = dict (zip (solutions[nextSolnIdx][1], solutions[nextSolnIdx][2]))
            badBps = solutions[nextSolnIdx][3]
            curDataJyPerK = solutions[nextSolnIdx][4]
            assert curSolns is not None, 'Bizarre interval calculation issues?'

            if flaggedAps is not None:
                dOut.writeHistory ('CALCTSYS: in previous solution, '
                                   'flagged %d antpols' % len (flaggedAps))
                for ap in flaggedAps:
                    dOut.writeHistory ('CALCTSYS:   flagged ' + util.fmtAP (ap))


            systemps = np.zeros (nants, dtype=np.float32) + reallyBadTSys
            goodAps = set ()

            jd = util.jdToFull (solutions[nextSolnIdx][0])
            dOut.writeHistory ('CALCTSYS: soln %s: temps for %d antpols' % (jd, len (curSolns)))

            for ap, tsys in sorted (curSolns.iteritems (), key=lambda x: x[0]):
                goodAps.add (ap)
                ant = util.apAnt (ap)
                systemps[ant-1] = tsys
                dOut.writeHistory ('CALCTSYS:  %5s %f' % (util.fmtAP (ap), tsys))

            dOut.writeHistory ('CALCTSYS: soln %s: flagging %d basepols' % (jd, len (badBps)))

            for bp in sorted (badBps):
                dOut.writeHistory ('CALCTSYS:   flagging %s' % util.fmtBP (bp))

            if not varyJyPerK:
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
        if bp in badBps:
            bad = True

        if bad:
            flags.fill (0)

        if varyJyPerK:
            if bad:
                jyperk = 1e-6
            else:
                sefd = np.sqrt (curSolns[bp[0]] * curSolns[bp[1]]) * curDataJyPerK
                jyperk = sefd / theSysTemp
            dOut.writeVarFloat ('jyperk', jyperk)

        inp.copyLineVars (dOut)
        dOut.writeVarInt ('pol', pol)
        dOut.write (preamble, data, flags)

    # All done.

    if flaggedAps is not None:
        dOut.writeHistory ('CALCTSYS: in previous solution, '
                           'flagged %d antpols' % len (flaggedAps))
        for ap in flaggedAps:
            dOut.writeHistory ('CALCTSYS:   flagged ' + util.fmtAP (ap))

    dOut.closeHistory ()
    dOut.close ()


# AWFF/ARF interface

try:
    import arf
except:
    pass
else:
    from awff import MultiprocessMake
    from awff.pathref import FileRef

    def _gettsysinfo (context, vis=None, params=None):
        context.ensureParent ()
        out = FileRef (context.fullpath ())

        interval = params.get ('interval', 5. / 60 / 24)
        flux = params.get ('flux')
        quant = ensureiterable (params.get ('quant', []))
        hann = params.get ('hann', 1)
        jyperk = params.get ('jyperk', -1)
        maxtsys = params.get ('maxtsys', 350)
        maxresid = params.get ('maxresid', 50)

        if len (quant) == 0:
            etaQ = 1
        else:
            levels = quant[0]

            if len (quant) > 1:
                beta = quant[1]
            else:
                beta = 1

            if (levels, beta) in etaQs:
                etaQ = etaQs[(levels, beta)]
            else:
                raise ValueError ('quant = %r' % quant)

        uvdatargs = {}
        uvdatargs['select'] = params.get ('select')
        uvdatargs['line'] = params.get ('line')
        uvdatargs['stokes'] = params.get ('stokes')
        uvdatargs['ref'] = params.get ('ref')
        uvdatargs['nocal'] = params.get ('nocal')
        uvdatargs['nopass'] = params.get ('nopass')
        uvdatargs['nopol'] = params.get ('nopol')

        dp = DataProcessor (interval, flux, etaQ, hann, jyperk, maxtsys, maxresid)
        for tup in vis.readLowlevel ('3', False, **uvdatargs):
            dp.process (*tup)
        dp.finish ()
        dumpText (dp.solutions, interval, str (out))

        return out

    GetTSysInfo = MultiprocessMake ('vis params', 'out', _gettsysinfo,
                                    [None, {}])

    from mirtask.util import mir2bp, bp2aap
    from arf.vispipe import VisPipeStage

    class AddTSysInfo (VisPipeStage):
        def __init__ (self, pathobj):
            self.pathobj = pathobj
            self.solutions = loadText (str (pathobj))

        def __str__ (self):
            return '%s(%s)' % (self.__class__.__name__, self.pathobj)

        def updateHash (self, updater):
            updater (self.__class__.__name__)
            updater (str (self.pathobj))

        def init (self, state):
            self.nextsolnidx = 0
            self.cursoln = None
            self.badbps = None
            self.goodaps = None
            self.curjyperk = None
            self.tsystrack = None
            self.systemps = None

        def record (self, state):
            nextsoldata = self.solutions[self.nextsolnidx]
            cursoln = self.cursoln
            badbps = self.badbps
            goodaps = self.goodaps
            curjyperk = self.curjyperk
            tsystrack = self.tsystrack
            systemps = self.systemps

            if tsystrack is None:
               tsystrack = self.tsystrack = state.inp.makeVarTracker ().track ('systemp')

            if tsystrack.updated ():
                nants = state.inp.getVarInt ('nants')
                systemps = self.systemps = state.inp.getVarFloat ('systemp', nants)

            if state.preamble[3] > nextsoldata[0] or cursoln is None:
                cursoln = self.cursoln = dict (zip (nextsoldata[1], nextsoldata[2]))
                badbps = self.badbps = nextsoldata[3]
                curjyperk = self.curjyperk = nextsoldata[4]
                goodaps = self.goodaps = set (cursoln.iterkeys ())
                self.nextsolnidx += 1

            bp = mir2bp (state.inp, state.preamble)
            ant1, ant2, pol = bp2aap (bp)

            if bp[0] not in goodaps or bp[1] not in goodaps or bp in badbps:
                state.flags.fill (0)
                jyperk = 1e-6
            else:
                jyperk = np.sqrt ((cursoln[bp[0]] * cursoln[bp[1]]) /
                                  (systemps[ant1 - 1] * systemps[ant2 - 1])) * curjyperk

            state.jyperk = jyperk


# Task implementation.

## quickutil: die
#- snippet: die.py
#- date: 2012 Feb 27
#- SHA1: 1bb64c8c018023854995c0f8954a2bdc625a7ee0
def die (fmt, *args):
    """Raise a :exc:`SystemExit` exception with a formatted error message.

:arg str format: a format string
:arg args: arguments to the format string

If *args* is empty, a :exc:`SystemExit` exception is raised with the
argument ``'error: ' + str (fmt)``. Otherwise, the string component is
``fmt % args``. If uncaught, the interpreter exits with an error code
and prints the exception argument.

Example::

   if ndim != 3:
      die ('require exactly 3 dimensions, not %d', ndim)
"""

    if not len (args):
        raise SystemExit ('error: ' + str (fmt))
    raise SystemExit ('error: ' + (fmt % args))
## end


def taskCalc (args):
    banner = util.printBannerGit ('calctsys',
                                  'compute TSys values from data noise properties', IDENT)

    # Keywords and argument checking

    ks = keys.KeySpec ()
    ks.keyword ('interval', 'd', 5.)
    ks.keyword ('flux', 'd', -1)
    ks.keyword ('maxtsys', 'd', 350.)
    ks.keyword ('maxresid', 'd', 50.)
    ks.keyword ('vis', 'f', ' ')
    ks.keyword ('out', 'f', ' ')
    ks.keyword ('textout', 'f', ' ')
    ks.mkeyword ('quant', 'i', 2)
    ks.keyword ('hann', 'i', 1)
    ks.keyword ('jyperk', 'd', -1.0)
    ks.keyword ('select', 'a', '')
    ks.option ('showpre', 'showfinal', 'showall', 'dualpol',
                 'nocal', 'nopass', 'nopol')
    args = ks.process (args)

    # Verify arguments that can be invalid

    if args.vis == ' ':
        print >>sys.stderr, 'Error: no UV input specified.'
        sys.exit (1)

    if args.showpre or args.showfinal or args.showall:
        try: import omega, omega.gtkInteg
        except ImportError, e:
            print >>sys.stderr, 'Unable to load module omega:', e
            print >>sys.stderr, 'Error: unable to plot solutions'
            sys.exit (1)

    if args.maxtsys <= 0:
        print >>sys.stderr, 'Error: invalid maximum TSys', maxtsys
        sys.exit (1)

    if args.maxresid <= 0:
        print >>sys.stderr, 'Error: invalid maximum residual', maxresid
        sys.exit (1)

    interval = args.interval / 60. / 24.
    if interval <= 0:
        print >>sys.stderr, 'Error: invalid interval', interval
        sys.exit (1)

    if args.hann < 1 or args.hann == 2 or args.hann == 3:
        print >>sys.stderr, 'Error: Hanning smoothing width must be 1 or >3; got', args.hann
        sys.exit (1)

    if args.jyperk == 0.:
        print >>sys.stderr, 'Error: jyperk argument may not be zero.'
        sys.exit (1)

    inputArgs = {}

    if args.nocal:
        inputArgs['nocal'] = True

    if args.nopass:
        inputArgs['nopass'] = True

    if args.nopol:
        inputArgs['nopol'] = True

    if args.select != '':
        inputArgs['select'] = args.select

    # Print out summary of config

    print 'Configuration:'
    rewrite = args.out != ' '
    if not rewrite:
        print '  Computing gains only, not writing new dataset.'

    writeText = args.textout != ' '
    if writeText:
        print '  Writing TSys information to text file', args.textout, '.'

    if args.flux < 0:
        print '  Assuming data are calibrated to Jansky units.'
        args.flux = None
    else:
        print '  Assuming data are uncalibrated, using source flux %3g' % args.flux

    print '  Flagging TSyses above %g, BL residuals above %g' % (args.maxtsys,
                                                                 args.maxresid)

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

    if args.hann == 1:
        print '  Not subtracting smoothed spectral data.'
    else:
        print '  Subtracting spectral data Hanning-smoothed with window size %d.' % args.hann

    if args.jyperk == -1.:
        print '  Using jyperk from UV data.'
    elif args.jyperk == 1.:
        print '  Computing SEFDs rather than TSyses.'
    elif args.jyperk > 0:
        print '  Using Jy/K = %g' % args.jyperk
    else:
        print '  Scaling value of jyperk in file by %g' % (-args.jyperk)

    if rewrite:
        if args.dualpol:
            print '  Rewriting jyperk variable for dual-pol data.'
        else:
            print '  Rewriting tsys variable; single-pol data only.'

    # Let's go!

    dp = DataProcessor (interval, args.flux, etaQ, args.hann, args.jyperk,
                        args.maxtsys, args.maxresid, args.showpre, args.showall,
                        args.showfinal)

    for tup in vis.readLowlevel ('3', False, **inputArgs):
        dp.process (*tup)

    dp.finish ()

    if writeText:
        dumpText (dp.solutions, interval, args.textout)

    if not rewrite:
        # All done in this case.
        return 0

    # Now write the new dataset with TSys data embedded.

    out = VisData (args.out)
    rewriteData (banner, vis, out, dp.solutions, args.dualpol, **inputArgs)
    return 0


def taskApply (args):
    banner = util.printBannerGit ('applytsys',
                                  'insert TSys information into UV data', IDENT)

    ks = keys.KeySpec ()
    ks.keyword ('vis', 'f', ' ')
    ks.keyword ('out', 'f', ' ')
    ks.keyword ('textin', 'f', ' ')
    ks.keyword ('select', 'a', '')
    ks.option ('dualpol', 'nocal', 'nopass', 'nopol')
    args = ks.process (args)

    if args.vis == ' ':
        return die ('no UV input specified')

    if args.out == ' ':
        return die ('no UV output specified')

    if args.textin == ' ':
        return die ('no TSys information input specified')

    inputArgs = {}

    if args.nocal:
        inputArgs['nocal'] = True

    if args.nopass:
        inputArgs['nopass'] = True

    if args.nopol:
        inputArgs['nopol'] = True

    if args.select != '':
        inputArgs['select'] = args.select

    vis = VisData (args.vis)
    out = VisData (args.out)

    try:
        solutions = loadText (args.textin)
    except TextFormatError, e:
        return die (str (e))

    rewriteData (banner, vis, out, solutions, args.dualpol, **inputArgs)
    return 0


if __name__ == '__main__':
    sys.exit (taskCalc (sys.argv[1:]))
