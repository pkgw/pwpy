## Copyright 2012 Peter Williams
## This work is dedicated to the public domain.
def popoption (ident, argv=None):
##<
## A lame routine for grabbing command-line arguments. Returns a
## boolean indicating whether the option was present. If it was, it's
## removed from the argument string. Because of the lame behavior,
## options can't be combined, and non-boolean options aren't
## supported. Operates on sys.argv by default.
##
## Note that this will proceed merrily if argv[0] matches your option.
##>
    if argv is None:
        from sys import argv
    if len (ident) == 1:
        ident = '-' + ident
    else:
        ident = '--' + ident
    found = ident in argv
    if found:
        argv.remove (ident)
    return found
