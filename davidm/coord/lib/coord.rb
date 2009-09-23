# Defines module Coord with methods for manipulation of geometric vectors.
# The Coord module is included in the Array class, so all methods of Coord are
# available to instances of Array.
#
# For method documentation, see the Coord module.

# Methods for manipulation of geometric vectors.  This module is included in
# Array, so all methods of Coord are available to instances of Array.
module Coord
  # call-seq: op(other_array) {|self[i], other[i]| ...} -> Array
  # call-seq: op(non_array) {|self[i], other| ...} -> Array
  #
  # Facilitates element-wise operations on self by other.
  # other can be Array but need not be.
  # If other is an array, yields elements from self and elements of other.
  # Otherwise, yields elements from self and other.
  #
  # Returns result; leaves self and other unchanged.
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
  # Facilitates in place element-wise operations on self by other.
  # other can be Array but need not be.
  # Returns modified self; leaves other unchanged.
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

  # Returns result of adding self and other.
  def add(other)
    op(other) {|a,b| a+b}
  end

  # Adds other to self.  Returns modified self.
  def add!(other)
    op!(other) {|a,b| a+b}
  end

  # Returns result of subtracting other from self.
  def sub(other)
    op(other) {|a,b| a-b}
  end

  # Subtracts other from self.  Returns modified self.
  def sub!(other)
    op!(other) {|a,b| a-b}
  end

  # Returns result of multiplying self and other.
  def mul(other)
    op(other) {|a,b| a*b}
  end

  # Multiplies self by other.  Returns modified self.
  def mul!(other)
    op!(other) {|a,b| a*b}
  end

  # Returns result of dividing self by other.
  def div(other)
    op(other) {|a,b| a/b}
  end

  # Divides self by other.  Returns modified self.
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

  # Returns dot product of self and other.
  def dot(other)
    mul(other).sum
  end

  # Returns cross product of self and other.
  def cross(other)
    raise 'self.length < 3' if length < 3
    raise 'other.length < 3' if other.length < 3
    [
      self[1] * other[2] - self[2] * other[1],
      self[2] * other[0] - self[0] * other[2],
      self[0] * other[1] - self[1] * other[0],
    ]
  end

  # Returns absolute value (aka magnitude) of self
  def abs
    Math.sqrt(dot(self))
  end
  alias :mag :abs

  # Returns angle between vectors represented by self and other
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
  # For length < 3, treats self as [r, th] and returns [x, y].
  # For length <= 3, treats self as [r, az, el] and returns [x, y, y].
  def p2r
    if length < 3
      r  = self[0] || 0
      th = self[1] || 0
      [r*Math.cos(th), r*Math.sin(th)]
    else
      r  = self[0]
      az = self[1]
      el = self[2]
      z = r * Math.sin(el)
      r *= Math.cos(el)
      [r*Math.cos(az), r*Math.sin(az), z]
    end
  end
end

class Array
  include Coord
end
