## Copyright 2012 Peter Williams
## This work is dedicated to the public domain.
##
def ensureiterable (value):
##<
## Return an iterable version of *value*. If *value* is an instance of
## basestring, it is treated as non-iterable and wrapped. (I've
## decided that basestring should never have been made iterable;
## instead it should have had a .chars() that returned an iterable
## version.)
##>
    if isinstance (value, basestring):
        return (value, )
    try:
        iter (value)
        return value
    except TypeError:
        return (value, )
