#!/usr/bin/env ruby
$-w = true if $0 == __FILE__ # Turn on warnings

# Do deep integrations

require 'pgplot/plotter'
include Pgplot

#require 'gsl'

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
  
  # Get axes scales
  xax = keya(:axis, 'freq')
  yax = keya(:axis, 'linear')

  # Get tau fudge factor
  tau_fudge = keyr(:taufudge, 1)
keyfin

# Create Hash to store data
data = {}

# Variable to hold xaxis info from dataset
lineinfo = nil
freqs = nil

# Loop through data files
while tno = uvDatOpn
  puts "----- #{uvDatGta(:name)} -----"

  # Get number of channels
  nchan = uvDatGti(:nchan)
  nchan = uvrdvri(tno, :nchan) if nchan == 0
  # Create a new Vis object
  v = Vis.new(nchan)

  # Loop through data
  while uvDatRd(v)

    # Lazy init line and frequency info for x axis
    lineinfo ||= uvinfo(tno, :line)
    freqs ||= uvinfo(tno, :frequency)

    # Get keys
    time = v.time
    a1a2 = v.basant

    # Build value
    tau = uvrdvrf(tno, :inttime)
    warn "tau == 0 for #{a1a2[0]}-#{a1a2[1]} at #{time}" if tau == 0
    next if tau == 0
    val = [tau, v.data.dup]

    # Store into data Hash
    data[time] ||= {}
    data[a1a2] ||= {}
    data[time][a1a2] = val
    data[a1a2][time] = val
  end

  uvDatCls
end

keys = data.keys
timestamps = keys.grep(Float).sort
baselines = keys.grep(Array).sort

puts "got #{timestamps.length} distinct times"
puts "got #{baselines.length} baselines"

Plotter.new(:device=>device, :nx=>nx, :ny=>ny, :ask=>true)
pgsch(1.5)

# Hash for integrations
# {[a1,a2] => [sum_tau, sum_visdata]}
integrations = {}

baselines.each do |bl|
  integrations[bl] ||= [0.0, NArray.scomplex(nchan)]
  data[bl].values.each do |tau, visdata|
    integrations[bl][0] += tau
    integrations[bl][1] += visdata
  end
end

# Generate xaxis values once
if xax[0,1] == 'f'
  xx=freqs
else
  xx=NArray.float(nchan).indgen!
  # Compute "virtual" channel numbers based on line parameters
  #xxplot = xx * lineinfo[4] + lineinfo[2] + lineinfo[3]/2.0 - 0.5
  xx = xx.mul!(lineinfo[4]).add!(lineinfo[2] + lineinfo[3]/2.0 - 0.5)
end

baselines.each do |bl|
  a1, a2 = bl
  next if a1 == a2

  tau12, vis12 = integrations[bl]
  mag_scale = yax

  # Normalize by geometric mean of the autos if present
  have_autos = integrations.has_key?([a1,a1]) && integrations.has_key?([a2,a2])
  if have_autos
    tau11, vis11 = integrations[[a1,a1]]
    tau22, vis22 = integrations[[a2,a2]]
    if tau12 == tau11 && tau12 == tau22
      mag_label = "Correlation Coefficient"
      geomean = (vis11.real*vis22.real)**0.5
      geomean0_idx = geomean.eq(0).where
      geomean[geomean0_idx] = 1.0
      #vis12[geomean0_idx] = 0.0
      vis12.div!(geomean)
    else
      warn "baseline #{a1}-#{a2} has different inttime than #{a1}-#{a1} or #{a2}-#{a2}"
      have_autos = false
    end
  else
    # Doesn't make much sense to do dB if not a ratio
    mag_scale = 'log' if yax =~ /db/i
    mag_label = "Magnitude"
  end

  title = "Ants #{a1}-#{a2};  Inputs #{a1-1}-#{a2-1}"
  title2 = "tau = #{(tau_fudge*tau12/3600).to_hmsstr(3)}"
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
           :mag_label => mag_label,
           :mag_scale => mag_scale
          )
end
