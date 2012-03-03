# -*- python ; coding: utf-8 -*-
#
# Copyright 2011 Peter Williams, the MeqTree Foundation,
# Netherlands Foundation for Research in Astronomy
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>,
# or write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA, 02111-1307, USA

from Timba.TDL import *
from Meow import Bookmarks, Context, MeqMaker, MSUtils, ParmGroup, StdTrees
from Calico.OMS import (central_point_source, ifr_based_errors,
                        solvable_jones, solvable_sky_jones)
from Siamese.OMS import fitsimage_sky, gridded_sky, feed_angle

try:
    from Siamese.OMS.tigger_lsm import TiggerSkyModel
except Exception, e:
    print '*** Tigger sky model not available:', e
    TiggerSkyModel = None

assert MSUtils.TABLE is not None, 'A table API is required!'


def mssel_compile_options ():
    TDLCompileOptionSeparator ('MS selection')

    mssel = MSUtils.MSSelector (has_input=True, tile_sizes=None,
                                read_flags=True, write_flags=True,
                                hanning=False, invert_phases=False)
    TDLCompileOptions (*mssel.compile_options ())
    TDLRuntimeMenu ('Data selection & flag handling',
                    *mssel.runtime_options ())

    Context.mssel = mssel
    return mssel


# Calibration quantity selection

class CalVisibilities (object):
    desc = 'complex visibilities'

    @staticmethod
    def apply (ifrs, lhs, rhs):
        """Returns (newlhs, newrhs, weights, modulus)."""
        return lhs, rhs, None, None


class CalAmplitudes (object):
    desc = 'amplitudes'

    @staticmethod
    def apply (ifrs, lhs, rhs):
        for side in rhs, lhs:
            for p, q in ifrs:
                side ('ampl', p, q) << Meq.Abs (side (p,q))

        return lhs ('ampl'), rhs ('ampl'), None, None


class CalLogAmplitudes (object):
    desc = 'log (amplitudes)'

    @staticmethod
    def apply (ifrs, lhs, rhs):
        for side in rhs, lhs:
            for p, q in ifrs:
                side ('logampl', p, q) << Meq.Log (Meq.Abs (side (p,q)))

        return lhs ('logampl'), rhs ('logampl'), None, None


class CalPhases (object):
    desc = 'phases'

    @staticmethod
    def apply (ifrs, lhs, rhs):
        for side in rhs, lhs:
            for p, q in ifrs:
                side ('phase', p, q) << Meq.Arg (side (p, q))

        for p, q in ifrs:
            rhs ('ampl', p, q) << Meq.Abs (rhs (p, q))

        from math import pi
        return lhs ('phase'), rhs ('phase'), rhs ('ampl'), 2 * pi


cal_quantities = [CalVisibilities, CalAmplitudes, CalLogAmplitudes, CalPhases]


def cal_compile_options (mssel):
    TDLCompileOptionSeparator ('Processing options')

    doc = """<p>Select "complex visibilities" to directly fit a
complex model to complex data, using the real and imaginary parts. The
other options (warning: highly experimental!) will fit only the
complex amplitudes (or logs of amplitudes) or phases.</p>"""

    cal_quant_opt = TDLOption ('cal_quant', 'Calibration quantity',
                               [(q, q.desc) for q in cal_quantities],
                               doc=doc)

    doc = """<p>You can restrict calibration to a subset of
interferometers. Note that this selection applies on top of (not
instead of) the global interferometer selection specified above."""

    cal_ifrs_opt = TDLOption ('calibrate_ifrs', 'Use interferometers',
                              ['all'], more=str, doc=doc)

    mssel.when_changed (lambda msname: cal_ifrs_opt.set_option_list (mssel.ms_ifr_subsets))

    doc = """<p>Select this to include a calibration step in your
tree. Calibration involves comparing predicted visibilities to input
data, and iteratively adjusting the sky and/or instrumental model for
the best fit.</p>"""

    cal_toggle = TDLCompileMenu ('Solve for calibration parameters',
                                 cal_quant_opt, cal_ifrs_opt,
                                 toggle='do_solve', open=True,
                                 doc=doc)


# Output selection

class OutputPredict (object):
    desc = 'Model prediction'
    need_data = False
    need_model = True
    flag_data = False

    @staticmethod
    def apply (ns, meqmaker, ifrs, data, predict):
        return predict


class OutputDataPlusPredict (object):
    desc = 'Data plus model prediction'
    need_data = True
    need_model = True
    flag_data = False

    @staticmethod
    def apply (ns, meqmaker, ifrs, data, predict):
        outputs = ns.output
        for p, q in ifrs:
            outputs(p,q) << data(p,q) + predict(p,q)
        return outputs


class OutputCorrectedData (object):
    desc = 'Corrected data'
    need_data = True
    need_model = False
    flag_data = True

    @staticmethod
    def apply (ns, meqmaker, ifrs, data, predict):
        return meqmaker.correct_uv_data (ns, data)


class OutputUncorrectedResiduals (object):
    desc = 'Uncorrected residuals'
    need_data = True
    need_model = True
    flag_data = True

    @staticmethod
    def apply (ns, meqmaker, ifrs, data, predict):
        residuals = ns.residuals

        for p, q in ifrs:
            residuals(p,q) << data(p,q) - predict(p,q)

        meqmaker.make_per_ifr_bookmarks (residuals, 'Uncorrected residuals')
        return residuals


class OutputCorrectedResiduals (object):
    desc = 'Corrected residuals'
    need_data = True
    need_model = True
    flag_data = True

    @staticmethod
    def apply (ns, meqmaker, ifrs, data, predict):
        residuals = ns.residuals

        for p, q in ifrs:
            residuals(p,q) << data(p,q) - predict(p,q)

        meqmaker.make_per_ifr_bookmarks (residuals, 'Uncorrected residuals')
        return meqmaker.correct_uv_data (ns, data)


output_types = [OutputCorrectedData, OutputUncorrectedResiduals,
                OutputCorrectedResiduals, OutputPredict,
                OutputDataPlusPredict]


def output_compile_options ():
    doc = """<p>This selects what sort of visibilities get
written to the output column:</p>

<ul>
<li><b>Predict</b> refers to the visibilities given by the sky model
(plus an optional uv-model column), corrupted by the current
instrumental model using the Measurement Equation specified
below.</li>

<li><b>Corrected data</b> is the input data corrected for the
instrumental model (by applying the inverse of the M.E.)</li>

<li><b>Uncorrected residuals</b> refer to input data minus
predict. This corresponds to whatever signal is left in your data that
is <b>not</b> represented by the model, and still subject to
instrumental corruptions.</li>

<li><b>Corrected residuals</b> are residuals corrected for the
instrumental model. This is what you usually want to see during
calibration.</li>

<li><b>Data+predict</b> is a special mode where the predict is
<i>added</i> to the input data. This is used for injecting synthetic
sources into your data, or for accumulating a uv-model in several
steps. (In the latter case your input column needs to be set to the
uv-model column.)</li>
</ul>

<p>If calibration is enabled above, then a calibration step is
executed prior to generating output data. This will update the
instrumental and/or sky models. If calibration is not enabled, then
the current models may still be determined by the results of past
calibration, since these are stored in persistent <i>MEP
tables.</i></p>"""

    output_option = TDLCompileOption ('output_type', 'Output visibilities',
                                      [(o, o.desc.lower ()) for o in output_types],
                                      doc=doc)
    return output_option


def flag_compile_options (mssel, output_option):
    doc = """<p>If selected, your tree will flag all visibilities (per
IFR/timeslot/channel) where the residual complex amplitude exceeds the
given value.</p>"""

    flag_res_opt = TDLOption ('flag_res', 'Flag on residual amplitudes >',
                              [None], more=float, doc=doc)

    doc = """<p>If selected, your tree will flag entire timeslots (per
channel) where the mean residual complex amplitude over all IFRs
within the timeslots exceeds the given value.</p>"""

    flag_meanres_opt = TDLOption('flag_mean_res',
                                 'Flag on mean residual amplitudes (over all IFRs) >',
                                 [None], more=float, doc=doc)

    flag_menu = TDLCompileMenu ('Flag output visibilities',
                                flag_res_opt, flag_meanres_opt, toggle='flag_enable')

    def outputchanged (output_type):
        if output_type.flag_data:
            flag_menu.show (True)
        else:
            flag_menu.show (False)

    output_option.when_changed (outputchanged)
    flag_menu.when_changed (mssel.enable_write_flags)


def meqmaker_compile_options ():
    meqmaker = MeqMaker.MeqMaker (solvable=True,
                                  use_jones_inspectors=True,
                                  use_skyjones_visualizers=False,
                                  use_decomposition=False)

    if TiggerSkyModel is not None:
        tsm = [TiggerSkyModel ()]
    else:
        tsm = []

    meqmaker.add_sky_models (tsm + [central_point_source, fitsimage_sky, gridded_sky])
    meqmaker.add_sky_jones('dE', 'differential gains',
                           [solvable_sky_jones.DiagRealImag ('dE'),
                            solvable_sky_jones.FullRealImag ('dE'),
                            solvable_sky_jones.DiagAmplPhase ('dE')])
    meqmaker.add_uv_jones ('P', 'feed orientation', [feed_angle])
    meqmaker.add_uv_jones ('B', 'bandpass', [solvable_jones.DiagRealImag ('B'),
                                             solvable_jones.FullRealImag ('B'),
                                             solvable_jones.DiagAmplPhase ('B')])
    meqmaker.add_uv_jones ('G', 'receiver gains/phases',
                           [solvable_jones.DiagRealImag ('G'),
                            solvable_jones.FullRealImag ('G'),
                            solvable_jones.DiagAmplPhase ('G')])
    meqmaker.add_vis_proc_module ('IG', 'multiplicative IFR errors',
                                  [ifr_based_errors.IfrGains ()])
    meqmaker.add_vis_proc_module ('IC', 'additive IFR errors',
                                  [ifr_based_errors.IfrBiases ()])

    TDLCompileOptions (*meqmaker.compile_options ())
    return meqmaker


def compile_options ():
    mssel = mssel_compile_options ()
    cal_compile_options (mssel)
    output_option = output_compile_options ()
    flag_compile_options (mssel, output_option)
    meqmaker = meqmaker_compile_options ()
    return mssel, meqmaker

mssel, meqmaker = compile_options ()


def _define_forest (ns, parent=None, **kw):
    if not mssel.msname:
        raise RuntimeError ('MS name not set')

    mssel.setup_observation_context (ns)
    array = Context.array

    # Data and model input

    if do_solve or output_type.need_data:
        mssel.enable_input_column (True)
        spigots = array.spigots (corr=mssel.get_corr_index ())
        meqmaker.make_per_ifr_bookmarks (spigots, 'Input visibilities')
    else:
        mssel.enable_input_column (False)
        spigots = None

    if do_solve or output_type.need_model:
        predict = meqmaker.make_predict_tree (ns, uvdata=None)
    else:
        predict = None

    # Data output

    outputs = output_type.apply (ns, meqmaker, array.ifrs (), spigots, predict)

    # Flagging

    if flag_enable and output_type.flag_data:
        flaggers = []

        if flag_res is not None or flag_mean_res is not None:
            for p, q in array.ifrs ():
                ns.absres(p,q) << Meq.Abs (outputs(p,q))

        if flag_res is not None:
            for p, q in array.ifrs ():
                ns.flagres(p,q) << Meq.ZeroFlagger (ns.absres(p,q) - flag_res,
                                                    oper='gt',
                                                    flag_bit=MSUtils.FLAGMASK_OUTPUT)
            flaggers.append (ns.flagres)
            meqmaker.make_per_ifr_bookmarks (ns.flagres, 'Residual amplitude flags')

        if flag_mean_res is not None:
            ns.meanabsres << Meq.Mean (*[ns.absres(p,q) for p, q in array.ifrs()])
            ns.flagmeanres << Meq.ZeroFlagger (ns.meanabsres - flag_mean_res,
                                               oper='gt', flag_bit=MSUtils.FLAGMASK_OUTPUT)
            Bookmarks.Page ('Mean residual amplitude flags').add (ns.flagmeanres,
                                                                  viewer='Result Plotter')
            flaggers.append (lambda p, q: ns.flagmeanres)

        if flaggers:
            meqmaker.make_per_ifr_bookmarks (outputs, output_type.desc + ' (unflagged)')
            for p, q in array.ifrs ():
                ns.flagged(p,q) << Meq.MergeFlags (outputs(p,q), *[f(p,q) for f in flaggers])
            outputs = ns.flagged

    meqmaker.make_per_ifr_bookmarks (outputs, output_type.desc)

    # Solve trees

    if do_solve:
        # parse ifr specification
        solve_ifrs = array.subset (calibrate_ifrs, strict=False).ifrs()

        if not solve_ifrs:
            raise RuntimeError ('No interferometers selected for calibration. '
                                'Check your ifr specification (under calibration options).')

        lhs, rhs, weights, modulo = cal_quant.apply (solve_ifrs, predict, spigots)
        solve_tree = StdTrees.SolveTree (ns, lhs, solve_ifrs=solve_ifrs,
                                         weights=weights, modulo=modulo)
        outputs = solve_tree.sequencers (inputs=rhs, outputs=outputs)

    StdTrees.make_sinks (ns, outputs, spigots=spigots,
                         post=meqmaker.get_inspectors () or [],
                         corr_index=mssel.get_corr_index ())

    if not do_solve:
        name = 'Generate ' + output_type.desc.lower ()
        comment = 'Generated ' + output_type.desc.lower ()

        def run_tree (mqs, parent, wait=False, **kw):
            return mqs.execute (Context.vdm.name, mssel.create_io_request (tile_size),
                                wait=wait)

        doc = """Input data are sliced by time, and processed in chunks (tiles) of
the indicated size. Larger tiles are faster, but use more memory."""

        TDLRuntimeMenu(name, TDLOption ('tile_size', 'Tile size, in timeslots',
                                        [10, 60, 120, 240], more=int, doc=doc),
                       TDLJob (run_tree, name, job_id='generate_visibilities'))

    # very important -- insert meqmaker's runtime options properly
    # this should come last, since runtime options may be built up
    # during compilation.

    TDLRuntimeOptions (*meqmaker.runtime_options (nest=False))

    if do_solve:
        TDLRuntimeOptions (*ParmGroup.get_solvejob_options ())

    imsel = mssel.imaging_selector (npix=512, arcmin=meqmaker.estimate_image_size ())
    TDLRuntimeMenu ('Make an image', *imsel.option_list ())
    meqmaker.close()
