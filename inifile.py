"""A simple parser for ini-style files that's better than Python's
ConfigParser/configparser."""

__all__ = ('Holder readStream read').split ()


class Holder (object):
    def __init__ (self, **kwargs):
        self.set (**kwargs)

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

    def __str__ (self):
        d = self.__dict__
        s = sorted (d.iterkeys ())
        return '{' + ', '.join ('%s=%s' % (k, d[k]) for k in s) + '}'

    def __repr__ (self):
        d = self.__dict__
        s = sorted (d.iterkeys ())
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join ('%s=%r' % (k, d[k]) for k in s))

    def copy (self):
        new = self.__class__ ()
        new.__dict__ = dict (self.__dict__)
        return new


import re

sectionre = re.compile (r'^\[(.*)]\s*$')
keyre = re.compile (r'^(\S+)\s*=(.*)$') # leading space chomped later
escre = re.compile (r'^(\S+)\s*=\s*"(.*)"\s*$')

def readStream (stream):
    section = None
    key = None
    data = None

    for fullline in stream:
        line = fullline.split ('#', 1)[0]

        m = sectionre.match (line)
        if m is not None:
            # New section
            if section is not None:
                if key is not None:
                    section.setone (key, data.strip ().decode ('utf8'))
                    key = data = None
                yield section

            section = Holder ()
            section.section = m.group (1)
            continue

        if len (line.strip ()) == 0:
            if key is not None:
                section.setone (key, data.strip ().decode ('utf8'))
                key = data = None
            continue

        m = escre.match (fullline)
        if m is not None:
            if section is None:
                raise Exception ('key seen without section!')
            if key is not None:
                section.setone (key, data.strip ().decode ('utf8'))
            key = m.group (1)
            data = m.group (2).replace (r'\"', '"').replace (r'\n', '\n').replace (r'\\', '\\')
            section.setone (key, data.decode ('utf8'))
            key = data = None
            continue

        m = keyre.match (line)
        if m is not None:
            if section is None:
                raise Exception ('key seen without section!')
            if key is not None:
                section.setone (key, data.strip ().decode ('utf8'))
            key = m.group (1)
            data = m.group (2)
            if not data[-1].isspace ():
                data += ' '
            continue

        if line[0].isspace () and key is not None:
            data += line.strip () + ' '
            continue

        raise Exception ('unparsable line: ' + line[:-1])

    if section is not None:
        if key is not None:
            section.setone (key, data.strip ().decode ('utf8'))
        yield section


def read (stream_or_path):
    if isinstance (stream_or_path, basestring):
        return readStream (open (stream_or_path))
    return readStream (stream_or_path)
