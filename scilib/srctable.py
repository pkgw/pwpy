"""srctable - flexible table of astronomical source information
"""

from astutil import *
from flatdb import *

__all__ = 'Holder stdcols getCustom sfindcols nvsscols parseSFind parseNVSS'.split ()

stdcols = {}

def makestdcol (name, width, kind, **rest):
    stdcols[name] = Column (name=name, width=width, kind=kind, **rest)

def mkscalep (scale):
    def f (s):
        if not len (s):
            return None
        return float (s) * scale
    return f

def mkscalef (scale, fmt='%e'):
    def f (v):
        if v is None:
            return ''
        return fmt % (v / scale)
    return f

def floatcol (name, width, fmt, scale=None):
    if scale is None:
        parse = float
        def format (v):
            if v is None:
                return ''
            return fmt % v
    else:
        parse = mkscalep (scale)
        format = mkscalef (scale, fmt)

    return Column (name=name, width=width, kind=K_FLOAT,
                   parse=parse, format=format)

def makefltcol (name, width, fmt, scale=None):
    stdcols[name] = floatcol (name, width, fmt, scale)


makestdcol ('ident', 20, K_STR)
makestdcol ('ra', 12, K_CUSTOM, parse=parsehours, format=fmthours) # rad
makefltcol ('ra_uc', 8, '%.3f', A2R) # rad
makestdcol ('dec', 12, K_CUSTOM, parse=parsedeglat, format=fmtdeglat) # rad
makefltcol ('dec_uc', 8, '%.2f', A2R) # rad
makefltcol ('totflux', 12, '%.5f') # jy
makefltcol ('totflux_uc', 12, '%.7f') # jy
makestdcol ('totflux_is_ul', 1, K_BOOL)
makefltcol ('pkflux', 12, '%.5f') # jy
makefltcol ('pkflux_uc', 12, '%.7f') # jy
makestdcol ('pkflux_is_ul', 1, K_BOOL)
makefltcol ('bgrms', 12, '%.5f') # jy
makefltcol ('major', 7, '%.2f', A2R) # rad
makefltcol ('major_uc', 12, '%.2f', A2R) # rad
makestdcol ('major_is_ul', 1, K_BOOL)
makefltcol ('minor', 7, '%.2f', A2R) # rad
makefltcol ('minor_uc', 12, '%.2f', A2R) # rad
makestdcol ('minor_is_ul', 1, K_BOOL)
makefltcol ('pa', 7, '%+.2f', D2R) # rad
makefltcol ('pa_uc', 12, '%.2f', D2R) # rad


def getCustom (col):
    if col.name in stdcols:
        return stdcols[col.name].parse, stdcols[col.name].format, True
    return str, str, False


# Parsing output of MIRIAD sfind

_sfindMiscColumns = ('ra_uc dec_uc pkflux pkflux_uc totflux major '
                     'minor pa bgrms sfind_fitrms').split ()
_sfindMiscOffsets = [24, 32, 40, 50, 58, 68, 74, 80, 86, 92, 100]
_sfindUnits= [A2R, A2R, 1e-3, 1e-3, 1e-3, A2R,
              A2R, D2R, 1e-3, 1e-3]

def parseSFind (lines):
    for linenum, line in enumerate (lines):
        if line[0] == '#':
            continue

        a = line.strip ().split ()
        source = Holder ()
        source.ra = parsehours (a[0])
        source.dec = parsedeglat (a[1])

        for i, name in enumerate (_sfindMiscColumns):
            substr = line[_sfindMiscOffsets[i]:_sfindMiscOffsets[i+1]]

            if '*' in substr:
                val = None
            else:
                val = float (substr) * _sfindUnits[i]

            setattr (source, name, val)

        if source.pkflux_uc is None or source.pkflux_uc == 0.:
            source.totflux_uc = source.pkflux_uc = None
        else:
            source.totflux_uc = source.totflux * source.pkflux_uc / source.pkflux

        if source.ra_uc == 0.:
            source.ra_uc = None

        if source.dec_uc == 0.:
            source.dec_uc = None

        yield source


makefltcol ('sfind_fitrms', 12, '%9.5f') # jy

sfindcols = [stdcols[n] for n in
             'ra ra_uc dec dec_uc pkflux pkflux_uc totflux totflux_uc '
             'major minor pa bgrms sfind_fitrms'.split ()]


# Parsing the NVSS textual catalog
# NOTE: if non-deconvolved source parameters are requested, peak fluxes are
# returned, not total fluxes! We don't detect this (you'd have to poke at
# the comment lines).

nvss_columns1 = {
    # Each tuple gives the Python slice info for extracting that column:
    # for tuple t, take text[t[0]:t[1]].
    'ra': (0, 11), # [hr] space-separated sexigesimal
    'dec': (12, 23), # [deg] space-separated signed sexigesimal
    'nvss_dist': (24, 30), # [arcsec] dist of src from search origin
    'totflux': (31, 37), # [mjy]
    'major': (38, 43), # [arcsec]; (bool, float), bool indicating if upper limit
    'minor': (44, 49), # ditto
    'pa': (50, 55), # [deg], poss. absent
    'nvss_resid_code': (56, 59), # P*=high pk, R*=high rms, S*=high sum
    'nvss_linpol_flux': (60, 65), # [mjy] linear polarized flux
    'nvss_linpol_pa': (66, 71), # [deg] lin. pol E vector PA
    'nvss_field': (72, 80),
    'nvss_pixel_x': (81, 88),
    'nvss_pixel_y': (89, 96),
}

nvss_columns2 = {
    'ra_uc': (0, 11), # [time-sec]
    'dec_uc': (12, 23), # [arcsec]
    'nvss_angle': (24, 30), # [deg] PA of src *location* relative to search origin
    'totflux_uc': (31, 37), # [mjy]
    'major_uc': (38, 43), # [arcsec], poss. absent
    'minor_uc': (44, 49), # [arcsec], poss. absent
    'pa_uc': (50, 55), # [deg], poss. absent
    'nvss_resid_val': (56, 59), # [100s of ujy] value triggering residual flag
    'nvss_linpol_flux_uc': (60, 65), # [mjy]
    'nvss_linpol_pa_uc': (66, 71), # [deg] poss. absent
}


def nvss_parsera (t):
    chars = list (t)
    chars[2] = ':'
    chars[5] = ':'
    return parsehours (''.join (chars))


def nvss_parsedec (t):
    chars = list (t)
    chars[3] = ':'
    chars[6] = ':'
    return parsedeglat (''.join (chars))


nvss_asec2rad = lambda t: float (t) * A2R
nvss_tsec2rad = lambda t: float (t) * A2R * 15
nvss_mjy2jy = lambda t: float (t) * 1e-3

def nvss_maybeulasec (t):
    if t[0] == '<':
        return (True, float (t[1:]) * A2R)
    return (False, float (t) * A2R)


def nvss_strornone (t):
    t = t.strip ()
    if not len (t):
        return None
    return t

def nvss_scaleornone (scale):
    def f (t):
        t = t.strip ()
        if not len (t):
            return None
        return float (t) * scale
    return f

nvss_floatornone = nvss_scaleornone (1)
nvss_degornone = nvss_scaleornone (D2R)
nvss_asecornone = nvss_scaleornone (A2R)
nvss_mjyornone = nvss_scaleornone (1e-3)
nvss_hujyornone = nvss_scaleornone (1e-4)

nvss_parsers = {
    # default parser is float()
    'ra': nvss_parsera,
    'ra_uc': nvss_tsec2rad,
    'dec': nvss_parsedec,
    'dec_uc': nvss_asec2rad,
    'nvss_dist': nvss_asec2rad,
    'nvss_angle': nvss_degornone,
    'totflux': nvss_mjy2jy,
    'totflux_uc': nvss_mjy2jy,
    'major': nvss_maybeulasec,
    'major_uc': nvss_asecornone,
    'minor': nvss_maybeulasec,
    'minor_uc': nvss_asecornone,
    'pa': nvss_degornone,
    'pa_uc': nvss_degornone,
    'nvss_resid_code': nvss_strornone,
    'nvss_resid_val': nvss_hujyornone,
    'nvss_linpol_flux': nvss_mjy2jy,
    'nvss_linpol_flux_uc': nvss_mjyornone,
    'nvss_linpol_pa': nvss_degornone,
    'nvss_linpol_pa_uc': nvss_degornone,
    'nvss_field': str,
}


def parseNVSS (stream):
    linenum = 0
    datalinenum = 0
    source = None

    for line in stream:
        linenum += 1

        if line[0] == '#':
            continue

        if datalinenum % 2 == 0:
            assert source is None, 'NVSS internal logic error 1'
            source = Holder ()
            colspec = nvss_columns1
        else:
            colspec = nvss_columns2

        try:
            for key, (b0, b1) in colspec.iteritems ():
                parser = nvss_parsers.get (key, float)
                setattr (source, key, parser (line[b0:b1]))
        except Exception as e:
            raise Exception ('line %d, item %s: %s' % (linenum, key, e))

        if datalinenum % 2 == 1:
            # Fixups
            source.major_is_ul = source.major[0]
            source.major = source.major[1]
            source.minor_is_ul = source.minor[0]
            source.minor = source.minor[1]
            # Done
            yield source
            source = None

        datalinenum += 1

    assert source is None, 'NVSS internal logic error 2'


makefltcol ('nvss_dist', 12, '%f'),
makefltcol ('nvss_angle', 12, '%f'),
makefltcol ('nvss_resid_code', 12, '%f'),
makefltcol ('nvss_resid_val', 12, '%f'),
makefltcol ('nvss_linpol_flux', 12, '%f'),
makefltcol ('nvss_linpol_flux_uc', 12, '%f'),
makefltcol ('nvss_linpol_pa', 12, '%f'),
makefltcol ('nvss_linpol_pa_uc', 12, '%f'),
makefltcol ('nvss_field', 12, '%f'),
makefltcol ('nvss_pixel_x', 12, '%f'),
makefltcol ('nvss_pixel_y', 12, '%f'),


nvsscols = [stdcols[n] for n in
            'ra ra_uc dec dec_uc totflux totflux_uc major major_uc '
            'major_is_ul minor minor_uc minor_is_ul pa pa_uc '
            'nvss_dist nvss_angle nvss_resid_code nvss_resid_val '
            'nvss_linpol_flux nvss_linpol_flux_uc nvss_linpol_pa '
            'nvss_linpol_pa_uc nvss_field nvss_pixel_x nvss_pixel_y'.split ()]


# Transformations on sources

has = lambda s, f: hasattr (s, f) and getattr (s, f) is not None

def deconvolve (source, bmaj, bmin, bpa):
    if (not has (source, 'major') or not has (source, 'minor')
        or not has (source, 'pa')):
        source.deconvolve_error = 'missing shape information'
        return source

    dmaj, dmin, dpa, status = gaussianDeconvolve (source.major,
                                                  source.minor,
                                                  source.pa,
                                                  bmaj, bmin, bpa)

    if status == 'fail':
        dmaj = dmin = dpa = None
        source.deconvolve_error = 'deconvolution failed'
    elif status == 'pointlike':
        dmaj = dmin = dpa = None
        source.deconvolve_error = None
    elif status == 'ok':
        source.deconvolve_error = None
    else:
        raise Exception ('unexpected deconvolution status ' + status)

    if has (source, 'major_uc'):
        if dmaj is None:
            source.major_uc = None
        else:
            source.major_uc *= dmaj / source.major

    if has (source, 'minor_uc'):
        if dmin is None:
            source.minor_uc = None
        else:
            source.minor_uc *= dmin / source.minor

    assert not has (source, 'pkflux'), ('need more info to update pkflux; '
                                        'clear it if info not needed')

    source.major = dmaj
    source.minor = dmin
    source.pa = dpa
    return source


# Overlays for ndshow

def loadAsOverlay (path, topixel, imgheight):
    headers, cols, recs = readStreamedTable (open (path).read, getCustom)
    compact = []
    ellipse = []

    for rec in recs:
        y, x = topixel ([rec.dec, rec.ra])

        if not hasattr (rec, 'major') or rec.major is None or rec.major == 0:
            compact.append ((x, y))
            continue

        # TODO: draw Gaussians with the right shape
        compact.append ((x, y))

    def drawoverlay (ctxt, width, height, x0, y0, d2p):
        ctxt.set_source_rgb (255, 0, 0)

        for dx, dy in compact:
            cx = (dx + 0.5 - x0) * d2p
            cy = (imgheight - dy - 0.5 - y0) * d2p

            ctxt.move_to (cx - 5, cy)
            ctxt.line_to (cx + 5, cy)
            ctxt.stroke ()
            ctxt.move_to (cx, cy - 5)
            ctxt.line_to (cx, cy + 5)
            ctxt.stroke ()

    return drawoverlay
