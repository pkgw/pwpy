## Copyright 2014 Peter Williams
## This work is dedicated to the public domain.
##
def reraise_context (fmt, *args):
##<
## Reraise an exception with its message modified to specify additional context.
##>
    import sys
    if len (args):
        cstr = fmt % args
    else:
        cstr = str (fmt)
    ex = sys.exc_info ()[1]
    if len (ex.args):
        cstr = '%s: %s' % (cstr, ex.args[0])
    ex.args = (cstr, ) + ex.args[1:]
    raise
