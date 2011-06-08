#! /usr/bin/env python

"""= gptext - convert antenna gains to and from text format
& pkgw
: uv Analysis
+
 GPTEXT exports and imports MIRIAD gain calibration data from
 its binary storage in datasets to a textual file format.

@ vis
 A filename.

@ out
 A filename.

@ mode
 One of "totext", "applyvis", or "createvis".
--
"""

import numpy as N
from mirtask import util


__all__ = ('SVNID DEFAULT_BANNER BadInfoError GainsInfo task').split ()

__version_info__ = (1, 0)
SVNID = '$Id$'
DEFAULT_BANNER = 'PYTHON gptext - foo'


class BadInfoError (Exception):
    def __init__ (self, fmt, *rest):
        self.msg = fmt % rest
    def __str__ (self):
        return self.msg


class GainsInfo (object):
    interval = None
    nfeeds = 0
    nants = 0
    havetau = False
    times = None
    data = None


    def fromDataset (self, handle):
        from mirtask.readgains import GainsReader

        self.interval = handle.getHeaderDouble ('interval', 0.5)
        if self.interval <= 0.:
            raise BadInfoError ('interval should be positive; got %s',
                                self.interval)

        gr = GainsReader (handle)
        gr.prep ()
        self.nfeeds = gr.nfeeds
        self.nants = gr.nants
        self.havetau = (gr.ntau > 0)

        self.times, self.data = gr.readAll ()
        return self


    def toDataset (self, handle):
        """Caller's responsibility to modify the history."""

        ngains = self.nants * (self.nfeeds + int (self.havetau))

        handle.writeHeaderInt ('nsols', len (self.times))
        handle.writeHeaderInt ('nfeeds', self.nfeeds)
        handle.writeHeaderInt ('ntau', int (self.havetau))
        handle.writeHeaderInt ('ngains', ngains)
        handle.writeHeaderDouble ('interval', self.interval)

        gi = handle.getItem ('gains', 'w')
        offset = 8

        for i, time in enumerate (self.times):
            gi.writeDoubles (time, offset, 1)
            offset += 8
            gi.writeComplex (self.data[i], offset, ngains)
            offset += 8 * ngains

        gi.close ()
        return self


    def toDatasetPath (self, path, mode):
        """Valid values of *mode* are "rw" or "c"."""
        from miriad import CalData

        ds = CalData (path)
        handle = ds.open (mode)
        try:
            self.toDataset (handle)
        finally:
            handle.close ()
        return self


    def fromText (self, stream):
        interval = nfeeds = nants = havetau = None
        times = []
        data = []
        curdata = None

        for line in stream:
            a = line.split ('#', 1)[0].strip ().split ()
            if not len (a):
                continue

            if curdata is None:
                if a[0] == 'interval':
                    interval = float (a[1])
                elif a[0] == 'nfeeds':
                    nfeeds = int (a[1])
                elif a[0] == 'nants':
                    nants = int (a[1])
                elif a[0] == 'havetau':
                    havetau = bool (int (a[1]))
                elif a[0] == 'solution':
                    if interval is None:
                        raise BadInfoError ('no gain interval')
                    if interval <= 0:
                        raise BadInfoError ('interval must be positive; got %s',
                                            interval)
                    if nfeeds is None:
                        raise BadInfoError ('no nfeeds')
                    if nfeeds < 1 or nfeeds > 2:
                        raise BadInfoError ('nfeeds must be 1 or 2; got %d', nfeeds)
                    if nants is None:
                        raise BadInfoError ('no nants')
                    if nants < 1:
                        raise BadInfoError ('nants must be positive; got %d', nants)
                    if havetau is None:
                        raise BadInfoError ('no havetau')

                    q = nfeeds + int (havetau)
                    times.append (util.dateOrTimeToJD (a[1]))
                    curdata = N.zeros (q * nants, dtype=N.complex64)
                    data.append (curdata)
            else:
                if a[0] == 'solution':
                    times.append (util.dateOrTimeToJD (a[1]))
                    curdata = N.zeros (q * nants, dtype=N.complex64)
                    data.append (curdata)
                elif a[1].startswith ('g'):
                    ant = int (a[0]) - 1
                    gnum = int (a[1][1:]) - 1
                    if ant < 0 or ant >= nants:
                        raise BadInfoError ('got entry for illegal antnum %d', ant)
                    if gnum < 0 or gnum >= nfeeds:
                        raise BadInfoError ('got gain entry for illegal feednum %d',
                                            gnum + 1)
                    curdata[ant * q + gnum] = complex (float (a[2]), float (a[3]))
                elif a[1] == 'tau':
                    ant = int (a[0]) - 1
                    if ant < 0 or ant >= nants:
                        raise BadInfoError ('got entry for illegal antnum %d', ant)
                    if not havetau:
                        raise BadInfoError ('got tau entry with havetau = 0')
                    curdata[ant * q + nfeeds] = complex (float (a[2]), float (a[3]))

        self.interval = interval
        self.nfeeds = nfeeds
        self.nants = nants
        self.havetau = havetau
        self.times = N.asarray (times)
        self.data = N.asarray (data)
        return self


    def toText (self, stream):
        print >>stream, 'interval %.18e' % self.interval
        print >>stream, 'nfeeds', self.nfeeds
        print >>stream, 'nants', self.nants
        print >>stream, 'havetau', int (self.havetau)

        q = self.nfeeds + int (self.havetau)

        for i, time in enumerate (self.times):
            print >>stream, 'solution', util.jdToFull (time)
            d = self.data[i]

            for ant in xrange (self.nants):
                ofs = ant * q

                for k in xrange (self.nfeeds):
                    g = d[ofs + k]

                    if abs (g) > 0:
                        print >>stream, '%2d g%d %+.18e %+.18e' % \
                            (ant + 1, k + 1, g.real, g.imag)

                if self.havetau:
                    print >>stream, '%2d tau %+.18e %+.18e' % \
                        (ant + 1, d[ofs+self.nfeeds].real, d[ofs+self.nfeeds].imag)

        return self


# AWFF make implementation

try:
    from awff import MultiprocessMake
except ImportError:
    pass
else:
    __all__ += ('applyText genFromText').split ()

    def _applytext (context, vis=None, gaintext=None):
        from miriad import VisData
        context.ensureParent ()
        out = VisData (context.fullpath ())
        out.delete ()
        vis.lwcpTo (out)

        try:
            gi = GainsInfo ().fromText (open (str (gaintext)))
            gi.toDatasetPath (str (out), 'rw')
        except Exception:
            out.delete ()
            raise

        return out

    applyText = MultiprocessMake ('vis gaintext', 'out', _applytext,
                                  [None, None])

    def _genfromtext (context, gaintext=None):
        from miriad import CalData
        context.ensureParent ()
        out = CalData (context.fullpath ())
        out.delete ()

        try:
            gi = GainsInfo ().fromText (open (str (gaintext)))
            gi.toDatasetPath (str (out), 'c')
        except Exception:
            out.delete ()
            raise

        return out

    genFromText = MultiprocessMake ('gaintext', 'out', _genfromtext,
                                    [None])


# Task functionality

def task (args):
    from miriad import CalData
    from mirtask import cliutil, keys

    banner = util.printBannerSvn ('gptext', 'convert gains to and from text',
                                  SVNID)

    ks = keys.KeySpec ()
    ks.keyword ('vis', 'f', ' ')
    ks.keyword ('out', 'f', ' ')
    ks.keymatch ('mode', 1, ['totext', 'applyvis', 'createvis'])
    opts = ks.process (args)

    if opts.out == ' ':
        util.die ('must specify an output filename (out=...)')

    if opts.vis == ' ':
        util.die ('must specify an input filename (vis=...)')

    mode = opts.mode[0]
    gi = GainsInfo ()
    
    if mode == 'totext':
        gi.fromDataset (CalData (opts.vis).open ('rw'))

        if opts.out == '-':
            gi.toText (sys.stdout)
        else:
            gi.toText (open (opts.out, 'w'))
    elif mode == 'applyvis':
        gi.fromText (open (opts.vis))
        h = CalData (opts.out).open ('rw')
        gi.toDataset (h)
        h.openHistory ()
        h.writeHistory (banner)
        h.logInvocation ('PYTHON gptext', ['gptext'] + args)
        h.closeHistory ()
        h.close ()
    elif mode == 'createvis':
        gi.fromText (open (opts.vis))
        h = CalData (opts.out).open ('c')
        gi.toDataset (h)
        h.openHistory ()
        h.writeHistory (banner)
        h.logInvocation ('PYTHON gptext', ['gptext'] + args)
        h.closeHistory ()
        h.close ()
    else:
        util.die ('unrecognized mode "%s"', mode)


if __name__ == '__main__':
    import sys
    task (sys.argv[1:])
