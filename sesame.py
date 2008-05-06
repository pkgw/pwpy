"""sesame -- library for getting object coordinates

Uses the SIMBAD 'sesame' command-line client."""

import subprocess
import xml.dom.minidom
import os
from math import pi


def _nodeText (n):
    assert (len (n.childNodes) == 1)
    c = n.childNodes[0]
    assert (c.nodeType == c.TEXT_NODE)
    return c.wholeText

def _run (source):
    p = subprocess.Popen (['sesame', source], shell=False,
                          stdin=file (os.devnull, 'r'),
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    stdout, stderr = p.communicate ()

    if p.returncode != 0:
        raise Exception ('Invocation of sesame failed!')

    doc = xml.dom.minidom.parseString (stdout)

    radeg = decdeg = None
    
    for n1 in doc.documentElement.childNodes:
        if n1.nodeType != doc.ELEMENT_NODE: continue
        if n1.localName != 'Resolver': continue

        for n2 in n1.childNodes:
            if n2.nodeType != doc.ELEMENT_NODE: continue
            if n2.localName == 'jradeg':
                radeg = float (_nodeText (n2))
            elif n2.localName == 'jdedeg':
                decdeg = float (_nodeText (n2))

    if radeg is None or decdeg is None:
        raise Exception ('Couldn\'t get info for ' + source)

    return radeg, decdeg

_cache = {}

def _get (source):
    tup = _cache.get (source)

    if tup is None:
        tup = _run (source)
        _cache[source] = tup

    return tup

def lookupdd (source):
    """Look up the ICRS J2000 location of a source, returning both RA
and Dec in degrees."""
    
    return _get (source)

def lookuphd (source):
    """Look up the ICRS J2000 location of a source, returning RA in
hours and Dec in degrees."""

    rad, decd = _get (source)
    return rad / 15., decd

def lookuprr (source):
    """Look up the ICRS J2000 location of a source, returning both RA
and Dec in radians."""

    rad, decd = _get (source)
    return rad * pi / 180, decd * pi / 180

_itemCache = {}

def makeItem (source):
    """Return a RALP CatItem corresponding to the source, with RA
and Dec filled in with ICRS J2000 values and the property 'name'
set to the source name. Results are cached, so that multiple calls
with the same argument return the same object."""

    s = _itemCache.get (source)

    if s is None:
        import ralp

        rah, decd = lookuphd (source)

        s = ralp.CatItem ()
        s.name = source
        s.ra = rah
        s.dec = decd

        _itemCache[source] = s

    return s

def formathd (source):
    """Return a string giving the ICRS J2000 location of a source,
formatted as sexagesimal with colons for separators."""
    
    import ralp
    rah, decd = lookuphd (source)
    return ralp.fmtRaDec (rah, decd)

__all__ = ['lookupdd', 'lookuphd', 'lookuprr', 'makeItem', 'formathd']
