#!/usr/bin/env ruby

require 'gsl'
require 'mirdl'
include Mirdl
require 'pgplot/plotter'
include Pgplot

# This should be in mirdl!
def basant(bl)
  [bl.to_i >> 8, bl.to_i % 256]
end

keyini
  # d = use select keyword
  # s = use stokes keyword (needed?)
  # l = use line keyword
  uvDatInp('dsl')

  # Get pgplot device
  device = keya(:device, ENV['PGPLOT_DEV']||'/xs')

  # Get nxy
  nx = keyi(:nxy, 2)
  ny = keyi(:nxy, 2)

  # Get nsigma
  nsigma = keyr(:nsigma, 3.0)

  # Get options
  optkeys = [:polar, :rect, :scatter]
  optvals = options(optkeys)
  # Convert optkeys and optvals into a Hash
  opts = Hash[*optkeys.zip(optvals).flatten!]
keyfin

ltype = uvDatGta(:ltype)
if ltype != '' && ltype != 'channel'
  bug(:fatal, "unsupported line type '#{ltype}'")
end

# Default to polar
opts[:polar] ||= (!opts[:rect] && !opts[:scatter])

# Iniitalize plot device
Plotter.new(:device => device,
            :nx=>nx,
            :ny=>ny,
            :ask=>true)
# Make text bigger
pgsch(1.5)

k = 4 # Cubic
bss_nchan = nil

while tno = uvDatOpn

  # Get number of channels
  nchan = uvDatGti(:nchan)
  nchan = uvrdvri(tno, :nchan) if nchan == 0

  v = Vis.new(nchan)
  xx=NArray.float(nchan).indgen!

  # Setup B-Spline solver for this nchan
  if bss_nchan != nchan
    bss_nchan != nchan
    ncoeff = (nchan+31) / 32
    nbreak = ncoeff - k + 2
    if nbreak < 2
      nbreak = 2
      ncoeff = nbreak + k - 2
    end
    bss = GSL::BSpline.alloc(k, nbreak)
    bss.knots_uniform(0,nchan-1)
    bx = GSL::Matrix[nchan, ncoeff]
    (0...nchan).each do |i|
      bss.eval(xx[i], bx[i,nil])
    end
  end

  while uvDatRd(v)
    # Skip to next if completely flagged
    next if v.flags.sum == 0
    # TODO Handle partial flagging

    # Do B-Spline fits to real and imag
    yr = v.data.real
    yrv = yr.to_gv
    yi = v.data.imag
    yiv = yi.to_gv
    bcr, covr, chisqr, statusr = GSL::MultiFit.linear(bx, yrv)
    bci, covi, chisqi, statusi = GSL::MultiFit.linear(bx, yiv)
    var = (chisqr + chisqi)/(nchan - 1)

    # Evaluate fits to get smoothed real/imag
    byr = bx * bcr
    byr_na = byr.to_na
    byi = bx * bci
    byi_na = byi.to_na
    bz = byr_na + byi_na.to_type(NArray::SCOMPLEX)*1.im

    # Identify points that are more than nsigma standard deviations out from
    # real/imag fits
    rr = yr-byr_na
    ir = yi-byi_na
    res2 = rr**2 + ir**2
    outliers = res2.gt(nsigma*var).where

    # Setup plot metadata
    rms = Math.sqrt(var)
    bl = v.preamble[3]
    a1, a2 = basant(bl)
    src = uvrdvra(tno, :source)
    title = '%s %d-%d (rms=%.3f)' % [src, a1, a2, rms]
    lineinfo ||= uvinfo(tno, :line, 6)
    # Compute "virtual" channel numbers based on line parameters
    xxplot = xx * lineinfo[4] + lineinfo[2] + lineinfo[3]/2.0 - 0.5

    if opts[:polar]
      magphase(xxplot,v.data,
               :title => title,
               :xlabel => 'Channel',
               :mag_color => Color::BLUE,
               :phase_color => Color::YELLOW
              )
      magphase(xxplot,bz,:overlay=>true,
               :mag_color => Color::CYAN,
               :phase_color => Color::GREEN
              )
      axis(:mag)
      pgsci(Color::RED)
      pgpt((xx+lineinfo[2])[outliers], v.data[outliers].abs, Marker::CIRCDOT)
    end
    if opts[:rect]
      xmin = xxplot[0]
      xmax = xxplot[-1]
      ymin = [yr.min, yi.min].min
      ymax = [yr.max, yi.max].max
      # Setup plot range
      #pgsci(Color::WHITE)
      plot([xmin, xmax], [ymin, ymax],
           :line=>:none,
           :title=> title,
           :xlabel => 'Channel',
           :ylabel => 'Real (Blue), Imag (Yellow)',
           :line_color => Color::WHITE
          )

      pgsci(Color::BLUE)
      pgline(xx+lineinfo[2], yr)
      pgsci(Color::CYAN)
      pgline(xx+lineinfo[2], byr_na)
      pgsci(Color::YELLOW)
      pgline(xx+lineinfo[2], yi)
      pgsci(Color::GREEN)
      pgline(xx+lineinfo[2], byi_na)
      pgsci(Color::RED)
      pgpt((xx+lineinfo[2])[outliers], yr[outliers], Marker::CIRCDOT)
      pgpt((xx+lineinfo[2])[outliers], yi[outliers], Marker::CIRCDOT)
    end
    if opts[:scatter]
      xmin, xmax = yrv.minmax
      ymin, ymax = yiv.minmax
      # Setup plot range
      #pgsci(Color::WHITE)
      plot([xmin, xmax], [ymin, ymax],
           :line=>:none,
           :title=> title,
           :xlabel => 'Real',
           :ylabel => 'Imag',
           :line_color => Color::WHITE
          )

      pgsci(Color::BLUE)
      pgline(yr, yi)
      pgpt1(yr[0], yi[0], Marker::STAR)
      pgsci(Color::CYAN)
      pgline(byr_na, byi_na)
      pgpt1(byr_na[0], byi_na[0], Marker::STAR)
      pgsci(Color::RED)
      pgpt(yr[outliers], yi[outliers], Marker::CIRCDOT)
    end
  end

  uvDatCls
end # uvDatOpn
