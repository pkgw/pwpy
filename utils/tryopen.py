def tryopen (*args, **kwargs):
    """Simply a wrapper for open(), unless an IOError with errno=2 (ENOENT)
is raised, in which case None is retured."""

    try:
        return open (*args, **kwargs)
    except IOError as e:
        if e.errno == 2:
            return None
        raise
