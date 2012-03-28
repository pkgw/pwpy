## Copyright 2012 Peter Williams
## This work is dedicated to the public domain.

class AccDict (dict):
    """An accumulating dictionary.

create = lambda: <new accumulator object>
accum = lambda a, v: <accumulate v into accumulator a>

e.g.: create = list, accum = lambda l, v: l.append (v)
"""

    __slots__ = '_create _accum'.split ()

    def __init__ (self, create, accum):
        self._create = create
        self._accum = accum

    def accum (self, key, val):
        entry = self.get (key)
        if entry is None:
            self[key] = entry = self._create ()

        self._accum (entry, val)
        return self
