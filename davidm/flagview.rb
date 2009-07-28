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
pgsch(1.5)

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

  while uvDatRd(v)
    jd = v.preamble[3]
    flag_accumulator[jd] ||= NArray.int(nchan)
    flag_accumulator[jd] += (1-v.flags)
    break if flag_accumulator.keys.length > 4
  end

  jds = flag_accumulator.keys.sort

  vis ||= 'TODO'
  xmin = 0.5
  xmax = nchan + 0.5
  ymin = 0.5
  ymax = jds.length + 0.5
  title = "Flag-o-gram of #{vis}"

  # TODO Setup plot
  plot([xmin, xmax], [ymin, ymax],
       :line=>:none,
       :title=> title,
       :xlabel => 'Channel',
       :ylabel => 'Dump',
       :line_color => Color::WHITE
      )

#  jds.each_with_index do |jd, y|
#    x = 0
#    counts = flag_accumulator[jd]
#    counts.each do |n|
#      pgsfs(
#      pgrect(x, x+1, y, y+1)
#      x += 1
#    end
#  end

  image = NMatrix.int(nchan,jds.length)
  jds.each_with_index do |jd, y|
    image[true,y] = flag_accumulator[jd]
  end
  pgimag(image)

  uvDatCls
end # uvDatOpn
