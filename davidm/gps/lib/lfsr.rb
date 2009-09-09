#!/usr/bin/env ruby
#
# Implements a linear feedback shift register

class LFSR
  def initialize(nbits, poly, init=0, length=nil)
    raise "invalid number of bits (#{nbits})" unless (1..64) === nbits
    @nbits = nbits
    @mask = (1 << nbits) - 1
    @poly = (poly >> 1)
    @init = init
    @length = length || @mask
    reinitialize
  end

  def reinitialize
    @state = @init
    @avail = @length
    self
  end

  def inspect
    "#<#{self.class.name}:#{object_id} @nbits=#{@nbits} " \
    "@poly=#{(@poly << 1).to_s(2)} " \
    "@init=#{@init.to_s(2).rjust(@nbits,'0')} " \
    "@state=#{@state.to_s(2).rjust(@nbits,'0')} " \
    "(#{@length-@avail}/#{@length})"
  end

  def poly
    v = 0
    w = @state & @poly
    @nbits.times {|b| v ^= 1 if w[b] == 1}
    v
  end

  def next(n=1)
    val = 0
    remaining = n
    while remaining > @avail
      remaining -= @avail
      val <<= @avail
      val |= self.next(@avail)
    end
    if remaining > 0
      remaining.times do
        @state = (@state << 1) | poly
      end
      @avail -= remaining
      val <<= remaining
      val |= @state >> @nbits
      @state &= @mask

      raise 'went past end of cycle' if @avail < 0
      reinitialize if @avail == 0
    end

    val
  end
end

if $0 == __FILE__
  delay = (ARGV[0] || '5').to_i

  g1 = LFSR.new(10,0x409,0x3ff); #p g1
  g2 = LFSR.new(10,0x74c,0x3ff); #p g2

  c1 = g1.next(1023)
  # "Delay" g2 by advancing it -delay mod 1023
  g2.next(-delay % 1023)
  c2 = g2.next(1023)

  ca = (c1 ^ c2)
  puts((ca >> 1013).to_s(8).rjust(4,'0'))

  x1a = LFSR.new(12,0x1941,0x248,4092)
  x1b = LFSR.new(12,0x1f27,0x554,4093)
  x2a = LFSR.new(12,0x1fbb,0x925,4092)
  x2b = LFSR.new(12,0x131d,0x554,4093)

  p1a = x1a.next(12+delay)
  p1b = x1b.next(12+delay)
  p2a = x2a.next(12)
  p2b = x2b.next(12)
  p = p1a ^ p1b ^ p2a ^ p2b
  puts p1a.to_s(2).rjust(12+delay,'0')
  puts p1b.to_s(2).rjust(12+delay,'0')
  puts p2a.to_s(2).rjust(12,'0').rjust(12+delay)
  puts p2b.to_s(2).rjust(12,'0').rjust(12+delay)
  puts '-' * (12+delay)
  puts p.to_s(2).rjust(12+delay,'0')
  puts((p>>delay).to_s(8).rjust(4,'0'))
end
