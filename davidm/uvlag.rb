#!/usr/bin/env ruby
$-w = true if $0 == __FILE__ # Turn on warnings

# Plot UV spectra in lag space

require 'rubygems'
require 'pgplot/plotter'
include Pgplot

require 'gsl'

require 'mirdl'
include Mirdl

keyini
  # d = use select keyword
  # s = use stokes keyword (needed?)
  # l = use line keyword
  # 3 = include w in preamble
  uvDatInp('dsl3')

  # Get plot device
  device = keya(:device, ENV['PGPLOT_DEV']||'/xs')

  # Get nxy
  nx = keyi(:nxy, 2)
  ny = keyi(:nxy, 2)

  # Get y axis info
  yaxis  = keya(:yaxis,  'amplitude')
  yscale = keya(:yscale, 'linear')

  # Get xrange
  xmin = keyi(:xrange, 2**31-1); xmin = nil if xmin == 2**31-1
  xmax = keyi(:xrange, 2**31-1); xmax = nil if xmax == 2**31-1

  # Get yrange
  ymin = keyr(:yrange, -1.0/0); ymin = nil if ymin == -1.0/0
  ymax = keyr(:yrange, +1.0/0); ymax = nil if ymax == +1.0/0

keyfin

# Variable to hold xaxis info from dataset
lineinfo = nil

Plotter.new(:device=>device, :nx=>nx, :ny=>ny, :ask=>true)
pgsch(1.5) if nx > 1 || ny > 1

# Loop through data files
while tno = uvDatOpn
  puts "----- #{uvDatGta(:name)} -----"

  # Get number of channels
  nchan = uvDatGti(:nchan)
  nchan = uvrdvri(tno, :nchan) if nchan == 0
  # Create a new Vis object
  v = Vis.new(nchan)
  # Create a new FFT buffer
  f = GSL::Vector::Complex[2*nchan]
  # Create x axis values
  # TODO Use xrange
  # TODO Check 0 lag
  xx = NArray.float(2*nchan).indgen!(1-nchan)

  # Loop through data
  while uvDatRd(v)

    # Lazy init line and frequency info for x axis
    lineinfo ||= uvinfo(tno, :line)

    # Arrange vis data into FFT buffer
    f[0...nchan]   = v.data.to_gv.conj!.reverse!
    f[nchan]       = 0
    f[nchan+1..-1] = v.data[0..-2].to_gv
    # Nuke the "DC" channel
    f[0] = 0
    f[1] = 0; f[-1] = 0

    # Plot magnitude of correlation space
    magphase(f[0...nchan].conj.reverse!,
            :xlabel => 'Channel',
            :title => "Baseline #{v.basant.join('-')} #{POLMAP[uvDatGti(:pol)]}",
            :title2 => 'Frequency Space'
            )

    # Compute lag space
    f.forward!.fftshift!

    # Plot magnitude of lag space
    plot(xx, f.abs,
            :xlabel => 'Lag',
            :title => "Baseline #{v.basant.join('-')} #{POLMAP[uvDatGti(:pol)]}",
            :title2 => 'Lag Space'
            )

  end

  uvDatCls
end

__END__

keys = data.keys
timestamps = keys.grep(Float).sort
baselines = keys.grep(Array).sort

puts "got #{timestamps.length} distinct times"
puts "got #{baselines.length} baselines"

## Hash for integrations
## {[a1,a2] => [sum_tau, sum_visdata]}
#integrations = {}
#
#baselines.each do |bl|
#  integrations[bl] ||= [0.0, NArray.scomplex(nchan)]
#  data[bl].values.each do |tau, visdata|
#    integrations[bl][0] += tau
#    integrations[bl][1] += visdata
#  end
#end

# Generate xaxis values once
if xax[0,1] == 'f'
  xx=freqs
else
  xx=NArray.float(nchan).indgen!
  # Compute "virtual" channel numbers based on line parameters
  #xxplot = xx * lineinfo[4] + lineinfo[2] + lineinfo[3]/2.0 - 0.5
  xx = xx.mul!(lineinfo[4]).add!(lineinfo[2] + lineinfo[3]/2.0 - 0.5)
end

Plotter.new(:device=>device, :nx=>nx, :ny=>ny, :ask=>true)
pgsch(1.5) if nx > 1 || ny > 1

baselines.each do |bl|
  ap1, ap2 = bl
  next if ap1 == ap2 # Skip autos

  a1 = ap1[0..-2].to_i
  p1 = ap1[-1,1]
  a2 = ap2[0..-2].to_i
  p2 = ap2[-1,1]


  ap1ap1 = [ap1, ap1]
  ap1ap2 = [ap1, ap2]
  ap2ap2 = [ap2, ap2]

  tau12, vis12 = data[ap1ap2]
  mag_scale = yax

  # Normalize by geometric mean of the autos if present
  have_autos = data.has_key?(ap1ap1) && data.has_key?(ap2ap2)
  if have_autos
    tau11, vis11 = data[ap1ap1]
    tau22, vis22 = data[ap2ap2]
    if tau12 == tau11 && tau12 == tau22
      mag_label = "Correlation Coefficient"
      geomean = (vis11.real*vis22.real)**0.5
      geomean0_idx = geomean.eq(0).where
      geomean[geomean0_idx] = 1.0
      #vis12[geomean0_idx] = 0.0
      vis12.div!(geomean)
    else
      warn "baseline #{ap1}-#{ap2} has different inttime than #{ap1}-#{ap1} or #{ap2}-#{ap2}"
      have_autos = false
    end
  else
    # Doesn't make much sense to do dB if not a ratio
    mag_scale = 'log' if yax =~ /db/i
    warn "autos not present/selected; plotting magnitude"
    mag_label = "Magnitude"
  end

  # Calculate mean and max amplitudes
  vis12abs = vis12.abs
  mean = vis12abs.mean
  max = vis12abs.max
  # maxx is NArray of x values where y == max
  maxx = xx[vis12abs.eq(max).where]
  case mag_scale
  when /^db/i # dB
    mean = 10*Math.log10(mean+1e-12)
    max = 10*Math.log10(max+1e-12)
  when /^lo/i # log
    mean = Math.log10(mean+1e-12)
    max = Math.log10(max+1e-12)
  end
  # maxy is Array with same length as maxx, all elements are max
  maxy = [max] * maxx.length

  title = "Ants #{a1}-#{a2} #{p1}#{p2} / Inputs #{a1-1}-#{a2-1} #{p1}#{p2}"
  # TODO Fix format for linear and/or channel-based plots
  title2 = sprintf('tau = %s, mean=%.3f, max=%.3f @ %.3f MHz',
                   (tau_fudge*tau12/3600).to_hmsstr(3), mean, max, 1000*maxx[0]
                  )

  mag_label += case mag_scale
                when /^db/i # dB
                  ' (dB)'
                when /^lo/i # log
                  ' (log10)'
                else        # linear
                  ' (linear)'
                end

  magphase(xx, vis12,
           :title => title,
           :title2 => title2,
           :xlabel => xax[0,1] == 'f' ? 'Frequency (GHz)' : 'Channel',
           :mag_scale => mag_scale,
           :mag_label => mag_label,
           :mag_scale => mag_scale,
           :mag_range => [ymin, ymax]
          )

  axis(:mag)
  plot([xx[0], xx[-1]], [mean, mean],
       :overlay=>true,
       :line_color=>Color::RED
      )
  plot(maxx, maxy,
       :overlay=>true,
       :line=>nil,
       :marker=>Marker::DIAMOND,
       :line_color=>Color::RED
      )
end
