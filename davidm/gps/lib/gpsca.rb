#!/usr/bin/env ruby

require 'lfsr'

class GPSCA

  G1 = LFSR.new(10,0x409,0x3ff).next(1023)
  G2 = LFSR.new(10,0x74c,0x3ff).next(1023)

  PRN_MIN =  1
  PRN_MAX = 37

  PRN_DELAY = [
     nil, # PRN   0 (N/A)
       5, # PRN   1
       6, # PRN   2
       7, # PRN   3
       8, # PRN   4
      17, # PRN   5
      18, # PRN   6
     139, # PRN   7
     140, # PRN   8
     141, # PRN   9
     251, # PRN  10
     252, # PRN  11
     254, # PRN  12
     255, # PRN  13
     256, # PRN  14
     257, # PRN  15
     258, # PRN  16
     469, # PRN  17
     470, # PRN  18
     471, # PRN  19
     472, # PRN  20
     473, # PRN  21
     474, # PRN  22
     509, # PRN  23
     512, # PRN  24
     513, # PRN  25
     514, # PRN  26
     515, # PRN  27
     516, # PRN  28
     859, # PRN  29
     860, # PRN  30
     861, # PRN  31
     862, # PRN  32
     863, # PRN  33
     950, # PRN  34
     947, # PRN  35
     948, # PRN  36
     950, # PRN  37
  ]

  @@ca = []

  def self.[](prn)
    raise "invalid PRN (#{prn})" unless (PRN_MIN..PRN_MAX) === prn
    unless @@ca[prn]
      delay = PRN_DELAY[prn]
      wrap = G2 & ((1 << delay) - 1)
      g2_prn = (wrap << (1023 - delay)) |  (G2 >> delay)
      ca_prn = G1 ^ g2_prn
      @@ca[prn] = (0...1023).map {|b| ca_prn[1022-b]}
    end
    @@ca[prn]
  end
end

if $0 == __FILE__
  (GPSCA::PRN_MIN...GPSCA::PRN_MAX).each do |prn|
    cai = GPSCA[prn]
    #printf("%2d %4o\n", prn, cai >> 1013) # print prn and octal first 10 chips
    if prn < 3
      p cai
      #cais = cai.to_s(2).split('').join(',') + ';'
      #puts cais
    end
  end
  #puts "]';"
end
