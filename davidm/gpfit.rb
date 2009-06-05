#!/usr/bin/env ruby
$-w = true if $0 == __FILE__

#= gpfit.rb - Fit Gaussian primary beam to gains from hex7 data
#& dhem
#: calibration analysis
#+ gpfit.rb - Fit Gaussian primary beam to gains from hex7 data
#@ vis
# Specifies which datasets to use.  Need at least seven.
#@ options
# This controls processing and coordinate system options.
# Possible values are:
#   "azel"     Beam offsets calculated in an azimuth/elevation frame
#   "radec"    Beam offsets calculated in an RA/dec frame
#              (azel and radec are mutually exclusive)
#   "rect"     Beam offsets output in rectangular form
#   "polar"    Beam offsets output in polar form
#              (rect and polar are mutually exclusive)
#   "absolute" Azimuth or RA term is adjusted by cos(el or dec)
#   "squint"   Output difference between X and Y pol beam offsets
#   "verbose"  Output extra informaion (for debugging)
# If no options are given, gpfit.rb uses options=azel,rect.
#--

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

# Create Position class and add a "load(tno)" method
Position = Struct.new(:time, :lst, :latitud, :ra, :dec, :dra, :ddec, :az, :el, :daz, :del)
class Position
  UVMEMBERS = [:time, :lst, :latitud, :ra, :dec, :dra, :ddec]
  def self.load(tno)
    pos = Position.new
    UVMEMBERS.each {|vr| pos[vr] = uvrdvrd(tno, vr)}
    pos
  end
end

# gauss2d.fit returns sqrt(2)*sigma for sigma_x and sigma_y.
# This is why this conversion factor has a "/2" in the sqrt.
SIGMA2FWHM = 2*sqrt(-log(0.5)/2)

# Process command line
keyini
vislist = mkeyf(:vis).sort!

optkeys = [:squint, :absolute, :azel, :radec, :rect, :polar, :verbose]
optvals = options(optkeys)
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

bug('f','no datasets given (try "vis=...")') if vislist.empty?
bug('f',"need at least 7 datasets (got #{vislist.length})") if vislist.length < 7

# all_gains and all_pos are indexed by dataset name
# first dataset (sorted lexicographically) is assumed to be center pointing
all_gains = {}
all_pos = {}

ra0  = nil
dec0 = nil
az0 = nil
el0 = nil

nfeed = nil

# For each dataset name given
#first_vis = true
for vis in vislist
  STDERR.puts "reading dataset #{vis}" if opts[:verbose]

  # Open dataset
  tno = uvopen(vis, :r)


  # Get gains from dataset
  gains = get_gains(tno)
  # skip dataset if no gains
  next if gains.nil? || gains.empty?

  # Get nfeed (first time only)
  if nfeed.nil?
    nants = uvrdvri(tno, :nants)
    raise "dataset #{vis} lacks 'nants' UV variable" if nants == 0
    nfeed = gains[gains.keys.first].length / nants
    if nfeed == 1
      raise 'cannot do squint because nfeed = 1' if opts[:squint]
    elsif nfeed != 2
      raise "unsupported nfeed: #{nfeed}"
    end
  end

  # Get gains times for this dataset
  gain_times = gains.keys.sort!

  # Save dataset's time-ordered gains into all_gains
  all_gains[vis] = gain_times.map {|k| gains[k]}

  # Create empty array entry for dataset's time-ordered positions
  all_pos[vis] = []

  # For each gain time
  for gt in gain_times
    # Scan through dataset until first dump on or after current gain time (poor
    # man's search algoithm)
    time = uvrdvrd(tno, :time)
    while time > 0.0 && time < gt
      uvscan(tno, :time)
      time = uvrdvrd(tno, :time)
    end

    # Get current sky position from dataset
    pos = Position.load(tno)

    # Initialize ra0/dec0 and az0/el0?
    if ra0.nil?
      raise "cannot have dra != 0.0 in center pointing! (got #{pos[:dra].r2d * 3600} arcsec)" if pos[:dra] != 0.0
      raise "cannot have ddec != 0.0 in center pointing! (got #{pos[:ddec].r2d * 3600} arcsec)" if pos[:ddec] != 0.0
      ra0 = pos[:ra]
      dec0 = pos[:dec]
      # Precess to obspntra/obspntdec
      obsra0, obsdec0 = precess(DateTime::J2000.ajd, ra0, dec0, pos[:time])
      # Convert to az/el
      az0, el0 = azel(obsra0, obsdec0, pos[:lst], pos[:latitud])
    end

    # If dra and ddec are 0.0
    if pos[:dra] == 0.0 && pos[:ddec] == 0.0
      # Compute dra and ddec
      pos[:dra] = (pos[:ra] - ra0) * cos(dec0)
      pos[:ddec] = pos[:dec] - dec0
      # Set ra/dec to ra0/dec0
      pos[:ra] = ra0
      pos[:dec] = dec0
    end

    # Compute pntra/pntdec
    pntra = pos[:ra] + pos[:dra]/cos(pos[:dec])
    pntdec = pos[:dec] + pos[:ddec]
    # Precess to obspntra/obspntdec
    obspntra, obspntdec = precess(DateTime::J2000.ajd, pntra, pntdec, pos[:time])
    # Convert to az/el
    pos[:az], pos[:el] = azel(obspntra, obspntdec, pos[:lst], pos[:latitud])
    # Complute daz/del
    # Precess ra0, dec0 to obsra0, obsdec0
    obsra0, obsdec0 = precess(DateTime::J2000.ajd, ra0, dec0, pos[:time])
    # Convert to az0/el0
    az0, el0 = azel(obsra0, obsdec0, pos[:lst], pos[:latitud])
    # Compute and save daz/del
    # TODO Handle over-the-top and az wraps
    pos[:daz] = (pos[:az] - az0) * cos(el0)
    pos[:del] = pos[:el] - el0

    # Save position
    all_pos[vis] << pos
  end # foreach gain time

  uvclose(tno)
end # foreach vis

bug('f', "need at least 7 datasets with gains (got #{all_gains.length})") if all_gains.length < 7
nsols = all_gains.inject(0) {|m,(k,v)| m += v.length}
bug('f', "invalid number of solutions (#{nsols} % #{all_gains.length} != 0)") if nsols % all_gains.length != 0
STDERR.puts "got a total of #{nsols} solutions, will do #{nsols/all_gains.length} fits" if opts[:verbose]

## Dump all data in time order
#all_gains.keys.sort!.each do |vis|
#  gains = all_gains[vis]
#  pos = all_pos[vis]
#  puts "dataset: #{vis}"
#  pos.each_index do |i|
#    printf "sol %2d : %s : %s\n", i, pos[i], gains[i][0..3].abs.to_a.inspect
#    #printf "       : %5f : %5f\n", hypot(pos[i][:dra],pos[i][:ddec]).r2d*3600, hypot(pos[i][:daz],pos[i][:del]).r2d*3600
#  end
#end
#exit

# Convert all_gains and all_pos from Hashes indexed by vis name
# into Arrays with nvis entries, each of which is nsols long
gains_list = all_gains.keys.sort!.map {|k| all_gains[k]}
pos_list = all_pos.keys.sort!.map {|k| all_pos[k]}

# Transpose gains_list and pos_list so that they have nsols elements, each with
# nvis entries
gains_list = gains_list.transpose
pos_list = pos_list.transpose

# fits will store one array of fitted gaussian parameters per gains solution.
# Each array of fitted gaussian parameters will contain one fit per antpol
# Each fit consists of [niters, [gauss params], [chi], covar]
fits = []

# For each gain solution
gains_list.each_index do |soln_i|
  gains_soln_i = gains_list[soln_i]
  pos_soln_i = pos_list[soln_i]

  STDERR.puts "Fitting Gaussians to gain solution #{soln_i+1}" if opts[:verbose]

  # Get position offsets from each vis for this gain solution
  dpos = pos_soln_i.map do |p| # p is pos_soln_i_vis_j
    (opts[:radec] ? [p[:dra], p[:ddec]] : [p[:daz], p[:del]]).map {|rad| rad.r2d*60.0}
  end

  # Do a fit for each antpol in this gain solution
  antpol_count = gains_soln_i[0].length
  fits_soln_i = (0...antpol_count).map do |ap_k|
    # Gather gains from each vis for this antpol and gain solution
    gains_soln_i_ap_k = gains_soln_i.map {|g| g[ap_k]} # g is gains_soln_i_vis_j
    # If any vis had no gains solution, skip antpol
    # TODO Ignore vis datasets that have no gains solution, but only skip
    # antpol if too few vis have gains solutions.
    next nil if gains_soln_i_ap_k.any? {|apg| apg == 0.0}
    # Normalize gains for this antpol to central pointing and take abs
    #gains_soln_i_ap_k.map! {|apg| (gains_soln_i_ap_k[0]/apg).abs}
    # Invert gains for this antpol and take abs
    gains_soln_i_ap_k.map! {|apg| (1.0/apg).abs}

    #DEBUG p dpos; p gains_soln_i_ap_k; exit
    iter, solver, status = Gauss2d.fit(dpos, gains_soln_i_ap_k, solver)
    # dup stuff retuned from solver due to current GSL limitation/bug
    fit_soln_i_ap_k = [iter, solver.position.dup, solver.f.dup, solver.covar(0).dup*(solver.f.dnrm2**2/(dpos.length-5))]
    #fit_soln_i_ap_k
  end # foreach antpol fit for this gains solution

  fits << fits_soln_i
  #DEBUG p fits; exit
  #break # DEBUG: just do first one
end # foreach gains solution

if opts[:squint]
  ant = 0
  fits.transpose.each_slice(2) do |xfits, yfits|
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

    # TODO Be more tolerant of some but not all fits being bad
    badfit_x = xfits.transpose[0].any? {|n| n >= Gauss2d::MAXITER}
    badfit_y = yfits.transpose[0].any? {|n| n >= Gauss2d::MAXITER}
    if badfit_x && badfit_y
      printf "%02d badfitXY\n", ant
      next
    elsif badfit_x
      printf "%02d badfitX\n", ant
      next
    elsif badfit_y
      printf "%02d badfitY\n", ant
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
    # TODO Print quality indicated (X^2, ave_iters, etc)
    printf "%02d squint %7.3f x %7.3f arcmin  --> %7.3f arcmin @ %8.3f degrees\n",
      ant, sq0, sq1, sqr, sqt
  end
else
  # Print column header
  if opts[:azel] && opts[:rect]
    puts '#ant pol fit iters  :  pkval     az_off   el_off  az_fwhm  el_fwhm  |residual|'
  elsif opts[:radec] && opts[:rect]
    puts '#ant pol fit iters  :  pkval     ra_off  dec_off  ra_fwhm dec_fwhm  |residual|'
  elsif opts[:azel] && opts[:polar]
    puts '#ant pol fit iters  :  pkval    abs_off  ang_off  az_fwhm  el_fwhm  |residual|'
  else # opts[:radec] && opts[:polar]
    puts '#ant pol fit iters  :  pkval    abs_off  ang_off  ra_fwhm dec_fwhm  |residual|'
  end
    puts '###############################################################################'
  # dump results for each gains solution
  fits.transpose.each_with_index do |fits_soln_i, ap|
    # Calc ant differently and set pol to 'I' if nfeed is 1
    ant = (nfeed == 1) ? (ap + 1) : ((ap >> 1) + 1)
    pol = (nfeed == 1) ? 'I' : ((?X + (ap&1)).chr)
    fits_soln_i.each_with_index do |(iters, gauss, chi, covar), i|
      if iters.nil?
        #printf "%2d %s fit %d iters 0\n", ant, pol, i+1
        next
      end
      printf "%02d %s fit %d iters %-2d : %5.2e", ant, pol, i+1, iters, gauss[0]
      if opts[:polar]
        r, th = Complex(*gauss[1,2]).polar
        gauss[1] = r
        gauss[2] = th.r2d
      elsif opts[:absolute] && opts[:azel]
        # Divide by cos(el) of central pointing for this fit
        # TODO Should be el0 for this solution interval!
        gauss[1] /= cos(el0)
      elsif opts[:absolute] && opts[:radec]
        # Divide by cos(dec) of central pointing for this fit
        # TODO Should be dec0 for this solution interval!
        gauss[1] /= cos(dec0)
      end
      gauss[3] *= SIGMA2FWHM
      gauss[4] *= SIGMA2FWHM
      gauss[1..-1].each {|x| printf " %8.3f", x}
      printf "  |X|= %.4f\n", chi.dnrm2
    end
  end
end

# Done!
