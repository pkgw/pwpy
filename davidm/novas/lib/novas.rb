# Load extension library
require 'novas_ext'

module Novas

  # RDoc for constants
  if false
    # TDB Julian date of epoch J2000.0.
    T0 = 2451545.00000000
    # Astronomical Unit in kilometers.
    KMAU = 1.49597870e+8
    # Astronomical Unit in meters.
    MAU = 1.49597870e+11
    # Speed of light in AU/Day.
    C = 173.14463348
    # Heliocentric gravitational constant.
    GS = 1.32712438e+20
    # Radius of Earth in kilometers.
    EARTHRAD = 6378.140
    # Earth ellipsoid flattening.
    F = 0.00335281
    # Rotational angular velocity of Earth in radians/sec.
    OMEGA = 7.292115e-5
    # Value of 2*pi in radians.
    TWOPI = 6.28318530717958647692
    # Angle conversion constant (arcseconds per radian).
    RAD2SEC = 206264.806247096355
    # Angle conversion constant (radians per degree).
    DEG2RAD = 0.017453292519943296
    # Angle conversion constant (degrees per radian).
    RAD2DEG = 57.295779513082321
    # Flag to indicate barycentric option
    BARYCENTRIC = 0
    # Flag to indicate heliocentric option
    HELIOCENTRIC = 1
    # Flag to indicate no refraction
    NONE = 0
    # Flag to indicate default refraction
    DEFAULT = 1
    # Flag to indicate atmospheric refraction
    ATMOS = 2
  end

  module WGS72
    EARTHRAD = 6378.135
    F = 1.0/298.26
  end

  module IAU76
    EARTHRAD = 6378.140
    F = 0.00335281
  end

  module WGS84
    EARTHRAD = 6378.1370
    F = 1.0/298.257223563 
  end

  class Body
    def inspect
      "#<Novas::Body (#{name},#{type},#{number})>"
    end
  end

  class CatEntry
    def inspect
      s = "#<Novas::CatEntry (ra=#{ra},dec=#{dec}"
      s << ",starname=#{starname}" if starname
      s << ",starnumber=#{starnumber}" if starnumber
      s << ",catalog=#{catalog}" if catalog
      s << ",promora=#{promora}" if promora
      s << ",promodec=#{promodec}" if promodec
      s << ",parallax=#{parallax}" if parallax
      s << ",radialvelocity=#{radialvelocity}" if radialvelocity
      s << ")>"
    end

    def topo_hor(tjd, deltat, location, refopt=NONE, x=0.0, y=0.0)
      obsra, obsdec = topo_star(tjd, deltat, location)
      location.equ2hor(tjd, deltat, obsra, obsdec, refopt, x, y)
    end
  end

  class Site
    # Show useful info
    def inspect
      "#<Novas::Site (" \
      "latitude=#{latitude}," \
      "longitude=#{longitude}," \
      "height=#{height}," \
      "temperature=#{temperature}," \
      "pressure=#{pressure})>"
    end

    def topo_star(tjd, deltat, cat_entry)
      cat_entry.topo_star(tjd, deltat, self)
    end

    def topo_hor(tjd, deltat, cat_entry, refopt=NONE, x=0.0, y=0.0)
      obsra, obsdec = topo_star(tjd, deltat, cat_entry)
      equ2hor(tjd, deltat, obsra, obsdec, refopt, x, y)
    end

    # Computes local mean sidereal time at time +jd_high+ + +jd_low+.
    # For most uses, the input Julian date should be in the UT1 time scale. If
    # the input Julian date is in the TDB time scale, the output must be
    # considered to be dynamical sidereal time.
    def lmst(jd_high, jd_low=0)
      (Novas.sidereal_time(jd_high,jd_low,0) + longitude/15.0) % 24.0
    end

    # Computes local apparent sidereal time at time +jd_high+ + +jd_low+.
    # For most uses, the input Julian date should be in the UT1 time scale. If
    # the input Julian date is in the TDB time scale, the output must be
    # considered to be dynamical sidereal time.
    def last(jd_high, jd_low=0)
      mobl, tobl, ee, dpsi, deps = Novas.earthtilt(jd_high + jd_low)
      (Novas.sidereal_time(jd_high,jd_low,ee) + longitude/15.0) % 24.0
    end
  end

  # Computes Greenwich mean sidereal time at time +jd_high+ + +jd_low+.
  # For most uses, the input Julian date should be in the UT1 time scale. If
  # the input Julian date is in the TDB time scale, the output must be
  # considered to be dynamical sidereal time.
  def gmst(jd_high, jd_low=0)
    sidereal_time(jd_high,jd_low,0)
  end
  module_function :gmst

  # Computes Greenwich apparent sidereal time at time +jd_high+ + +jd_low+.
  # For most uses, the input Julian date should be in the UT1 time scale. If
  # the input Julian date is in the TDB time scale, the output must be
  # considered to be dynamical sidereal time.
  def gast(jd_high, jd_low=0)
    mobl, tobl, ee, dpsi, deps = Novas.earthtilt(jd_high + jd_low)
    sidereal_time(jd_high,jd_low,ee)
  end
  module_function :gast
end
