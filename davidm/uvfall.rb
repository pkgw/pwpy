#!/usr/bin/env ruby

#= uvfall.rb - View uv data in waterfall format
#& dhem
#: analysis
#+ uvfall.rb - View uv data in waterfall format
#
#@ vis
# Specifies which datasets to use
#
#@ select
# This selects the data to be processed, using the standard uvselect
# format.  Default is all data.
#
#@ line
# This selects the spectral data to be processed, using the standard line
# format.  Default is all channels.
#
#@ rgbmin
# Specifies RGB triple for minimum value
# Default is black (0.0,0.0,0.0)
#
#@ rgbmax
# Specifies RGB triple for maximum value.
# Default is dark red (0.2,0.0,0.0)
#
#--

require 'rubygems'
require 'mirdl'
include Mirdl
require 'pgplot/plotter'
include Pgplot

keyini
  # d = use select keyword
  # s = use stokes keyword (needed?)
  # l = use line keyword
  # 3 = return w in preamble
  uvDatInp('dsl3')

  # Get pgplot device
  device = keya(:device, ENV['PGPLOT_DEV']||'/xs')

  # Get subplot nxy
  nx = keyi(:nxy, 1)
  ny = keyi(:nxy, 1)

  # Get rgb for min and max colors
  rgbmin = []
  rgbmin << keyr(:rgbmin, 0.0)
  rgbmin << keyr(:rgbmin, 0.0)
  rgbmin << keyr(:rgbmin, 0.0)

  rgbmax = []
  rgbmax << keyr(:rgbmax, 1.0)
  rgbmax << keyr(:rgbmax, 0.0)
  rgbmax << keyr(:rgbmax, 0.0)

  ## Get options
  #optkeys = [:percent]
  #optvals = options(optkeys)
  ## Convert optkeys and optvals into a Hash
  #opts = Hash[*optkeys.zip(optvals).flatten!]
keyfin

# Iniitalize plot device
Plotter.new(:device => device,
            :nx=>2*nx,
            :ny=>ny,
            :ask=>true)

# Color ramp for amplutides
AMP_RAMP = [
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

# Loop through all datasets
while tno = uvDatOpn

  # Get number of channels
  nchan = uvDatGti(:nchan)
  nchan = uvrdvri(tno, :nchan) if nchan == 0

  xmin = 0.5
  xmax = nchan + 0.5
  xlabel = 'Channel'

  # Get vis name, number of channels, etc
  vis = uvDatGta(:name)

  v = Vis.new(nchan)

  # data[[a1,a2,polcode]][jd] = vis.data
  # flags[[a1,a2,polcode]][jd] = vis.flags
  # min[[a1,a2,polcode]] = min value over all jd
  data = {}
  flags = {}

  jd = 0

  while uvDatRd(v)

    a1, a2 = v.basant
    pol = uvDatGti(:pol)
    vjd = v.preamble[3]
    if vjd != jd
      jd = vjd
    end

    key = [a1, a2, pol]
    data[key] ||= {}
    data[key][jd] = v.data.dup
    flags[key] ||= {}
    flags[key][jd] = v.flags.dup
  end # uvDatRd loop

  uvDatCls

  # Plot waterfalls for each baseline cross-pol
  data.keys.sort.each do |key|
    
    a1, a2, pol = key

    jds = data[key].keys.sort
    # TODO Reuse image and flag2 arrays!
    image = NArray.scomplex(nchan,jds.length)
    flag2 = NArray.int(nchan,jds.length)
    jds.each_with_index do |jd, y|
      image[true,y] = data[key][jd]
      flag2[true,y] = flags[key][jd]
    end

    next if flag2.sum == 0

    # Limits for tics
    ymin = 0.5
    ymax = jds.length + 0.5
    title = "#{vis} #{a1}-#{a2} #{POLMAP[pol]}"

    # Setup amplitude plot
    z = image.abs
    z[z<1e-10] = 1e-10
    z = NMath.log10(z)
    zmin = z.min
    zmax = z.max
    zmax = zmin + 1 if zmax == zmin
    # Make sure flagged data gets lowest color bin
    z[flag2<1] = zmin - (zmax-zmin)/100

    plot([xmin, xmax], [ymin, ymax],
         :line=>:none,
         :title=> title,
         :xlabel => xlabel,
         :ylabel => 'Dump',
         :yrange=>[ymin, ymax],
         :line_color => Color::WHITE
        )

    pgctab(*AMP_RAMP.transpose)

    # Draw image and color wedge

    zlabel = 'Amplitude'
    pgimag(z, zmin..zmax)
    pgwedg('RI', 0.5, 3, zmin, zmax, zlabel)

    # Setup phase data
    z=image.angle.mul!(180/Math::PI)
    zmin = -180
    zmax =  180
    # Make sure flagged data gets lowest color bin
    z[flag2<1] = zmin - (zmax-zmin)/100

    # Setup phase plot
    zlabel = 'Phase'
    plot([xmin, xmax], [ymin, ymax],
         :line=>:none,
         :title=> title,
         :xlabel => xlabel,
         :ylabel => 'Dump',
         :yrange=>[ymin, ymax],
         :line_color => Color::WHITE
        )

    # TODO Make phase ramp that "wraps" the color
    pgctab(*AMP_RAMP.transpose)

    pgimag(z, zmin..zmax)
    pgwedg('RI', 0.5, 3, zmin, zmax, zlabel)
  end

end # uvDatOpn
