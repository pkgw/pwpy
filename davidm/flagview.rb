#!/usr/bin/env ruby

# $Id: bsflag.rb 470 2009-03-27 20:00:53Z davidm $

require 'mirdl'
include Mirdl
require 'pgplot/plotter'
include Pgplot

keyini
  # d = use select keyword
  # 3 = return w in preamble
  uvDatInp('d3')

  # Get pgplot device
  device = keya(:device, ENV['PGPLOT_DEV']||'/xs')

  # Get subplot nxy
  spnx = keyi(:nxy, 1)#3)
  spny = keyi(:nxy, 1)#2)

  # Get mode via "axis" keyword
  mode = keya(:axis, :chan)

  # Get bins (used for uvd and uva modes)
  bins = keyi(:bins, 100)

  # Get rgb for min and max colors
  rgbmin = []
  rgbmin << keyr(:rgbmin, 0.0)
  rgbmin << keyr(:rgbmin, 0.0)
  rgbmin << keyr(:rgbmin, 0.0)

  rgbmax = []
  rgbmax << keyr(:rgbmax, 0.2)
  rgbmax << keyr(:rgbmax, 0.0)
  rgbmax << keyr(:rgbmax, 0.0)

#  # Get nsigma
#  nsigma = keyr(:nsigma, 5.0)
#
#  # Get maxiters
#  iter_limit = keyr(:maxiter, 10)
#
#  # Get nbs, number of basis splines
#  nbs = keyi(:nbs)
#
  # Get options
  optkeys = [:percent]
  optvals = options(optkeys)
  # Convert optkeys and optvals into a Hash
  opts = Hash[*optkeys.zip(optvals).flatten!]
keyfin

# Patterns to match mode
CHAN_MODE = /^ch/
ANTS_MODE = /^ant/
UVD_MODE = /^uvd/
UVA_MODE = /^uva/

# Loop through all datasets
while tno = uvDatOpn

  case mode
  when CHAN_MODE
    nx = uvgetvr(tno, :nchan)
    xmin = 0.5
    xmax = nx + 0.5
    xlabel = 'Channel'
    zlabel = 'Baseline Flag Counts'
  when ANTS_MODE
    nx = uvgetvr(tno, :nants)
    xmin = 0.5
    xmax = nx + 0.5
    xlabel = 'Antenna'
    zlabel = 'Baseline-Channel Flag Counts'
  when UVD_MODE
    nx = bins
    xmin = Float::MAX # Set later
    xmax = Float::MIN # Set later
    xlabel = 'UV Distance'
    zlabel = opts[:percent] ? '% Flagged' : 'Flag Counts'
  when UVA_MODE
    nx = bins
    xmin = Float::MAX # Set later
    xmax = Float::MIN # Set later
    xlabel = 'UV Angle'
    zlabel = opts[:percent] ? '% Flagged' : 'Flag Counts'
  else
    raise "unknown mode: '#{mode}'"
  end

  # uvDat et al should not be aware of number of channels since
  # we did not ask it to process line keyword.
  raise 'uvDat should not know about nchan' if uvDatGti(:nchan) != 0

  # Get vis name, number of channels, etc
  vis = uvDatGta(:name)
  nchan = uvrdvri(tno, :nchan)
  nants = uvrdvri(tno, :nants)

  v = Vis.new(nchan)

  # Keys and values depend on mode
  #
  # Mode:  Key      => Value
  # -----------------------
  # CHAN:  jd       => NArray(nchan) of accumulated flags
  # ANTS:  jd       => NArray(nants) of accumulated flags
  # UVD:  [jd, uvd] => [Integer, Integer] (total flags, total channels)
  # UVA:  [jd, uva] => [Integer, Integer] (total flags, total channels)
  flag_accumulator = {}

  jd = 0
  jds = []
  intsecs = 0

  while uvDatRd(v)
    inttime = uvgetvr(tno, :inttime)
    if inttime != intsecs
      puts "inttime = #{inttime}"
      intsecs = inttime
    end
    # Funny business to handle sloppy timestamps
    intdays = inttime / (24 * 60 * 60)
    vjd = v.preamble[3]
    if vjd > jd + intdays/2.0
      break if jds.length > 400
      jd = vjd
      jds << jd
    end
    case mode
    when CHAN_MODE
      flag_accumulator[jd] ||= NArray.int(nchan)
      flag_accumulator[jd] += (1-v.flags)
    when ANTS_MODE
      a1, a2 = basant(v.preamble[4])
      n = nchan - v.flags.sum
      flag_accumulator[jd] ||= NArray.int(nants)
      flag_accumulator[jd][a1-1] += n
      flag_accumulator[jd][a2-1] += n
    when UVD_MODE
      uvd = Math.hypot(v.preamble[0], v.preamble[1])
      xmin = uvd if uvd < xmin
      xmax = uvd if uvd > xmax
      n = nchan - v.flags.sum
      flag_accumulator[[jd,uvd]] ||= [0, 0]
      flag_accumulator[[jd,uvd]][0] += n
      flag_accumulator[[jd,uvd]][1] += nchan
    when UVA_MODE
      uva = Math.atan2(v.preamble[0], v.preamble[1]) * 180 / Math::PI
      xmin = uva if uva < xmin
      xmax = uva if uva > xmax
      n = nchan - v.flags.sum
      flag_accumulator[[jd,uva]] ||= [0, 0]
      flag_accumulator[[jd,uva]][0] += n
      flag_accumulator[[jd,uva]][1] += nchan
    end
  end # uvDatRd loop

  jds.uniq!

  case mode
  when CHAN_MODE, ANTS_MODE
    jds = flag_accumulator.keys.sort
    image = NMatrix.int(nx,jds.length)
    jds.each_with_index do |jd, y|
      #puts(((jd+0.5)%1).to_hmsstr(3))
      image[true,y] = flag_accumulator[jd]
    end
  when UVD_MODE, UVA_MODE
    keys = flag_accumulator.keys.sort
    image = NMatrix.sfloat(nx,jds.length)
    total = NMatrix.int(nx,jds.length)
    dx = (xmax-xmin) / bins.to_f
    keys.each do |jd, x|
      bin = (x == xmax) ? bins-1 : ((x-xmin)/dx).floor
      y = jds.index(jd)
      image[bin,y] += flag_accumulator[[jd,x]][0]
      total[bin,y] += flag_accumulator[[jd,x]][1]
    end
    if opts[:percent]
      total[total.eq(0)] = 1
      image.mul!(100).div!(total)
    end
  end

  # Limits for tics
  ymin = 0.5
  ymax = jds.length + 0.5
  title = "Flagogram of #{vis}"

  # Iniitalize plot device
  Plotter.new(:device => device,
              :nx=>spnx,
              :ny=>spny,
              :ask=>true)

  # Setup plot
  plot([xmin, xmax], [ymin, ymax],
       :line=>:none,
       :title=> title,
       :xlabel => xlabel,
       :ylabel => 'Dump',
       :line_color => Color::WHITE
      )

  # Color ramp for indices 16-32
  ramp = [
    # Min color
    [0.0000, rgbmin[0], rgbmin[1], rgbmin[2]],
    #  pos    R    G    B
    [0.0001, 0.0, 1.0, 0.0], 
    [0.2500, 0.0, 1.0, 1.0], 
    [0.5000, 0.0, 0.0, 1.0], 
    [0.7500, 1.0, 0.0, 1.0], 
    [0.9998, 1.0, 0.0, 0.0],
    # Max color
    [0.9999, rgbmax[0], rgbmax[1], rgbmax[2]],
    [1.0000, rgbmax[0], rgbmax[1], rgbmax[2]], # Never used?
  ]

  pgscir(16, 16+100)
  pgctab(*ramp.transpose)

  # Draw image and color wedge
  zmax = image.max
  # Limits for image
  pgswin(0.5, nx + 0.5, ymin, ymax)
  pgimag(image, 0..zmax)
  pgwedg('RI', 0.5, 3, 0, zmax, zlabel)

  uvDatCls
end # uvDatOpn
