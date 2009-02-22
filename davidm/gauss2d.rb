#!/usr/bin/env ruby
$-w = true if $0 == __FILE__

module Gauss2d

  require 'gsl'
  include GSL

  NP = 5 # Number of parameters to fit
  MAXITER = 50 # Max number of iterations

  # Diagnostic info method
  def print_state(caption, solver, status=nil)
    printf "%s x =", caption
    solver.x.each {|xi| printf " %.3f", xi}
    printf " |f(x)| = %g", solver.f.dnrm2
    puts " #{status}" if status
    puts
  end
  module_function :print_state

  def gauss2d(x, y, a=1.0, x0=0.0, y0=x0, sx=1.0, sy=sx)
    a * Math.exp(-((x-x0)/sx)**2 - ((y-y0)/sy)**2)
  end
  module_function :gauss2d

  # x: Vector, list of the parameters to determine
  # t, y: observational data
  # f: Vector, function to minimize
  PROCF = lambda do |x, t, y, f|
    # Get current "guess" at parameters
    a, x0, y0, sx, sy = *x
    # For each observation
    for i in 0...t.length
      # Compute chi and store in f
      tx, ty = t[i]
      yi = gauss2d(tx, ty, a, x0, y0, sx, sy)
      f[i] = yi - y[i]
    end
  end

  # jac: Matrix, Jacobian
  PROCDF = lambda do |x, t, y, jac|
    # Get current "guess" at parameters
    a, x0, y0, sx, sy = *x
    # For each observation
    for i in 0...t.length
      # Compute elements of corresponding column of Jacobian matrix
      tx, ty = t[i]
      yi = gauss2d(tx, ty, a, x0, y0, sx, sy)
      # dyi/d(x[0]) (dyi/da)
      jac.set(i, 0, yi/a)
      # dyi/d(x[1]) (dyi/dx0)
      jac.set(i, 1, yi * 2 * (tx-x0) / sx**2)
      # dyi/d(x[2]) (dyi/dy0)
      jac.set(i, 2, yi * 2 * (ty-y0) / sy**2)
      # dyi/d(x[3]) (dyi/dsx)
      jac.set(i, 3, yi * 2 * (tx-x0)**2 / sx**3)
      # dyi/d(x[4]) (dyi/dsy)
      jac.set(i, 4, yi * 2 * (ty-y0)**2 / sy**3)
    end
  end

  # call-seq:
  #   Gauss2d.fit(t, y, solver=nil, init_guess=nil) -> [iter, solver, status]
  #
  # Fit a two dimensional Gaussian to observational data.  The formula for the
  # two dimensional Gaussian is:
  #
  #   y = a * Math.exp(-((tx-x0)/sigma_x)**2 - ((ty-y0)/sigma_y)**2)
  #
  # The parameters +t+ and +y+ provide the observational data to which the
  # parameters +a+, +x0+, +y0+, +sigma_x+, and +sigma_y+ are fit.  Because five
  # parameters are being fit, the number of observations in +t+ and +y+ must be
  # at least five.  Note that passing in weightings for the different
  # observations is not currently supported.
  #
  # +t+ is an Array of observed positions.  Elements of +t+ are two-element
  # Arrays [tx, ty].
  #
  # +y+ is an Array of observed values.  Length of +y+ must be the same as the
  # length of +t+.
  #
  # +solver+ is a GSL::MultiFit::FdfSolver instance.  If nil, a new one will be
  # allocated.  Typically used only for repetitive calls where the first call
  # will pass nil, and subsequent calls will pass the same solver instance that
  # was returned.
  #
  # +init_guess+ is the initial guess.  Should be GSL::Vector (or object that
  # has +#to_gv+ method) of five elements: a, x0, y0, sigma_x, sigma_y.
  #
  # +iter+ is number of iterations to converge
  #
  # +solver+ is the GSL::MultiFit::FdfSolver instance used to solve for the
  # fit.  <tt>solver.position</tt> gives the fitted paramters: +a+, +x0+, +y0+,
  # +sigma_x+, and +sigma_y+.  <tt>solver.covar(epsrel)</tt> will return the
  # covariance matrix (+epsrel+ is used to remove linear-dependent columns when
  # J (the Jacobian matrix) is rank deficient).  See the GSL documentation for
  # more details.
  def fit(t, y, solver=nil, init_guess=nil)
    # n is number of observations
    n = t.length

    # Require n >= NP
    raise "at least #{NP} observations needed, got #{t.length}" if NP > n
    raise "inconsistent number of observations (#{t.length} != #{y.length})" if n != y.length

    # Create function object for fitting 5 parameters based on procf and procdf
    f = MultiFit::Function_fdf.alloc(PROCF, PROCDF, NP)

    # Create solver
    solver ||= MultiFit::FdfSolver.alloc(MultiFit::FdfSolver::LMSDER, n, NP)

    # Create initial guess vector
    if init_guess
      x = init_guess
      # Convert to Vector unless it already is one
      x = x.to_gv unless Vector === x
    else
      s = t[1..-1].map{|a| a.to_gv.dnrm2}.to_gv.mean
      #            a,  x0,  y0, sx, sy
      x = Vector[y[0], 0.0, 0.0, s, s]
    end

    # Tell function object about observed data
    f.set_data(t, y)

    # Give function object and initial guess vector to solver
    solver.set(f, x)

    iter = 0
    #print_state("iter: #{iter}", solver)
    begin
      iter += 1
      status = solver.iterate
      # TODO Raise exception if status is bad?
      #print_state("iter: #{iter}", solver)
      status = solver.test_delta(1e-9, 1e-9)
    end while status == GSL::CONTINUE and iter < MAXITER

    #print_state("iter: #{iter}", solver)

    [iter, solver, status]
  end
  module_function :fit
end

if $0 == __FILE__
  ## Test data
  #R32 = sqrt(3)/2
  #t = [
  #  [ 0.0, 0.0],
  #  [ 1.0, 0.0],
  #  [ 0.5, R32],
  #  [-0.5, R32],
  #  [-1.0, 0.0],
  #  [-0.5,-R32],
  #  [ 0.5,-R32],
  #]
  #
  #y = t.map {|tx,ty| gauss2d(tx, ty, 0.95, 0.1, -0.5, 1.1, 0.9)}

  # Data from 2009/02/04/3c274mos
  #
  # dra and ddec from center pointing.
  # Interestingly, distance from center is not constant
  t = [
    [    0.0          ,    0.0               ],
    [-4751.97908192269,   -0.0563660778631118],
    [ 4757.38277865805,   -0.0433857304838948],
    [-2376.01060282106,-4021.58303952307     ],
    [ 2381.37929666652,-4021.55382645814     ],
    [-2376.01099948467, 4021.52986833353     ],
    [ 2381.36808515451, 4021.55966729603     ],
  ]

  gs = [
    [0.993,     0.998,     1.020,     0.000,     0.962,     0.982],
    [1.365,     1.503,     1.307,     0.000,     1.262,     1.258],
    [1.588,     1.464,     1.707,     0.000,     1.663,     1.703],
    [1.310,     1.404,     1.647,     0.000,     1.252,     1.293],
    [1.447,     1.396,     1.992,     0.000,     1.459,     1.513],
    [1.472,     1.506,     1.077,     0.000,     1.349,     1.355],
    [1.516,     1.488,     1.182,     0.000,     1.487,     1.573],
  ].transpose

  gs.each_with_index do |gy, i|
    ant = (i >> 1) + 1
    pol = (?X+(i&1)).chr 
    if gy.to_gv.sum == 0
      puts "#{ant}#{pol} (0 iters)"
      next
    end
    y = gy.map {|g| 1.0/g}
    #puts "Fitting for #{ant}#{pol}..."

    iter, solver, status = Gauss2d.fit(t, y, solver)

    Gauss2d.print_state("#{ant}#{pol} (#{iter} iters)", solver)#, status)
  end
end
