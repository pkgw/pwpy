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

# Keep the tasks alphabetized!

__all__ = ('applycal applycal_cli ApplycalConfig '
           'clearcal clearcal_cli '
           'concat concat_cli '
           'flagmanager_cli '
           'gaincal gaincal_cli GaincalConfig '
           'mfsclean mfsclean_cli MfscleanConfig '
           'setjy setjy_cli SetjyConfig '
           'split split_cli SplitConfig '
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


# Some utilities

precal_doc = \
"""
*** Pre-applied calibrations:

gaintable=
  Comma-separated list of calibration tables to apply on-the-fly
  before solving

gainfield=
  SEMICOLON-separated list of field selections to apply for each gain table.
  If there are fewer items than there are gaintable items, the list is
  padded with blank items, implying no selection by field.

interp=
  COMMA-separated list of interpolation types to use for each gain
  table. If there are fewer items, the list is padded with 'linear'
  entries. Allowed values:
    nearest linear cubic spline

spwmap=
  SEMICOLON-separated list of spectral window mappings for each
  existing gain table; each record is a COMMA-separated list of
  integers. For the i'th spw in the dataset, spwmap[i] specifies
  the record in the gain table to use. For instance [0, 0, 1, 1]
  maps four spws in the UV data to just two spectral windows in
  the preexisting gain table.

opacity=
  Comma-separated list of opacities in nepers. One for each spw; if
  there are more spws than entries, the last entry is used for the
  remaining spws.

gaincurve=
  Whether to apply VLA-specific built in gain curve correction
  (default: false)

parang=
  Whether to apply parallactic angle rotation correction
  (default: false)
"""

stdsel_doc = \
"""
*** Standard data selection keywords:

antenna=
array=
correlation=
field=
intent=
observation=
scan=
spw=
taql=
timerange=
uvrange=
"""

loglevel_doc = \
"""
loglevel=
  Level of detail from CASA logging system. Default: warn; allowed:
    severe warn info info1 info2 info3 info4 info5 debug1 debug2 debugging
"""

def extractmsselect (cfg, havearray=False, havecorr=False, haveintent=True, taqltomsselect=True):
    # expects cfg to have:
    #  antenna [correlation] field intent observation scan spw taql timerange uvrange
    # fills a dict with:
    #  baseline [correlation] field intent (msselect|taql) observation scan spw time uvrange

    selkws = {}

    direct = 'field observation scan spw uvrange'.split ()
    indirect = 'antenna:baseline timerange:time'.split ()

    if havearray:
        indirect.append ('array:subarray')

    if havecorr:
        direct.append ('correlation')

    if haveintent:
        direct.append ('intent')

    if taqltomsselect:
        indirect.append ('taql:msselect')
    else:
        direct.append ('taql')

    for k in direct:
        selkws[k] = getattr (cfg, k) or ''

    for p in indirect:
        ck, sk = p.split (':')
        selkws[sk] = getattr (cfg, ck) or ''

    return selkws


def applyonthefly (cb, cfg):
    # expects cfg to have:
    #   gaintable gainfield interp spwmap opacity gaincurve parang

    n = len (cfg.gaintable)

    if len (cfg.gainfield) < n:
        cfg.gainfield += [''] * (n - len (cfg.gainfield))
    elif len (cfg.gainfield) > n:
        raise ValueError ('more "gainfield" entries than "gaintable" entries')

    if len (cfg.interp) < n:
        cfg.interp += ['linear'] * (n - len (cfg.interp))
    elif len (cfg.interp) > n:
        raise ValueError ('more "interp" entries than "gaintable" entries')

    if len (cfg.spwmap) < n:
        cfg.spwmap += [[-1]] * (n - len (cfg.interp))
    elif len (cfg.spwmap) > n:
        raise ValueError ('more "spwmap" entries than "gaintable" entries')

    for table, field, interp, spwmap in zip (cfg.gaintable, cfg.gainfield,
                                             cfg.interp, cfg.spwmap):
        cb.setapply (table=table, field=field, interp=interp, spwmap=spwmap,
                     t=0., calwt=True)

    if len (cfg.opacity):
        cb.setapply (type='TOPAC', opacity=cfg.opacity, t=-1, calwt=True)

    if cfg.gaincurve:
        cb.setapply (type='GAINCURVE', t=-1, calwt=True)

    if cfg.parang:
        cb.setapply (type='P')


# applycal

applycal_doc = \
"""
casatask applycal vis=<MS> [keywords]

Fill in the CORRECTED_DATA column of a visibility dataset using
the raw data and a set of calibration tables.

vis=
  The MS to modify

calwt=
  Write out calibrated weights as well as calibrated visibilities.
  Default: true
""" + precal_doc + stdsel_doc + loglevel_doc


class ApplycalConfig (ParseKeywords):
    vis = Custom (str, required=True)
    calwt = False
    # skipping: applymode, flagbackup

    gaintable = [str]
    gainfield = Custom ([str], sep=';')
    interp = [str]
    @Custom ([str], sep=';')
    def spwmap (v):
        return [map (int, e.split (',')) for e in v]
    opacity = [float]
    gaincurve = False
    parang = False

    antenna = str
    field = str
    intent = str
    observation = str
    scan = str
    spw = str
    taql = str
    timerange = str
    uvrange = str

    loglevel = 'warn'


def applycal (cfg):
    cb = cu.tools.calibrater ()
    cb.open (filename=cfg.vis, compress=False, addcorr=True, addmodel=False)

    selkws = extractmsselect (cfg)
    selkws['chanmode'] = 'none' # ?
    cb.selectvis (**selkws)

    applyonthefly (cb, cfg)

    cb.correct ('calflag')
    cb.close ()


def applycal_cli (argv):
    checkusage (applycal_doc, argv, usageifnoargs=True)
    cfg = ApplycalConfig ().parse (argv[1:])
    cu.logger (cfg.loglevel)
    applycal (cfg)


# clearcal

clearcal_doc = \
"""
casatask clearcal [-w] <vis1> [more vises...]

Fill the imaging and calibration columns (MODEL_DATA, CORRECTED_DATA,
IMAGING_WEIGHT) of each measurement set with default values, creating
the columns if necessary.

-w - only create and fill the IMAGING_WEIGHT column
"""

clearcal_imaging_col_tmpl = {'_c_order': True,
                             'comment': '',
                             'dataManagerGroup': '',
                             'dataManagerType': '',
                             'keywords': {},
                             'maxlen': 0,
                             'ndim': 1,
                             'option': 0,
                             'shape': None,
                             'valueType': 'float'}
clearcal_imaging_dminfo_tmpl = {'TYPE': 'TiledShapeStMan',
                                'SPEC': {'DEFAULTTILESHAPE': [32, 128]},
                                'NAME': 'imagingweight'}

def clearcal (vis, weightonly=False):
    tb = cu.tools.table ()
    cb = cu.tools.calibrater ()

    # cb.open() will create the tables if they're not present, so
    # if that's the case, we don't actually need to run initcalset()

    tb.open (vis, nomodify=False)
    colnames = tb.colnames ()
    needinit = ('MODEL_DATA' in colnames) or ('CORRECTED_DATA' in colnames)
    if 'IMAGING_WEIGHT' not in colnames:
        c = dict (clearcal_imaging_col_tmpl)
        c['shape'] = tb.getcell ('DATA', 0).shape[-1:]
        tb.addcols ({'IMAGING_WEIGHT': c}, clearcal_imaging_dminfo_tmpl)
    tb.close ()

    if not weightonly:
        cb.open (vis)
        if needinit:
            cb.initcalset ()
        cb.close ()


def clearcal_cli (argv):
    checkusage (clearcal_doc, argv, usageifnoargs=True)

    argv = list (argv)
    weightonly = '-w' in argv
    if weightonly:
        sys.argv.remove ('-w')

    if len (argv) < 2:
        wrongusage (clearcal_doc, 'need at least one argument')

    cu.logger ()
    for vis in argv[1:]:
        clearcal (vis, weightonly=weightonly)


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


# flagmanager. Not really complicated enough to make it worth making a
# modular implementation to be driven from the CLI.

flagmanager_doc = \
"""
casatask flagmanager list <ms>
casatask flagmanager save <ms> <name>
casatask flagmanager restore <ms> <name>
casatask flagmanager delete <ms> <name>
"""

def flagmanager_cli (argv):
    import os.path
    checkusage (flagmanager_doc, argv, usageifnoargs=True)

    if len (argv) < 3:
        wrongusage (flagmanager_doc, 'expect at least a mode and an MS name')

    mode = argv[1]
    ms = argv[2]

    if mode == 'list':
        cu.logger ('info')
    elif mode == 'delete':
        # it WARNs 'deleting version xxx' ... yargh
        cu.logger ('severe')
    else:
        cu.logger ()

    try:
        factory = cu.tools.agentflagger
    except AttributeError:
        factory = cu.tools.testflagger

    af = factory ()
    af.open (ms)

    if mode == 'list':
        if len (argv) != 3:
            wrongusage (flagmanager_doc, 'expect exactly one argument in list mode')
        af.getflagversionlist ()
    elif mode == 'save':
        if len (argv) != 4:
            wrongusage (flagmanager_doc, 'expect exactly two arguments in save mode')
        name = argv[3]
        af.saveflagversion (versionname=name, merge='replace',
                            comment='version "%s" created by casatask flagmanager' % name)
    elif mode == 'restore':
        if len (argv) != 4:
            wrongusage (flagmanager_doc, 'expect exactly two arguments in restore mode')
        name = argv[3]
        af.restoreflagversion (versionname=name, merge='replace')
    elif mode == 'delete':
        if len (argv) != 4:
            wrongusage (flagmanager_doc, 'expect exactly two arguments in delete mode')
        name = argv[3]

        if not os.path.isdir (os.path.join (ms + '.flagversions', 'flags.' + name)):
            # This condition only results in a WARN from deleteflagversion ()!
            raise RuntimeError ('version "%s" doesn\'t exist in "%s.flagversions"'
                                % (name, ms))

        af.deleteflagversion (versionname=name)
    else:
        wrongusage (flagmanager_doc, 'unknown flagmanager mode "%s"' % mode)

    af.done ()


# gaincal
#
# I've folded in the bandpass functionality since there's
# so much overlap. Some limitations that this leads to:
#
# - bandpass solint has a frequency component that we don't support
# - bandpass combine defaults to 'scan'

gaincal_doc = \
"""
casatask gaincal vis=<MS> caltable=<TBL> [keywords]

Compute calibration parameters from data. Encompasses the functionality
of CASA tasks 'gaincal' *and* 'bandpass'.

vis=
  Input dataset

caltable=
  Output calibration table (can exist if append=True)

gaintype=
  Kind of gain solution:
    G       - gains per poln and spw (default)
    T       - like G, but one value for all polns
    GSPLINE - like G, with a spline fit. "Experimental"
    B       - bandpass
    BPOLY   - bandpass with polynomial fit. "Somewhat experimental"
    K       - antenna-based delays
    KCROSS  - global cross-hand delay ; use parang=True
    XY+QU   - ?
    XYf+QU  - ?

calmode=
  What parameters to solve for: amplitude ("a"), phase ("p"), or both
  ("ap"). Default is "ap". Not used in bandpass solutions.

solint=
  Solution interval; this is an upper bound, but solutions
  will be broken across certain boundaries according to "combine".
  'inf'    - solutions as long as possible (the default)
  'int'    - one solution per integration
  (str)    - a specific time with units (e.g. '5min')
  (number) - a specific time in seconds

combine=
  Comma-separated list of boundary types; solutions will NOT be
  broken across these boundaries. Types are:
    field scan spw

refant=
  Comma-separated list of reference antennas in decreasing
  priority order.

solnorm=
  Normalize solution amplitudes to 1 after solving (only applies
  to gaintypes G, T, B). Also normalizes bandpass phases to zero
  when solving for bandpasses. Default: false.

append=
  Whether to append solutions to an existing table. If the table
  exists and append=False, the table is overwritten! (Default: false)
""" + precal_doc + """
*** Low-level parameters:

minblperant=
  Number of baselines for each ant in order to solve (default: 4)

minsnr=
  Min. SNR for acceptable solutions (default: 3.0)

preavg=
  Interval for pre-averaging data within each solution interval,
  in seconds. Default is -1, meaning not to pre-average.
""" + stdsel_doc + loglevel_doc


class GaincalConfig (ParseKeywords):
    vis = Custom (str, required=True)
    caltable = Custom (str, required=True)
    gaintype = 'G'
    calmode = 'ap'

    solint = 'inf'
    combine = [str]
    refant = [str]
    solnorm = False
    append = False
    minblperant = 4
    minsnr = 3.0
    preavg = -1.0

    gaintable = [str]
    gainfield = Custom ([str], sep=';')
    interp = [str]
    opacity = [float]
    gaincurve = False
    parang = False

    @Custom ([str], sep=';')
    def spwmap (v):
        return [map (int, e.split (',')) for e in v]

    # gaincal keywords: splinetime npointaver phasewrap smodel
    # bandpass keywords: fillgaps degamp degphase visnorm maskcenter
    #   maskedge

    antenna = str
    field = str
    intent = str
    observation = str
    scan = str
    spw = str
    taql = str # msselect
    timerange = str
    uvrange = str

    loglevel = 'warn' # teeny hack for CLI


def gaincal (cfg):
    cb = cu.tools.calibrater ()
    cb.open (filename=cfg.vis, compress=False, addcorr=False, addmodel=False)

    selkws = extractmsselect (cfg)
    selkws['chanmode'] = 'none' # ?
    cb.selectvis (**selkws)

    applyonthefly (cb, cfg)

    # Solve

    solkws = {}

    for k in 'append preavg minblperant minsnr solnorm'.split ():
        solkws[k] = getattr (cfg, k)

    for p in 'caltable:table calmode:apmode'.split ():
        ck, sk = p.split (':')
        solkws[sk] = getattr (cfg, ck)

    if isinstance (cfg.solint, (int, float)):
        solkws['t'] = '%fs' % cfg.solint # sugar
    else:
        solkws['t'] = str (cfg.solint)

    solkws['combine'] = ','.join (cfg.combine)
    solkws['refant'] = ','.join (cfg.refant)
    solkws['phaseonly'] = False
    solkws['type'] = cfg.gaintype.upper ()

    if solkws['type'] == 'GSPLINE':
        cb.setsolvegainspline (**solkws)
    elif solkws['type'] == 'BPOLY':
        cb.setsolvebandpoly (**solkws)
    else:
        cb.setsolve (**solkws)

    cb.solve ()
    cb.close ()


def gaincal_cli (argv):
    checkusage (gaincal_doc, argv, usageifnoargs=True)
    cfg = GaincalConfig ().parse (argv[1:])
    cu.logger (cfg.loglevel)
    gaincal (cfg)


# mfsclean
#
# This isn't a CASA task, but we're pulling out a subset of the functionality
# of clean, which has a bajillion options and has a really gross implementation
# in the library.

mfsclean_doc = \
"""
casatask mfsclean vis=[] [keywords]

Drive the CASA imager with a very restricted set of options

vis=
  Input visibility MS

imbase=
  Base name of output files. We create files named "imbaseEXT"
  where EXT is all of "mask", "TTmodel", "TTrestored", "TTresidual",
  and "TTpsf", and TT is empty if nterms = 1, and "ttN." otherwise.

nterms=1
reffreq = 1 [GHz]
imsize = 256,256
cell = 1 [arcsec]
phasecenter = (blank) or 'J2000 12h34m56.7 -12d34m56.7'
stokes = I
niter = 500
gain = 0.1
threshold = 0 [mJy]
mask = (blank) or path of CASA-format region text file
""" + stdsel_doc + loglevel_doc

class MfscleanConfig (ParseKeywords):
    vis = Custom (str, required=True)
    imbase = Custom (str, required=True)

    nterms = 1
    reffreq = 1. # GHz
    imsize = [256, 256]
    cell = 1. # arcsec
    phasecenter = str
    stokes = 'I'
    niter = 500
    gain = 0.1
    threshold = 0. # mJy
    mask = str

    # mode = mfs
    # gridmode = ''
    # psfmode = clark
    # nchan = -1
    # width = 1
    # imagermode = csclean
    # cyclefactor = 1.5
    # cyclespeedup = -1
    # multiscale = []
    # interactive = False
    # uvtaper = False
    # modelimage = []
    # weighting = 'briggs'
    # robust = 0.5
    # restoringbeam = []
    # pbcor = False
    # minpb = 0.2
    # usescratch = False
    # allowchunk = False
    # npixels = 0
    # veltype = radio
    # smallscalebias = 0.6

    antenna = str
    field = str
    observation = str
    scan = str
    spw = str
    timerange = str
    uvrange = str
    taql = str

    loglevel = 'warn'


specframenames = 'REST LSRK LSRD BARY GEO TOPO GALACTO LGROUP CMB'.split ()


def mfsclean (cfg):
    import os.path

    ms = cu.tools.ms ()
    im = cu.tools.imager ()
    tb = cu.tools.table ()
    qa = cu.tools.quanta ()
    ia = cu.tools.image ()

    minpb = 0.2

    # Filenames. TODO: make sure nothing exists

    mask = cfg.imbase + 'mask'
    pb = cfg.imbase + 'flux'

    if cfg.nterms == 1:
        models = [cfg.imbase + 'model']
        restoreds = [cfg.imbase + 'restored']
        resids = [cfg.imbase + 'residual']
        psfs = [cfg.imbase + 'psf']
    else:
        for i in xrange (cfg.nterms):
            models = [cfg.imbase + 'tt%d.model' % i]
            restoreds = [cfg.imbase + 'tt%d.restored' % i]
            resids = [cfg.imbase + 'tt%d.residual' % i]
            psfs = [cfg.imbase + 'tt%d.psf' % i]

    # Get info on our selected data for various things we need to figure
    # out later.

    selkws = extractmsselect (cfg, havearray=False, haveintent=False, taqltomsselect=False)
    ms.open (cfg.vis)
    ms.msselect (selkws)
    rangeinfo = ms.range ('data_desc_id field_id'.split ())
    ddids = rangeinfo['data_desc_id']
    fields = rangeinfo['field_id']

    # Get the spectral frame from the first spw of the selected data

    tb.open (os.path.join (cfg.vis, 'DATA_DESCRIPTION'))
    ddspws = tb.getcol ('SPECTRAL_WINDOW_ID')
    tb.close ()
    spw0 = ddspws[ddids[0]]

    tb.open (os.path.join (cfg.vis, 'SPECTRAL_WINDOW'))
    specframe = specframenames[tb.getcell ('MEAS_FREQ_REF', spw0)]
    tb.close ()

    # Choose phase center

    if cfg.phasecenter is not None:
        phasecenter = cfg.phasecenter
    else:
        phasecenter = int (fields[0])

    # Set up all of this junk

    im.open (cfg.vis, usescratch=False)
    im.selectvis (nchan=-1, start=0, step=1, usescratch=False, writeaccess=False, **selkws)
    im.defineimage (nx=cfg.imsize[0], ny=cfg.imsize[1],
                    cellx=qa.quantity (cfg.cell, 'arcsec'),
                    celly=qa.quantity (cfg.cell, 'arcsec'),
                    outframe=specframe, phasecenter=phasecenter,
                    stokes=cfg.stokes,
                    spw=-1, # to verify: selectvis (spw=) good enough?
                    restfreq='', mode='mfs', veltype='radio',
                    nchan=-1, start=0, step=1, facets=1)
    im.weight (type='briggs', rmode='norm', robust=0.5, npixels=0) #noise=, mosaic=
    # im.filter (...)
    im.setscales (scalemethod='uservector', uservector=[0])
    im.setsmallscalebias (0.6)
    im.setmfcontrol ()
    im.setvp (dovp=True)
    im.makeimage (type='pb', image=pb, compleximage='', verbose=False)
    im.setvp (dovp=False, verbose=False)
    im.setoptions (ftmachine='ft', wprojplanes=1, freqinterp='linear',
                   padding=1.2, pastep=360.0, pblimit=minpb,
                   applypointingoffsets=False, dopbgriddingcorrections=True)

    if cfg.nterms > 1:
        im.settaylorterms (ntaylorterms=cfg.nterms, reffreq=cfg.reffreq * 1e9)

    im.setmfcontrol (stoplargenegatives=-1, cyclefactor=1.5,
                     cyclespeedup=-1, minpb=minpb)

    # Create the mask

    im.make (mask)
    ia.open (mask)
    maskcs = ia.coordsys ()
    maskcs.setreferencecode (specframe, 'spectral', True)
    ia.setcoordsys (maskcs.torecord ())

    if cfg.mask is not None:
        rg = cu.tools.regionmanager ()
        regions = rg.fromtextfile (filename=cfg.mask,
                                   shape=ia.shape (),
                                   csys=maskcs.torecord ())
        im.regiontoimagemask (mask=mask, region=regions)

    ia.close ()

    # Create blank model(s). Diverging from task_clean even more
    # significantly than usual here.

    for model in models:
        im.make (model)

    # Go!

    im.clean (algorithm='msmfs', niter=cfg.niter, gain=cfg.gain,
              threshold=qa.quantity (cfg.threshold, 'mJy'),
              model=models, residual=resids, image=restoreds,
              psfimage=psfs, mask=mask, interactive=False)
    im.close ()


def mfsclean_cli (argv):
    checkusage (mfsclean_doc, argv, usageifnoargs=True)
    cfg = MfscleanConfig ().parse (argv[1:])
    cu.logger (cfg.loglevel)
    mfsclean (cfg)


# setjy

setjy_doc = \
"""
casatask setjy vis= [keywords]

Insert model data into a measurement set. We force usescratch=False
and scalebychan=True. You probably want to specify "field".

fluxdensity=
  Up to four comma-separated numbers giving Stokes IQUV intensities in
  Jy. Default values are [-1, 0, 0, 0]. If the Stokes I intensity is
  negative (i.e., the default), a "sensible default" will be used:
  detailed spectral models if the source is known (see "standard"), or
  1 otherwise. If it is zero and "modimage" is used, the flux density
  of the model image is used. The built-in standards do NOT have
  polarimetric information, so for pol cal you do need to manually
  specify the flux density information -- or see the program
  "mspolmodel".

modimage=
  An image to use as the basis for the source's spatial structure and,
  potentialy, flux density (if fluxdensity=0). Only usable for Stokes
  I.  If the verbatim value of "modimage" can't be opened as a path,
  it is assumed to be relative to the CASA data directory; a typical
  value might be "nrao/VLA/CalModels/3C286_C.im".

spindex=
reffreq=
  If using fluxdensity, these specify the spectral dependence of the
  values, such that S = fluxdensity * (freq/reffreq)**spindex. Reffreq
  is in GHz. Default values are 0 and 1, giving no spectral
  dependence.

standard='Perley-Butler 2013'
  Solar-system standards are not supported by this implementation, so
  acceptable values are: Baars, Perley 90, Perley-Taylor 95,
  Perley-Taylor 99, Perley-Butler 2010, Perley-Butler 2013.

*** Supported data selection keywords:

field=
observation=
scan=
spw=
timerange=
""" + loglevel_doc

class SetjyConfig (ParseKeywords):
    vis = Custom (str, required=True)
    modimage = str
    fluxdensity = [-1., 0., 0., 0.]
    spindex = 0.
    reffreq = 1. # GHz
    standard = 'Perley-Butler 2013'

    field = str
    observation = str
    scan = str
    spw = str
    timerange = str

    loglevel = 'warn'


def setjy (cfg):
    import os.path
    kws = {}

    for kw in 'field fluxdensity observation scan spw standard'.split ():
        kws[kw] = getattr (cfg, kw) or ''

    kws['time'] = cfg.timerange or ''
    kws['reffreq'] = str (cfg.reffreq) + 'GHz'
    kws['spix'] = cfg.spindex
    kws['scalebychan'] = True # don't think you'd ever want false??

    if cfg.modimage is None:
        kws['modimage'] = ''
    else:
        if os.path.isdir (cfg.modimage):
            mi = cfg.modimage
        else:
            mi = cu.datadir (cfg.modimage)
            if not os.path.isdir (mi):
                raise RuntimeError ('no model image "%s" or "%s"' % (cfg.modimage, mi))
        kws['modimage'] = mi

    im = cu.tools.imager ()
    im.open (cfg.vis, usescratch=False) # don't think you'll ever want True?
    im.setjy (**kws)
    im.close ()


def setjy_cli (argv):
    checkusage (setjy_doc, argv, usageifnoargs=True)
    cfg = SetjyConfig ().parse (argv[1:])
    cu.logger (cfg.loglevel)
    setjy (cfg)


# split
#
# note: spw=999 -> exception; scan=999 -> no output, or error, generated

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
    all DATA MODEL_DATA CORRECTED_DATA FLOAT_DATA LAG_DATA

combine=[col1,col2,...]
  When time-averaging, don't start a new bin when the specified columns change.
  Acceptable column names:
    scan state
""" + stdsel_doc + loglevel_doc

class SplitConfig (ParseKeywords):
    vis = Custom (str, required=True)
    out = Custom (str, required=True)

    timebin = float # seconds
    step = 1
    col = 'all'
    combine = [str]

    antenna = str
    array = str
    correlation = str
    field = str
    intent = str
    obs = str
    scan = str
    spw = str
    taql = str
    timerange = str
    uvrange = str

    loglevel = 'warn'


def split (cfg):
    import os.path
    kws = {}

    # ms.split() seems to merrily overwrite existing MSes which
    # seems pretty questionable. Forbid that for now as best we can.
    # Race conditions ahoy.
    if os.path.exists (cfg.out):
        raise RuntimeError ('destination "%s" already exists' % cfg.out)

    kws = extractmsselect (cfg, havarray=True, havecorr=True,
                           taqltomsselect=False)

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
