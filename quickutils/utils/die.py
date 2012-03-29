## Copyright 2012 Peter Williams
## This work is dedicated to the public domain.
##
def die (fmt, *args):
##<
## Raise a :exc:`SystemExit` exception with a formatted error message.
##
## :arg str format: a format string
## :arg args: arguments to the format string
##
## If *args* is empty, a :exc:`SystemExit` exception is raised with the
## argument ``'error: ' + str (fmt)``. Otherwise, the string component is
## ``fmt % args``. If uncaught, the interpreter exits with an error code
## and prints the exception argument.
##
## Example::
##
##    if ndim != 3:
##       die ('require exactly 3 dimensions, not %d', ndim)
##>
    if not len (args):
        raise SystemExit ('error: ' + str (fmt))
    raise SystemExit ('error: ' + (fmt % args))
