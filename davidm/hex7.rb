#!/usr/bin/env ruby
$-w = true if $0 == __FILE__

require 'enumerator'
require 'gauss2d'
require 'mirdl'
include Mirdl
include Math

STDOUT.sync = true
STDERR.sync = true

# Add cis method to Numeric class
class Numeric
  def cis
    Complex.polar(1.0, self)
  end
end

# Process command line
keyini
vis = mkeyf(:vis)
keyfin

bug('f','no datasets given (try "vis=...")') if vis.empty?
bug('f',"need exactly 7 datasets (got #{vis.length})") unless vis.length == 7

all_gains = {}
all_pos = {}

# For each dataset name given
for dsname in vis
  STDERR.puts "reading dataset #{dsname}"

  # Open dataset
  tno = uvopen(dsname, :r)

  # Get gains from dataset
  ds_gains = get_gains(tno)

  # Save dataset's gains into all_gains
  all_gains.merge!(ds_gains)

  # Get gains times for this dataset
  gain_times = ds_gains.keys.sort!

  # Foreach gain time
  for gt in gain_times
    # Scan through dataset until first dump after current gain time
    # (poor man's search algoithm)
    uvscan(tno, :time) until gt < uvrdvrd(tno, :time)

    # Get sky position
    # TODO Allow selection of radec, obsradec, antazel, azel
    # Each position is an angle, so store it as sin/cos components (i.e.
    # polar(1,x)) to prevent problems wrapping around north etc.
    all_pos[gt] = [:ra, :dec].map {|v| uvrdvrd(tno, v).cis}
  end
end

all_times = all_gains.keys.sort!

nsols = all_times.length
raise "invalid number of solutions (#{nsols} % 7 != 0)" if nsols % 7 != 0
STDERR.puts "got a total of #{nsols} solutions, #{nsols/7} hex patterns"

## Dump all data in time order
#for t in all_times
#  pos = all_pos[t]
#  gains = all_gains[t]
#  printf "%s %6.2f %6.2f %s\n", DateTime.ajd(t),
#    pos[0].angle.r2d, pos[1].angle.r2d, gains.abs.to_a[0,4].inspect
#end

# Hexes will store one array of fitted gaussian parameters per hex pattern.
# Each array of fitted gaussian parameters will contain one fit per antpol
# Each fit consists of [niters, [gauss params], [chi], covar]
hexes = []

# Take positions and gain solutions seven at a time
# (i.e. one hex pattern at a time)
all_times.each_slice(7) do |hex_times|
  pos7 = hex_times.map {|t| all_pos[t]}
  gains7 = hex_times.map {|t| all_gains[t]}

  # Calc delta pos in arcmin
  # TODO Do not assume first pointing is center
  p0x, p0y = pos7[0].map {|z| z.conj}
  dpos7 = pos7.map do |px, py|
    dp = [px*p0x, py*p0y]
    # Convert from cis to arcminutes
    dp.map! {|c| c.angle * 180 * 60 / PI}
    # Multiply dpx (e.g. dra) by cos(p0y) (e.g. cos(el0))
    dp[0] *= p0y.real
    dp
  end

  # Calc inverse magnitude of all 7 gains arrays
  invgains7 = gains7.map do |gains|
    # NArray has no map method!?
    gains.to_a.map {|g| g==0 ? 0 : 1.0/g.abs}
  end
  # Transpose invgains7
  # Before: invgains7 = [[hex0ap0,hex0ap1,...],[hex1ap0,hex1ap1,...],...]
  # After:  invgains7 = [[hex0ap0,hex1ap0,...],[hex0ap1,hex1ap1,...],...]
  # (Array has no transpose! method!?)
  invgains7 = invgains7.transpose

  # For each invgains7 element (i.e. antpol hex inverse gains)
  STDERR.puts "Fitting Gaussian to hex pattern #{hexes.length+1}"
  hexes << invgains7.map do |aphex|
    if aphex[0] != 0
      # fit 2d gaussian
      iter, solver, status = Gauss2d.fit(dpos7, aphex, solver)
      # dup stuff retuned from solver due to current GSL limitation/bug
      [iter, solver.position.dup, solver.f.dup, solver.covar(0).dup*(solver.f.dnrm2**2/(7-5))]
      #p [iter, solver.position]
      #p solver.covar(0)*(solver.f.dnrm2**2/(7-5))
      #p solver.covar(0)
      #p GSL::MultiFit.covar(solver.jac, 0)
      #p solver.covar(0.1)
      #p GSL::MultiFit.covar(solver.jac, 0.1)
      #exit
    end
  end
  #break # DEBUG: just do first one
end

# dump results for each hex pattern
hexes.each_with_index do |hex, i|
  puts "---- Gaussian fits for hex pattern #{i+1} ----"
  hex.each_with_index do |(iters, gauss, chi, covar), ap|
    ant = (ap >> 1) + 1
    pol = (?X + (ap&1)).chr
    if iters.nil?
      #printf "%2d %s hex %d iters 0\n", ant, pol, i+1
      next
    end
    printf "%2d %s hex %d iters %-2d :  %5.3f", ant, pol, i+1, iters, gauss[0]
    gauss[1..-1].each {|x| printf "  %7.3f", x}
    printf "  |X|= %.4f\n", chi.dnrm2
  end
end

# Done!
