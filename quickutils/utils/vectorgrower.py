## Copyright 2012 Peter Williams
## This work is dedicated to the public domain.

class VectorGrower (object):
    __slots__ = 'dtype chunkSize _nextIdx _vec'.split ()

    def __init__ (self, dtype=None, chunkSize=128):
        if dtype is None:
            import numpy
            dtype = numpy.float

        self.dtype = dtype
        self.chunkSize = chunkSize
        self.clear ()


    def clear (self):
        self._nextIdx = 0
        self._vec = None
        return self


    def __len__ (self):
        return self._nextIdx


    def add (self, val):
        if self._vec is None:
            from numpy import ndarray
            self._vec = ndarray ((self.chunkSize, ), dtype=self.dtype)
        elif self._vec.size <= self._nextIdx:
            self._vec.resize ((self._vec.size + self.chunkSize, ))

        self._vec[self._nextIdx] = val
        self._nextIdx += 1
        return self


    def finish (self):
        if self._vec is None:
            from numpy import ndarray
            ret = ndarray ((0, ), dtype=self.dtype)
        else:
            self._vec.resize ((self._nextIdx, ))
            ret = self._vec

        self.clear ()
        return ret
