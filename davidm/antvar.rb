#!/usr/bin/env ruby
$-w = true if $0 == __FILE__ # Turn on warnings

# $Id$

# Derive antenna-based variances

require 'gsl'
require 'mirdl'
include Mirdl

# This should be in mirdl!
def basant(bl)
  [bl.to_i >> 8, bl.to_i % 256]
end

keyini
  # d = use select keyword
  # s = use stokes keyword (needed?)
  # l = use line keyword
  # 3 = include w in preamble
  uvDatInp('dsl3')

  # Time interval over which to average visdata
  # (given in minutes, but stored as days)
  interval = keyr(:interval, 1.0) / (24*60)
keyfin

# TODO Rename to more general name
def fit_antvar(d, n)
  base = d.keys.sort
  ants = base.flatten.uniq.sort
  nants = ants.length
  nbase = d.keys.length

  if nbase == 0 || nants == 0
    p d
    p [nbase, nants]
    return
  end

  # Create matrices for solving antenna based quantities (e.g. gains,
  # variances)
  a = GSL::Matrix[nbase, nants]
  b_gain = GSL::Vector[nbase]
  b_var = GSL::Vector[nbase]
  b_snr = GSL::Vector[nbase]
  work = GSL::MultiFit::Workspace.alloc(a.size1, a.size2)

  row = 0
  base.each do |bl|
    a1, a2 = bl
    # Compute average over time
    d[bl][n[bl].where] /= n[bl][n[bl].where]

    if n[bl].where.length > 1
      vv = d[bl][n[bl].where]
      blmean = vv.mean#.abs #** 2
      # Setting blvar to 1 gives inverse gains for flux=1
      # Setting blvar to stddev of data gives a kind of SNR measure
      #blvar = 1
      blvar = vv.stddev #** 2
      # Populate a and b
      a[row, ants.index(a1)] = 1
      a[row, ants.index(a2)] = 1
      begin
        b_gain[row] = Math.log(blmean.abs)
        b_var[ row] = blvar
        b_snr[ row] = Math.log(blmean.abs/blvar)
      rescue
        p [bl, blmean, blvar, n[bl].where]
        raise
      end
    end
    row += 1
  end
  # Solve for x_gains, x_var, x_snr
  x_gain, cov_gain, chisq_gain, status_gain = GSL::MultiFit.linear(a, b_gain, work)
  x_var, cov_var, chisq_var, status_var = GSL::MultiFit.linear(a, b_var, work)
  x_snr, cov_snr, chisq_snr, status_snr = GSL::MultiFit.linear(a, b_snr, work)
  # Repackage x
  h = {}
  ants.each_index do |i|
    h[ants[i]] = [Math.exp(x_gain[i]), x_var[i], Math.exp(x_snr[i])]
  end
  [h, chisq_gain, chisq_var, chisq_snr]
end

def display_antvar(v, caption='Antenna variances')
  return unless v
  puts caption if caption
  v.keys.sort.each do |ant|
    #printf "%02d  %.5f  %.5f\n", ant, *v[ant] 
    #printf "%02d  %.3f\n", ant, 1.0/v[ant][0].abs
    printf "%02d  %.3f  %.3f  %.3f  %.3f\n", ant,
      1/v[ant][0], v[ant][1], v[ant][2], v[ant][0] / v[ant][1]
  end
end

# Loop through data files
while tno = uvDatOpn

  puts "----- #{uvDatGta(:name)} -----"

  # Get number of channels
  nchan = uvDatGti(:nchan)
  nchan = uvrdvri(tno, :nchan) if nchan == 0
  # Create a new Vis object
  v = Vis.new(nchan)

  # Create Hashes to store data
  xxd = Hash.new {|h,k| h[k] = NArray.scomplex(nchan)}
  xxn = Hash.new {|h,k| h[k] = NArray.int(nchan)}
  yyd = Hash.new {|h,k| h[k] = NArray.scomplex(nchan)}
  yyn = Hash.new {|h,k| h[k] = NArray.int(nchan)}

  interval_end = uvrdvrd(tno, :time) + interval

  # Loop through data
  while uvDatRd(v)

    # If we are in a new interval
    if uvrdvrd(tno, :time) > interval_end
      if !xxd.empty?
        xxv, xxchisq = fit_antvar(xxd, xxn)
        caption = 'X pol variances, chisq = %.5f' % [xxchisq]
        display_antvar(xxv, caption)
      end
      if !yyd.empty?
        yyv, yychisq = fit_antvar(yyd, yyn)
        caption = 'Y pol variances, chisq = %.5f' % [yychisq]
        display_antvar(yyv, caption)
      end
      #exit
      # Clear buffers
      xxd.clear
      xxn.clear
      yyd.clear
      yyn.clear
      # Re-calculate end of next interval
      interval_end = uvrdvrd(tno, :time) + interval
    end

    # Get baseline
    bl = basant(v.preamble[4])

    # Skip auto correlations
    next if bl[0] == bl[1]
    # Skip if all flagged
    next if v.flags.sum == 0

    # Accumulate the data into the visdata buffer
    # TODO Figure out more robust polarization handling
    pol = uvDatGti(:pol)
    case pol
    when -5 # XX
      v.data[v.flags.not.where] = 0
      xxd[bl] += v.data
      xxn[bl] += v.flags
    when -6 # YY
      v.data[v.flags.not.where] = 0
      yyd[bl] += v.data
      yyn[bl] += v.flags
    else
      next
    end
  end

  uvDatCls

  if !xxd.empty?
    xxv, xxchisq = fit_antvar(xxd, xxn)
    caption = 'X pol variances, chisq = %.5f' % [xxchisq]
    display_antvar(xxv, caption)
  end
  if !yyd.empty?
    yyv, yychisq = fit_antvar(yyd, yyn)
    caption = 'Y pol variances, chisq = %.5f' % [yychisq]
    display_antvar(yyv, caption)
  end
  
end
