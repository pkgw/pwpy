#! /usr/bin/env python
# -*- python -*-

"""= dualscal - selfcal polarizations separately
& pkgw
: calibration
+
 DUALSCAL runs SELFCAL or MSELFCAL on the specified dataset(s) twice,
 selecting XX polarizations once and YY polarizations once. It then
 merges the XX and YY gains tables and saves them either in a 
 gains-only Miriad dataset (via the out= keyword) or writes the
 calibration tables into the source dataset (if no out= keyword is
 supplied and there is only a single visibility input file).

 By default, DUALSCAL will run the two selfcal tasks in parallel.
 This behavior should result in a nontrivial speed boost in most
 cases, but it does result in the output of the selfcal tasks
 being interleaved in an unpredictable manner. The tasks can be
 run serially via the "serial" option.

 DUALSCAL supports all of the options that SELFCAL and MSELFCAL do. 
 This includes the option "verbose", which is only supported by
 MSELFCAL -- an error will be raised if you attempt to give SELFCAL
 this option. The following arguments are specific to DUALSCAL:

@ ttol
 The tolerance for differing gain solution timestamps in the datasets,
 measured in seconds. The gain solution timestamps derived by the
 self-calibration tasks may vary slightly between the two gains solutions
 depending on the data flagging and contents of the raw observations.
 Default is 1 second, which should be strict but not overly so.

@ postinterval
 The SELFCAL tasks use the "interval" keyword to specify both the
 averaging interval for determining the selfcal solution and the time
 tolerance that will be used for extrapolating solutions when the
 gains are applied. The "postinterval" keyword can be used to override
 this latter value, so that selfcal solutions can be derived on a fast
 timescale but then extrapolated to more distant times. "postinterval"
 is measured in minutes and defaults to "interval".

@ options
 Options are specified separated by commas. Minimum-match is used.

 'usemself' - Use MSELFCAL instead of SELFCAL to perform the selfcal.
 'serial'   - Run the selfcal tasks serially, rather than in parallel.
--
"""

from mirexec import TaskSelfCal, TaskMSelfCal
from miriad import *
from mirtask import util
import numpy as np
from gpmergepols import merge, DEFAULT_TTOL

IDENT = '$Id$'
__version_info__ = (1, 0)
__all__ = 'dualSelfCal task'.split ()


def dualSelfCal (vis, out, usemself=False, ttol=DEFAULT_TTOL, outexists=False,
                 serial=False, select='', postinterval=None,
                 banner='PYTHON dualSelfCal', **kwargs):
    vis = ensureiterable (vis)

    if len (vis) == 0:
        util.die ('must specify at least one visibility file')

    for ivis in vis:
        if not ivis.exists:
            util.die ('visibility input file %s does not exist', ivis)

    if usemself:
        task = TaskMSelfCal ()
    else:
        task = TaskSelfCal ()
        if 'verbose' in kwargs and kwargs['verbose']:
            util.die ('option "verbose" only supported by mselfcal')

    if ttol <= 0:
        util.die ('parameter "ttol" must be positive')

    if out is None:
        if len (vis) != 1:
            util.die ('must specify "out" if more than '
                      'one visibility input specified')
        dest = vis[0].open ('rw')
    else:
        if outexists:
            dest = out.open ('rw')
        else:
            dest = out.open ('c')
        src1 = vis[0].open ('rw')
        src1.copyItem (dest, 'history')
        src1.close ()

    if len (select) == 0:
        selformat = 'pol(%s)'
    else:
        selformat = select + ',pol(%s)'

    task.vis = vis
    task.set (**kwargs)

    # Go

    worksets = []
    procs = []

    for pol in 'xx', 'yy':
        workset = vis[0].makeVariant ('sc' + pol, CalData)
        workset.delete ()
        worksets.append (workset)
        task.select = selformat % pol
        task.out = workset

        if serial:
            task.run ()
        else:
            procs.append (task.launch ())

    for proc in procs:
        proc.checkwait ()

    src1 = worksets[0].open ('rw')
    src2 = worksets[1].open ('rw')
    merge (str (worksets[0]), src1, str (worksets[1]), src2, dest, banner, ttol)

    for workset in worksets:
        workset.delete ()

    if postinterval is not None:
        dest.setScalarItem ('interval', np.float32, postinterval / (60. * 24))


# AWFF/ARF workflow interface

try:
    from awff import SimpleMake
    from arf import calinfo, visutil
    from arf.workflow.vis import getSource, getFreq
except:
    pass
else:
    def _dualscal (context, vis=None, params=None, fluxtable=None):
        context.ensureParent ()
        out = VisData (context.fullpath ())

        if fluxtable is not '':
            params = dict (params)
            params['flux'] = visutil.lookupFlux (str (fluxtable), vis)

        out.delete ()
        vis.lwcpTo (out)

        try:
            dualSelfCal (vis, out, outexists=True, **params)
        except Exception:
            out.delete ()
            raise

        return out

    asMake = SimpleMake ('vis params fluxtable', 'out', _dualscal,
                         [None, {}, ''])
    __all__.append ('asMake')


# Command-line task interface

def task (args):
    banner = util.printBannerGit ('dualscal', 'selfcal polarizations separately', IDENT)
    basicTrace ()

    # Define all the arguments 

    from mirtask.keys import KeySpec

    ks = KeySpec ()
    ks.mkeyword ('vis', 'f', 128)
    ks.keyword ('select', 'a', ' ')
    ks.keyword ('model', 'f', ' ')
    ks.keyword ('clip', 'd', np.nan)
    ks.keyword ('interval', 'd', np.nan)
    ks.keyword ('minants', 'i', -1)
    ks.keyword ('refant', 'i', -1)
    ks.keyword ('flux', 'd', np.nan)
    ks.mkeyword ('offset', 'd', 2)
    ks.mkeyword ('line', 'a', 5)
    ks.keyword ('out', 'f', ' ')
    ks.option ('amplitude', 'phase', 'smooth', 'polarized', 'mfs',
               'relax', 'apriori', 'noscale', 'mosaic', 'verbose')
    # Specific to this task:
    ks.keyword ('ttol', 'd', DEFAULT_TTOL * 86400)
    ks.keyword ('postinterval', 'd', np.nan)
    ks.option ('usemself', 'serial')

    kws = ks.process (args)

    # Process the arguments

    vises = [VisData (x) for x in kws.vis]

    if kws.select == ' ':
        kws.select = ''

    kws.ttol /= 86400. # seconds -> days

    if np.isnan (kws.postinterval):
        kws.postinterval = None

    if kws.out == ' ':
        out = None
    else:
        out = Data (kws.out)

    # Copy parameters, leaving defaults when unspecified

    rest = {}

    for filenamekw in ('model', ):
        v = getattr (kws, filenamekw)
        if v != ' ':
            rest[filenamekw] = v

    for floatkw in ('clip', 'interval', 'flux'):
        v = getattr (kws, floatkw)
        if not np.isnan (v):
            rest[floatkw] = v

    for intkw in ('minants', 'refant'):
        v = getattr (kws, intkw)
        if v >= 0:
            rest[intkw] = v

    for listkw in ('offset', 'line'):
        v = getattr (kws, listkw)
        if len (v):
            rest[listkw] = v

    for option in ('amplitude', 'phase', 'smooth', 'polarized', 'mfs',
                   'relax', 'apriori', 'noscale', 'mosaic', 'verbose'):
        rest[option] = bool (getattr (kws, option, False))


    # Ready to do the real work

    dualSelfCal (vises, out, kws.usemself, kws.ttol, False, kws.serial,
                 kws.select, kws.postinterval, banner, **rest)
    return 0


if __name__ == '__main__':
    from sys import argv, exit
    exit (task (argv[1:]))
