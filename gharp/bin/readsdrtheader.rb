#! /usr/local/bin/ruby
# Readsdrtheader
# Dumps SDRT header data to the screen for a SDRT file - for info purposes

fn = ARGV[0]
if fn == nil
    puts "Must specify file name as argument"
    puts "ie, readsdrtheader.rb infile.ts"
    exit
end

x = File.new(fn,"r")
hdr = x.sysread(70)
hdrarr = hdr.unpack("V2E4V8")
sn = hdrarr[0]
ldat = hdrarr[1]
fcen = hdrarr[2]
fsky = hdrarr[3]
fbw = hdrarr[4]
gain=hdrarr[5]
ver = hdrarr[6]
ntph = hdrarr[7]
ntpl = hdrarr[8]
streams = hdrarr[9]
flags=hdrarr[10]
x.close

puts "====== Read header format ========"
puts "Serial Number of First Frame: #{sn}"
puts "LDAT (Packing Number): #{ldat}"
puts "Center Frequency: #{fcen}"
puts "Sky tuning Frequency: #{fsky}"
puts "Bandwidth: #{fbw}"
puts "Gain: #{gain}"
puts "Version Number of File: #{ver}"
puts "NTP_High: #{ntph}"
puts "NTP_Low: #{ntpl}"
puts "Streams: #{streams}"
puts "Flags: #{flags}"
puts "=================================="
