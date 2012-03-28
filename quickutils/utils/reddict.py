## Copyright 2012 Peter Williams
## This work is dedicated to the public domain.

class RedDict (dict):
    """A reducing dictionary.

nothingEquiv = the null value
reducefn = lambda cur, new: <reduction of cur and new>

E.g.: nothingEquiv = 0, reducefn = operator.add
"""

    __slots__ = '_nothingEquiv _reduce'.split ()

    def __init__ (self, nothingEquiv, reducefn):
        self._nothingEquiv = nothingEquiv
        self._reduce = reducefn

    def reduce (self, key, val):
        prev = self.get (key)
        if prev is None:
            prev = self._nothingEquiv

        self[key] = self._reduce (prev, val)
        return self

    def rget (self, key):
        return self.get (key, self._nothingEquiv)
