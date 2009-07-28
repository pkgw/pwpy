#!/usr/bin/env ruby

# $Id: bsflag.rb 470 2009-03-27 20:00:53Z davidm $

require 'gsl'
require 'mirdl'
include Mirdl
require 'pgplot/plotter'
include Pgplot

keyini
  # 3 = return w in preamble
  uvDatInp('3')

  # Get pgplot device
  device = keya(:device, ENV['PGPLOT_DEV']||'/xs')

  # Get nxy
  nx = keyi(:nxy, 1)#3)
  ny = keyi(:nxy, 1)#2)

#  # Get nsigma
#  nsigma = keyr(:nsigma, 5.0)
#
#  # Get maxiters
#  iter_limit = keyr(:maxiter, 10)
#
#  # Get nbs, number of basis splines
#  nbs = keyi(:nbs)
#
#  # Get options
#  optkeys = [:polar, :rect, :scatter, :nofit, :flag]
#  optvals = options(optkeys)
#  # Convert optkeys and optvals into a Hash
#  opts = Hash[*optkeys.zip(optvals).flatten!]
keyfin

# Iniitalize plot device
Plotter.new(:device => device,
            :nx=>nx,
            :ny=>ny,
            :ask=>true)
# Make text bigger
#pgsch(1.5)

# Loop through all datasets
while tno = uvDatOpn

  # uvDat et al should not be aware of number of channels since
  # we did not ask it to process line keyword.
  raise 'uvDat should not know about nchan' if uvDatGti(:nchan) != 0

  # Get number of channels
  nchan = uvrdvri(tno, :nchan)

  v = Vis.new(nchan)
  # Keys are jd, values are NArray.int(nchan)
  flag_accumulator = {}
  jd = 0
  intsecs = 0

  while uvDatRd(v)
    inttime = uvgetvr(tno, :inttime)
    if inttime != intsecs
      puts "inttime = #{inttime}"
      intsecs = inttime
    end
    intdays = inttime / (24 * 60 * 60)
    vjd = v.preamble[3]
    jd = vjd if vjd > jd + intdays/2.0
    flag_accumulator[jd] ||= NArray.int(nchan)
    flag_accumulator[jd] += (1-v.flags)
    break if flag_accumulator.keys.length > 400
  end

  jds = flag_accumulator.keys.sort

  vis ||= 'TODO'
  xmin = 0.5
  xmax = nchan + 0.5
  ymin = 0.5
  ymax = jds.length + 0.5
  title = "Flag-o-gram of #{vis}"

  # Setup plot
  plot([xmin, xmax], [ymin, ymax],
       :line=>:none,
       :title=> title,
       :xlabel => 'Channel',
       :ylabel => 'Dump',
       :line_color => Color::WHITE
      )

  image = NMatrix.int(nchan,jds.length)
  jds.each_with_index do |jd, y|
    #puts(((jd+0.5)%1).to_hmsstr(3))
    image[true,y] = flag_accumulator[jd]
  end

  # Color ramp for indices 16-32
  pgscir(16, 32)
  pgctab([0,0.25,0.5,0.75,1],[0,0,0,1,1],[0,1,1,1,0],[1,1,0,0,0])
  # Make max be black
  pgscir(16, 33)
  pgscr(33, 0, 0, 0)

  # Draw image and color wedge
  zmax = image.max
  pgimag(image, 0..zmax)
  pgwedg('RI', 0.5, 3, 0, zmax, 'Flag Counts')

  uvDatCls
end # uvDatOpn
