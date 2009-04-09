#!/usr/bin/env ruby
$-w = true if $0 == __FILE__

require 'gsl'

module VisFit

  MAXITER = 100 # Max number of iterations

  # call-seq:
  #   VisFit.prod_fit(map_ij_yij, work=nil) -> [map_i_x, chisq, work]
  #
  # Given a Hash +map_ij_yij+  whose keys are two element Arrays of integers
  # (e.g. [i,j] or [a1,a2]) and whose corresponsing values are the product of
  # two *positive* factors (e.g. x[i]*x[j] or x[a1]*x[a2]), determine the
  # factors and return them in a Hash, +map_i_x+ with integer key and
  # corresponding value.  Also return the chisq of the fit and the workspace
  # used.
  #
  # Note that the fit is done as log(yij) = log(xi) + log(xj), which will
  # minimize chisq in log space, but might not result in the minimum chisq in
  # linear space.
  def prod_fit(ij_yij, work=nil)
    # ij is Array of [i,j] pairs
    ij = ij_yij.keys.sort
    # ii is Array of all distinct i (and j) values
    ii = ij.flatten.uniq.sort

    # n is number of products
    n = ij.length

    # nx is number of parameters.
    nx = ii.length

    # Require n >= nx
    raise "at least #{nx} observations needed, got #{n}" if nx > n

    # Create fit objects
    a = GSL::Matrix[n, nx]
    b = GSL::Vector[n]
    work ||= GSL::MultiFit::Workspace.alloc(n, nx)

    row = 0
    ij.each do |k|
      i, j = k

      # Populate a and b
      a[row, ii.index(i)] = 1
      a[row, ii.index(j)] = 1
      y = ij_yij[k].abs
      b[row] = Math.log(y == 0.0 ? Float::EPSILON : y)

      row += 1
    end

    # Do fit
    logx, covar, logchisq, status = GSL::MultiFit.linear(a, b, work)

    # TODO Check status

    # Convert x back to linear
    x = logx.exp

    # Build i_x
    i_x = {}
    ii.each_index do |idx|
      i_x[ii[idx]] = x[idx]
    end

    # Calc linear space chisq
    chisq = 0.0
    ij.each do |k|
      i, j = k
      chisq += (x[i]*x[j] - ij_yij[k]) ** 2
    end

    [i_x, chisq, work]
  end
  module_function :prod_fit

  # call-seq:
  #   VisFit.diff_fit(map_ij_yij, ref_i, work=nil) -> [map_i_x, chisq, covar, work]
  #
  # Given a Hash +map_ij_yij+  whose keys are two element Arrays of integers
  # (e.g. [i,j] or [a1,a2], with i <= j or a1 <= a2) and whose corresponsing
  # values are the difference of two reals (e.g. x[i]-x[j] or x[a1]-x[a2]),
  # determine the reals *relative to x[ref_i]* and return them in a Hash,
  # +map_i_x+ with integer key and corresponding value.  Also returns chisq and
  # the covariance matrix of the fit and the workspace used.
  def diff_fit(ij_yij, ref_i, work=nil)
    # ij is Array of [i,j] pairs
    ij = ij_yij.keys.sort
    # ii is Array of all distinct i (and j) values
    ii = ij.flatten.uniq.sort

    # n is number of differences
    n = ij.length

    # nx is number of parameters.
    nx = ii.length

    # Require n >= nx
    raise "at least #{nx} observations needed, got #{n}" if nx > n

    # Create fit objects
    a = GSL::Matrix[n, nx]
    b = GSL::Vector[n]
    work ||= GSL::MultiFit::Workspace.alloc(n, nx)

    row = 0
    ij.each do |k|
      i, j = k

      # Populate a and b
      a[row, ii.index(i)] = (i == ref_i ? 0 :  1)
      a[row, ii.index(j)] = (j == ref_i ? 0 : -1)
      b[row] = ij_yij[k]

      row += 1
    end

    # Do fit
    x, covar, chisq, status = GSL::MultiFit.linear(a, b, work)

    # TODO Check status

    # Build i_x
    i_x = {}
    ii.each_index do |idx|
      i_x[ii[idx]] = x[idx]
    end

    [i_x, chisq, work]
  end
  module_function :diff_fit
end

if $0 == __FILE__

  nx = 4
  re = (0...nx).map {rand}
  im = (0...nx).map {rand}
  noise_re = (0...nx).map {rand/1e3}
  noise_im = (0...nx).map {rand/1e3}
  z = re.to_gv + im.to_gv*GSL::Complex[0,1]
  noise_z = noise_re.to_gv + noise_im.to_gv*GSL::Complex[0,1]
  ij_magij = {}
  ij_phaij = {}
  noise_power = 0.0
  (0...nx-1).each do |i|
    (i+1...nx).each do |j|
      zz = (z[i]+noise_z[i]) * (z[j]+noise_z[j]).conj
      ij_magij[[i,j]] = zz.abs
      ij_phaij[[i,j]] = zz.angle
    end
  end
  
  ref_i = 2
  magfit, magchisq, ignore = VisFit.prod_fit(ij_magij)
  phafit, phachisq, ignore = VisFit.diff_fit(ij_phaij, ref_i)
  p z.abs
  p magfit.keys.sort.map {|k| magfit[k]}
  p magchisq
  p (z*z[ref_i].conj).angle
  p phafit.keys.sort.map {|k| phafit[k]}
  p phachisq
end
