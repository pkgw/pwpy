#! /usr/bin/env ruby

require "gsl"
include GSL
ephemFile = ARGV[0]
ephemTime = ARGV[1].to_f
az = []
el = []
times = []
az.inspect
File.open(ephemFile).each do |row|
  rowValues = row.split
  times << rowValues[0].to_f
  az << rowValues[1].to_f
  el << rowValues[2].to_f
end
#NArray.to_na(az)
azVector = Vector.alloc(az) 
elVector = Vector.alloc(el)
timesVector = Vector.alloc(times)
azSpline = Spline.alloc(timesVector,azVector)
elSpline = Spline.alloc(timesVector,elVector)
puts azSpline.eval(ephemTime)
puts elSpline.eval(ephemTime)
