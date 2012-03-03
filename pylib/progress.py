"""progress - Easy progress reports during long computations.

This module provides a function, 'progress', that can be used
to print out progress reports as a specially-crafted subfunction
is executed. It also provides a decorator, 'progressive', to ease
the creation of such functions. In most cases you should only have
to use the decorator.

When the computation begins, the total number of items to process is
printed along with an optional situation-specific message. After the
first item is processed, the time elapsed, estimated time until
finish, and an optional situation-specific message are
printed. Updates are printed more and more rarely as the computation
proceeds with a minimal spacing of about one update as every 10% of
the job is completed.

A subfunction passed to 'progress' or wrapper by 'progressive' should
be a generator function. After initialization, it should yield a tuple
of (ntot, banner), where 'ntot' is the number of further items that
will be yielded and 'banner' is a user-friendly message that is
printed to the screen by default at the beginning of the
computation. If 'banner' is None, nothing is printed.

The subfunction should then yield 'ntot' more tuples of (data, msg),
where 'data' is some computed data item and 'msg' may be printed to
the screen as a status report. The last value of 'data' yielded to the
caller is considered the return value of the function. If 'msg' is
None, nothing is printed.

In the usual usage, the subfunction has to process 'ntot' items of
data in a similar way, and 'msg' gives the identifier of the data item
being processed."""


def _fmtSpan (s):
    if s < 60:
        return '%.1f s' % s
    if s < 3600:
        return '%.1f m' % (s / 60.)
    if s < 86400:
        return '%.1f h' % (s / 3600.)
    return '%.1f d' % (s / 86400.)


def progress (f, quiet=False):
    """Print progress reports as the specially-crafted function f
    runs.

    If quiet is True, no messages are printed as f is executed.

    Read the docstring of the 'progress' module for a description of
    the required behavior of 'f'. For this function, 'f' may take no
    arguments.

    If possible, you should use the 'progressive' decorator rather
    than this function."""

    import time, math

    gen = f ()

    ntot, banner = gen.next ()
    if ntot < 1:
        raise RuntimeError ('Invalid value of ntot: %s' % ntot)

    if not quiet:
        if banner is None:
            print '-> %d to do' % ntot
        else:
            print '->', banner, '(%d to do)' % ntot

    w = int (math.ceil (math.log10 (ntot)))
    n = 0
    nnext = 1
    t0 = time.time ()

    for val, msg in gen:
        n += 1

        if n != nnext or quiet:
            continue

        t = time.time ()

        if msg is None:
            msg = ''
        else:
            msg = ': ' + str (msg)

        print '  %*d (%3.0f%%, tot %s, ETA %s)%s' \
              % (w, n, 100. * n / ntot, _fmtSpan ((t - t0) * ntot / n),
                 _fmtSpan ((t - t0) * (ntot - n) / n), msg)

        if nnext <= ntot // 64:
            nnext *= 8
        else:
            nnext += ntot // 8

    if not quiet:
        print '<- Done (%s elapsed).' % (_fmtSpan (time.time () - t0))

    return val


def progressive (f):
    """Progress reports are printed as the decorated function is
    executed. The decorated function must be specially-crafted; read
    the docstring of the 'progress' module for a description of what
    is required. The decorated function may accept positional and/or
    keyword arguments. A keyword argument 'quiet', however, is handled
    by the wrapper -- it specifies whether the progress reports are
    actually printed or not."""

    import functools

    def func (*args, **kwargs):
        if 'quiet' in kwargs:
            quiet = bool (kwargs.pop ('quiet'))
        else:
            quiet = False
        return progress (lambda: f (*args, **kwargs), quiet)

    return functools.update_wrapper (func, f)
