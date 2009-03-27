#!/usr/bin/env ruby

# $Id$

require 'gsl'
require 'mirdl'
include Mirdl
require 'pgplot/plotter'
include Pgplot

# This should be in mirdl!
def basant(bl)
  [bl.to_i >> 8, bl.to_i % 256]
end
def polmap(pp)
  case pp
  when  1: 'I'
  when  2: 'Q'
  when  3: 'U'
  when  4: 'V'
  when -1: 'RR'
  when -2: 'LL'
  when -3: 'RL'
  when -4: 'LR'
  when -5: 'XX'
  when -6: 'YY'
  when -7: 'XY'
  when -8: 'YX'
  else '??'
  end
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
  nsigma = keyr(:nsigma, 5.0)

  # Get maxiters
  iter_limit = keyr(:maxiter, 10)

  # Get nbs, number of basis splines
  nbs = keyi(:nbs)

  # Get options
  optkeys = [:polar, :rect, :scatter, :nofit, :flag]
  optvals = options(optkeys)
  # Convert optkeys and optvals into a Hash
  opts = Hash[*optkeys.zip(optvals).flatten!]
keyfin

ltype = uvDatGta(:ltype)
if ltype != '' && ltype != 'channel'
  bug(:fatal, "unsupported line type '#{ltype}'")
end

# Require flag or plot type option
if !opts[:flag] && !opts[:polar] && !opts[:rect] && !opts[:scatter]
  bug(:fatal, 'must specify flag or plot type using options=')
end

# Disallow flagging and plotting simultaneously
if opts[:flag] && (opts[:polar] || opts[:rect] || opts[:scatter])
  bug(:fatal, 'cannot flag and plot at the same time')
end

# Disallow flag and nofit options simultaneously
if opts[:flag] && opts[:nofit]
  bug(:fatal, "cannot specify both 'flag' and 'nofit' at the same time")
end

if opts[:polar] || opts[:rect] || opts[:scatter]
  # Iniitalize plot device
  Plotter.new(:device => device,
              :nx=>nx,
              :ny=>ny,
              :ask=>true)
  # Make text bigger
  pgsch(1.5)
end

k = 4 # Cubic
bss_nchan = nil

while tno = uvDatOpn

  # Get number of channels
  nchan = uvDatGti(:nchan)
  nchan = uvrdvri(tno, :nchan) if nchan == 0

  v = Vis.new(nchan)
  xx=NArray.float(nchan).indgen!

  bx = nil
  mfwork = nil
  # Setup B-Spline solver for this nchan
  if bss_nchan != nchan
    bss_nchan != nchan
    ncoeff = (nbs != 0 ? nbs : (nchan+31) / 32)
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
    # Create multi-fit workspace
    mfwork = GSL::MultiFit::Workspace.new(nchan, ncoeff)
  end

  # Counter so we cal call garbage collector every so often
  gc_counter = 0
  while uvDatRd(v)
    # Skip to next if completely flagged
    next if v.flags.sum == 0
    # TODO Handle partial flagging

    gc_counter += 1
    if gc_counter % 10 == 0
      ObjectSpace.garbage_collect
      gc_counter = 0
    end

    # Setup for B-Spline fits to real and imag
    yr = v.data.real
    yrv = yr.to_gv
    yi = v.data.imag
    yiv = yi.to_gv
    inliers = v.flags
    inliers_count = inliers.sum
    var = 0.0
    byr_na = NArray.float(yr.length)
    byi_na = NArray.float(yi.length)

    # Iteration loop
    iter = 0
    if !opts[:nofit]
      begin
        # Increment iter counter
        iter += 1

        # Do weighted B-Spline fits to real and imag
        inliers_count = inliers.sum
        wv = inliers.to_gv
        bcr, covr, chisqr, statusr = GSL::MultiFit.wlinear(bx, wv, yrv, mfwork)
        bci, covi, chisqi, statusi = GSL::MultiFit.wlinear(bx, wv, yiv, mfwork)
        var = (chisqr + chisqi)/(nchan - 1)

        # Evaluate fits to get smoothed real/imag
        byr = bx * bcr
        byi = bx * bci

        # Convert GSL::Vector to NArray.float
        byr_na[] = byr.to_na_ref
        byi_na[] = byi.to_na_ref

        # Identify points that are more than nsigma standard deviations out from
        # real/imag fits
        #rr = byr_na.dup.sbt!(yr)
        #ir = byi_na.dup.sbt!(yi)
        rr = yr-byr_na
        ir = yi-byi_na
        res2 = rr**2 + ir**2
        inliers = res2.lt(nsigma*var).and(inliers).to_type(NArray::INT)
      
      # Keep iterating until limit is exceeded or no new outliers found
      end until iter >= iter_limit || inliers_count == inliers.sum
      #TODO p [uvDatGti(:visno), iter]
    end

    # Convert NArray.floats to NArray.scomplex (scomplex should provide
    # sufficent resolution/precision and facilitates subsequenct plotting).
    #bz = byr_na + byi_na.to_type(NArray::SCOMPLEX)*1.im unless opts[:nofit]
    bz = byi_na.to_type(NArray::SCOMPLEX).mul!(1.im).add!(byr_na) unless opts[:nofit]

    # If flagging
    if opts[:flag]
      # Write out new flags
      uvflgwr(tno, inliers.to_type(NArray::INT))
      next # Skip plots
    end
    # Determine outlier indexes
    outliers_idx = inliers.not.where

    # Setup plot metadata
    rms = Math.sqrt(var)
    bl = v.preamble[3]
    a1, a2 = basant(bl)
    src = uvrdvra(tno, :source)
    utstr = uvrdvrd(tno, :ut).r2h.to_hmsstr(0)
    polstr = polmap(uvDatGti(:pol))
    #title = '%s %d-%d (rms=%.3f, niter=%d)' % [src, a1, a2, rms, iter]
    # title is "src utstr polstr a1-a2"
    title = '%s %s %s %d-%d' % [src, utstr, polstr, a1, a2]
    # title2 is "plot_type"
    title2 = opts[:nofit] ? ('%s') : ('%%s: RMS=%.5g Iters=%d' % [rms, iter])
    lineinfo ||= uvinfo(tno, :line, 6)
    # Compute "virtual" channel numbers based on line parameters
    xxplot = xx * lineinfo[4] + lineinfo[2] + lineinfo[3]/2.0 - 0.5

    if opts[:polar]
      magphase(xxplot,v.data,
               :title => title,
               :title2 => title2 % ['Polar'],
               :xlabel => 'Channel',
               :mag_color => Color::BLUE,
               :phase_color => Color::YELLOW
              )
      magphase(xxplot,bz,:overlay=>true,
               :mag_color => Color::CYAN,
               :phase_color => Color::GREEN
              ) if bz
      axis(:mag)
      pgsci(Color::RED)
      pgpt((xx+lineinfo[2])[outliers_idx], v.data[outliers_idx].abs, Marker::CIRCDOT)
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
           :title2 => title2 % ['Rect'],
           :xlabel => 'Channel',
           :ylabel => 'Real (Blue), Imag (Yellow)',
           :line_color => Color::WHITE
          )

      pgsci(Color::BLUE)
      pgline(xxplot, yr)
      pgsci(Color::YELLOW)
      pgline(xxplot, yi)
      if byr_na
        pgsci(Color::CYAN)
        pgline(xxplot, byr_na)
        pgsci(Color::GREEN)
        pgline(xxplot, byi_na)
      end
      pgsci(Color::RED)
      pgpt((xxplot)[outliers_idx], yr[outliers_idx], Marker::CIRCDOT)
      pgpt((xxplot)[outliers_idx], yi[outliers_idx], Marker::CIRCDOT)
    end
    if opts[:scatter]
      xmin, xmax = yrv.minmax
      ymin, ymax = yiv.minmax
      # Setup plot range
      #pgsci(Color::WHITE)
      plot([xmin, xmax], [ymin, ymax],
           :line=>:none,
           :title=> title,
           :title2 => title2 % ['Scatter'],
           :xlabel => 'Real',
           :ylabel => 'Imag',
           :line_color => Color::WHITE
          )

      pgsci(Color::BLUE)
      pgline(yr, yi)
      pgpt1(yr[0], yi[0], Marker::STAR)
      if byr_na
        pgsci(Color::CYAN)
        pgline(byr_na, byi_na)
        pgpt1(byr_na[0], byi_na[0], Marker::STAR)
      end
      pgsci(Color::RED)
      pgpt(yr[outliers_idx], yi[outliers_idx], Marker::CIRCDOT)
    end
  end

  uvDatCls
end # uvDatOpn
