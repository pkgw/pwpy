## Copyright 2012 Peter Williams
## This work is dedicated to the public domain.

class Holder (object):
    def __init__ (self, **kwargs):
        self.set (**kwargs)


    def __str__ (self):
        d = self.__dict__
        s = sorted (d.iterkeys ())
        return '{' + ', '.join ('%s=%s' % (k, d[k]) for k in s) + '}'


    def __repr__ (self):
        d = self.__dict__
        s = sorted (d.iterkeys ())
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join ('%s=%r' % (k, d[k]) for k in s))

    def set (self, **kwargs):
        for name, value in kwargs.iteritems ():
            self.__dict__[name] = value
        return self


    def get (self, name, defval=None):
        return self.__dict__.get (name, defval)


    def setone (self, name, value):
        self.__dict__[name] = value
        return self


    def has (self, name):
        return name in self.__dict__


    def copy (self):
        new = self.__class__ ()
        new.__dict__ = dict (self.__dict__)
        return new
