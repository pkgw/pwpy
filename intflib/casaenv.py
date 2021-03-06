# Copyright 2012 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""casaenv - provide standard names from the casapy interactive environment

We're basically copying the definitions in casapy.py without all of
the bells and whistles. There's also some moderately aggressive
curation happening.
"""

# Misc constants.

true = T = True
false = F = False
__all__ = 'true T false F'.split ()


# matplotlib

def _setup_matplotlib ():
    import matplotlib, os

    if matplotlib.get_backend () == 'MacOSX':
        matplotlib.use ('TkAgg')
    if 'DISPLAY' not in os.environ and matplotlib.get_backend () == 'TkAgg':
        matplotlib.use ('Agg')

_setup_matplotlib ()


# the taskinit module.
#
# taskinit wants a dictionary named "casa" with various init info, and
# it finds it in an evil way. Fortunately it is easy to outsmart.

def _setup_casadict ():
    import os.path, platform, sys, casadef

    if 'CASAPATH' in os.environ:
        cp = os.environ['CASAPATH'].split ()[0]
    else:
        cp = casac.__file__

        while len (cp) and cp != '/':
            if os.path.isdir (os.path.join (cp, 'data')):
                break
            cp = os.path.dirname (cp)
        else:
            raise RuntimeError ('cannot determine CASA root path')

        if sys.platform == 'darwin':
            casaplatform = 'darwin'
        elif sys.platform.startswith ('linux'):
            if platform.architecture ()[0] == '64bit':
                casaplatform = 'linux_64b'
            else:
                casaplatform = 'linux_gnu'
        else:
            raise RuntimeError ('unknown platform ' + sys.platform)

        # ASAP stuff relies on the environment variable and gets invoked
        # when we import tasks, so set it.
        os.environ['CASAPATH'] = cp + ' ' + casaplatform

    return {
        'build': dict (time=casadef.build_time, version=casadef.casa_version,
                       number=casadef.subversion_revision),
        'source': dict (url=casadef.subversion_url, revision=casadef.subversion_revision),
        'helpers': {},
        'dirs': dict (rc=os.path.expanduser ('~/.casa'),
                      root=cp, data=os.path.join (cp, 'data'),
                      recipes=os.path.join (casadef.python_library_directory, 'recipes')),
        'flags': {},
        'files': dict (logfile=None),
        'state': dict (startup=True),
    }

import taskinit
taskinit.casa = _setup_casadict ()
from taskinit import *
_taskinit_badnames = frozenset ('announce_async_task array2string casa casaglobals '
                                'defaultsdir inspect os recursivermdir string sys '
                                'write_history write_task_obit'.split ())
__all__ += [n for n in dir (taskinit)
            if n[0] != '_' and n not in _taskinit_badnames]


# names from math

import math
from math import *
__all__ += [n for n in dir (math) if n[0] != '_']


# tasks module and its names. The "taskmanager" module, imported by
# tasks, tries to launch the programs "ipcontroller" and "ipengine",
# and I see no way to trick it into not doing that. They may not be in
# $PATH in which case we crash. taskmanager tries to allow
# customization of the paths to these programs, but it uses gross
# logic to search the stack for the 'casa' dict, and that won't work
# for us. So we need to futz with $PATH. We'll be running in the CASA
# version of the Python interpreter, and the needed programs will be
# distributed with it. If we make sure that the directory containing
# the current Python interpreter is in $PATH, we should be OK.
#
# We could avoid some of this rigamarole if we imported tasks as the
# task_foo modules rather than the foo_cli modules. (To do this,
# rather than slurping tasks.py, we'd have to get the list of tasks
# ourselves. We could find tasks.py and parse it ...) This would also
# avoid the heinous _setup_toplevel_hooks() stuff below. On the other
# hand, the task_foo functions have the problem of assuming that their
# keyword parameters are not None even though that's the default for
# all of them. The defaults are embedded in the foo_cli modules but it
# seems impractical to extract them in any reasonable way.
#
# Or we could parse the task definition XML files in share/xml/...

def _setup_exepath ():
    import sys, os.path

    path = os.environ['PATH'].split (':')
    pydir = os.path.dirname (sys.executable)

    if pydir not in path:
        path.append (pydir)
        os.environ['PATH'] = ':'.join (path)

_setup_exepath ()

import tasks
from tasks import *
_tasks_badnames = frozenset ('allcat category deprecated experimental inspect key '
                             'mytasks odict os pdb string sys tget tget_check_params '
                             'tget_defaults tget_description thecats'.split ())
__all__ += [n for n in dir (tasks) if n[0] != '_' and n not in _tasks_badnames]


# When tasks are invoked as Python functions, they reach up into the
# top stack frame and call functions called update_params and
# saveinputs. Because you know what would be unreasonable about that?

def _setup_toplevel_hooks ():
    def dummy_function (*args, **kwargs):
        pass

    import sys, inspect
    top = len (inspect.stack ()) - 1
    topglobals = sys._getframe (top).f_globals
    topglobals['update_params'] = dummy_function
    topglobals['saveinputs'] = dummy_function

_setup_toplevel_hooks ()


# wrap up. I don't know if this 'startup' flag changes anything we care about.

taskinit.casa['state']['startup'] = False
# __all__.sort () # for testing
