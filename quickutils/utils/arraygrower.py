class ArrayGrower (object):
    __slots__ = 'dtype ncols chunkSize _nextIdx _arr'.split ()

    def __init__ (self, ncols, dtype=None, chunkSize=128):
        if dtype is None:
            import numpy as np
            dtype = np.float

        self.dtype = dtype
        self.ncols = ncols
        self.chunkSize = chunkSize
        self.clear ()


    def clear (self):
        self._nextIdx = 0
        self._arr = None
        return self


    def __len__ (self):
        return self._nextIdx


    def addLine (self, line):
        from numpy import asarray, ndarray

        line = asarray (line, dtype=self.dtype)
        if line.size != self.ncols:
            raise ValueError ('line is wrong size')

        if self._arr is None:
            self._arr = ndarray ((self.chunkSize, self.ncols),
                                 dtype=self.dtype)
        elif self._arr.shape[0] <= self._nextIdx:
            self._arr.resize ((self._arr.shape[0] + self.chunkSize,
                               self.ncols))

        self._arr[self._nextIdx] = line
        self._nextIdx += 1
        return self


    def add (self, *args):
        self.addLine (args)
        return self


    def finish (self):
        if self._arr is None:
            from numpy import ndarray
            ret = ndarray ((0, self.ncols), dtype=self.dtype)
        else:
            self._arr.resize ((self._nextIdx, self.ncols))
            ret = self._arr

        self.clear ()
        return ret
