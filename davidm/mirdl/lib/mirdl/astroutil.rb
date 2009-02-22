# Astronomy friendly extensions to Ruby.
# Does not really need to be part of Mirdl.
# Could live on its own.

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
  def d2r(d) d*PI/180; end; module_function :d2r
  # Convert radians to degrees
  def r2d(r) r*180/PI; end; module_function :r2d
  # Convert hours to radians
  def h2r(h) h*PI/12; end; module_function :h2r
  # Convert radians to hours
  def r2h(r) r*12/PI; end; module_function :r2h
  # Convert degrees to hours
  def d2h(d) d/15.0; end; module_function :d2h
  # Convert hours to degrees
  def h2d(h) h*15.0; end; module_function :h2d
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
  # TODO truncate instead of round if prec < 0?
  def to_dmsstr(prec=3)
    width = prec == 0 ? 2 : prec+3
    scale = (3600 * 10 ** prec).to_f
    "%02dd%02dm%0#{width}.#{prec}fs" % ((self*scale).round/scale).to_dms
  end
  # Convert +self+ to "##:##:##.###" format truncated to +prec+ fractional places.
  def to_hmsstr(prec=3)
    width = prec == 0 ? 2 : prec+3
    scale = (3600 * 10 ** prec).to_f
    "%02d:%02d:%0#{width}.#{prec}f" % ((self*scale).to_i/scale).to_dms
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
    d, m, s = d.to_i, m.to_i, s.to_f
    m, s = -m, -s if d == 0 && self =~ /^\s*-/
    Math::dms_to_d(d,m,s)
  end
  # Parse a "hh:mm:ss.sss" String to Float hours.
  alias :hms_to_h :dms_to_d
end

# Add astronomy-related and other utilty methods to the +DateTime+ class.
class DateTime

  # The J2000 epoch
  J2000 = civil(2000,1,1,12)

  # Create a +DateTime+ object from a numeric Astronomical Julian Date.
  def self.ajd(d)
    J2000 + d - J2000.ajd
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
end
