## Copyright 2012 Peter Williams
## This work is dedicated to the public domain.

try:
    from awff import MultiprocessMake
    from arf.visutil import propagateHeaders
except ImportError:
    pass
else:
    __all__ += ['asMake']

    def _asmake (context, vis=None, params=None):
        params = dict (params) # copy so we don't modify:
        naver = params.pop ('naver', 0)

        context.ensureParent ()
        out = VisData (context.fullpath ())
        out.delete ()

        channelAverageWithSetup (vis, out, naver, **params)
        propagateHeaders (vis, out)
        return out

    asMake = MultiprocessMake ('vis params', 'out', _asmake,
                               [None, {}])
