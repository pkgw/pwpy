class WeightAccumulator (object):
    """Standard statistical weighting is wt_i = sigma_i**-2. We don't
need the 'n' variable to do any stats, but it can be nice to have that
information."""

    __slots__ = 'xwtot wtot n _shape'.split ()

    def __init__ (self, shape=None):
        self._shape = shape
        self.clear ()

    def clear (self):
        if self._shape is None:
            self.xwtot = 0.
            self.wtot = 0.
        else:
            from numpy import zeros
            self.xwtot = zeros (self._shape)
            self.wtot = zeros (self._shape)

        self.n = 0
        return self

    def add (self, x, wt):
        self.xwtot += x * wt
        self.wtot += wt
        self.n += 1
        return self

    def num (self):
        return self.n

    def wtavg (self, nullval):
        if self._shape is None:
            if self.wtot == 0:
                return nullval
            return self.xwtot / self.wtot

        # Vectorized case. Trickier.
        zerowt = (self.wtot == 0)
        if not zerowt.any ():
            return self.xwtot / self.wtot

        from numpy import putmask
        weff = self.wtot.copy ()
        putmask (weff, zerowt, 1)
        result = self.xwtot / weff
        putmask (result, zerowt, nullval)
        return result

    def var (self):
        """Assumes wt_i = sigma_i**-2"""
        return 1. / self.wtot

    def std (self):
        """Uncertainty of the mean (i.e., scales as ~1/sqrt(n_vals))"""
        if self._shape is None:
            from math import sqrt
        else:
            from numpy import sqrt
        return sqrt (self.var ())
