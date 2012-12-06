# Copyright 2012 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""casautil - utilities for using the CASA Python libraries
"""

__all__ = ('INVERSE_C_MS INVERSE_C_MNS pol_names pol_to_miriad msselect_keys '
           'logger tools').split ()


# Some constants that can be useful

INVERSE_C_MS  = 3.3356409519815204e-09 # inverse speed of light in m/s
INVERSE_C_MNS = 3.3356409519815204 # inverse speed of light in m/ns

pol_names = {
    0: '?',
    1: 'I', 2: 'Q', 3: 'U', 4: 'V',
    5: 'RR', 6: 'RL', 7: 'LR', 8: 'LL',
    9: 'XX', 10: 'XY', 11: 'YX', 12: 'YY',
    13: 'RX', 14: 'RY', 15: 'LX', 16: 'LY',
    17: 'XR', 18: 'XL', 19: 'YR', 20: 'YL',
    21: 'PP', 22: 'PQ', 23: 'QP', 24: 'QQ',
    25: 'RCirc', 26: 'Lcirc', 27: 'Lin', 28: 'Ptot', 29: 'Plin',
    30: 'PFtot', 31: 'PFlin', 32: 'Pang',
}

pol_to_miriad = {
    # see mirtask.util for the MIRIAD magic numbers.
    1: 1, 2: 2, 3: 3, 4: 4, # IQUV
    5: -1, 6: -3, 7: -4, 8: -2, # R/L
    9: -5, 10: -7, 11: -8, 12: -6, # X/Y
    # rest are inexpressible
}

# "polarization" is technically valid, but it pretty much doesn't do
# what you'd want since records generally contain multiple
# pols. ms.selectpolarization() should be used instead. Maybe ditto
# for spw?
msselect_keys = frozenset ('array baseline field observation '
                           'scan scaninent spw taql time uvdist'.split ())


# Trying to use the logging facility in a sane way.
#
# As soon as you create a logsink, it creates a file called casapy.log.
# So we do some junk to not leave turds all around the filesystem.

def _rmtree_error (func, path, excinfo):
    import sys
    print >>sys.stderr, 'warning: couldn\'t delete temporary file %s: %s (%s)' \
        % (path, excinfo[0], func)


def logger (filter='WARN'):
    import os, shutil, tempfile

    cwd = os.getcwd ()
    tempdir = None

    try:
        tempdir = tempfile.mkdtemp (prefix='casautil')

        try:
            os.chdir (tempdir)
            sink = tools.logsink ()
            sink.setlogfile (os.devnull)
            os.unlink ('casapy.log')
        finally:
            os.chdir (cwd)
    finally:
        if tempdir is not None:
            shutil.rmtree (tempdir, onerror=_rmtree_error)

    sink.showconsole (True)
    sink.setglobal (True)
    sink.filter (filter)
    return sink


# Tool factories.

class _Tools (object):
    """This class is structured so that it supports useful tab-completion
    interactively, but also so that new tools can be constructed if the
    underlying library provides them."""

    _builtinNames = ('agentflagger atmosphere calanalysis calibrater calplot componentlist '
                     'coordsys deconvolver fitter flagger functional image imagepol '
                     'imager logsink measures msmetadata ms msplot plotms regionmanager '
                     'simulator spectralline quanta table tableplot utils vlafiller '
                     'vpmanager').split ()

    def __getattribute__ (self, n):
        """Returns factories, not instances."""
        # We need to make this __getattribute__, not __getattr__, only because
        # we set the builtin names in the class __dict__ to enable tab-completion.
        import casac

        if hasattr (casac, 'casac'): # casapy >= 4.0?
            t = getattr (casac.casac, n, None)
            if t is None:
                raise AttributeError ('tool "%s" not present' % n)
            return t
        else:
            try:
                return casac.homefinder.find_home_by_name (n + 'Home').create
            except Exception:
                # raised exception is class 'homefinder.error'; it appears unavailable
                # on the Python layer
                raise AttributeError ('tool "%s" not present' % n)

for n in _Tools._builtinNames:
    setattr (_Tools, n, None) # ease autocompletion

tools = _Tools ()
