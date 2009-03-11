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

# gauss2d.fit returns sqrt(2)*sigma for sigma_x and sigma_y.
# This is why this conversion factor has a "/2" in the sqrt.
SIGMA2FWHM = 2*sqrt(-log(0.5)/2)

# Process command line
keyini
vis = mkeyf(:vis)

optkeys = [:squint, :absolute, :azel, :radec, :rect, :polar]
optvals = options(optkeys, :hexopts)
# Convert optkeys and optvals into a Hash
opts = Hash[*optkeys.zip(optvals).flatten!]
keyfin

if opts[:azel] && opts[:radec]
  bug('f',"cannot specify both azel and radec")
elsif !opts[:radec]
  opts[:azel] = true
end

if opts[:rect] && opts[:polar]
  bug('f',"cannot specify both rect and polar")
elsif !opts[:polar]
  opts[:rect] = true
end

bug('f','no datasets given (try "vis=...")') if vis.empty?
bug('f',"need exactly 7 datasets (got #{vis.length})") unless vis.length == 7

all_gains = {}
all_radec = {}
all_azellst = {}
lat = nil
radec0 = []
azellst0 = []

# For each dataset name given
first_vis = true
for dsname in vis
  STDERR.puts "reading dataset #{dsname}"

  # Open dataset
  tno = uvopen(dsname, :r)

  # Get latitude (first time only)
  lat ||= uvrdvrd(tno, :latitud)

  # Get gains from dataset
  ds_gains = get_gains(tno)

  # Save dataset's gains into all_gains
  all_gains.merge!(ds_gains)

  # Get gains times for this dataset
  gain_times = ds_gains.keys.sort!

  # For each gain time
  for gt in gain_times
    # Scan through dataset until first dump after current gain time
    # (poor man's search algoithm)
    uvscan(tno, :time) until gt < uvrdvrd(tno, :time)

    # Get obsra/obsdec position
    radec = [:obsra, :obsdec].map {|v| uvrdvrd(tno, v)}

    # Compute az/el
    lst = uvrdvrd(tno, :lst)
    azel = azel(radec[0], radec[1], lst, lat)

    # Each position is an angle, so store it as sin/cos components (i.e.
    # polar(1,x)) to prevent problems wrapping around north etc.
    all_radec[gt] = radec.map {|radians| radians.cis}
    all_azellst[gt] = azel.map {|radians| radians.cis}

    # Store lst along with az,el.  No need to convert lst to cos/sin comonents
    all_azellst[gt] << lst

    if first_vis
      radec0 << all_radec[gt]
      azellst0 << all_azellst[gt]
    end
  end
  first_vis = false
end

all_times = all_gains.keys.sort!

nsols = all_times.length
raise "invalid number of solutions (#{nsols} % 7 != 0)" if nsols % 7 != 0
STDERR.puts "got a total of #{nsols} solutions, #{nsols/7} hex patterns"

## Dump all data in time order
#for t in all_times
#  gains = all_gains[t]
#  radec = all_radec[t]
#  azellst = all_azellst[t]
#  printf "%s %s %6.2f %6.2f %6.2f %6.2f %s\n",
#    DateTime.ajd(t), azellst[2].r2h.to_hmsstr
#    radec[0].angle.r2d, radec[1].angle.r2d,
#    azellst[0].angle.r2d, azellst[1].angle.r2d,
#    gains.abs.to_a[0,4].inspect
#end

# Hexes will store one array of fitted gaussian parameters per hex pattern.
# Each array of fitted gaussian parameters will contain one fit per antpol
# Each fit consists of [niters, [gauss params], [chi], covar]
hexes = []

# Take positions and gain solutions seven at a time
# (i.e. one hex pattern at a time)
all_times.each_slice(7) do |hex_times|
  gains7 = hex_times.map {|t| all_gains[t]}
  radec7 = hex_times.map {|t| all_radec[t]}
  azellst7 = hex_times.map {|t| all_azellst[t]}

  # Calc delta pos in arcmin
  # TODO Do not assume first pointing is center
  ra0, dec0 = radec7[0]
  if opts[:radec]
    ra0, dec0 = ra0.conj, dec0.conj
    dpos7 = radec7.map do |ra, dec|
      # This is a small angle approximation.  If needed, ra/dec and ra0/dec0
      # could be converted to vectors and their dot product taken
      dp = [ra*ra0, dec*dec0]
      # Convert from cis to arcminutes
      dp.map! {|z| z.angle * 180 * 60 / PI}
      # Multiply dra by cos(dec0)
      dp[0] *= dec0.real
      #p dp
      dp
    end
  else
    dpos7 = azellst7.map do |az, el, lst|
      azel0 = azel(ra0.angle, dec0.angle, lst, lat).map {|radians| radians.cis.conj}
      # This is a small angle approximation.  If needed, az/el and azel0
      # could be converted to vectors and their dot product taken
      dp = [az*azel0[0], el*azel0[1]]
      # Convert from cis to arcminutes
      dp.map! {|z| z.angle * 180 * 60 / PI}
      # Multiply daz by cos(el0)
      dp[0] *= azel0[1].real
      #p dp
      dp
    end
  end
  #exit

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
  hexes << invgains7.map do |aphexinvgains|
    if aphexinvgains[0] != 0
      # fit 2d gaussian
      iter, solver, status = Gauss2d.fit(dpos7, aphexinvgains, solver)
      # dup stuff retuned from solver due to current GSL limitation/bug
      apfit = [iter, solver.position.dup, solver.f.dup, solver.covar(0).dup*(solver.f.dnrm2**2/(7-5))]
      apfit
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

if opts[:squint]
  ant = 0
  hexes.transpose.each_slice(2) do |xfits, yfits|
    ant += 1
    if xfits[0].nil? && yfits[0].nil?
      printf "%02d absent\n", ant
      next
    elsif xfits[0].nil?
      printf "%02d missingX\n", ant
      next
    elsif yfits[0].nil?
      printf "%02d missingY\n", ant
      next
    end
    xgauss = xfits.transpose[1]
    ygauss = yfits.transpose[1]
    xoff = [1,2].map {|i| xgauss.inject(0) {|s,g| s += g[i]} / xgauss.length}
    yoff = [1,2].map {|i| ygauss.inject(0) {|s,g| s += g[i]} / ygauss.length}
    #p [ant, xoff, yoff]
    sq0 = yoff[0] - xoff[0]
    sq1 = yoff[1] - xoff[1]
    sqr, sqt = Complex(sq0, sq1).polar
    sqt = sqt.r2d
    # TODO Print header
    # TODO Print quality indicated (X^2, ave_iters, etc)
    printf "%02d squint %7.3f x %7.3f arcmin  --> %7.3f arcmin @ %8.3f degrees\n",
      ant, sq0, sq1, sqr, sqt
  end
else
  # dump results for each hex pattern
  # TODO Print column header
  hexes.transpose.each_with_index do |fits, ap|
    ant = (ap >> 1) + 1
    pol = (?X + (ap&1)).chr
    fits.each_with_index do |(iters, gauss, chi, covar), i|
      if iters.nil?
        #printf "%2d %s hex %d iters 0\n", ant, pol, i+1
        next
      end
      printf "%02d %s hex %d iters %-2d : %5.3f", ant, pol, i+1, iters, gauss[0]
      if opts[:polar]
        r, th = Complex(*gauss[1,2]).polar
        gauss[1] = r
        gauss[2] = th.r2d
      elsif opts[:absolute] && opts[:azel]
        # Divide by cos(el) of central pointing for this hex
        gauss[1] /= azellst0[i][1].real
      elsif opts[:absolute] && opts[:radec]
        # Divide by cos(dec) of central pointing for this hex
        gauss[1] /= radec0[i][1].real
      end
      gauss[3] *= SIGMA2FWHM
      gauss[4] *= SIGMA2FWHM
      gauss[1..-1].each {|x| printf "  %8.3f", x}
      printf "  |X|= %.4f\n", chi.dnrm2
    end
  end
end

# Done!
