# TODO Convert this to Ruby unit test
require 'tle'

tle = <<END
1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753
2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667     0.00      4320.0        360.00
END

lines = tle.split("\n")

#p tle
#p lines[0]
#p lines[1]
#p lines.length
satrec = Tle::Elements.new(lines[0], lines[1], Tle::WGS72)

puts "satnum=#{satrec.satnum}"
puts "epochyr=#{satrec.epochyr}"
puts "epochtynumrev=#{satrec.epochtynumrev}"
puts "error=#{satrec.error}"
puts "init=#{satrec.init}"
puts "method=#{satrec.method}"
puts "t=#{satrec.t}"
puts "epochdays=#{satrec.epochdays}"
puts "jdsatepoch=#{satrec.jdsatepoch}"

12.times do |i|
  r, v = satrec.sgp4(360*i, Tle::WGS72)
  printf("%17.8f%17.8f%17.8f%17.8f%13.9f%13.9f%13.9f\n", 360*i, *[r, v].flatten)
end
