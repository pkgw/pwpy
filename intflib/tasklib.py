# Copyright 2012 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""tasklib - library of clones of CASA tasks

The way that the casapy code is written it's basically impossible to
import its tasks into a straight-Python environment (trust me, I've
tried), so we're more-or-less duplicating lots of CASA code. I try
to provide saner semantics, APIs, etc.

The goal is to make task-like functionality as a real Python library
with no side effects, so that we can actually script data
processing. While we're at it, we make them available on the command
line.
"""

import casautil as cu
from kwargv import ParseKeywords, Custom

__all__ = ('split split_cli SplitConfig '
           'concat concat_cli '
           'cmdline_driver').split ()


## quickutil: usage die
#- snippet: usage.py (2012 Oct 01)
#- SHA1: ac032a5db2efb5508569c4d5ba6eeb3bba19a7ca
def showusage (docstring, short, stream, exitcode):
    if stream is None:
        from sys import stdout as stream
    if not short:
        print >>stream, 'Usage:', docstring.strip ()
    else:
        intext = False
        for l in docstring.splitlines ():
            if intext:
                if not len (l):
                    break
                print >>stream, l
            elif len (l):
                intext = True
                print >>stream, 'Usage:', l
        print >>stream, \
            '\nRun with a sole argument --help for more detailed usage information.'
    raise SystemExit (exitcode)

def checkusage (docstring, argv=None, usageifnoargs=False):
    if argv is None:
        from sys import argv
    if len (argv) == 1 and usageifnoargs:
        showusage (docstring, True, None, 0)
    if len (argv) == 2 and argv[1] in ('-h', '--help'):
        showusage (docstring, False, None, 0)

def wrongusage (docstring, *rest):
    import sys
    intext = False

    if len (rest) == 0:
        detail = 'invalid command-line arguments'
    elif len (rest) == 1:
        detail = rest[0]
    else:
        detail = rest[0] % tuple (rest[1:])

    print >>sys.stderr, 'error:', detail, '\n' # extra NL
    showusage (docstring, True, sys.stderr, 1)
#- snippet: die.py (2012 Oct 01)
#- SHA1: 3bdd3282e52403d2dec99d72680cb7bc95c99843
def die (fmt, *args):
    if not len (args):
        raise SystemExit ('error: ' + str (fmt))
    raise SystemExit ('error: ' + (fmt % args))
## end

# "split" functionality
#
# note: spw=999 -> except; scan=999 -> no output (or error) generated

split_doc = \
"""
casatask split vis=<MS> out=<MS> [keywords...]

timebin=
  Time-average data into bins of "timebin" seconds; defaults to no averaging

step=
  Frequency-average data in bins of "step" channels; defaults to no averaging

col=all
  Extract the column "col" as the DATA column. If "all", copy all available
  columns without renaming. Possible values:
  DATA MODEL_DATA CORRECTED_DATA FLOAT_DATA LAG_DATA

combine=[col1,col2,...]
  When time-averaging, don't start a new bin when the specified columns change.
  Acceptable column names:
  scan state

Also accepts standard u-v filtering keywords:
  baseline correlation field intent obs spw subarray taql time uvrange

And standard logging keyword "loglevel" (default: warn; allowed:
  severe warn info info1 info2 info3 info5 info5 debug1 debug2 debugging)
"""

class SplitConfig (ParseKeywords):
    vis = Custom (str, required=True)
    out = Custom (str, required=True)

    timebin = float # seconds
    step = 1
    col = 'all'
    combine = [str]

    # basic selection keywords:
    baseline = str
    correlation = str
    field = str
    intent = str
    obs = str
    scan = str
    spw = str
    subarray = str
    taql = str
    time = str
    uvrange = str

    # teeny hack for CLI
    loglevel = 'warn'

def split (cfg):
    import os.path
    kws = {}

    # ms.split() seems to merrily overwrite existing MSes which
    # seems pretty questionable. Forbid that for now as best we can.
    # Race conditions ahoy.
    if os.path.exists (cfg.out):
        raise RuntimeError ('destination "%s" already exists' % cfg.out)

    for k in ('baseline correlation field intent obs scan spw step subarray '
              'taql time uvrange').split ():
        v = getattr (cfg, k)
        if v is None:
            v = ''
        kws[k] = v

    for m in ('out:outputms col:whichcol').split ():
        myk, ck = m.split (':')
        kws[ck] = getattr (cfg, myk)

    if cfg.timebin is None:
        kws['timebin'] = '-1s'
    else:
        kws['timebin'] = str (cfg.timebin) + 's'

    kws['combine'] = ','.join (cfg.combine)

    ms = cu.tools.ms ()
    ms.open (cfg.vis)
    ms.split (**kws)
    ms.close ()


def split_cli (argv):
    checkusage (split_doc, argv, usageifnoargs=True)
    cfg = SplitConfig ().parse (argv[1:])
    cu.logger (cfg.loglevel.upper ()) # log warnings, errors to stderr
    split (cfg)


# concat

concat_doc = \
"""
casatask concat [-s] <input vises ...> <output vis>

Concatenate the visibility measurement sets.

-s - sort the output in time
"""

concat_freqtol = 1e-5
concat_dirtol = 1e-5

def concat (invises, outvis, timesort=False):
    import os.path
    tb = cu.tools.table ()
    ms = cu.tools.ms ()

    if os.path.exists (outvis):
        raise RuntimeError ('output "%s" already exists' % outvis)

    for invis in invises:
        if not os.path.isdir (invis):
            raise RuntimeError ('input "%s" does not exist' % invis)

    tb.open (invises[0])
    tb.copy (outvis, deep=True, valuecopy=True)
    tb.close ()

    ms.open (outvis, nomodify=False)

    for invis in invises[1:]:
        ms.concatenate (msfile=invis, freqtol=concat_freqtol,
                        dirtol=concat_dirtol)

    ms.writehistory (message='taskname=tasklib.concat', origin='tasklib.concat')
    ms.writehistory (message='vis = ' + ', '.join (invises), origin='tasklib.concat')
    ms.writehistory (message='timesort = ' + 'FT'[int (timesort)], origin='tasklib.concat')

    if timesort:
        ms.timesort ()

    ms.close ()


def concat_cli (argv):
    checkusage (concat_doc, argv, usageifnoargs=True)

    argv = list (argv)
    timesort = '-s' in argv
    if timesort:
        sys.argv.remove ('-s')

    if len (argv) < 3:
        wrongusage (concat_doc, 'need at least two arguments')

    cu.logger ()
    concat (argv[1:-1], argv[-1], timesort)


# Driver for command-line access

def cmdline_usage (stream, exitcode):
    print >>stream, 'usage: casatask <task> [task-specific arguments]'
    print >>stream
    print >>stream, 'Supported tasks:'
    print >>stream

    for name in sorted (globals ().iterkeys ()):
        if name.endswith ('_cli'):
            print >>stream, name[:-4]

    raise SystemExit (exitcode)


def cmdline_driver (argv):
    import sys

    if len (argv) < 2 or argv[1] == '--help':
        cmdline_usage (sys.stdout, 0)

    driver = globals ().get (argv[1] + '_cli')
    if driver is None:
        print >>sys.stderr, 'error: unknown task "%s"; run with no arguments for a list' % argv[1]
        sys.exit (1)

    subargv = [' '.join (argv[:2])] + argv[2:]
    driver (subargv)


if __name__ == '__main__':
    import sys
    cmdline_driver (sys.argv)
