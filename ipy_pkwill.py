""" Peter Williams' IPython user configuration.

Sets defaults the way I like them, and defines the following
magics:

%slurp
%reload
%lstore

"""

import IPython.ipapi
init_ip = IPython.ipapi.get()

import ipy_defaults    

# Options

o = init_ip.options
o.autocall = 0
o.automagic = 0
o.autoindent = 1
o.banner = False
o.confirm_exit = False
o.nosep = True
del o

# %slurp

def magic_slurp (shell, argstr):
    """Import the names from one or more modules.

    Provide slurp with a list of one or more module names. Each
    module will either be reloaded or imported, depending on if
    the module has already been imported or not. All of the symbols
    from the module are imported into the current namespace as if
    'from module import *' had been run.

    Options:
    
    -q   Suppress an informational message giving the names of the
    modules and names imported.
    """
        
    import sys

    ip = shell.getapi ()
    opts, args = shell.parse_options (argstr, 'q', mode='list')
        
    quiet = opts.has_key ('q')

    for modname in args:
        need_reload = modname in sys.modules
        
        try:
            module = __import__ (modname)
            if need_reload: module = reload (module)
        except ImportError, e:
            print ' * Failed to import or reload \'%s\': ' % modname, e
            continue

        if hasattr (module, '__all__'):
            list = module.__all__
        else:
            list = [x for x in dir (module) if x[0] != '_']

        for name in list:
            ip.user_ns[name] = getattr (module, name)

        if not quiet:
            if need_reload: verb = 'Reloaded'
            else: verb = 'Loaded'
        
            print ' * %s \'%s\' and imported: ' % (verb, modname), ', '.join (list)

init_ip.expose_magic ('slurp', magic_slurp)

# %reload

def magic_reload (shell, argstr):

    import sys

    ip = shell.getapi ()

    for modname in argstr.split (' '):
        need_reload = modname in sys.modules
        
        try:
            module = __import__ (modname)
            if need_reload: module = reload (module)
        except ImportError, e:
            print ' * Failed to import or reload \'%s\': ' % modname, e
            continue

        ip.user_ns[modname] = module

init_ip.expose_magic ('reload', magic_reload)

# %lstore - Per-directory storage.

import os, inspect, textwrap
from IPython.FakeModule import FakeModule
    
def get_local_key ():
    # Figure out our canonical PWD. HOME stuff copied from
    # os.path.expanduser from python 2.4.
        
    pwd = os.path.realpath (os.path.curdir)
        
    homedir = os.environ.get ('HOME')
    if homedir is None:
        import pwd
        homedir = pwd.getpwuid (os.getuid ()).pw_dir
    homedir = os.path.realpath (homedir)
        
    if pwd.startswith (homedir):
        pwd = '~' + pwd[len(homedir):]

    dbprefix = 'lstore/' + pwd

    if dbprefix[-1] != '/': dbprefix += '/'
        
    return pwd, dbprefix
    
def reload_local_vars (ip, db, verbose=False):
    import sys

    pwd, dbprefix = get_local_key ()
    skeys = []
        
    for key in db.keys (dbprefix + '*'):
        k = key[key.rindex ('/') + 1:]
        skeys.append (k)
            
        try:
            obj = db[key]
        except KeyError:
            print 'Unable to restore variable "%s" stored for "%s"' % (k, pwd)
            print 'Use "%%lstore -d %s" to forget this variable.' % k
            print 'The error was:', sys.exc_info()[0]
        else:
            ip.user_ns[k] = obj

    if len (skeys) > 0:
        print 'Restored for "%s":' % pwd, ', '.join (skeys)
    elif verbose:
        print 'No variables to restore for "%s"' % pwd

def reload_local_hook (shell):
    ip = shell.getapi ()
    db = ip.get_db ()
    reload_local_vars (ip, db)
    raise IPython.ipapi.TryNext # ??? copied from %store
    
init_ip.set_hook ('late_startup_hook', reload_local_hook)
    
def magic_lstore (self, param_s=''):
    """Per-directory persistence of Python variables along the lines
    of the %store magic.
    
    %lstore <vars...>     - Store the named variables.
    %lstore               - Print names and values of all variables
                            stored for this directory.
    %lstore -d <vars...>  - Forget the named variables.
    %lstore -r            - Reload all variables for this directory.
    %lstore -z            - Forget all variables for this directory.

    Upon initialization, locally stored variables will be recovered,
    and their names will be printed.
    """

    import sys

    opts, args = self.parse_options (param_s, 'drz', mode='list')
    ip = self.getapi ()
    db = ip.get_db ()

    dodel = opts.has_key ('d')
    dozap = opts.has_key ('z')
    dorel = opts.has_key ('r')

    if dodel + dozap + dorel > 1:
        print 'Error: Can only specify one of the -d, -r, and -z options.'
        return
    
    pwd, dbprefix = get_local_key ()

    # Ok. Now do stuff. Copied from magic_store, basically.
        
    if dodel:
        # Delete
        if len (args) < 1:
            print 'Error: You must specify the variable to forget.'
            return
        
        for todel in args:
            try: del db[dbprefix + todel]
            except: print 'Error: Can\'t delete variable "%s":' % todel, \
                    sys.exc_info ()[0]
    elif dozap:
        # Kill all vars
        if len (args) != 0:
            print 'Error: %lstore -z takes no arguments.'
            return
        
        for k in db.keys (dbprefix + '*'):
            del db[k]
    elif dorel:
        # Reload
        if len (args) != 0:
            print 'Error: %lstore -r takes no arguments.'
            return
        
        reload_local_vars (ip, db, True)
    elif not args:
        # List stored vars
        v = db.keys (dbprefix + '*')
        v.sort ()

        if not v:
            print 'There are no variables stored for "%s".' % pwd
            return
        
        size = max ((len (x) for x in v))

        print 'Stored variables for "%s":' % pwd
        fmt = '%-' + str (size) + 's -> %s'

        for var in v:
            k = var[var.rindex ('/') + 1:]
            print fmt % (k, repr (db.get (var, '<unavailable>'))[:50])
    else:
        # Store variables.
        stored = []
        
        for a in args:
            try:
                obj = ip.user_ns[a]
            except KeyError:
                print 'Error: unknown variable "%s" (aliases not supported)' % a
            else:
                if isinstance (inspect.getmodule (obj), FakeModule):
                    print textwrap.dedent ("""\
                    Warning: can't store "%s" (= %s)
                
                    Proper storage of interactively declared classes (or instances
                    of those classes) is not possible! Only instances of classes
                    in real modules on the filesystem can be %%lstore'd. Sorry.
                    """ % (a, obj))
                else:
                    self.db[dbprefix + a] = obj
                    stored.append ((a, obj))

        if len (stored) < 1:
            print 'Couldn\'t store any variables!'
        else:
            descs = ('%s (%s)' % (a, o.__class__.__name__) for (a, o) in stored)
            print 'Stored in "%s":' % pwd, ', '.join (descs)

init_ip.expose_magic ('lstore', magic_lstore)
