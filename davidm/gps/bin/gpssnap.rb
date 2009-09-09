#!/usr/bin/env ruby
$-w = true if $0 == __FILE__

# Loads and analyzes a dat file from an ibob ddc snepshot of a gps signal.  An
# ibob ddc snapshot is a text file containing four columns...
#
# re0 im0 re1 im1
#
# It has 8192 rows.

# Number of samples per chip
SC = 102.5
NCHIPS = (8192 / SC).to_i + 1

require 'cacorr'
require 'pgplot/plotter'
include Pgplot
include Math

filename = ARGV[0]
prn = Integer(ARGV[1])

g0, g1 = load_ddc(filename)
g = g0

# Get full CA chipping sequence for given PRN
# (upsampled to DDC sample rate)
ca = chips(prn, 0, 1023)
x, fx, fy = correlate(g, ca, fx, fy)
pk = x.abs.max_index
quality = x[pk].abs / (g.abs.sum * Math.sqrt(2.0/3.0))
puts "quality = #{quality*100} %"
chip, chip_fract = (ca.len-pk-1).divmod(SC)
chip = chip.to_i # Ruby 1.8.4-ism
ca=chips(prn,chip,NCHIPS+1)[chip_fract.to_i,8192]
# py is the P(Y) code that remains after taking out the C/A code
py = g * -ca
phase = py.sum.angle
puts "phase = #{phase*180/PI} degrees"
grot90 = g * GSL::Complex.polar(1, PI/2-phase);
grot = g * GSL::Complex.polar(1, -phase);
pyrot = py * GSL::Complex.polar(1, -phase);

Plotter.new(:ask=>true)
plot(0...8192, grot90.angle)
#plot(0...1000, g[0,1000].angle)
pgsci(Color::GREEN)
pgline((0...8192).to_a, pyrot.angle.to_na)
pgsci(Color::RED)
pgline((0...8192).to_a, (-PI*ca/2).to_na)
plot(grot.re, grot.im,
  :line=>:none,
  :marker=>Marker::DOT,
  :just=>true,
  :xlabel=>'Real (counts)',
  :ylabel=>'Imaginary (counts)',
  :title=>'Raw voltages (rotated)')
plot(grot.re, grot.im,
  #:line=>:none,
  #:marker=>Marker::DOT,
  :just=>true,
  :xlabel=>'Real (counts)',
  :ylabel=>'Imaginary (counts)',
  :title=>'Raw voltages (rotated)')
#plot(pyrot.re, pyrot.im,
#  :line=>:none,
#  :marker=>Marker::DOT,
#  :just=>true,
#  :title=>'C/A demodulated voltages (rotated)')
#pyrot2 = (pyrot-pyrot.mean).pow(GSL::Complex[2,0])
#plot(pyrot2.re, pyrot2.im,
#  :line=>:none,
#  :marker=>Marker::DOT,
#  :just=>true,
#  :title=>'(C/A demodulated voltages (rotated) less mean) squared')
