# Copyright 2012 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""flatdb - a very quick flat-text database

Implementing your own database is stupid, so if this turns out
to be a lot of work to get right, I'm doing something wrong.
"""

__all__ = ('Holder Column FlatTable readStreamedTable writeStreamedTable '
           'openForceColumns FlatDBError PadError ParseError '
           'K_INT K_FLOAT K_STR K_BOOL K_CUSTOM').split ()

class Holder (object):
    def __init__ (self, **kwargs):
        self.__dict__.update (**kwargs)

    def __str__ (self):
        d = self.__dict__
        s = sorted (d.iterkeys ())
        return '{' + ', '.join ('%s=%s' % (k, d[k]) for k in s) + '}'

    def __repr__ (self):
        d = self.__dict__
        s = sorted (d.iterkeys ())
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join ('%s=%r' % (k, d[k]) for k in s))

_forbidden_colnames = frozenset (['recno'])

K_INT = 0
K_FLOAT = 1
K_STR = 2
K_BOOL = 3
K_CUSTOM = 4
_K_LAST_VALID = K_CUSTOM

class Column (object):
    name = None
    width = None
    parse = None
    format = None
    kind = None

    def __init__ (self, **kwargs):
        self.__dict__.update (kwargs)


    def _fixup (self):
        assert len (self.name) <= W_HEADER_NAME
        assert self.name not in _forbidden_colnames
        assert self.width > 0 and self.width < 512
        assert self.kind >= 0 and self.kind <= _K_LAST_VALID

        if self.format is None and self.kind in _formatters:
            self.format = _formatters[self.kind]
        if self.parse is None and self.kind in _parsers:
            self.parse = _parsers[self.kind]


HS_INVALID = 0
HS_AVAILABLE = 1
HS_SCANNING = 2
HS_APPENDING = 3
HS_REWRITING = 4

W_HEADER_INT = 7
W_HEADER_NAME = 15

class FlatTable (object):
    # XXX FIXME: unaware of headers
    handle = None

    def __init__ (self, handle, recclass=Holder):
        self.handle = handle
        self.hstate = HS_INVALID
        self.recclass = recclass

        self.cols = None
        self.recsz = -1


    def __del__ (self):
        if self.handle is not None:
            self.handle.close ()
            self.handle = None


    def all (self):
        assert self.hstate == HS_AVAILABLE
        self.hstate = HS_SCANNING

        try:
            for recno, recdata in self._allRecData (False, True):
                rec = self.recclass ()
                self._recFill (rec, recno, recdata)
                yield rec
        finally:
            self.hstate = HS_AVAILABLE


    def append (self, recs):
        assert self.hstate == HS_AVAILABLE
        self.hstate = HS_APPENDING

        self.handle.seek (0, 2) # move to EOF
        assert (self.handle.tell () - self.dofs) % self.recsz == 0

        recno = (self.handle.tell () - self.dofs) / self.recsz
        recdata = [None] * len (self.cols)

        try:
            for rec in recs:
                self._recFlatten (rec, recdata)
                self._writeRecData (recdata)
                rec.recno = recno
                recno += 1
        finally:
            self.handle.flush ()
            self.hstate = HS_AVAILABLE


    def rewrite (self, recs):
        assert self.hstate == HS_AVAILABLE
        self.hstate = HS_REWRITING

        nextrec = -1
        recdata = [None] * len (self.cols)

        try:
            for rec in recs:
                assert rec.recno >= 0
                self._recFlatten (rec, recdata)

                if rec.recno != nextrec:
                    self.handle.seek (self.dofs + rec.recno * self.recsz)

                self._writeRecData (recdata)
                nextrec = rec.recno + 1
        finally:
            self.handle.flush ()
            self.hstate = HS_AVAILABLE


    def sort (self, cmp=None, key=None, reverse=False):
        if not callable (key):
            raise ValueError ('key')

        alldata = sorted (self.all (), cmp=cmp, key=key, reverse=reverse)

        for i in xrange (len (alldata)):
            alldata[i].recno = i

        self.rewrite (alldata)


    def recClear (self, rec):
        for col in self.cols:
            setattr (rec, col.name, None)
        return rec


    def recDelete (self, rec):
        assert self.hstate == HS_AVAILABLE
        assert rec.recno >= 0

        self.handle.seek (self.dofs + rec.recno * self.recsz)
        self._writeRecData (None)
        self.handle.flush ()
        return rec


    def recRewrite (self, rec):
        assert self.hstate == HS_AVAILABLE
        assert rec.recno >= 0

        self.handle.seek (self.dofs + rec.recno * self.recsz)

        recdata = [None] * len (self.cols)
        self._recFlatten (rec, recdata)
        self._writeRecData (recdata)
        self.handle.flush ()
        return rec


    def _recFlatten (self, rec, recdata):
        for index, col in enumerate (self.cols):
            recdata[index] = getattr (rec, col.name)


    def _recFill (self, rec, recno, recdata):
        rec.recno = recno
        for index, col in enumerate (self.cols):
            setattr (rec, col.name, recdata[index])


    def _setCols (self, cols):
        # In case it's a generator or something
        self.cols = cols = list (cols)
        assert len (cols)

        recsz = len (cols) + 1 # ncols delimiters, \n
        seennames = set ()

        for col in cols:
            col._fixup ()
            assert col.name not in seennames
            recsz += col.width
            seennames.add (col.name)

        self.recsz = recsz
        return cols


    def _createHeader (self, cols):
        assert self.hstate == HS_INVALID
        cols = self._setCols (cols)

        # Offset of column info start is c.i. offset string size +
        # sep + data offset string size + newline
        #
        # Offset of data start is that plus
        # (col name width + sep + col width width + sep + col type width + sep)
        # * ncols + newline

        h = self.handle

        ncols = len (cols)
        ciofs = W_HEADER_INT * 3 + 3
        dofs = ciofs + 1 + ncols * (W_HEADER_NAME + W_HEADER_INT * 2 + 3)

        h.write (pad (ncols, W_HEADER_INT, True) + '|')
        h.write (pad (ciofs, W_HEADER_INT, True) + '|')
        h.write (pad (dofs, W_HEADER_INT, True) + '\n')

        for col in cols:
            h.write (pad (col.name, W_HEADER_NAME) + '/')
            h.write (pad (col.width, W_HEADER_INT, True) + '/')
            h.write (pad (col.kind, W_HEADER_INT, True) + '|')

        h.write ('\n')
        h.flush ()

        self.ciofs = ciofs
        self.dofs = dofs
        self.hstate = HS_AVAILABLE


    def _readHeader (self):
        assert self.hstate == HS_INVALID

        h = self.handle
        h.seek (0)

        ncols = int (unpad (h.read (W_HEADER_INT)))
        h.read (1) # separator
        ciofs = int (unpad (h.read (W_HEADER_INT)))
        h.read (1) # separator
        dofs = int (unpad (h.read (W_HEADER_INT)))

        assert ncols > 0 and ncols < 128, 'invalid ncols'
        assert ciofs > 0 and ciofs < 32768, 'invalid colinfo offset'
        assert dofs > 0 and dofs < 32768, 'invalid data offset'

        self.ciofs = ciofs
        self.dofs = dofs

        # Read in the column info associated with the saved table
        h.seek (ciofs)

        def readcol ():
            col = Column ()
            col.name = unpad (h.read (W_HEADER_NAME))
            h.read (1) # sep
            col.width = int (unpad (h.read (W_HEADER_INT)))
            h.read (1) # sep
            col.kind = int (unpad (h.read (W_HEADER_INT)))
            h.read (1) # sep
            return col

        self.hstate = HS_AVAILABLE
        return self._setCols (readcol () for i in xrange (ncols))


    def _allRecData (self, deleted, parse):
        self.handle.seek (self.dofs)
        x = [None] * len (self.cols)
        crange = xrange (len (x))
        cols = self.cols
        recno = -1

        while True:
            recno += 1
            s = self.handle.read (self.recsz)

            if not len (s):
                break

            if s[cols[0].width] == '-':
                # hypen in separator column -> deleted (I guess this
                # will break for ncol = 1)
                if deleted:
                    yield recno, None
                continue

            st = 0
            for i in crange:
                w = cols[i].width
                v = unpad (s[st:st + w])
                if parse:
                    if v == '':
                        v = None
                    else:
                        v = cols[i].parse (v)
                x[i] = v
                st += w + 1

            yield recno, x


    def _writeRecData (self, recdata, format=True):
        if recdata is None:
            # Deleted record
            self.handle.write ('-' * (self.recsz - 1) + '\n')
            return

        def get (i):
            v = recdata[i]
            if format:
                v = self.cols[i].format (v)
            return pad (v, self.cols[i].width)

        strs = [get (i) for i in xrange (len (self.cols))]

        for s in strs:
            self.handle.write (s)
            self.handle.write ('|')

        self.handle.write ('\n')


# Streaming a tables. No seeks required (or allowed).

def readStreamedTable (read, getcustom, recfactory=Holder):
    """Read a flat table from a stream without seeking. Generates a
stream of records.

      read: equivalent of a read() method on a file-like object
 getcustom: called for each column. Given Column with name and
            width, returns parser and formatter functions and flag indicating
            whether builtin functions should be overridden.
            I.e. getcustom: str -> (func, func, bool)).
            Formatter may be None if you won't use the columns to write
            out any data
recfactory: factory for "record" objects; one attr set for each column

   Returns: (headers, cols, recs), where headers is list of header strings,
            cols are the columns, and recs is generator of record data.
"""

    if not callable (read):
        raise ValueError ('read not callable')

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

    # Read column info

    recsz = ncols + 1 # ncols delimiters, \n
    cols = []

    for i in xrange (ncols):
        col = Column ()
        col.name = unpad (read (W_HEADER_NAME))
        read (1) # sep
        col.width = int (unpad (read (W_HEADER_INT)))
        read (1) # sep
        col.kind = int (unpad (read (W_HEADER_INT)))
        read (1) # sep
        curofs += W_HEADER_NAME + W_HEADER_INT * 2 + 3

        cparse, cfmt, override = getcustom (col)
        col._fixup ()

        if col.parse is None or override:
            col.parse, col.format = cparse, cfmt

        if col.parse is None:
            raise Exception ('no parser for column %s' % col.name)

        recsz += col.width
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

            if s[cols[0].width] == '-':
                # hypen in separator column -> deleted (I guess this
                # will break for ncol = 1)
                continue

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
            except Exception as e:
                raise ParseError ('exception while parsing value "%s" of row %d in '
                                  'column %s: %s (%s)', s[i:i+col.width], recno,
                                  col.name, e, e.__class__.__name__, recno=recno,
                                  colname=col.name, value=s[i:i+col.width],
                                  subexc=e)

            yield rec

    return headers, cols, getrecords ()


def writeStreamedTable (write, headers, cols, recs):
    """Write a table without seeking.

  write: equivalent of a write() method on a file-like object
headers: iterable of strings, lines of header data
   cols: iterable of columns
   recs: iterable of record-type objects; assumed to have a
         property matching each column name
"""

    if not callable (write):
        raise ValueError ('write not callable')

    # Setup headers

    if not len (headers):
        headerdata = ''
    else:
        headerdata = '\n'.join (str (h) for h in headers) + '\n'

    # Setup columns

    cols = list (cols)
    ncols = len (cols)

    for col in cols:
        col._fixup ()
        assert callable (col.format)

    # Write preamble

    ciofs = W_HEADER_INT * 3 + 3 + len (headerdata)
    dofs = ciofs + 1 + ncols * (W_HEADER_NAME + W_HEADER_INT * 2 + 3)

    write (pad (ncols, W_HEADER_INT, True) + '|')
    write (pad (ciofs, W_HEADER_INT, True) + '|')
    write (pad (dofs, W_HEADER_INT, True) + '\n')

    # Write headers

    write (headerdata)

    # Write column info

    for col in cols:
        write (pad (col.name, W_HEADER_NAME) + '/')
        write (pad (col.width, W_HEADER_INT, True) + '/')
        write (pad (col.kind, W_HEADER_INT, True) + '|')

    write ('\n')

    # Write data

    try:
        for rec in recs:
            for index, col in enumerate (cols):
                write (pad (col.format (getattr (rec, col.name)), col.width))
                write ('|')
            write ('\n')
    except PadError as e:
        raise Exception ('formatting fail in column %s for %s: %s' %
                         (col.name, rec, e))


# Opening a flat table and possibly rewriting it if the columns
# expected in software have changed from what's on disk.

def openForceColumns (fn, cols, tblclass=FlatTable, recclass=Holder):
    # XXX FIXME: unaware of headers
    h = None

    try:
        h = open (fn, 'r+b', 1024)
    except IOError as e:
        if e.errno != 2:
            # Not a file-not-found error - reraise
            raise

    if h is None:
        # Create a new, empty table
        h = open (fn, 'wb', 1024)
        wtbl = tblclass (h, recclass)
        wtbl._createHeader (cols)
        del wtbl

        h = open (fn, 'r+b', 1024)
        tbl = tblclass (h, recclass)
        tbl._readHeader ()
        return tbl

    # It does exist. Have columns changed?

    tbl = tblclass (h, recclass)
    savedcols = tbl._readHeader ()
    needRewrite = False

    if len (cols) != len (savedcols):
        needRewrite = True
    else:
        for i in xrange (len (cols)):
            # We ignore whether the type has changed.
            if savedcols[i].name != cols[i].name:
                needRewrite = True
                break
            if savedcols[i].width != cols[i].width:
                needRewrite = True
                break

    if not needRewrite:
        return tbl

    # Darn, they have. Figure out what we'll need to do with all of
    # the columns to get the data right in the new format.

    from os import rename, unlink

    savedmap = dict ((x[CI_NAME], (i, x)) for i, x in enumerate (savedcols))

    def makemapper (col):
        if col.name not in savedmap:
            # This is a new column. Fill it with blanks.
            return lambda x: ''

        savedi = savedmap[col.name][0]
        return lambda x: x[savedi]

    maps = [makemapper (x) for x in cols]

    # Write out a new file.

    hnew = open (fn + '.new', 'wb', 1024)
    newtbl = tblclass (hnew, recclass)
    newtbl._createHeader (cols)

    colidxs = xrange (len (cols))
    recdata = [None] * len (cols)

    for recno, oldrec in tbl._allRecData (True, False):
        if oldrec is not None:
            for i in colidxs:
                recdata[i] = maps[i] (oldrec)

        newtbl._writeRecData (recdata, False)

    del newtbl
    del tbl

    # Let's just assume this all works ... our model is
    # VCS-backed table storage so this isn't very risky.
    rename (fn, fn + '.old')
    rename (fn + '.new', fn)
    unlink (fn + '.old')

    # Finally, reopen in the right mode

    h = open (fn, 'r+b', 1024)
    tbl = tblclass (h, recclass)
    tbl._readHeader ()
    return tbl


# Parsing and formatting column data

def _p_bool (v):
    if v == 'T':
        return True
    return False


_parsers = {
    K_INT: int,
    K_FLOAT: float,
    K_STR: lambda x: x,
    K_BOOL: _p_bool,
    }


def _f_bool (v):
    if v:
        return 'T'
    return 'F'


def _f_stringable (v):
    if v is None:
        return ''
    return str (v)


def _f_float (v):
    if v is None:
        return ''
    return '%e' % v


_formatters = {
    K_INT: _f_stringable,
    K_FLOAT: _f_float,
    K_STR: lambda x: x,
    K_BOOL: _f_bool,
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
