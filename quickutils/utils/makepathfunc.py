def makepathfunc (base):
    """Return a function that joins paths onto some base directory."""
    from os.path import join

    def pathfunc (*args):
        return join (base, *args)

    return pathfunc
