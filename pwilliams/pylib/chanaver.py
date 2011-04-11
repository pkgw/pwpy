#! /usr/bin/env python

"""= chanaver - Average spectral channels after applying bandpass
& pkgw
: uv Analysis
+
 CHANAVER averages spectral channels. It is less powerful than
 UVCAT/UVAVER, but it averages after applying gain and bandpass
 corrections to the input dataset. If you want to average a dataset in
 channel space after solving for the bandpass, CHANAVER saves you the
 UVCAT of the dataset normally needed to apply the bandpass before
 averaging. (If you don't do this UVCAT, the bandpass is applied after
 the channel averaging, resulting in the message "Performing linetype
 averaging before applying bandpass!!  ... this may be very unwise".)

 In some circumstances CHANAVER can also provide a more precise
 bandpass application than what is obtained via UVCAT. If the
 correlation data are stored in scaled 16-bit integer format and
 there's a birdie (a very large amplitude spike in one channel) in a
 given spectrum, there will have been a loss of precision in the input
 dataset due to the dynamic range compression needed to encode the
 birdie. When UVCAT applies the bandpass, it will maintain the birdie
 (flagged though it may be), so there will be a secondary loss of
 precision as the bulk of the data are written with a compressed
 dynamic range. CHANAVER, on the other hand, will apply the flagging
 when averaging, eliminating the birdie (assuming it has been flagged)
 and thus avoiding the second round of dynamic-range compression. This
 can be a nontrivial effect in some datasets.

 A related distinction is that averaging with the line= keyword is
 performed in the 16-bit scaled-integer space, whereas CHANAVER does
 its averaging after multiplication by the scaling factor. This should
 result in CHANAVER being subject to slightly more roundoff errors
 compared to line= averaging, but the differences should be trivial
 compared to the loss-of-precision inherent in the use of the scaled-
 integer format to begin with.

 A minor difference between CHANAVER and UVAVER is that CHANAVER does
 not share the default UVAVER behavior of discarding
 completely-flagged records.

 LIMITATIONS: CHANAVER only works with datasets containing a single
 spectral window.

@ vis
 The input dataset or datasets.

@ out
 The name of the averaged output dataset to create.

@ naver
 The number of channels to average together. This number must divide
 evenly into the number of spectral channels. A value of one is
 acceptable, meaning that calibrations will be applied and flagged
 data will be zeroed out in the output dataset.

@ slop
 The fraction of channels in each averaging bin that must be present
 in order for the averaged bin to be considered valid. Default is
 0.5, i.e., half of the channels must be unflagged. If slop is zero,
 one channel must still be good in each bin in order for the data
 to remain unflagged.

@ select
 The standard MIRIAD UV-data selection keyword. For more information,
 see "mirhelp select".

@ line
 The standard MIRIAD line processing keyword. For more information,
 see "mirhelp line".

@ stokes
 The standard MIRIAD Stokes processing keyword. For more information,
 see "mirhelp stokes".

@ ref
 The standard MIRIAD reference-line processing keyword. For more
 information, see "mirhelp ref".

@ options.
 Multiple options can be specified, separated by commas. Minimum-match
 is used.

 'nocal'  Do not apply gain/phase calibration tables.
 'nopass' Do not apply the bandpass correction. Included for
          completeness, but if you are specifying this, you should use
          UVAVER instead.
 'nopol'  Do not apply polarization leakage correction.

--
"""

import numpy as N
from miriad import VisData
from mirtask import keys, util, uvdat


__all__ = ('SVNID DEFAULT_SLOP DEFAULT_BANNER InputStructureError '
           'channelAverage task').split ()

__version_info__ = (1, 0)
SVNID = '$Id$'
DEFAULT_SLOP = 0.5
DEFAULT_BANNER = 'PYTHON chanaver - channel average after applying bandpass'
UVDAT_OPTIONS = 'dslr3'


class InputStructureError (Exception):
    def __init__ (self, vis, why):
        self.vis = vis
        self.why = why
    def __str__ (self):
        return 'Cannot handle input dataset %s: %s' % (self.vis, self.why)


def channelAverage (out, naver, slop=DEFAULT_SLOP, banner=DEFAULT_BANNER):
    if naver < 1:
        raise ValueError ('must average at least one channel (got naver=%d)' % naver)
    if slop < 0 or slop > 1:
        raise ValueError ('slop must be between 0 and 1 (got slop=%f)' % slop)

    try:
        _channelAverage (uvdat.read (), out, naver, slop, banner)
    except:
        out.delete ()
        raise


def channelAverageWithSetup (toread, out, naver, slop=DEFAULT_SLOP, 
                             banner=DEFAULT_BANNER, **uvdargs):
    if naver < 1:
        raise ValueError ('must average at least one channel (got naver=%d)' % naver)
    if slop < 0 or slop > 1:
        raise ValueError ('slop must be between 0 and 1 (got slop=%f)' % slop)

    try:
        gen = uvdat.setupAndRead (toread, UVDAT_OPTIONS, False, **uvdargs)
        _channelAverage (gen, out, naver, slop, banner)
    except:
        out.delete ()
        raise


def _channelAverage (gen, out, naver, slop, banner):
    from numpy import sum, greater_equal, maximum

    nmin = max (int (round (slop * naver)), 1)

    first = True
    prevhnd = None
    prevnpol = 0
    npolvaried = False

    outhnd = out.open ('c')
    outhnd.setPreambleType ('uvw', 'time', 'baseline')

    for vishnd, preamble, data, flags in gen:
        if first:
            first = False

            corrtype, _, _ = vishnd.probeVar ('corr')
            if corrtype != 'r' and corrtype != 'j' and corrtype != 'c':
                raise InputStructureError (vis, 'type of "corr" variable (%c) not '
                                           'expected (one of rjc)' % corrtype)
            outhnd.setCorrelationType (corrtype)

            vishnd.copyHeader (outhnd, 'history')
            outhnd.openHistory ()
            outhnd.writeHistory (banner)
            outhnd.logInvocation ('PYTHON chanaver')
            outhnd.writeHistory ('PYTHON chanaver: naver=%d slop=%f' % (naver, slop))
            outhnd.closeHistory ()

        if vishnd is not prevhnd:
            prevhnd = vishnd

            npol = 0

            tracker = vishnd.makeVarTracker ()
            tracker.track ('nchan', 'nspect', 'nwide', 'sdf', 'nschan',
                           'ischan', 'sfreq')

            # We don't care about these, but they would normally be copied
            # by the VarCopy(line=channel) logic.
            for var in 'restfreq systemp xtsys ytsys xyphase'.split ():
                vishnd.trackVar (var, False, True)

            vishnd.initVarsAsInput (' ')
            outhnd.initVarsAsOutput (vishnd, ' ')

        if tracker.updated ():
            # Potentially new spectral configuration.

            nspect = vishnd.getVarFirstInt ('nspect', 0)
            nwide = vishnd.getVarFirstInt ('nwide', 0)
            nchan = vishnd.getVarFirstInt ('nchan', 0)

            if nspect != 1:
                raise InputStructureError (vis, 'require exactly one spectral window')
            if nwide != 0:
                raise InputStructureError (vis, 'require no wideband windows')

            sdf = vishnd.getVarDouble ('sdf', nspect)
            nschan = vishnd.getVarInt ('nschan', nspect)
            ischan = vishnd.getVarInt ('ischan', nspect)
            sfreq = vishnd.getVarDouble ('sfreq', nspect)

            if nschan != nchan:
                raise InputStructureError (vis, 'require nchan (%d) = nschan (%d)' %
                                           (nchan, nschan))
            if ischan != 1:
                raise InputStructureError (vis, 'require ischan (%d) = 1' % ischan)

            if nchan % naver != 0:
                raise InputStructureError (vis, 'require nchan (%d) to be a multiple '
                                           'of naver (%d)' % (nchan, naver))

            # OK, everything is hunky-dory. Compute new setup.

            nout = nchan // naver
            sdfout = sdf * naver
            sfreqout = sfreq + 0.5 * sdf * (naver - 1)

            outdata = N.empty (nout, dtype=N.complex64)
            outflags = N.empty (nout, dtype=N.int32)
            counts = N.empty (nout, dtype=N.int32)

            outhnd.writeVarInt ('nspect', 1)
            outhnd.writeVarInt ('nschan', nout)
            outhnd.writeVarInt ('ischan', 1)
            outhnd.writeVarDouble ('sdf', sdfout)
            outhnd.writeVarDouble ('sfreq', sfreqout)

        # Do the averaging. This is as fast as I know how to make it
        # within numpy. Have no idea if there's a way to take advantage
        # of multicore processors that is robustly faster and not a
        # ton of effort.

        data *= flags # zero out flagged data
        sum (data.reshape ((nout, naver)), axis=1, out=outdata)
        sum (flags.reshape ((nout, naver)), axis=1, out=counts)
        greater_equal (counts, nmin, outflags)
        maximum (counts, 1, counts) # avoid div-by-zero
        outdata /= counts

        # Write, with the usual npol tomfoolery.

        vishnd.copyLineVars (outhnd)
        vishnd.copyMarkedVars (outhnd)

        if npol == 0:
            npol = uvdat.getNPol ()
            if npol != prevnpol:
                outhnd.writeVarInt ('npol', npol)
                npolvaried = npolvaried or prevnpol != 0
                prevnpol = npol

        outhnd.writeVarInt ('pol', uvdat.getPol ())
        outhnd.write (preamble, outdata, outflags)
        npol -= 1

    # All done. 

    if not npolvaried:
        outhnd.writeHeaderInt ('npol', prevnpol)

    outhnd.close ()


try:
    from awff import SimpleMake
except ImportError:
    pass
else:
    __all__ += ['asMake']

    # FIXME: make the propagation a library routine

    def _asmake (context, vis=None, params=None):
        params = dict (params) # copy so we don't modify:
        naver = params.pop ('naver', 0)

        context.ensureDir ()
        out = VisData (context.fullpath ('out'))
        out.delete ()

        channelAverageWithSetup (vis, out, naver, **params)

        ihandle = vis.open ('rw')
        ohandle = out.open ('rw')

        if ihandle.hasItem ('arfinstr'):
            instr = ihandle.getHeaderString ('arfinstr', 'uhoh')
            ohandle.writeHeaderString ('arfinstr', instr)

        if ihandle.hasItem ('arfvbds'):
            a = ihandle.getArrayHeader ('arfvbds')
            ohandle.writeArrayHeaderDouble ('arfvbds', a)

        if ihandle.hasItem ('source'):
            source = ihandle.getHeaderString ('source', 'uhoh')
            ohandle.writeHeaderString ('source', source)

        if ihandle.hasItem ('freq'):
            freq = ihandle.getHeaderDouble ('freq', 0.)
            ohandle.writeHeaderDouble ('freq', freq)

        ihandle.close ()
        ohandle.close ()

        return out

    asMake = SimpleMake ('vis params', 'out', _asmake)


def task (args):
    from mirtask import cliutil

    banner = util.printBannerSvn ('chanaver', 'average channels after applying bandpass', 
                                  SVNID)

    ks = keys.KeySpec ()
    ks.keyword ('out', 'f', ' ')
    ks.keyword ('naver', 'i', -1)
    ks.keyword ('slop', 'd', DEFAULT_SLOP)
    ks.uvdat (UVDAT_OPTIONS)
    opts = ks.process (args)

    if opts.out == ' ':
        util.die ('must specify an output filename (out=...)')
    out = VisData (opts.out)

    if opts.naver == -1:
        util.die ('must specify the number of channels to average (naver=...)')

    try:
        channelAverage (out, opts.naver, opts.slop, banner)
    except (InputStructureError, ValueError), e:
        util.die (str (e))


if __name__ == '__main__':
    import sys
    task (sys.argv[1:])
