#!/usr/bin/env ruby
$-w = true if $0 == __FILE__

require 'mirdl'
include Mirdl
include Math

require 'gsl'
include GSL

N  = 7  # Number of observations
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

def gauss2(x, y, a=1.0, x0=0.0, y0=x0, sx=1.0, sy=sx)
  a * exp(-((x-x0)/sx)**2 - ((y-y0)/sy)**2)
end

# x: Vector, list of the parameters to determine
# t, y: observational data
# f: Vector, function to minimize
procf = lambda do |x, t, y, f|
  # Get current "guess" at parameters
  a, x0, y0, sx, sy = *x
  # For each observation
  for i in 0...t.length
    # Compute chi and store in f
    tx, ty = t[i]
    yi = gauss2(tx, ty, a, x0, y0, sx, sy)
    f[i] = yi - y[i]
  end
end

# jac: Matrix, Jacobian
procdf = lambda do |x, t, y, jac|
  # Get current "guess" at parameters
  a, x0, y0, sx, sy = *x
  # For each observation
  for i in 0...t.length
    # Compute elements of corresponding column of Jacobian matrix
    tx, ty = t[i]
    yi = gauss2(tx, ty, a, x0, y0, sx, sy)
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

# Create function object for fitting 5 parameters based on procf and procdf
f = MultiFit::Function_fdf.alloc(procf, procdf, 5)

# TODO Get observed data

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
#y = t.map {|tx,ty| gauss2(tx, ty, 0.95, 0.1, -0.5, 1.1, 0.9)}

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

# Create solver
solver = MultiFit::FdfSolver.alloc(MultiFit::FdfSolver::LMSDER, N, NP)

gs.each_with_index do |gy, i|
  ant = (i >> 1) + 1
  pol = (?X+(i&1)).chr 
  if gy.to_gv.sum == 0
    puts "#{ant}#{pol} (0 iters)"
    next
  end
  y = gy.map {|g| 1.0/g}
  #puts "Fitting for #{ant}#{pol}..."

  # Expecting N observations
  raise "expected #{N} observations, got #{t.length}" if N != t.length
  raise "inconsistent number of observations (#{t.length} != #{y.length})" if t.length != y.length

  # Create initial guess vector
  a = y[0]
  s = t[1..-1].map{|a| a.to_gv.dnrm2}.to_gv.mean
  #            a,  x0,  y0, sx, sy
  x = Vector[y[0], 0.0, 0.0, s, s]

  # Tell function object about observed data
  f.set_data(t, y)

  # Give initial guess vector and function object to solver
  solver.set(f, x)

  iter = 0
  #print_state("iter: #{iter}", solver)
  begin
    iter += 1
    status = solver.iterate
    #print_state("iter: #{iter}", solver)
    status = solver.test_delta(1e-9, 1e-9)
  end while status == GSL::CONTINUE and iter < MAXITER

  print_state("#{ant}#{pol} (#{iter} iters)", solver)#, status)
end
