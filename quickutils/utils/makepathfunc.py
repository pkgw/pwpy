## Copyright 2012 Peter Williams
## This work is dedicated to the public domain.

def makepathfunc (base):
    """Return a function that joins paths onto some base directory."""
    from os.path import join

    def pathfunc (*args):
        return join (base, *args)

    return pathfunc
