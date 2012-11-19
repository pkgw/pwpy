# Copyright 2012 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""flatdb - a very quick flat-text database

Implementing your own database is stupid, so if this turns out
to be a lot of work to get right, I'm doing something wrong.
"""

__all__ = ('Holder Column Mapping readtable writetable '
           'FlatDBError PadError ParseError').split ()


class Holder (object):
    def __init__ (self, **kwargs):
        self.__dict__.update (kwargs)

    def __str__ (self):
        d = self.__dict__
        s = sorted (d.iterkeys ())
        return '{' + ', '.join ('%s=%s' % (k, d[k]) for k in s) + '}'

    def __repr__ (self):
        d = self.__dict__
        s = sorted (d.iterkeys ())
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join ('%s=%r' % (k, d[k]) for k in s))


# Columns and Mappings -- define how we map between the
# textual data and Python objects

MAX_COL_WIDTH = 512

_forbidden_colnames = frozenset (['recno'])

_kind_to_code = {
    int: 'i',
    float: 'f',
    str: 's',
    bool: 'b',
    object: 'g', # generic
}

_code_to_kind = {
    'i': int,
    'f': float,
    's': str,
    'b': bool,
    'g': object,
    # compat with older style:
    '0': int,
    '1': float,
    '2': str,
    '3': bool,
    '4': object,
}

class Column (Holder):
    name = None
    width = None
    parse = None
    format = None
    kind = None

    def _fixup (self):
        if len (self.name) > W_HEADER_NAME:
            raise ValueError ('column name "%s" is too long' % self.name)
        if self.name in _forbidden_colnames:
            raise ValueError ('column name "%s" is forbidden' % self.name)
        assert self.width > 0 and self.width < 512
        assert self.kind in _kind_to_code

        if self.format is None and self.kind in _builtin_formatters:
            self.format = _builtin_formatters[self.kind]
        if self.parse is None and self.kind in _builtin_parsers:
            self.parse = _builtin_parsers[self.kind]


    def clone (self, **overrides):
        other = self.__class__ (**self.__dict__)
        other.__dict__.update (overrides)
        return other


def _make_scaled_float_parser (scale):
    def f (s):
        if not len (s):
            return None
        return float (s) * scale
    return f


def _make_scaled_float_formatter (scale, fmt):
    def f (v):
        if v is None:
            return ''
        return fmt % (v / scale)
    return f


class Mapping (object):
    columns = None

    def __init__ (self):
        self.columns = {}


    def add (self, name, kind, width, existingok=False, **rest):
        assert name not in _forbidden_colnames
        assert len (name) <= W_HEADER_NAME
        assert kind in _kind_to_code
        assert width > 0
        assert width < MAX_COL_WIDTH

        if not existingok and name in self.columns:
            raise FlatDBError ('column "%s" is already defined' % name,
                               name=name)

        self.columns[name] = Column (name=name, width=width,
                                     kind=kind, **rest)
        return self


    def addfloat (self, name, fmt, width, scale=1, existingok=False):
        """The scale is from textual units to Python units. If text
        values are arcsec and Python values are radians, scale should
        be A2R = 1/206265."""

        assert name not in _forbidden_colnames
        assert len (name) <= W_HEADER_NAME
        assert width > 0
        assert width < MAX_COL_WIDTH

        if not existingok and name in self.columns:
            raise FlatDBError ('column "%s" is already defined' % name,
                               name=name)

        parse = _make_scaled_float_parser (scale)
        format = _make_scaled_float_formatter (scale, fmt)
        self.columns[name] = Column (name=name, width=width,
                                     kind=float, parse=parse,
                                     format=format)
        return self


    def include (self, othermapping):
        """Note: doesn't care if columns are overridden."""
        self.columns.update (othermapping.columns)


    def cols (self, *colnames):
        seencols = set ()

        for item in colnames:
            if isinstance (item, basestring):
                subnames = item.split ()
            else:
                subnames = item

            for name in subnames:
                if name not in seencols:
                    seencols.add (name)
                    yield self.columns[name]


# The actual I/O: reading and writing tables

W_HEADER_INT = 7
W_HEADER_NAME = 15

def readtable (source, mapping=None, recfactory=Holder):
    """Read a flat table from a stream without seeking. Generates a
stream of records.

    source: a file-like read() method equivalent, an object with a
            read method, or a path
   mapping: a mapping object defining the columns that may be present
            in the table, or None. Unrecognized columns with a basic
            type are handled automatically.
recfactory: factory for "record" objects; one attr set for each column

   Returns: (headers, cols, recs), where headers is list of header strings,
            cols is the list of columns defined in the table, and recs is
            a generator of record data.
"""

    if callable (source):
        read = source
    elif hasattr (source, 'read') and callable (source.read):
        read = source.read
    elif isinstance (source, basestring):
        read = open (source).read
    else:
        raise ValueError ('don\'t know what to do with "source"')

    # Read preamble

    ncols = int (unpad (read (W_HEADER_INT)))
    read (1) # separator
    ciofs = int (unpad (read (W_HEADER_INT)))
    read (1) # separator
    dofs = int (unpad (read (W_HEADER_INT)))
    read (1) # newline
    curofs = W_HEADER_INT * 3 + 3

    assert ncols > 0 and ncols < 128, 'invalid ncols'
    assert ciofs >= curofs and ciofs < 32768, 'invalid colinfo offset for streaming'

    # Read headers

    if ciofs == curofs:
        headers = []
    else:
        headers = read (ciofs - curofs).splitlines ()
        curofs = ciofs

    # Read column info. We do things in a little bit of a weird way
    # here to avoid mutating the Mapping and the Column objects it
    # contains. ckind is of width W_HEADER_INT for historical reasons.

    recsz = ncols + 1 # ncols delimiters, \n
    cols = []

    for i in xrange (ncols):
        name = unpad (read (W_HEADER_NAME))
        read (1) # sep
        width = int (unpad (read (W_HEADER_INT)))
        read (1) # sep
        kind = _code_to_kind[unpad (read (W_HEADER_INT))]
        read (1) # sep
        curofs += W_HEADER_NAME + W_HEADER_INT * 2 + 3

        if mapping is None:
            col = None
        else:
            col = mapping.columns.get (name)

        if col is None:
            col = Column (name=name, width=width, kind=kind)
        else:
            col = col.clone (width=width) # avoid mutating original
            if col.kind != kind:
                raise Exception ('disagreeing column kinds in DB and mapping:'
                                 ' expected %s, found %s' % (col.kind, kind))

        col._fixup ()

        if col.parse is None:
            raise Exception ('no parser for column %s' % col.name)

        recsz += width
        cols.append (col)

    assert dofs >= curofs, 'too small data offset for streaming'
    assert dofs - curofs < 32768, 'too large data offset for streaming'

    # Read data

    read (dofs - curofs) # move to data

    def getrecords ():
        recno = -1

        while True:
            recno += 1
            s = read (recsz)

            if not len (s):
                break

            rec = recfactory ()
            rec.recno = recno

            i = 0

            try:
                for col in cols:
                    v = unpad (s[i:i + col.width])
                    if v == '':
                        v = None
                    else:
                        v = col.parse (v)

                    setattr (rec, col.name, v)
                    i += col.width + 1
            except FlatDBError:
                raise
            except Exception, e:
                raise ParseError ('exception while parsing value "%s" of row %d in '
                                  'column %s: %s (%s)', s[i:i+col.width], recno,
                                  col.name, e, e.__class__.__name__, recno=recno,
                                  colname=col.name, value=s[i:i+col.width],
                                  subexc=e)

            yield rec

    return headers, cols, getrecords ()


def writetable (dest, headers, cols, recs):
    """Write a table without seeking.

   dest: a file-like write() method equivalent, an object with a write()
         method, or a file path that will be opened in 'w' mode with
         line buffering.
headers: iterable of strings, lines of header data
   cols: iterable of columns
   recs: iterable of record-type objects; assumed to have a
         property matching each column name
"""

    if callable (dest):
        write = dest
    elif hasattr (dest, 'write') and callable (dest.write):
        write = dest.write
    elif isinstance (dest, basestring):
        write = open (dest, 'w', 1).write
    else:
        raise ValueError ('don\'t know what to do with "dest"')

    # Some setup

    if not len (headers):
        headerdata = ''
    else:
        headerdata = '\n'.join (str (h) for h in headers) + '\n'

    cols = list (cols)
    ncols = len (cols)

    for col in cols:
        col._fixup ()
        assert callable (col.format)

    ciofs = W_HEADER_INT * 3 + 3 + len (headerdata)
    dofs = ciofs + 1 + ncols * (W_HEADER_NAME + W_HEADER_INT * 2 + 3)

    # And this is all pretty straightforward:

    write (pad (ncols, W_HEADER_INT, True) + '|')
    write (pad (ciofs, W_HEADER_INT, True) + '|')
    write (pad (dofs, W_HEADER_INT, True) + '\n')
    write (headerdata)

    for col in cols:
        write (pad (col.name, W_HEADER_NAME) + '/')
        write (pad (col.width, W_HEADER_INT, True) + '/')
        write (pad (_kind_to_code[col.kind], W_HEADER_INT, True) + '|')

    write ('\n')

    try:
        for rec in recs:
            for col in cols:
                write (pad (col.format (getattr (rec, col.name)), col.width))
                write ('|')
            write ('\n')
    except PadError, e:
        raise Exception ('formatting fail in column %s for %s: %s' %
                         (col.name, rec, e))


# Parsing and formatting utilities

def _p_bool (v):
    if v in '+TY':
        return True
    if v in '.FN':
        return False
    raise ParseError ('illegal text for boolean: must be one of "+.TFYN"',
                      value=v)

_builtin_parsers = {
    int: int,
    float: float,
    str: lambda x: x,
    bool: _p_bool,
    }


def _f_bool (v):
    if v:
        return '+'
    return '.'


def _f_stringable (v):
    if v is None:
        return ''
    return str (v)


def _f_float (v):
    if v is None:
        return ''
    return '%e' % v


_builtin_formatters = {
    int: _f_stringable,
    float: _f_float,
    str: lambda x: x,
    bool: _f_bool,
    }


# Text helpers

class FlatDBError (Exception):
    def __init__ (self, fmt, *args, **kwargs):
        self.themsg = fmt % args
        self.__dict__.update (kwargs)

    def __str__ (self):
        return self.themsg


class PadError (FlatDBError):
    text = None
    width = None


class ParseError (FlatDBError):
    recno = None
    colname = None
    value = None
    subexc = None


def pad (s, width, mkstr=False):
    if s is None:
        s = ''

    if not isinstance (s, basestring) and mkstr:
        s = str (s)

    if len (s) > width:
        raise PadError ('string too wide for its column: %s', s, text=s, width=width)
    if len (s) and s[-1] == ' ':
        raise PadError ('string not safely paddable: >%s<', s, text=s, width=width)

    return s.ljust (width, ' ')


def unpad (s):
    return s.rstrip (' ')
