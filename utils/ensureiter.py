def ensureiterable (value):
    """Return an iterable version of *value*. If *value* is an instance of
basestring, it is treated as non-iterable and wrapped."""

    if isinstance (value, basestring):
        return (value, )

    try:
        iter (value)
        return value
    except TypeError:
        return (value, )
