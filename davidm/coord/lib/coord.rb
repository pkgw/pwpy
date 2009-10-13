# Defines module Coord with methods for manipulation of geometric vectors.
# The Coord module is included in the Array class, so all methods of Coord are
# available to instances of Array.
#
# For method documentation, see the Coord module.

# Methods for manipulation of geometric vectors.  This module is included in
# Array, so all methods of Coord are available to instances of Array, but the
# module tries to be as general as possible.
module Coord
  # Returns self[0]||0
  def x; self[0]||0; end

  # Returns self[1]||0
  def y; self[1]||0; end

  # Returns self[2]||0
  def z; self[2]||0; end

  # Sets self[0] to +x+.
  def x=(x); self[0] = x; end

  # Sets self[1] to +y+
  def y=(y); self[1] = y; end

  # Sets self[2] to +z+
  def z=(z); self[2] = z; end

  # call-seq: op(other_array) {|self[i], other[i]| ...} -> Array
  # call-seq: op(non_array) {|self[i], other| ...} -> Array
  #
  # Facilitates element-wise operations on +self+ by +other+.
  # +other+ can be Array but need not be.
  # If +other+ is an array, yields elements from +self+ and elements of +other+.
  # Otherwise, yields elements from +self+ and +other+.
  #
  # Returns result; leaves +self+ and +other+ unchanged.
  def op(other)
    n = length
    if Array === other
      n = other.length if other.length < n
      (0...n).map do |i|
        yield self[i], other[i]
      end
    else
      map {|e| yield e, other}
    end
  end

  # call-seq: op!(other_array) {|self[i], other[i]| ...} -> modified self
  # call-seq: op!(non_array) {|self[i], other| ...} -> modified self
  #
  # Facilitates in place element-wise operations on +self+ by +other+.
  # +other+ can be Array but need not be.
  # Returns modified +self+; leaves +other+ unchanged.
  def op!(other)
    n = length
    if Array === other
      n = other.length if other.length < n
      (0...n).map do |i|
        self[i] = yield self[i], other[i]
      end
    else
      map! {|e| yield e, other}
    end
  end

  # Returns result of adding +self+ and +other+.
  def add(other)
    op(other) {|a,b| a+b}
  end

  # Adds +other+ to self.  Returns modified +self+.
  def add!(other)
    op!(other) {|a,b| a+b}
  end

  # Returns result of subtracting +other+ from +self+.
  def sub(other)
    op(other) {|a,b| a-b}
  end

  # Subtracts +other+ from self.  Returns modified +self+.
  def sub!(other)
    op!(other) {|a,b| a-b}
  end

  # Returns result of multiplying +self+ and +other+.
  def mul(other)
    op(other) {|a,b| a*b}
  end

  # Multiplies self by +other+.  Returns modified +self+.
  def mul!(other)
    op!(other) {|a,b| a*b}
  end

  # Returns result of dividing +self+ by +other+.
  def div(other)
    op(other) {|a,b| a/b}
  end

  # Divides self by +other+.  Returns modified +self+.
  def div!(other)
    op!(other) {|a,b| a/b}
  end

  # Returns sum of all elements
  def sum
    inject {|s,x| s+=x}
  end

  # Returns product of all elements
  def prod
    inject {|s,x| s*=x}
  end

  # Returns dot product of +self+ and +other+.
  def dot(other)
    mul(other).sum
  end

  # Returns cross product of +self+ and +other+.
  def cross(other)
    raise 'self.length < 3' if length < 3
    raise 'other.length < 3' if other.length < 3
    [
      self[1] * other[2] - self[2] * other[1],
      self[2] * other[0] - self[0] * other[2],
      self[0] * other[1] - self[1] * other[0],
    ]
  end

  # Returns absolute value (aka magnitude) of +self+
  def abs
    Math.sqrt(dot(self))
  end
  alias :mag :abs

  # Returns angle between vectors represented by +self+ and +other+
  # or NaN if the product of their absolute values is <= small**2.
  def angle(other, small=0.00000001)
     absv1 = self.abs
     absv2 = other.abs

     if (absv1*absv2 > small*small)
       temp = dot(other) / (absv1*absv2)
       temp = 1.0 if temp > 1.0
       temp = -1.0 if temp < -1.0
       Math.acos( temp );
     else
       # Return NaN
       0.0/0.0
     end
  end

  # Polar to rectangular conversion.
  # For length < 3, treats +self+ as [r, th] and returns [x, y].
  # For length >= 3, treats +self+ as [r, az, el] and returns [x, y, z].
  def p2r
    if length < 3
      r  = self[0] || 0
      th = self[1] || 0
      [r*Math.cos(th), r*Math.sin(th)]
    else
      r  = self[0]
      az = self[1]
      el = self[2]
      rxy = r * Math.cos(el)
      x = rxy * Math.cos(az)
      y = rxy * Math.sin(az)
      z = r * Math.sin(el)
      [x, y, z]
    end
  end

  # Rectangular to polar conversion.
  # For length < 3, treats +self+ as [x, y] and returns [r, th].
  # For length >= 3, treats +self+ as [x, y, z] and returns [r, az, el].
  def r2p
    if length < 3
      x = self[0] || 0
      y = self[1] || 0
      [Math.hypot(x,y), Math.atan2(y,x)]
    else
      x = self[0]
      y = self[1]
      z = self[2]
      rxy = Math.hypot(x,y)
      az = Math.atan2(y,x)
      el = Math.atan2(z,rxy)
      r = Math.hypot(rxy,z)
      [r, az, el]
    end
  end

  # Rotates +self+ around axis by +theta+ radians
  # +axis+ = 0 -> rotate around X axis
  # +axis+ = 1 -> rotate around Y axis
  # +axis+ = 2 -> rotate around Z axis
  def rot(theta, axis)
    i, j = [0, 1, 2] - [axis]
    c = Math.cos(theta)
    s = Math.sin(theta)
    s = -s if axis == 1
    a = self[i]*c - self[j]*s
    b = self[i]*s + self[j]*c
    r = []
    r[i] = a
    r[j] = b
    r[axis] = self[axis]
    r
  end

  # In-pace versino of rot (modifies +self+)
  def rot!(theta, axis)
    self[0,3] = rot(theta, axis)
  end

  # Rotates +self+ counter-clockwise around X axis by +theta+ radians
  def rotx(theta)
    rot(theta, 0)
  end

  # In-place version of rotx (modifies +self+)
  def rotx!(theta)
    rot!(theta, 0)
  end

  # Rotates +self+ counter-clockwise around Y axis by +theta+ radians
  def roty(theta)
    rot(theta, 1)
  end

  # In-place version of roty (modifies +self+)
  def roty!(theta)
    rot!(theta, 1)
  end

  # Rotates +self+ counter-clockwise around Z axis by +theta+ radians
  def rotz(theta)
    rot(theta, 2)
  end

  # In-place version of rotz (modifies +self+)
  def rotz!(theta)
    rot!(theta, 2)
  end

end

class Array
  include Coord
end
