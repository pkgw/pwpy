#!/usr/bin/env ruby

require 'mirdl'

class Numeric
  def to_dmsstr_old(prec=3)
    width = prec == 0 ? 2 : prec+3
    scale = (3600 * 10 ** prec).to_f
    d,m,s = to_dms
    "%02dd%02dm%0#{width}.#{prec}fs" % [d,m,s+5*10**(-prec-1)]
  end
  def to_hmsstr_old(prec=3)
    width = prec == 0 ? 2 : prec+3
    h,m,s = to_hms
    "%02d:%02d:%0#{width}.#{prec}f" % [h,m,s+5*10**(-prec-1)]
  end
end

secs = [0, 1, 2, 3, 5, 10]

secs.each do |intsec|
  10.times do |prec|
    sec = (intsec + 10.0**(-prec))
    hour = sec / 60.0 / 60.0
    puts "#{sec} #{hour.to_hmsstr(prec)} #{hour.to_hmsstr(15)}"
  end
end

secs.each do |intsec|
  10.times do |prec|
    sec = (intsec - 10.0**(-prec))
    hour = sec / 60.0 / 60.0
    puts "#{sec} #{hour.to_hmsstr(prec)} #{hour.to_hmsstr(15)}"
  end
end
