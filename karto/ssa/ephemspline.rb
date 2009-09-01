#! /usr/bin/env ruby

require "gsl"
include GSL

def ephemspline(ephemFile,ephemTime)
  az = [] # List of Az positions
  el = [] # List of El positions
  times = [] # List of times for positions
  File.open(ephemFile).each do |row| # Open the file and begin constucting the az, el and time arrays
    rowValues = row.split
    times << rowValues[0].to_f
    az << rowValues[1].to_f
    el << rowValues[2].to_f
  end
  # GSL requires things to be a vector type to do several operations, so we convert to Vectors
  azVector = Vector.alloc(az) 
  elVector = Vector.alloc(el)
  timesVector = Vector.alloc(times)
  # And go ahead and perform the spline fit
  azSpline = Spline.alloc(timesVector,azVector)
  elSpline = Spline.alloc(timesVector,elVector)
  return [azSpline.eval(ephemTime),elSpline.eval(ephemTime)].transpose
end

ephemFile = ARGV[0]
ephemTime = ARGV[1].split(',')
ephemFit = ephemspline(ephemFile,ephemTime)
puts ephemFit
