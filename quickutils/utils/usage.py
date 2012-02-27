def showusage (docstring):
    """Print program usage information and exit.

:arg str docstring: the program help text

This function just prints *docstring* and exits. In most cases, the
function :func:`checkusage` should be used: it automatically checks
:data:`sys.argv` for a sole "-h" or "--help" argument and invokes this
function.

This function is provided in case there are instances where the user
should get a friendly usage message that :func:`checkusage` doesn't
catch. It can be contrasted with :func:`wrongusage`, which prints a
terser usage message and exits with an error code.
"""
    print docstring.strip ()
    raise SystemExit (0)


def checkusage (docstring, argv=None, usageifnoargs=False):
    """Check if the program has been run with a --help argument; if so,
print usage information and exit.

:arg str docstring: the program help text
:arg argv: the program arguments; taken as :data:`sys.argv` if
  given as :const:`None` (the default). (Note that this implies
  ``argv[0]`` should be the program name and not the first option.)
:arg bool usageifnoargs: if :const:`True`, usage information will be
  printed and the program will exit if no command-line arguments are
  passed. Default is :const:`False`.

This function is intended for small programs launched from the command
line. The intention is for the program help information to be written
in its docstring, and then for the preamble to contain something
like::

  \"\"\"myprogram - this is all the usage help you get\"\"\"
  import sys
  ... # other setup
  checkusage (__doc__)
  ... # go on with business

If it is determined that usage information should be shown,
:func:`showusage` is called and the program exits.

See also :func:`wrongusage`.
"""

    if argv is None:
        from sys import argv

    if len (argv) == 1 and usageifnoargs:
        showusage (docstring)

    if len (argv) == 2 and argv[1] in ('-h', '--help'):
        showusage (docstring)


def wrongusage (docstring, *rest):
    """Print a message indicating invalid command-line arguments and
exit with an error code.

:arg str docstring: the program help text
:arg rest: an optional specific error message

This function is intended for small programs launched from the command
line. The intention is for the program help information to be written
in its docstring, and then for argument checking to look something
like this::

  \"\"\"mytask <input> <output>

  Do something to the input to create the output.
  \"\"\"
  ...
  import sys
  ... # other setup
  checkusage (__doc__)
  ... # more setup
  if len (sys.argv) != 3:
     wrongusage (__doc__, "expect exactly 2 arguments, not %d",
                 len (sys.argv))

When called, an error message is printed along with the *first stanza*
of *docstring*. The program then exits with an error code and a
suggestion to run the program with a --help argument to see more
detailed usage information. The "first stanza" of *docstring* is
defined as everything up until the first blank line, ignoring any
leading blank lines.

The optional message in *rest* is treated as follows. If *rest* is
empty, the error message "invalid command-line arguments" is
printed. If it is a single item, the stringification of that item is
printed. If it is more than one item, the first item is treated as a
format string, and it is percent-formatted with the remaining
values. See the above example.

See also :func:`checkusage` and :func:`showusage`.
"""

    import sys
    intext = False

    if len (rest) == 0:
        detail = 'invalid command-line arguments'
    elif len (rest) == 1:
        detail = rest[0]
    else:
        detail = rest[0] % tuple (rest[1:])

    print >>sys.stderr, 'error:', detail
    print >>sys.stderr

    for l in docstring.splitlines ():
        if intext:
            if not len (l):
                break
            print >>sys.stderr, l
        elif len (l):
            intext = True
            print >>sys.stderr, 'Usage:', l
    print >>sys.stderr

    print >>sys.stderr, \
        'Run with a sole argument --help for more detailed usage information.'
    raise SystemExit (1)
