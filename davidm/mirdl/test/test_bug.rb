#!/usr/bin/env ruby
$-w = true if $0 == __FILE__

require 'rubygems'
require 'mirdl'
include Mirdl

keyini
keyfin

puts '-----'
bug(:i, 'this is informational')
puts '-----'
bug(:w, 'this is a warning')
puts '-----'
begin
  bug(:e, 'this is an error')
rescue => e
  puts e
  puts e.backtrace.join("\n")
end
puts '-----'
bug(:f, 'this is a fatal error')

puts 'this should NOT be output'
