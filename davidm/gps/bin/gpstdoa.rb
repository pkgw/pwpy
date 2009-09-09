#!/usr/bin/env ruby

require 'optparse'

opts = {
  :device    => ENV['PGPLOT_DEV'] || '/xs',
  :freq      => 1.57542,
  :glevel    => 1,
  :nxy       => [2, 2],
  :verbose   => 0
}

OP = OptionParser.new do |op|
  op.program_name = File.basename($0)

  op.banner = "Usage: #{op.program_name} PRN [OPTIONS] FILENAME"
  op.separator('')
  op.separator('Performs TDOA analysis of GPS time domain data')
  op.separator('')
  op.separator('Options:')

  op.on('-d', '--device=DEV', "PGPLOT device [ENV['PGPLOT_DEV']||'/xs']") do |o|
    opts[:device] = o
  end
  op.on('-f', '--freq=MHZ', Float, 'Specify sky frequency in MHz [1575.42]') do |o|
    opts[:freq] = o / 1e3
  end
  op.on('-g', '--glevel=LEVEL', Integer, 'Specify graph level [1]') do |o|
    opts[:glevel] = o
  end
  op.on('-n', '--nxy=NX,NY', Array, 'Controls subplot layout [2,2]') do |o|
    if o.length != 2
      raise OptionParser::InvalidArgument.new('invalid NX,NY')
    end
    opts[:nxy] = o.map {|s| Integer(s) rescue 2}
  end
  op.on('-v', '--verbose=[LEVEL]', Integer, 'Verbosity level [0]') do |o|
    opts[:verbose] = (o ? o : opts[:verbose] + 1)
  end
  #op.on('-v', '--[no-]verbose', 'Be verbose') do |o|
  #  opts[:verbose] +=  o ? 1 : -1
  #end
  op.separator('')
  op.on_tail('-h','--help','Show this message') do
    puts op.help
    exit
  end
end
OP.parse!

if ARGV.empty?
  puts OP.help()
  exit
end

require 'gpsdump'
require 'pgplot/plotter'
include Pgplot

STDOUT.sync = true

class GSL::Vector
  def unwrap!(tol=Math::PI, wrap=2*Math::PI)
    wraps = 0
    prev = self[0]
    (1...size).each do |i|
      diff = self[i] - prev
      if diff > tol
        wraps -= wrap
      elsif diff < -tol
        wraps += wrap
      end
      self[i] += wraps
      prev += diff
    end
    self
  end
  def unwrap(tol=Math::PI, wrap=2*Math::PI)
    dup.unwrap!(tol,wrap)
  end
end

def delay_phase(v)
  len = v.length
  dcbin = len/2
  vpad = LAG_WORK[v.length] ||= GSL::Vector::Complex(8*v.length)

  # vpad[0...dcbin] = v[-dcbin..-1]
  dcbin.times {|i| vpad[i] = v[

  vpad[-dcbin..-1] = v[0...dcbin]
  vpad[0] = 0
  lag = vpad.to_gv_complex.forward!
  #magphase(lag, :xlabel => 'Lag', :title => "Lag Space (w/o DC)")
  labs=lag.abs
  peak_idx = labs.max_index
  peak_lag = ((peak_idx + vpad.length/2) % vpad.length - vpad.length/2) / 8.0
  #puts "Max lag is #{peak_lag}"
  [peak_lag, ((v[dcbin-1]+v[dcbin+1])/2).angle]
end

# Sampling frequency (samples per second)
FS = 100 * (1<<20)
# Sampling interval (seconds per sample)
TS = Rational(1,FS)
TS_NANOS = Rational(1e9.to_i,FS)
# CA chip frequency (chips per second)
FC = 1023000
# CA chip period (seconds per chip)
TC = Rational(1,FC)
# Samples per chip
SCRational = Rational(FS,FC)
SC = 102.5

C = GSL::CONST::MKSA::SPEED_OF_LIGHT

# L1 frequency (GHz)
L1_GHZ = 1.575420
# L2 frequency (GHz)
L2_GHZ = 1.227600

# TODO Loop through files
filename = ARGV[0]

#prn = Integer(ARGV[1])
#num_chips = Integer(ARGV[2]||40).abs rescue 40
#num_steps = Integer(ARGV[3]||1).abs rescue 1
#step_chips = Integer(ARGV[4]||num_chips/2) rescue num_chips/2
#offset = Integer(ARGV[5]||0) rescue 0
# TODO Reconcile naming
prn = opts[:prn]
num_chips = opts[:nchips]
num_steps = opts[:nsteps]
step_chips = opts[:step_size]
offset = opts[:offset]

# TODO Maybe rename to epoch_offset?
# TODO Maybe nuke this?
# File offset is number of samples from "top of second" to first sample in file
file_offset = Integer(ARGV[6]||0) rescue 0

off_chips = 2
nsamps = (num_chips * SC).round

# Load data file
zraw = GPS.load(filename, nsamps + (num_steps*step_chips*SC).ceil, (offset*SC).round)

sky_doppler_ghz = opts[:freq] - opts[:doppler]/1e9
case sky_doppler_ghz
when L1_GHZ
  FG_GHZ = L1_GHZ
  puts 'Sky freq less Doppler is exactly L1 carrier freq'
  z = zraw
when L2_GHZ
  FG_GHZ = L2_GHZ
  puts 'Sky freq less Doppler is exactly L2 carrier freq'
  z = zraw
else
  # FG is the frequency of the GPS carrier in GHz
  # Auto detect L1 vs L2 based on +/- 51 MHz of sky freq + doppler
  FG_GHZ = case sky_doppler_ghz
       when (L1_GHZ-0.051)..(L1_GHZ+0.051): L1_GHZ
       when (L2_GHZ-0.051)..(L2_GHZ+0.051): L2_GHZ
       else raise "Sky freq plus Doppler (#{sky_doppler_ghz*1e3} MHz) is too far from GPS L1 and L2"
       end
  # Correct for sky freq being other than carrier frequency
  # by mixing with sky-carrier to shift carrier freq to DC
  lohz = (sky_doppler_ghz-FG_GHZ)*1e9
  puts "Mixing with complex LO at #{lohz} Hz"
  lo = GSL::Complex.exp(GSL::Complex[0,2*GSL::M_PI]*GSL::Vector.indgen(zraw.size1)/(100*2**20)*lohz)
  z = zraw.dup
  z.size2.times {|c| z.col(c).mul!(lo)}
end

# TODO Determine all usable inputs and ignore others
#
# Find first chip for first usable input
refinp = nil
refchip = nil
quality = 0.0
# Correlate with full CA chip sequence
# TODO De-Doppler shift CA sequence
ca  = chips(prn,0,1023+num_chips-1)
fx = fy = nil
#z.each_index do |i|
z.size2.times do |i|
  # Get sample slice for first slice
  g = z.col(i).subvector(0,nsamps)
  x, fx, fy = correlate(g,ca,fx,fy)
  pk = x.abs.max_index
  quality = x[pk].abs / (g.abs.sum * Math.sqrt(2.0/3.0))
  chip, chip_fract = (ca.len-pk-1).divmod(SC)
  chip = chip.to_i # Ruby 1.8.4-ism
  next if quality < 0.5
  refinp = i
  refchip = chip + off_chips - ((chip&1 == 0) ? 0 : 1)
  printf "prn %d refinp %d refchip %d (%.1f %%)\n", prn, i, refchip, 100*quality
  break
end

raise "no gps signals found for prn #{prn} (%.1f %%)" % [100*quality] unless refchip

if opts[:glevel] > 0
  Plotter.new(:device => opts[:device], :nx=>opts[:nxy][0], :ny=>opts[:nxy][1], :ask=>true)
  pgsfs(2)
  pgsch(1.5)
end

# Range to plot (+/- peak)
r=50

delays_sample = GSL::Matrix::Int[num_steps,z.size2]
delays_fit    = GSL::Matrix[num_steps,z.size2]
peaks         = GSL::Matrix::Complex[num_steps,z.size2]
# dr is Detection Ratio (max abs/next highest abs)
dr = GSL::Matrix[num_steps,z.size2]
# mir is measured/ideal ratio
mir  = GSL::Matrix[num_steps,z.size2]

num_steps.times do |step|
  # Calc offset for step
  step_offset = (step*step_chips*SC).round
  # Correlate with CA sub-sequence
  ca  = chips(prn,refchip+step*step_chips-off_chips,num_chips+2*off_chips)
  fx = fy = nil

  z.size2.times do |i|
    # Get sample slice for step
    g = z.col(i).subvector(step_offset,nsamps)

    x, fx, fy = correlate(g,ca,fx,fy)

    # Get peak
    pk = x.abs.max_index
    peaks.set(step, i, x[pk])

    # TODO Change to be delay from top of millisecond to first sample being
    # considered (i.e. offset)
    #
    # delays_sample is measure of time from ms_top (i.e. 'top of the
    # millisecond') to first sample being considered (i.e. offset).  It can be
    # computed as tau_chip - tau_pk, where...
    #
    # tau_chip is the number of samples (TODO keep this as seconds?) from
    # ms_top to midpoint of CA at peak correlation.  It can be computed as...
    tau_chip = ((refchip+step*step_chips+num_chips/2.0)*SC).round
    #
    # tau_pk is number of samples from offset to peak.  It can be computed
    # as...
    tau_pk = step_offset + pk - ca.length/2 + 1
    #
    #OLD # Get delay samples from first sample to refchip based on peaks for current
    #OLD # step
    #OLD #delays_sample[step,i] = (pk-(ca.len-1)-step*step_chips*SC).round
    #OLD delays_sample[step,i] = pk - (ca.len-1)
    delays_sample[step,i] = tau_chip - tau_pk
    #delays_sample[step,i] = tau_pk - (step*step_chips*SC).round

    # It is also useful to know the first sample of the portion of the slice
    # the maximally correlated with the PRN subsequence.
    pk_sample = pk - ca.length + 1

    # Fit lines to ramps on either side of correlation peak to determine peak
    # at higher resolution.
    fitrange=50
    xilo = GSL::Vector.indgen(fitrange,pk-fitrange-1)
    yilo = x.subvector(pk-fitrange-1,fitrange).abs
    xihi = GSL::Vector.indgen(fitrange,pk+2)
    yihi = x.subvector(pk+2,fitrange).abs
    blo, mlo, *ignore = GSL::Fit.linear(xilo,yilo)
    bhi, mhi, *ignore = GSL::Fit.linear(xihi,yihi)
    pk_fit = (bhi-blo)/(mlo-mhi)
    # Calc delays_fit similarly to delays_sample
    ##delays_fit[step,i] = pk_fit - (ca.len-1) - step*step_chips*SC
    #delays_fit[step,i] = pk_fit - (ca.len-1) + (refchip*TC).to_f
    tau_pk_fit = pk_fit + step_offset - ca.length/2 + 1
    delays_fit[step,i] = tau_chip - tau_pk_fit
    #delays_fit[step,i] = tau_pk_fit - (step*step_chips*SC).round

    #p [step, i, pk, pk_fit, delays_sample[step,i], delays_fit[step,i]] if i == 3
    #p [step, i, pk, pk_fit, delays_sample[step,i], delays_fit[step,i].divmod(1)] if i == 3

    # Convert to ns
    delays_fit[step,i] = (tau_chip - tau_pk_fit) * TS_NANOS

    # Assess quality
    falsepeak_lo = falsepeak_hi = 0
    falsepeak_lo = x.subvector(0,pk-103).abs.max if (pk-103) > 0
    falsepeak_hi = x.subvector(pk+103,x.size-(pk+103)).abs.max if (x.size-(pk+103)) > 0
    falsepeak = [falsepeak_lo, falsepeak_hi].max
    # dr is "detection ratio"
    dr[step,i] = x[pk].abs / falsepeak
    goff = [0, pk_sample].max
    glen = [g.size-pk_sample, g.size].min
    begin
      mir[step,i] = x[pk].abs / (g.subvector(goff,glen).abs.sum * Math.sqrt(2.0/3.0)) * 100.0
    rescue
      p [step, i, pk_sample, glen, g.size]
      raise
    end

    maxadc = [zraw.col(i).re.abs.max, zraw.col(i).im.abs.max].max.to_i
    pct_sat = (zraw.col(i).re.abs.ge(127).or(zraw.col(i).im.abs.ge(127)).where2[0]||[]).size.to_f / zraw.size1
    num_sat = (zraw.col(i).re.abs.ge(127).or(zraw.col(i).im.abs.ge(127)).where2[0]||[]).size
    if opts[:glevel] > 1
      title = 'PRN %d In %d DR=%.1f, %d samples, meas/ideal=%.1f%%' % [prn, i, dr[step,i], nsamps, mir[step,i]]
      magphase((-r..r).to_a,x.subvector(pk-r,2*r+1), :ph_range=>nil, :title=>title)
      plot((0...glen),(g.subvector(goff,glen)*ca.subvector(0,glen)*GSL::Complex.exp(0,-x[pk].phase)).phase.to_na * 180/Math::PI)
      pgsci(Color::RED)
      pgline((0...glen).to_a,ca.subvector(0,glen).to_na*100)
      pgsci(Color::BLUE)
    end
    if opts[:glevel] > 2
      plot(x.re,x.im,:xlabel=>'Real',:ylabel=>'Imag',:title=>"Input #{i} Real/Imag", :marker=>Marker::STAR)
    end
    if opts[:verbose] > 0 && mir[step,i] >= 33.3
      sample = delays_sample[step,i] #+ (refchip*SC).round
      fit = delays_fit[step,i] #+ (refchip*SC).round
      printf "In %d %d samples @ %d | DR %4.1f | MIR %5.1f | tau %d samples %.2f fit %.2f ns | pkph %6.1f\n",
        i, nsamps, offset, dr[step,i], mir[step,i], sample, fit/TS_NANOS, fit, x[pk].phase * 180 / Math::PI
    end

  end
  if opts[:verbose] > 0
    puts
  else
    print '.'
    ObjectSpace.garbage_collect
  end
end
# Newline after progress dots
puts unless opts[:verbose] > 0

if opts[:glevel] > 0
  xx = (0...num_steps).map {|step| step*step_chips + offset}
  vxx = xx.to_gv

  doppler = []

  # Plot absolute delays/phases
  delays_fit.size2.times do |i|
    # Skip bad inputs
    next if mir.col(i).min < 50.0
    #next # Skip "autos"

    d = delays_fit.col(i)
    #d = delays_sample.col(i).to_f * TS_NANOS.to_f
    dmean = d.mean
    drms = Math.sqrt(d.tss/d.size)
    title = 'PRN %d In %d DR %.1f MIR %.1f%% Range %.3f' % [prn, i, dr.col(i).min, mir.col(i).min, d.max-d.min]
    title2 = 'Delay: mean=%.3f, rms=%.3f' % [d.mean, drms]
    plot(xx, d-dmean, :xlabel=>'elapsed chips', :ylabel=>'Delay deviation from mean (ns)', :marker=>Marker::STAR, :title=>title, :title2=>title2)
    #plot(xx, d, :xlabel=>'elapsed chips', :ylabel=>'Delay deviation from mean (ns)', :marker=>Marker::STAR, :title=>title, :title2=>title2)

    b_dfit, m_dfit, *ignore = GSL::Fit.linear(vxx,d)
    pgsci(Color::RED)
    pgline(xx, (vxx*m_dfit+b_dfit-dmean).to_a)
    pgsci(Color::BLUE)

    #ph = peaks.col(i).phase # Radians
    #  plot(xx, ph*180/Math::PI, :xlabel=>'elapsed chips',
    #       :ylabel=>'Wrapped Phase (degrees)',
    #       :title=>title, :title2 => title2)
    #  ph.unwrap!
    #  ph /= (2*Math::PI)
    #ph = peaks.col(i).phase.unwrap! * 180 / Math::PI # Degrees
    ph = peaks.col(i).phase.unwrap! / 2 / Math::PI # Turns

    b_dfit, m_dfit, *ignore = GSL::Fit.linear(vxx,ph)
    ph_residuals = ph - (vxx*m_dfit+b_dfit)
    doppler[i] = m_dfit*FC + opts[:doppler]

    title = 'PRN %d In %d DR %.1f MIR %.1f%% Range %.3f' % [prn, i, dr.col(i).min, mir.col(i).min, ph.max-ph.min]
    title2 = "\\gf: %.3f\xb0; df: %.3f Hz (%.3f m/s)" % [ph[0]*360, doppler[i], doppler[i]*C/FG_GHZ/1e9]

    #plot(xx, ph*360, :xlabel=>'elapsed chips',
    #     :ylabel=>'Phase (degrees)',
    #     :title=>title, :title2 => title2)

    plot(xx, ph_residuals*360, :xlabel=>'elapsed chips',
         :ylabel=>'Phase residuals (degrees)',
         :line=>:impulse, :title=>title, :title2 => title2)
  end

  # Plot relative delays/phases
  n = delays_fit.size2
  delays_fit.size2.times do |i|
    # Skip bad inputs
    next if mir.col(i).min < 50.0

    (i+1...n).each do |j|
      # Skip bad inputs
      next if mir.col(j).min < 50.0

      dd = delays_fit.col(i) - delays_fit.col(j)
      #dd = (delays_sample.col(i) - delays_sample.col(j)).to_f * TS_NANOS.to_f
      ddrms = Math.sqrt(dd.tss/dd.size)
      title = 'PRN %d In%d-In%d Relative Delay' % [prn, i, j]
      title2 = '\gDdelay: mean=%.3f, rms=%.3f' % [dd.mean, ddrms]
      plot(xx, dd, :xlabel=>'elapsed chips', :ylabel=>'Relative Delay (ns)', :marker=>Marker::STAR, :title=>title, :title2=>title2)

      b_dfit, m_dfit, *ignore = GSL::Fit.linear(vxx,dd)
      pgsci(Color::RED)
      pgline(xx, (vxx*m_dfit+b_dfit).to_a)
      pgsci(Color::BLUE)

      zz = peaks.col(i)  * peaks.col(j).conj
      zp = zz.phase.unwrap! * 180 / Math::PI
      title = 'PRN %d In%d-In%d Relative Carrier Phase' % [prn, i, j]
      title2 = '\gDdf: %.3f Hz (%.3f m/s)' % [doppler[i] - doppler[j], (doppler[i] - doppler[j])*C/FG_GHZ/1e9]
      plot(xx, zp, :xlabel=>'elapsed chips', :ylabel=>'Relative Phase (degrees)', :marker=>Marker::STAR, :title=>title, :title2=>title2)
    end
  end
end

# TODO Calc instrumental phases based on relative delays and relative carrier phases
# rel_ph(delay) = ((delay(1) - delay(2))%TC)*2*pi
# rel_ph(delay) + ph(1) - ph(2) = rel_ph(carrier)
