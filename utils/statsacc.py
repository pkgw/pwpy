class StatsAccumulator (object):
    # FIXME: I worry about loss of precision when n gets very large:
    # we'll be adding a tiny number to a large number.  We could
    # periodically rebalance or something. I'll think about it more if
    # it's ever actually a problem.

    __slots__ = 'xtot xsqtot n _shape'.split ()

    def __init__ (self, shape=None):
        self._shape = shape
        self.clear ()

    def clear (self):
        if self._shape is None:
            self.xtot = 0.
            self.xsqtot = 0.
        else:
            from numpy import zeros
            self.xtot = zeros (self.shape)
            self.xsqtot = zeros (self.shape)

        self.n = 0
        return self

    def add (self, x):
        if self._shape is not None:
            from numpy import asarray
            x = asarray (x)
            if x.shape != self._shape:
                raise ValueError ('x has wrong shape')

        self.xtot += x
        self.xsqtot += x**2
        self.n += 1
        return self

    def num (self):
        return self.n

    def mean (self):
        return self.xtot / self.n

    def rms (self):
        if self._shape is None:
            from math import sqrt
        else:
            from numpy import sqrt
        return sqrt (self.xsqtot / self.n)

    def std (self):
        if self._shape is None:
            from math import sqrt
        else:
            from numpy import sqrt
        return sqrt (self.var ())

    def var (self):
        return self.xsqtot/self.n - (self.xtot/self.n)**2
