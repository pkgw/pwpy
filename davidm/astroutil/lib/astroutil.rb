#
# $Id$
#

# Astronomy related extensions for Ruby.

require 'date'

# Add angle conversion methods to the Math module
module Math
  # Convert possibly non-integer degrees +fr+ to [degrees, minutes, seconds]
  # where degrees and minutes are integers.
  def d_to_dms(fr)
    sign = fr <=> 0
    fr *= sign
    d = fr.to_i; fr %= 1; fr *= 60
    m = fr.to_i; fr %= 1; fr *= 60
    return d*sign, m, fr
  end
  module_function :d_to_dms

  # Convert possibly non-integer hours +fr+ to [hours, minutes, seconds]
  # where hours and minutes are integers.
  def h_to_hms(fr); d_to_dms(fr); end; module_function :h_to_hms

  # Convert degrees, minutes, seconds to possibly non-integer degrees.
  # Missing arguments are assumed to be 0.
  def dms_to_d(*args)
    d = 0.to_r
    d += args.shift unless args.empty?
    sign = d < 0 ? -1 : 1
    d += args.shift * Rational(sign,60) unless args.empty?
    d += args.shift * Rational(sign,3600) unless args.empty?
    return d
  end
  module_function :dms_to_d

  # Convert hours, minutes, seconds to possibly non-integer hours.
  # Missing arguments are assumed to be 0.
  def hms_to_h(*args); dms_to_d(*args); end

  # Convert degrees to radians
  def d2r(d) d*Rational(1,180)*PI; end; module_function :d2r
  # Convert radians to degrees
  def r2d(r) r*180/PI; end; module_function :r2d
  # Convert hours to radians
  def h2r(h) h*Rational(1,12)*PI; end; module_function :h2r
  # Convert radians to hours
  def r2h(r) r*12/PI; end; module_function :r2h
  # Convert degrees to hours
  def d2h(d) d*Rational(1,15); end; module_function :d2h
  # Convert hours to degrees
  def h2d(h) h*15; end; module_function :h2d
end

# Add angle conversion and angle formatting methods to Numeric class.
class Numeric
  # Convert +self+ to [degrees, minutes, seconds] where degrees and minutes are
  # integers.
  def to_dms() Math.d_to_dms(self); end
  # Convert +self+ to [hours, minutes, seconds] where hours and minutes are
  # integers.
  alias :to_hms :to_dms
  # Convert +self+ to "##d##m##.###s" format rounded to +prec+ fractional places.
  # TODO Might need/want different quantization behavior than sprintf gives.
  def to_dmsstr(prec=3)
    width = prec == 0 ? 2 : prec+3
    "%02dd%02dm%0#{width}.#{prec}fs" % to_dms
  end
  # Convert +self+ to "##:##:##.###" format rounded to +prec+ fractional places.
  # TODO Might need/want different quantization behavior than sprintf gives.
  def to_hmsstr(prec=3)
    width = prec == 0 ? 2 : prec+3
    "%02d:%02d:%0#{width}.#{prec}f" % to_dms
  end
  # Convert +self+ from degrees to radians (i.e. <tt>Math.d2r(self)</tt>).
  def d2r() Math.d2r(self); end
  # Convert +self+ from radians to degrees (i.e. <tt>Math.r2d(self)</tt>).
  def r2d() Math.r2d(self); end
  # Convert +self+ from hours to radians (i.e. <tt>Math.h2r(self)</tt>).
  def h2r() Math.h2r(self); end
  # Convert +self+ from radians to hours (i.e. <tt>Math.r2h(self)</tt>).
  def r2h() Math.r2h(self); end
  # Convert +self+ from degrees to hours (i.e. <tt>Math.d2h(self)</tt>).
  def d2h() Math.d2h(self); end
  # Convert +self+ from hours to degrees (i.e. <tt>Math.h2d(self)</tt>).
  def h2d() Math.h2d(self); end
end

# Add #to_r method to Float
class Float
  # Convert +self+ to a Rational.
  def to_r
    Rational(1,Rational(1,self)) rescue Rational(0,1)
  end
end

# Add angle conversion methods to Array class.
class Array
  # Convert +self+ from [degrees, minutes, seconds] to degrees.
  # Missing arguments are assumed to be 0.
  def dms_to_d; Math::dms_to_d(*self); end
  # Convert +self+ from [hours, minutes, seconds] to hours.
  # Missing arguments are assumed to be 0.
  alias :hms_to_h :dms_to_d
end

# Add angle parsing methods to String class.
class String
  # Parse a "dd:mm:ss.sss" String to Numeric degrees.
  # <b>NOT</b> the inverse of Numeric#to_dmsstr (but may become so).
  def dms_to_d;
    d, m, s = split(':',3)
    d, m, s = d.to_f, m.to_f, s.to_f
    m, s = -m, -s if d == 0 && self =~ /^\s*-/
    Math::dms_to_d(d,m,s)
  end
  # Parse a "hh:mm:ss.sss" String to Float hours.
  alias :hms_to_h :dms_to_d
end

# Adds astronomy-related and other utilty methods to the +DateTime+ class.
# Includes conversions between various time scales:
#
# - GPS
# - TAI
# - TT
# - UT1
# - UTC
#
# This class represents these differences between time scales as fractions of a
# "day", which is assumed to be 86,400 "seconds" long.  Differences between
# time scales can be fixed or variable.  Fixed differences are defined as
# constants; variable differences are defined as methods.  The difference
# between timescale +XXx+ and timescale +yyy+ is expressed as xxx_yyy+ (or
# +XXX_YYY+ if it is a constant).  The underscore is a mnemonic for a minus
# sign.  For example, +TAI_GPS+ is the constant difference between the TAI time
# scale and the GPS time scale (i.e. <tt>TAI-GPS</tt>), which is defined as 19
# seconds.
#
# This table describes the time scale differences defined here:
#
#   --> |   TAI     TT     UT1
#  ------------------------------
#   GPS | TAI_GPS
#   TAI |         TT_TAI
#   UTC | tai_utc        ut1_utc(*)
#
# (*) Note that conversions involving UT1 requires a value for UT1-UTC.  This
# value can be passed explicitly to the methods that convert to/from UT1.  If a
# UT1-UTC value is not passed, the conversion methods will call
# <tt>self.ut1_utc</tt> if it has been externally defined (NB: the #ut1_utc
# method is not defined here).  The eop extension defines DateTime#ut1_utc.  If
# a value for UT1-UTC is not explicitly passed, and DateTime#ut1_utc is not
# defined, conversion to/from UT1 is equivalent to conversion to/from UTC.
#
# Using the differences in the above tables, a supported time scale can be
# converted to any other supported time scales.  Time scale conversion methods
# have the form +xxx_to_yyy+, treat +self+ as being in time scale +xxx+, and
# return a new DateTime object representing the same time in time scale +yyy+.
#
# This extension defines a TAI-UTC table that captures leap second information.
# When a leap seconds is announced, this extension should be updated to include
# it.

class DateTime

  # The J2000 epoch
  J2000 = civil(2000,1,1,12)

  # Create a +DateTime+ object from a numeric Astronomical Julian Date.
  # If +n+ is given and d is an Integer, the Astronomical Julian Date is taken
  # as <tt>Rational(d,n)</tt>.
  def self.ajd(d,n=nil)
    d = Rational(d, n) if n && Integer === d
    J2000 + (d - J2000.ajd)
  end

  # Create a +DateTime+ object from a numeric Astronomical Modified Julian Date.
  # If +n+ is given and d is an Integer, the Astronomical Modified Julian Date
  # is taken as <tt>Rational(d,n)</tt>.
  def self.amjd(d,n=nil)
    d = Rational(d, n) if n && Integer === d
    J2000 + (d - J2000.amjd)
  end

  # A +DateTime+ object corresponding to the same time as +self+, but
  # with an offset of 0.  Returns +self+ if <tt>self.offset == 0</tt>.
  def to_utc
    (offset == 0) ? self : new_offset(0)
  end

  # Create a +DateTime+ object corresponding to now, but with an offset of 0.
  def self.utc
    now.to_utc
  end

  class << self
    # Undefine method from superclass
    undef today rescue nil

    # Create a +DateTime+ object corresponding to (local) today.
    def today
      n = self.now
      n - n.day_fraction
    end
  end

  # (TAI - UTC) table (in days).
  TAI_UTC_TABLE = [
    # Add new leap seconds here
    [DateTime.civil(2009,1,1), Rational(34, 86400)],
    [DateTime.civil(2006,1,1), Rational(33, 86400)],
    [DateTime.civil(1999,1,1), Rational(32, 86400)],
    [DateTime.civil(1997,7,1), Rational(31, 86400)],
    [DateTime.civil(1996,1,1), Rational(30, 86400)],
    [DateTime.civil(1994,7,1), Rational(29, 86400)],
    [DateTime.civil(1993,7,1), Rational(28, 86400)],
    [DateTime.civil(1992,7,1), Rational(27, 86400)],
    [DateTime.civil(1991,1,1), Rational(26, 86400)],
    [DateTime.civil(1990,1,1), Rational(25, 86400)],
    [DateTime.civil(1988,1,1), Rational(24, 86400)],
    [DateTime.civil(1985,7,1), Rational(23, 86400)],
    [DateTime.civil(1983,7,1), Rational(22, 86400)],
    [DateTime.civil(1982,7,1), Rational(21, 86400)],
    [DateTime.civil(1981,7,1), Rational(20, 86400)],
    [DateTime.civil(1980,1,1), Rational(19, 86400)],
    [DateTime.civil(1979,1,1), Rational(18, 86400)],
    [DateTime.civil(1978,1,1), Rational(17, 86400)],
    [DateTime.civil(1977,1,1), Rational(16, 86400)],
    [DateTime.civil(1976,1,1), Rational(15, 86400)],
    [DateTime.civil(1975,1,1), Rational(14, 86400)],
    [DateTime.civil(1974,1,1), Rational(13, 86400)],
    [DateTime.civil(1973,1,1), Rational(12, 86400)],
    [DateTime.civil(1972,7,1), Rational(11, 86400)],
  ] # :nodoc:

  # TT-TAI in days.
  TT_TAI = Rational(32184, 86400000)

  # TAI-GPS in days.
  TAI_GPS = Rational(19, 86400)

  # Returns TAI-UTC as of date represented by +self+.
  def tai_utc
    if self >= TAI_UTC_TABLE[0][0]
      TAI_UTC_TABLE[0][1]
    elsif self < TAI_UTC_TABLE[-1][0]
      0
    else
      (TAI_UTC_TABLE.find {|epoch,dt| epoch <= self})[1]
    end
  end

  # Returns TAI-UTC as of DateTime given or Numeric day offset given (defaults
  # to <tt>DateTime.now</tt>).
  def self.tai_utc(t=DateTime.now)
    t = DateTime.now + t unless DateTime === t
    t.tai_utc
  end

  # Returns TT_UT1 as of date represented by +self+.
  def tt_ut1(ut1_utc_days=nil)
    if ut1_utc_days
      TT_TAI + tai_utc - ut1_utc_days
    elsif defined? ut1_utc
      TT_TAI + tai_utc - ut1_utc
    else
      TT_TAI + tai_utc
    end
  end
  alias :deltat :tt_ut1

  # Returns TT-UT1 as of DateTime given or Numeric day offset given (defaults
  # to <tt>DateTime.now</tt>).
  def self.tt_ut1(t=DateTime.now, ut1_utc_days=nil)
    t = DateTime.now + t unless DateTime === t
    t.tt_ut1(ut1_utc_days)
  end
  class << self
    alias :deltat :tt_ut1
  end

  # Returns TAI version of +self+, treating +self+ as UTC
  def utc_to_tai
    self + self.tai_utc
  end
  alias :utc2tai :utc_to_tai

  # Returns TT version of +self+, treating +self+ as UTC
  def utc_to_tt
    self + (self.tai_utc + TT_TAI)
  end
  alias :utc2tt :utc_to_tt

  # Returns GPS version of +self+, treating +self+ as UTC
  def utc_to_gps
    self + (self.tai_utc - TAI_GPS)
  end
  alias :utc2gps :utc_to_gps

  # Returns UT1 version of +self+, treating +self+ as UTC
  def utc_to_ut1(ut1_utc_days=nil)
    if ut1_utc_days
      self + ut1_utc_days
    elsif defined? ut1_utc
      self + ut1_utc
    else
      self
    end
  end
  alias :utc2ut1 :utc_to_ut1

  # Returns UTC version of +self+, treating +self+ as TAI
  def tai_to_utc
    self - self.tai_utc
  end
  alias :tai2utc :tai_to_utc

  # Returns TT version of +self+, treating +self+ as TAI
  def tai_to_tt
    self + TT_TAI
  end
  alias :tai2tt :tai_to_tt

  # Returns GPS version of +self+, treating +self+ as TAI
  def tai_to_gps
    self - TAI_GPS
  end
  alias :tai2gps :tai_to_gps

  # Returns UT1 version of +self+, treating +self+ as TAI
  def tai_to_ut1(ut1_utc_days=nil)
    if ut1_utc_days
      self - (self.tai_utc - ut1_utc_days)
    elsif defined? ut1_utc
      self - (self.tai_utc - ut1_utc)
    else
      self - self.tai_utc
    end
  end
  alias :tai2ut1 :tai_to_ut1

  # Returns UTC version of +self+, treating +self+ as TT
  def tt_to_utc
    self - (TT_TAI + self.tai_utc)
  end
  alias :tt2utc :tt_to_utc

  # Returns TAI version of +self+, treating +self+ as TT
  def tt_to_tai
    self - TT_TAI
  end
  alias :tt2tai :tt_to_tai

  # Returns GPS version of +self+, treating +self+ as TT
  def tt_to_gps
    self - (TT_TAI + TAI_GPS)
  end
  alias :tt2gps :tt_to_gps

  # Returns UT1 version of +self+, treating +self+ as TT
  def tt_to_ut1(ut1_utc_days=nil)
    if ut1_utc_days
      self - (TT_TAI + self.tai_utc - ut1_utc_days)
    elsif defined? ut1_utc
      self - (TT_TAI + self.tai_utc - ut1_utc)
    else
      self - (TT_TAI + self.tai_utc)
    end
  end
  alias :tt2ut1 :tt_to_ut1

  # Returns UTC version of +self+, treating +self+ as GPS
  def gps_to_utc
    self + (TAI_GPS - self.tai_utc)
  end
  alias :gps2utc :gps_to_utc

  # Returns TAI version of +self+, treating +self+ as GPS
  def gps_to_tai
    self + TAI_GPS
  end
  alias :gps2tai :gps_to_tai

  # Returns TT version of +self+, treating +self+ as GPS
  def gps_to_tt
    self + (TAI_GPS + TT_TAI)
  end
  alias :gps2tt :gps_to_tt

  # Returns UT1 version of +self+, treating +self+ as GPS
  def gps_to_ut1(ut1_utc_days=nil)
    if ut1_utc_days
      self + (TAI_GPS - self.tai_utc + ut1_utc_days)
    elsif defined? ut1_utc
      self + (TAI_GPS - self.tai_utc + ut1_utc)
    else
      self + (TAI_GPS - self.tai_utc)
    end
  end
  alias :gps2ut1 :gps_to_ut1

  # Returns UTC version of +self+, treating +self+ as UT1
  def ut1_to_utc(ut1_utc_days=nil)
    if ut1_utc_days
      self + ut1_utc_days
    elsif defined? ut1_utc
      self + ut1_utc
    else
      self
    end
  end
  alias :ut12utc :ut1_to_utc

  # Returns TAI version of +self+, treating +self+ as UT1
  def ut1_to_tai(ut1_utc_days=nil)
    if ut1_utc_days
      self - (self.tai_utc - ut1_utc_days)
    elsif defined? ut1_utc
      self - (self.tai_utc - ut1_utc)
    else
      self - self.tai_utc
    end
  end
  alias :ut12tai :ut1_to_tai

  # Returns TT version of +self+, treating +self+ as UT1
  def ut1_to_tt(ut1_utc_days=nil)
    if ut1_utc_days
      self - (TT_TAI + self.tai_utc - ut1_utc_days)
    elsif defined? ut1_utc
      self - (TT_TAI + self.tai_utc - ut1_utc)
    else
      self - (TT_TAI + self.tai_utc)
    end
  end
  alias :ut12tt :ut1_to_tt

  # Returns GPS version of +self+, treating +self+ as UT1
  def ut1_to_gps(ut1_utc_days=nil)
    if ut1_utc_days
      self + (TAI_GPS - self.tai_utc + ut1_utc_days)
    elsif defined? ut1_utc
      self + (TAI_GPS - self.tai_utc + ut1_utc)
    else
      self + (TAI_GPS - self.tai_utc)
    end
  end
  alias :ut12gps :ut1_to_gps

  # Avoid warning about redefining to_s
  undef to_s rescue nil

  # Format +self+ as String with (optional) fractional seconds
  def to_s(prec=0)
    width = prec == 0 ? 2 : prec+3
    secf = sec + sec_fraction*86400
    "%04d-%02d-%02dT%02d:%02d:%0#{width}.#{prec}f%s" %
      [year, mon, day, hour, min, secf, zone]
  end
end

# Returns the angular velocity of Earth in radians per second for a given +lod+ in
# milliseconds.  From http://www.iers.org/MainDisp.csl?pid=95-97 ...
#
# The difference between the astronomically determined duration of the day and
# 86400 SI seconds is also called length of day (LOD). The relationship of the
# angular velocity of the earth Omega with LOD is...
#
# Omega = 72,921,151.467064 - 0.843994809*LOD
#
# ...where Omega is in picoradians/s and LOD in milliseconds [but note that
# this method returns radians per second].
#--
# TODO? Move this into a module?
#++
def Omega(lod)
  omega = Rational(72921151467064,1e18)
  omega -= Rational(843994809,1e21)*lod.to_r if lod != 0
  omega
end

# Angular velocity of Earth ignoring length of day variations.
Omega = Omega(0)
