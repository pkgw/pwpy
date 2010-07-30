#! /usr/bin/env python

"""= pwmodel - helpful wrapper around UVMODEL
& pkgw
: uv analysis
+
 PWMODEL is a wrapper around UVMODEL that makes it somewhat easier to
 use and avoids changing the polarizations in the output dataset, at
 the cost of extra processing time and unusual changes to the data
 stream.

 The primary motivation for PWMODEL is that UVMODEL can often create
 an output dataset with different polarization information than its
 input. In the common case that UVMODEL is operating in the 'II'
 Stokes mode, the XX and YY polarizations of the input are converted
 into Stokes I polarizations. PWMODEL undoes this change by modeling
 the two polarizations separately and then using UVCAL to hack the
 data back into their original polarization state.

 PWMODEL will also optionally UVCAT the input dataset(s) into a 
 temporary dataset to apply their calibration parameters. The UV 
 modeling subsystem in MIRIAD ignores calibration parameters associated
 with UV data, which can be confusing and inconvenient to deal with.

 By default, PWMODEL creates two correctly-polarized output datasets,
 as described above, and then just UVCATs them together into one
 dataset. This has the limitation of creating datasets with an unusual
 structure, in which all of the XX data appear, then all of the YY data
 follow. This is unacceptable if one wishes to, e.g., perform Stokes
 processing on the data after the modeling step. PWMODEL can optionally
 "touch up" the output dataset, putting the XX and YY pols in the
 correct order, so that the output can be Stokes processed. This
 touchup step involves running UVSORT and can thus be very
 time-intensive.

 PWMODEL accepts multiple input datasets, which are passed on the
 command line WITHOUT a "vis=" keyword. Any item appearing on the
 command line that does not look like one of the options described below
 is interpreted as an input dataset.

 LIMITATIONS: PWMODEL assumes that your telescope has X/Y feeds rather
 than R/L feeds. It discards XY and YX data which makes all the stuff
 about further polarization processing kind of pointless.

@ vis
 There is NO 'vis' keyword. Inputs are specified directly on the command
 line; they are detected by the lack of '=' in an argument string.
 Obviously, if you give a dataset a name containing an equals sign, this
 breaks.

@ model
 The name of the model image, which should be a JY/PIXEL MIRIAD image.
 If unspecified, a point source model must be specified via the 
 keyword "flux".

@ out
 The name of the output dataset.

@ mode
 The way in which the model is applied to the UV data. Valid values are
 'add', 'subtract', 'multiply', 'divide', and 'replace'. These parallel
 the options to UVMODEL. The default is 'subtract'.

@ select
 Standard UV selection options. Don't include a polarization selection
 here!

@ clip
 A clip value to apply to the model image, passed verbatim to UVMODEL.

@ flux
 If not using a model image, the flux of a point source model, in
 Janskys.

@ offset
 If not using a model image, the RA and dec. offsets to apply to the
 position of the point source model, in arcseconds. North and east are
 positive offsets, respectively. The default is no offset (i.e., 0,0).

@ options
 PWMODEL accepts some Unix-style command-line flags. They cannot be
 combined in the usual Unix way since I'm lazy.

 '-c' UVCAT the input datasets into a single dataset before performing
      the modeling, so as to apply their calibration parameters.
 '-p' Preserve intermediate datasets created by PWMODEL. These have
      names that look like the output name with varying suffixes added.
      By default these datasets are all deleted.
 '-t' Perform the post-modeling "touchup" step to make the format of
      the output dataset less unusual.
 '-z' Pass the "zero" option to UVMODEL.
 '-a' Pass the "autoscale" option to UVMODEL.
--
"""

import sys
import miriad, mirexec
from mirtask import util

MODE_REPLACE = 0
MODE_SUBTRACT = 1
MODE_ADD = 2
MODE_MULTIPLY = 3
MODE_DIVIDE = 4

__all__ = ['MODE_REPLACE', 'MODE_SUBTRACT', 'MODE_ADD', 'MODE_MULTIPLY',
           'MODE_DIVIDE']

_modeOptionMap = {
    MODE_REPLACE: 'replace',
    MODE_SUBTRACT: 'subtract',
    MODE_ADD: 'add',
    MODE_MULTIPLY: 'multiply',
    MODE_DIVIDE: 'divide',
}

class ModelerParamsError (StandardError): pass

class Modeler (object):
    out = None
    model = None
    mode = MODE_SUBTRACT
    precat = False
    flux = None
    preserve = False
    touchup = False
    defaultModelMisc = {'mfs': True, 'line': 'chan'}
    defaultSelect = []

    def __init__ (self):
        self.vises = []
        self.modelMisc = self.defaultModelMisc.copy ()
        self.select = list (self.defaultSelect)


    def checkSetup (self):
        for v in self.vises:
            if not v.exists:
                raise ModelerParamsError ('nonexistant input dataset \'%s\'.' % v)

        if self.out is None:
            raise ModelerParamsError ('must specify output dataset.')

        if self.out.exists:
            raise ModelerParamsError ('output dataset \'%s\' exists.' % out)

        if self.model is None and self.flux is None:
            raise ModelerParamsError ('must specify model image or point source flux.')

        if self.model is not None and self.flux is not None:
            raise ModelerParamsError ('cannot specify both model image '
                                      'and point source flux.')

        if self.model is not None and not self.model.exists:
            raise ModelerParamsError ('nonexistant model image \'%s\'.' % self.model)


    def run (self):
        cleanup = []

        vises = self.vises

        if self.precat:
            cattmp = self.out.vvis ('cat')
            cattmp.delete ()
            mirexec.TaskUVCat (vis=vises, out=cattmp).run ()
            vises = [cattmp]
            cleanup.append (cattmp)

        t = mirexec.TaskUVModel (vis=vises, model=self.model)
        setattr (t, _modeOptionMap[self.mode], True)
        t.set (flux=self.flux)
        t.set (**self.modelMisc)

        cmodel = []

        # Run the two model tasks in parallel. (One task for each pol.)  There
        # are several steps to execute serially for each pol, so instead of
        # running the MIRIAD tasks asynchronously, which would add a few extra
        # sync points to the processing, we actually spawn a couple of
        # threads, since it's not very complicated to do so.

        def doone (modeltask, pol, polcode):
            pv = self.out.vvis ('mdl' + pol)
            pv.delete ()
            modeltask.set (select=self.select + ['pol(%s)' % (pol * 2)], 
                           out=pv).run ()
            cleanup.append (pv)

            # If the user is modeling with a point-source model, UVMODEL
            # doesn't write any polarization information into the output
            # dataset, which causes UVCAL to not apply the polcode correction
            # (even though the default assumption is I pol, I believe).  So we
            # edit the dataset to insert polarization information
            # unconditionally. We append npol and pol UV variables because
            # UVCAL checks the presence of these UV variables when deciding if
            # its input has any polarization information. We also write header
            # items so that the values of the UV variables will be defined for
            # the entire UV stream via the override mechanism -- otherwise,
            # they'd remain undefined until the entire stream was finished!
            # Appending in this way means that we don't have to rewrite the
            # entire dataset just to stick a "pol = npol = 1" at its
            # beginning.

            phnd = pv.open ('a')
            phnd.writeVarInt ('npol', 1)
            phnd.writeVarInt ('pol', util.POL_I)
            phnd.writeHeaderInt ('npol', 1)
            phnd.writeHeaderInt ('pol', util.POL_I)
            phnd.close ()

            cv = self.out.vvis ('cal' + pol)
            cv.delete ()
            mirexec.TaskUVCal (vis=pv, out=cv, polcode=polcode).run ()
            cmodel.append (cv)
            cleanup.append (cv)

        from threading import Thread
        from copy import deepcopy

        threads = []

        for pol, polcode in zip ('xy', (-6, -7)):
            thread = Thread (target=doone, args=(deepcopy (t), pol, polcode))
            thread.start ()
            threads.append (thread)

        for thread in threads:
            thread.join ()

        # Done with the per-pol processing.

        if not self.touchup:
            mirexec.TaskUVCat (vis=sorted (str (v) for v in cmodel),
                               out=self.out).run ()
        else:
            combined = self.out.vvis ('comb')
            combined.delete ()
            mirexec.TaskUVCat (vis=sorted (str (v) for v in cmodel),
                               out=combined).run ()
            cleanup.append (combined)

            sortvis = self.out.vvis ('sort')
            sortvis.delete ()
            mirexec.TaskUVSort (vis=combined, out=sortvis).run ()
            cleanup.append (sortvis)

            mirexec.TaskUVAver (vis=sorted, interval=1e-6, out=self.out).run ()

        if not self.preserve:
            for v in cleanup:
                v.delete ()


def _error (fmt, *args):
    print >>sys.stderr, 'Error:', fmt % args


def task (argv):
    miriad.basicTrace ()

    # Handle arguments

    m = Modeler ()

    for arg in argv:
        if arg.startswith ('out='):
            m.out = miriad.VisData (arg[4:])
        elif arg.startswith ('model='):
            m.model = miriad.ImData (arg[6:])
        elif arg.startswith ('mode='):
            rest = arg[5:]

            if rest == 'replace':
                m.mode = MODE_REPLACE
            elif rest == 'subtract':
                m.mode = MODE_SUBTRACT
            elif rest == 'add':
                m.mode = MODE_ADD
            elif rest == 'multiply':
                m.mode = MODE_MULTIPLY
            elif rest == 'divide':
                m.mode = MODE_DIVIDE
            else:
                _error ('unknown operation mode \'%s\'.' % rest)
                return 1
        elif arg == '-c':
            m.precat = True
        elif arg == '-p':
            m.preserve = True
        elif arg == '-t':
            m.touchup = True
        elif arg.startswith ('flux='):
            m.flux = float (arg[5:])
        elif arg.startswith ('select='):
            # This won't handle commas within parentheses with semantic
            # correctness, but it'll work for our needs.
            m.select += arg[7:].split (',')
        elif arg == '-z':
            m.modelMisc['zero'] = True
        elif arg == '-a':
            m.modelMisc['autoscale'] = True
        elif arg.startswith ('clip='):
            m.modelMisc['clip'] = float (arg[5:])
        elif arg.startswith ('offset='):
            m.modelMisc['offset'] = [float (x) for x in arg[7:].split (',')]
        else:
            m.vises.append (miriad.VisData (arg))

    try:
        m.checkSetup ()
    except ModelerParamsError, e:
        _error ('%s', e)
        return 1

    m.run ()
    return 0

__all__ += ['ModelerParamsError', 'Modeler']


if __name__ == '__main__':
    sys.exit (task (sys.argv[1:]))
