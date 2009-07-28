#!/bin/env ruby

require 'optparse'
require 'pgplot/plotter'
include Pgplot

opts = {
  :caption => '',
  :device  => ENV['PGPLOT_DEV'] || '/xs',
  :nxy     => [4, 3],
  :range   => 100.0,
  :width   => 1,
}

OP = OptionParser.new do |op|
  op.program_name = File.basename($0)

  op.banner = "Usage: #{op.program_name} [OPTIONS] FILENAME [...]"
  op.separator('')
  op.separator('Plot primary beam fits from gpfit.rb output.')
  op.separator('Reads stdin if no filename given.')
  op.separator('')
  op.separator('Options:')
  op.on('-c', '--caption=STRING', "Caption to add to plots []") do |o|
    opts[:caption] = ", #{o}"
  end
  op.on('-d', '--device=DEV', "PGPLOT device [ENV['PGPLOT_DEV']||'/xs']") do |o|
    opts[:device] = o
  end
  op.on('-n', '--nxy=NX,NY', Array, 'Controls subplot layout [4,3]') do |o|
    if o.length != 2
      raise OptionParser::InvalidArgument.new('invalid NX,NY')
    end
    opts[:nxy] = o.map {|s| Integer(s) rescue 2}
  end
  op.on('-r', '--range=ARCMIN', Float, 'Range of plots in arcmin [100.0]') do |o|
    opts[:range] = o
  end
  op.on('-w', '--width=ISCALE', Integer, 'Line width integer scale factor [1]') do |o|
    opts[:width] = o
  end
  #op.separator('')
  op.on_tail('-h','--help','Show this message') do
    puts op.help
    exit
  end
end
OP.parse!

range = opts[:range]
nxy = opts[:nxy]

# rx and ry are half width half maximum
PBFit = Struct.new(:pk, :x, :y, :rx, :ry, :iters)

# Read and parse the data
fits = {}
ARGF.each do |l|
  if /^\s*#/ =~ l
    # TODO Pick up on mode (i.e. rect vs polar)
    next
  end

  w=l.split

  ap = [w[0].to_i, w[1].downcase, ARGF.filename]
  iters = w[5].to_i
  pk = w[ 7].to_f
  x  = w[ 8].to_f
  y  = w[ 9].to_f
  rx = w[10].to_f / 2.0
  ry = w[11].to_f / 2.0

  fits[ap] ||= []
  fits[ap] << PBFit.new(pk, x, y, rx, ry, iters)
end

# Iniitalize plot device
Plotter.new(:device => opts[:device],
            :nx=>opts[:nxy][0],
            :ny=>opts[:nxy][1],
            :ask=>true)
pgsfs(Fill::OUTLINE)
pgsch(1.5)

def crosshair(x, y, r)
  pgline([-2*r, 2*r], [y, y])
  pgline([x, x], [-2*r, 2*r])
end

nsides = 100
th = NArray.float(nsides).indgen! * 2.0 * Math::PI / nsides
keys = fits.keys.sort
prevant = 0
prevfn = ''
colors = {}
next_color = Color::WHITE
keys.each do |apfn|
  ant, pol, fn = apfn
  if prevfn != fn
    prevfn = fn
    # Setup color
    if !colors.has_key?(fn)
      next_color += 1
      colors[fn] = next_color
    end
  end
  if prevant != ant
    prevant = ant
    # Setup plot range
    pgsci(Color::WHITE)
    plot([-range, range], [-range, range],
         :line=>:none,
         :title=> "Antenna #{ant}",
         :title2 => "X solid, Y dotted#{opts[:caption]}",
         :xlabel => 'Azimuth (arcmin)',
         :ylabel => 'Elevation (arcmin)',
         :line_color => Color::WHITE,
         :just => true)

    #pgline([-2*range, 2*range], [0, 0])
    #pgline([0, 0], [-2*range, 2*range])
    crosshair(0, 0, range)
  end
  pgsci(colors[fn])
  pgslw(opts[:width])
  pgsls(pol == 'x' ? Line::SOLID : Line::DOTTED)

  fits[apfn].each do |fit|
    next unless fit
    x  = fit.x
    y  = fit.y
    rx = fit.rx
    ry = fit.ry
    pgpt1(x, y, Marker::PLUS)
    #crosshair(x, y, range)
    pgpoly(rx*NMath.cos(th)+x, ry*NMath.sin(th)+y)
  end
  pgslw(1)
  pgsls(Line::SOLID)
end
