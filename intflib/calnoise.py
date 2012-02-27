#! /usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

"""\
Use a bandpass calibrator observation to information calibrating the
system noise levels to the autocorrelation amplitudes of raw data.
An ARF preprocessing stage can then use this calibration information
to insert appropriate TSys and Jy/K information.

"""

import sys, os.path
import cPickle
import numpy as N
import scipy.optimize
import numutils
from miriad import *
from mirtask import util, uvdat

__version_info__ = (1, 0)
__all__ = ('NoiseCal loadNoiseCalExport').split ()

TTOL = 1./1440 # 1 minute


class NoiseCal (object):
    instr = None # the ARF instrument used to take the data

    saps = None # sorted list of seen (autocorr) antpols

    raras = None # raw autocorrelation rms amplitudes: {apidx:
    # (3,n)-ndarray} with n sets of: JD timestamp, raw autocorrelation
    # RMS amplitudes, RARA msmt weight; apidx is an index into saps

    sqbps = None # squashed sample basepols: (n,2)-ndarray with two
    # indexes into saps 

    bpdata = None # basepol sample data: (n,5)-ndarray where n is the
    # same as in sqbps. items are JD timestamp, spectrum variance,
    # variance measurement weight, rara product, rara product weight

    solution = None # noise coefficient solutions: n-element vector
    # where n is the number of seen antpols, such that
    # (solution1 * rara1 * solution2 * rara2) gives the expected
    # visibility variance for a set of correlations

    covar = None # Covariance matrix of derived solutions: (n,n)-
    # element ndarray, where n is len(saps).

    svals = None # solution values for samples: n-element vector
    # with n the same as in sqbps, with svals[i] = solution1 *
    # solution2 for the i'th good sample.

    suncerts = None # formal uncertainties in the per-sample
    # solutions: n-element vector, n as in sqbps

    def load (self, path, partial=False):
        f = open (path)
        self.instr = cPickle.load (f)
        self.saps = cPickle.load (f)
        self.solution = N.load (f)
        self.covar = N.load (f)
        if not partial:
            self.raras = cPickle.load (f)
            self.sqbps = N.load (f)
            self.bpdata = N.load (f)
            self.svals = N.load (f)
            self.suncerts = N.load (f)
        f.close ()
        

    def printsefdinfo (self):
        raras = self.raras
        solution = self.solution
        saps = self.saps
        n = len (saps)
        maxant = util.apAnt (saps[-1]) + 1

        msefds = N.empty (n)
        pstds = N.empty (n)
        antcounts = N.zeros (maxant)
        antprods = N.ones (maxant)

        for i in xrange (n):
            info = raras[i]
            # TODO later: we're ignoring the RARA weighting
            # sqrt (2 * 102.4 khz * 10 s)
            sefd = 1431 * solution[i] * info[1]
            msefds[i] = sefd.mean ()
            pstds[i] = 100. * sefd.std () / msefds[i]

            ant = util.apAnt (saps[i])
            antcounts[ant] += 1
            antprods[ant] *= msefds[i]

        w = N.where (antcounts == 2)[0]
        if w.size == 0:
            bestant = -1
        else:
            bestant = w[N.argmin (antprods[w])]

        mmarks = ['     |     '] * n
        smarks = ['     |     '] * n

        sm = N.argsort (msefds)
        ss = N.argsort (pstds)

        for i in xrange (5):
            mmarks[sm[i]] = ' ' * i + '*' + ' ' * (4 - i) + '|     '
            mmarks[sm[-1 - i]] = '     |' + ' ' * (4 - i) + '*' + ' ' * i
            smarks[ss[i]] = ' ' * i + '*' + ' ' * (4 - i) + '|     '
            smarks[ss[-1 - i]] = '     |' + ' ' * (4 - i) + '*' + ' ' * i

        print 'instrument:', self.instr
        print
        print '%4s %7s %5s %13s %13s' % ('AP', 'SEFD', 'Var.', 'SEFD Rank',
                                         'Var. Rank')

        for i in xrange (n):
            print '%4s %7.0f %4.1f%% [%s] [%s]' % \
                (util.fmtAP (saps[i]), msefds[i], pstds[i], mmarks[i], smarks[i])

        print
        print 'Median (mean SEFD):', N.median (msefds)
        print '       Equiv. TSys:', N.median (msefds) / 153.

        if bestant < 0:
            print 'No dual-pol antennas'
        else:
            print 'Best dual-pol antenna:', bestant


    def export (self, stream):
        solution = self.solution
        saps = self.saps

        for i in xrange (len (saps)):
            print >>stream, self.instr, util.fmtAP (saps[i]), '%.5e' % solution[i]


    def compute (self, toread, **uvdatoptions):
        for vis in toread:
            if not os.path.exists (vis.path ('gains')):
                util.die ('input "%s" has no gain calibration tables', vis)

        self._compute_getraras (toread, uvdatoptions)
        self._compute_getbpvs (toread, uvdatoptions)
        self._compute_solve ()


    def save (self, outpath):
        f = open (outpath, 'w')
        # Start with just the info needed to apply to noise calibration:
        cPickle.dump (self.instr, f)
        cPickle.dump (self.saps, f)
        self.solution.dump (f)
        self.covar.dump (f)
        # Then (potentially large) extra data for checking the quality
        # of the noise calibration:
        cPickle.dump (self.raras, f)
        self.sqbps.dump (f)
        self.bpdata.dump (f)
        self.svals.dump (f)
        self.suncerts.dump (f)
        f.close ()


    # The bits that actually do the calibration:

    def _compute_getraras (self, toread, uvdatoptions):
        seenaps = set ()
        rarawork = {}

        previnp = None
        gen = uvdat.setupAndRead (toread, 'a3', False,
                                  nopass=True, nocal=True, nopol=True,
                                  **uvdatoptions)

        for inp, preamble, data, flags in gen:
            if previnp is None or inp is not previnp:
                instr = inp.getScalarItem ('arfinstr', 'UNDEF')
                if instr != 'UNDEF':
                    if self.instr is None:
                        self.instr = instr
                    elif instr != self.instr:
                        util.die ('input instrument changed from "%s" to '
                                  '"%s" in "%s"', self.instr, instr,
                                  inp.path ())
                previnp = inp

            # the 'a' uvdat options limits us to autocorrelations,
            # but includes 1X-1Y-type autocorrelations
            bp = util.mir2bp (inp, preamble)
            if not util.bpIsInten (bp):
                continue
            ap = bp[0]
            t = preamble[3]

            w = N.where (flags)[0]
            if not w.size:
                continue

            data = data[w]
            rara = N.sqrt ((data.real**2).mean ())

            seenaps.add (ap)
            ag = rarawork.get (ap)
            if ag is None:
                ag = rarawork[ap] = numutils.ArrayGrower (3)

            # We record w.size as a weight for the RARA measurement,
            # but it's essentially noise-free.
            ag.add (t, rara, w.size)

        self.saps = sorted (seenaps)
        raras = self.raras = {}
        apidxs = dict ((t[1], t[0]) for t in enumerate (self.saps))

        for ap in rarawork.keys ():
            raradata = rarawork[ap].finish ().T
            apidx = apidxs[ap]
            sidx = N.argsort (raradata[0])
            raras[apidx] = raradata[:,sidx]


    def _compute_getbpvs (self, toread, uvdatoptions):
        raras = self.raras
        apidxs = dict ((t[1], t[0]) for t in enumerate (self.saps))

        sqbps = numutils.ArrayGrower (2, dtype=N.int)
        bpdata = numutils.ArrayGrower (5)
        
        nnorara = 0
        seenidxs = set ()
        gen = uvdat.setupAndRead (toread, 'x3', False,
                                  nopass=False, nocal=False, nopol=False,
                                  **uvdatoptions)

        for inp, preamble, data, flags in gen:
            bp = util.mir2bp (inp, preamble)
            t = preamble[3]

            w = N.where (flags)[0]
            if not w.size:
                continue

            idx1, idx2 = apidxs.get (bp[0]), apidxs.get (bp[1])
            if idx1 is None or idx2 is None:
                nnorara += 1
                continue

            rdata1, rdata2 = raras[idx1], raras[idx2]

            tidx1 = rdata1[0].searchsorted (t)
            tidx2 = rdata2[0].searchsorted (t)

            if (tidx1 < 0 or tidx1 >= rdata1.shape[1] or
                tidx2 < 0 or tidx2 >= rdata2.shape[1]):
                nnorara += 1
                continue

            tr1, rara1, rwt1 = rdata1[:,tidx1]
            tr2, rara2, rwt2 = rdata2[:,tidx2]
            dt1 = N.abs (tr1 - t)
            dt2 = N.abs (tr2 - t)

            if max (dt1, dt2) > TTOL:
                nnorara += 1
                continue

            # We propagate the weight for crara but once again,
            # it's basically noiseless.
            crara = rara1 * rara2
            cwt = 1. / (rara2**2 / rwt1 + rara1**2 / rwt2)

            data = data[w]
            rvar = data.real.var (ddof=1)
            ivar = data.imag.var (ddof=1)
            var = 0.5 * (rvar + ivar)
            # The weight of the computed variance (i.e., the
            # inverse square of the maximum-likelihood variance
            # in the variance measurement) is 0.5 * (nsamp - ndof) / var**2.
            # We have 2*w.size samples and 2 degrees of freedom, so:
            wtvar = (w.size - 1) / var**2

            seenidxs.add (idx1)
            seenidxs.add (idx2)
            sqbps.add (idx1, idx2)
            bpdata.add (t, var, wtvar, crara, cwt)

        sqbps = self.sqbps = sqbps.finish ()
        self.bpdata = bpdata.finish ()
        nsamp = sqbps.shape[0]

        if nnorara > nsamp * 0.02:
            print >>sys.stderr, ('Warning: no autocorr data for %d/%d '
                                 '(%.0f%%) of samples' % (nnorara, nsamp,
                                                          100. * nnorara / nsamp))

        if len (seenidxs) == len (apidxs):
            return

        # There exist antpols that we got autocorrelations for but
        # have no contributing baselines. This can happen if there are
        # no gains for the given antpol. To avoid running into a
        # singular matrix in the solve step, we have to eliminate
        # them. To avoid a bunch of baggage in the analysis code, we
        # rewrite our data structures, which actually isn't so bad.

        mapping = {}
        newsaps = []
        newraras = {}

        for idx in xrange (len (apidxs)):
            if idx in seenidxs:
                mapping[idx] = len (mapping)
                newsaps.append (self.saps[idx])
                newraras[mapping[idx]] = raras[idx]

        self.saps = newsaps
        self.raras = newraras

        for i in xrange (nsamp):
            sqbps[i,0] = mapping[sqbps[i,0]]
            sqbps[i,1] = mapping[sqbps[i,1]]


    def _compute_solve (self):
        nap = len (self.saps)
        sqbps = self.sqbps
        bpdata = self.bpdata
        nsamp = bpdata.shape[0]

        # Get approximate solution by using a linear least squares
        # solver on the log of our equation.

        coeffs = N.zeros ((nap, nsamp))
        values = N.empty (nsamp)
        invsigmas = N.empty (nsamp)

        for i in xrange (nsamp):
            idx1, idx2 = sqbps[i]
            var, wtvar, crara = bpdata[i,1:4]

            coeffs[idx1,i] = coeffs[idx2,i] = 1
            values[i] = N.log (var / crara)
            # Here we ignore the noise in crara.
            invsigmas[i] = crara * N.sqrt (wtvar)

        soln = util.linLeastSquares (coeffs, values)

        # Now refine and get uncertainties with a nonlinear solver.

        soln = N.exp (soln)
        values = N.exp (values)
        modelvals = N.empty (nsamp)

        def nonlin (params):
            for i in xrange (nsamp):
                idx1, idx2 = sqbps[i]
                modelvals[i] = params[idx1] * params[idx2]
            return (values - modelvals) * invsigmas

        from scipy.optimize import leastsq
        soln, cov, misc, mesg, flag = leastsq (nonlin, soln, full_output=True)
        if flag < 1 or flag > 4 or cov is None:
            if cov is None:
                expln = 'encountered singular matrix'
            else:
                expln = 'return flag was %d' % flag

            if 'CALNOISE_DEBUG' in os.environ:
                print >>sys.stderr, 'Nonlinear fit failed! Saving anyway!'
                print >>sys.stderr, 'expln:', expln
                print >>sys.stderr, 'mesg:', mesg
                cov = None
            else:
                util.die ('nonlinear fit failed: %s; mesg: %s', expln, mesg)

        rchisq = (((values - modelvals) * invsigmas)**2).sum () / (nsamp - nap)
        print 'reduced chi squared: %.3f for %d DOF' % (rchisq, nsamp - nap)

        if cov is None:
            cov = suncerts = N.empty (0)
        else:
            cov *= rchisq # copying scipy.optimize.curve_fit
            suncerts = N.empty (nsamp)

            for i in xrange (nsamp):
                idx1, idx2 = sqbps[i]
                suncerts[i] = N.sqrt ((soln[idx1]**2 * cov[idx2,idx2] +
                                       soln[idx2]**2 * cov[idx1,idx1]))

        self.solution = soln
        self.covar = cov
        self.svals = modelvals
        self.suncerts = suncerts


def loadNoiseCalExport (path):
    byinstr = {}

    for line in open (path):
        a = line.split ('#', 1)[0].strip ().split ()
        if len (a) == 0:
            continue

        instr = a[0]
        ap = util.parseAP (a[1])
        value = float (a[2])

        byap = byinstr.setdefault (instr, {})
        byap[ap] = value

    for instr, byap in byinstr.items ():
        default = N.median (byap.values ())
        byinstr[instr] = (byap, default)

    return byinstr


# AWFF/ARF interface

try:
    import arf
except:
    pass
else:
    from mirtask.util import mir2bp, apAnt
    from awff import MultiprocessMake
    from awff.pathref import FileRef
    from arf.vispipe import VisPipeStage

    def _calnoise (context, vis=None, params=None):
        context.ensureParent ()
        out = FileRef (context.fullpath ())

        nc = NoiseCal ()
        nc.compute (ensureiterable (vis), **params)
        nc.save (str (out))
        return out

    CalNoise = MultiprocessMake ('vis params', 'out', _calnoise, [None, {}])

    class InsertNoiseInfo (VisPipeStage):
        def __init__ (self, pathobj):
            self.pathobj = pathobj
            self.byinstr = loadNoiseCalExport (str (pathobj))


        def __str__ (self):
            return '%s(%s)' % (self.__class__.__name__, self.pathobj)


        def updateHash (self, updater):
            updater (self.__class__.__name__)
            from awff.stdhash import updatefile
            updatefile (updater, str (self.pathobj))


        def init (self, state):
            if not hasattr (state, 'nbp'):
                raise ValueError ('this stage only works in arf.ata.vispipe')

            self.track = None
            self.systemps = None
            self.prefactor = None
            self.raras = {}
            self.bps = None
            self.bpfactors = None


        def record (self, state):
            inp = state.inp
            track = self.track
            systemps = self.systemps
            prefactor = self.prefactor
            bps = self.bps
            bpfactors = self.bpfactors

            if track is None:
               track = inp.makeVarTracker ().track ('systemp', 'sdf', 'inttime')
               self.track = track

            if track.updated ():
                nants = inp.getVarInt ('nants')
                systemps = self.systemps = inp.getVarFloat ('systemp', nants)
                nspect = inp.getVarInt ('nspect')
                sdf = inp.getVarDouble ('sdf', nspect)
                if nspect > 1:
                    sdf = sdf[0]
                inttime = inp.getVarFloat ('inttime')
                prefactor = self.prefactor = 2 * inttime * sdf * 1e9

            if bpfactors is None or bpfactors.size != state.nbp:
                bpfactors = self.bpfactors = N.empty (state.nbp)
                bps = self.bps = N.empty ((state.nbp, 2), dtype=N.int)

            ap1, ap2 = mir2bp (inp, state.preamble)

            if ap1 == ap2:
                # Autocorrelation! Get the RARA (raw autocorrelation
                # RMS amplitude)
                w = N.where (state.flags)[0]
                if w.size == 0:
                    self.raras.pop (ap1, 0)
                else:
                    self.raras[ap1] = N.sqrt ((state.data.real[w]**2).mean ())

            # Get the factor that will go in front of the RARAs for
            # jyperk computations. Do this for autocorrs too because
            # there's no reason not to.

            if state.instr not in self.byinstr:
                raise Exception ('need information for instrument ' +
                                 state.instr)

            byap, default = self.byinstr[state.instr]
            cal1 = byap.get (ap1, default)
            cal2 = byap.get (ap2, default)
            ant1, ant2 = apAnt (ap1), apAnt (ap2)
            tsys1, tsys2 = systemps[ant1 - 1], systemps[ant2 - 1]

            bpindex = state.bpindex
            bps[bpindex,0] = ap1
            bps[bpindex,1] = ap2
            bpfactors[bpindex] = prefactor * cal1 * cal2 / (tsys1 * tsys2)


        def dumpdone (self, state):
            seen = state.dump_seen
            jyperks = state.dump_jyperks
            bps = self.bps
            bpfactors = self.bpfactors
            raras = self.raras

            jyperks.fill (0)

            defaultrara = N.median (raras.values ())
            get = lambda ap: raras.get (ap, defaultrara)

            for i in xrange (state.nbp):
                if seen[i]:
                    ap1, ap2 = bps[i]
                    jyperks[i] = bpfactors[i] * get (ap1) * get (ap2)

            N.sqrt (jyperks, jyperks)
            raras.clear ()

    __all__ += ['CalNoise', 'InsertNoiseInfo']


# Command-line interface

def tui_compute (args):
    toread = []
    uvdatoptions = {}

    for arg in args:
        if '=' in arg:
            key, value = arg.split ('=', 1)
            uvdatoptions[key] = value
        else:
            toread.append (arg)

    if len (toread) < 2:
        util.die ('usage: <vis1> [... visn] [uvdat options] <output name>')

    outpath = toread[-1]
    toread = [VisData (x) for x in toread[:-1]]

    try:
        tmp = open (outpath, 'w')
        tmp.close ()
    except Exception, e:
        util.die ('cannot open output path "%s" for writing: %s',
                  outpath, e)

    nc = NoiseCal ()
    nc.compute (toread, **uvdatoptions)
    nc.save (outpath)
    return 0


def tui_checkfit (args):
    import omega as O

    if len (args) != 1:
        util.die ('usage: <datfile>')

    nc = NoiseCal ()
    nc.load (args[0])

    vals = nc.bpdata[:,1]
    modelvals = nc.bpdata[:,3] * nc.svals
    resids = vals - modelvals
    runcerts = N.sqrt (1./nc.bpdata[:,2] + (nc.suncerts * nc.bpdata[:,3])**2)
    normresids = resids / runcerts

    n = normresids.size
    mn = normresids.mean ()
    s = normresids.std ()
    md = N.median (normresids)
    smadm = 1.4826 * N.median (N.abs (normresids - md)) # see comment below

    print '                 Number of samples:', n
    print '           Normalized mean residal:', mn
    print '                            Median:', md
    print 'Normalized std. dev. (should be 1):', s
    print '                             SMADM:', smadm

    # Check for problematic antpols and basepols

    saps = nc.saps
    sqbps = nc.sqbps
    nap = len (saps)
    dumbnbp = nap**2
    apcounts = N.zeros (nap, dtype=N.int)
    apsumsqresids = N.zeros (nap)
    bpcounts = N.zeros (dumbnbp, dtype=N.int)
    bpsumsqresids = N.zeros (dumbnbp)

    for i in xrange (n):
        idx1, idx2 = sqbps[i]

        apcounts[idx1] += 1
        apsumsqresids[idx1] += normresids[i]**2
        apcounts[idx2] += 1
        apsumsqresids[idx2] += normresids[i]**2

        bpidx = idx1 * nap + idx2
        bpcounts[bpidx] += 1
        bpsumsqresids[bpidx] += normresids[i]**2

    aprmsresids = N.sqrt (apsumsqresids / apcounts)
    sapresids = N.argsort (aprmsresids)

    print
    print 'Extreme residual RMS by antpol:'
    for i in xrange (5):
        idx = sapresids[i]
        print ' %10s %8.2f' % (util.fmtAP (saps[idx]), aprmsresids[idx])
    print '       ....'
    for i in xrange (5):
        idx = sapresids[i - 5]
        print ' %10s %8.2f' % (util.fmtAP (saps[idx]), aprmsresids[idx])

    wbpgood = N.where (bpcounts)[0]
    wbpbad = N.where (bpcounts == 0)[0]
    bpcounts[wbpbad] = 1
    bprmsresids = bpsumsqresids / bpcounts
    sbpresids = N.argsort (bprmsresids[wbpgood])

    print
    print 'Extreme residual RMS by basepol:'
    for i in xrange (3):
        idx = wbpgood[sbpresids[i]]
        ap2 = saps[idx % nap]
        ap1 = saps[idx // nap]
        print ' %10s %8.2f' % (util.fmtBP ((ap1, ap2)), bprmsresids[idx])
    print '       ....'
    for i in xrange (7):
        idx = wbpgood[sbpresids[i - 7]]
        ap2 = saps[idx % nap]
        ap1 = saps[idx // nap]
        print ' %10s %8.2f' % (util.fmtBP ((ap1, ap2)), bprmsresids[idx])

    # Plot the distribution of residuals

    bins = 50
    rng = -5, 5
    p = O.quickHist (normresids, keyText='Residuals', bins=bins, range=rng)
    x = N.linspace (-5, 5, 200)
    area = 10. / bins * n
    y = area / N.sqrt (2 * N.pi) * N.exp (-0.5 * x**2)
    p.addXY (x, y, 'Ideal')
    p.rebound (False, False)
    p.show ()

    return 0


def tui_checkap (args):
    import omega as O

    if len (args) != 2:
        util.die ('usage: <datfile> <antpol>')

    nc = NoiseCal ()
    nc.load (args[0])

    ap = util.parseAP (args[1])
    apidx = nc.saps.index (ap)
    if apidx < 0:
        util.die ('no antpol %s in data file!', util.fmtAP (ap))

    sqbps = nc.sqbps
    vals = nc.bpdata[:,1]
    modelvals = nc.bpdata[:,3] * nc.svals
    resids = vals - modelvals

    runcerts = N.sqrt (1./nc.bpdata[:,2] + (nc.suncerts * nc.bpdata[:,3])**2)
    resids /= runcerts

    w = N.where ((sqbps[:,0] == apidx) | (sqbps[:,1] == apidx))
    resids = resids[w]

    n = resids.size
    mn = resids.mean ()
    s = resids.std ()
    md = N.median (resids)
    smadm = 1.4826 * N.median (N.abs (resids - md)) # see comment below

    print '       Number of samples:', n
    print '      Norm. mean residal:', mn
    print '                  Median:', md
    print 'Norm. residual std. dev.:', s
    print '                   SMADM:', smadm


    bins = 50
    rng = -5, 5
    p = O.quickHist (resids, keyText='%s Residuals' % util.fmtAP (ap),
                     bins=bins, range=rng)
    x = N.linspace (-5, 5, 200)
    area = 10. / bins * n
    y = area / N.sqrt (2 * N.pi) * N.exp (-0.5 * x**2)
    p.addXY (x, y, 'Ideal')
    p.rebound (False, False)
    p.show ()

    return 0


def tui_checkabs (args):
    import omega as O

    if len (args) != 1:
        util.die ('usage: <datfile>')

    nc = NoiseCal ()
    nc.load (args[0])

    saps = nc.saps
    sqbps = nc.sqbps
    vals = nc.bpdata[:,1]
    uncerts = nc.bpdata[:,2]**-0.5
    modelvals = nc.bpdata[:,3] * nc.svals
    muncerts = nc.suncerts * nc.bpdata[:,3]

    pg = O.quickPager ([])

    for idx in xrange (len (saps)):
        w = N.where ((sqbps[:,0] == idx) | (sqbps[:,1] == idx))

        p = O.quickXYErr (vals[w], modelvals[w], muncerts[w], 
                          util.fmtAP (saps[idx]), lines=False)
        p.setLabels ('Measured variance (Jy²)', 'Modeled variance (Jy²)')
        pg.send (p)

    pg.done ()
    return 0


def tui_checkcal (args):
    import omega as O, scipy.stats as SS
    toread = []
    uvdatoptions = {}

    for arg in args:
        if '=' in arg:
            key, value = arg.split ('=', 1)
            uvdatoptions[key] = value
        else:
            toread.append (VisData (arg))

    if len (toread) < 1:
        util.die ('usage: <vis1> [... visn] [uvdat options]')

    samples = numutils.VectorGrower ()
    gen = uvdat.setupAndRead (toread, 'x3', False, **uvdatoptions)

    for inp, pream, data, flags in gen:
        w = N.where (flags)[0]
        if w.size == 0:
            continue

        data = data[w]
        var = 0.5 * (data.real.var (ddof=1) + data.imag.var (ddof=1))
        uvar = N.sqrt (1. / (w.size - 1)) * var # uncert in variance msmt
        thy = inp.getVariance ()
        samples.add ((var - thy) / uvar)

    samples = samples.finish ()
    n = samples.size
    m = samples.mean ()
    s = samples.std ()
    med = N.median (samples)
    smadm = 1.4826 * N.median (N.abs (samples - med)) # see comment below

    print '                  Number of samples:', n
    print 'Mean normalized error (should be 0):', m
    print '                             Median:', med
    print ' Normalized std. dev. (should be 1):', s
    print '                              SMADM:', smadm
    print 'Probability that samples are normal:', SS.normaltest (samples)[1]

    bins = 50
    rng = -5, 5
    p = O.quickHist (samples, keyText='Samples', bins=bins, range=rng)
    x = N.linspace (-5, 5, 200)
    area = 10. / bins * n
    y = area / N.sqrt (2 * N.pi) * N.exp (-0.5 * x**2)
    p.addXY (x, y, 'Ideal')
    p.rebound (False, False)
    p.show ()
    return 0

# A footnote on the SMADM: this is the Scaled Median Absolute
# Difference from the Median. Unsurprisingly this is supposed to be an
# outlier-resistant version of the standard deviation.
#
# But what is the exact relationship between this and an actual
# standard deviation? Consider a true normal distribution. Its median
# is its mean, so if we subtract the median, we center on zero. Taking
# the absolute value then mirrors the negative axis to the positive
# axis. The median of *this* distribution is the median of the top half
# of the normal distribution, that is, the 75th percentile of the normal
# distribution. We should divide the (unscaled) MADM by that number to
# get a psuedo standard deviation. It works out to sqrt(2) erfinv (1/2),
# the inverse of which is the value used above.


def tui_export (args):
    if len (args) < 1:
        util.die ('usage: <dat1> [... datn]')

    nc = NoiseCal ()
    for path in args:
        nc.load (path, partial=True)
        nc.export (sys.stdout)
    return 0


def tui_sefds (args):
    if len (args) != 1:
        util.die ('usage: <datfile>')

    nc = NoiseCal ()
    nc.load (args[0])
    nc.printsefdinfo ()
    return 0


if __name__ == '__main__':
    if len (sys.argv) == 1:
        util.die ('add a subcommand: one of "checkabs checkap checkcal checkfit '
                  'compute export sefds"')

    subcommand = sys.argv[1]
    if 'tui_' + subcommand not in globals ():
        util.die ('unknown subcommand "%s"', subcommand)

    sys.exit (globals ()['tui_' + subcommand] (sys.argv[2:]))
