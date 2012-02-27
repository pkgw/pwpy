def ensuredir (path, parents=False):
    """Returns a boolean indicating whether the directory already
    existed.  Will attempt to create parent directories if *parents*
    is True."""
    import os

    if parents:
        from os.path import dirname
        parent = dirname (path)
        if len (parent) and parent != path:
            ensuredir (parent, True)

    try:
        os.mkdir (path)
    except OSError, e:
        if e.errno == 17: # EEXIST
            return True
        raise
    return False
