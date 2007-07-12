# A few useful functions from numpy

import numpy

from numpy import linspace, logspace, ones, zeros, identity
from numpy import asarray, array, ndarray, hstack, vstack
from numpy import where, any, all
from numpy import sum, dot, min, max
from numpy import sin, cos, tan, sinh, cosh, tanh
from numpy import arcsin, arccos, arctan, arcsinh, arccosh, arctanh
from numpy import log, log10, exp, sqrt

def poparray (dims, func, dtype=numpy.double, **kwargs):
    """Populate a new array from the results of a function, which
    is given a set of indices as arguments. That is, if dims is
    (2, 2, 2), the resulting array will be 2x2x2, and array[i,j,k]
    will be equal to func (i, j, k)

    Arguments:

      dims - A tuple giving the dimensions of the new array
      func - The function used to populate the array

    Optional arguments:

      dtype    - The datatype of the array. Defaults to 'double'
      **kwargs - Other arguments that can be passed to the ndarray
                 constructor.

    Returns: the newly-constructed and populated array.
    """
    
    a = ndarray (dims, dtype=dtype, **kwargs)
    l = len (dims)
    idxs = [0] * l

    while True:
        t = tuple (idxs)
        a[t] = func (*t)
        
        order = l - 1

        while True:
            idxs[order] += 1

            if idxs[order] < dims[order]: break

            if order == 0: return a
            
            idxs[order] = 0
            order -= 1

