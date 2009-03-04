#!/usr/bin/env ruby
$-w = true if $0 == __FILE__

#
# $Id$
#

STDOUT.sync = true
STDERR.sync = true

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
rescue MiriadError => e
  puts e
  puts e.backtrace.join("\n")
end
puts '-----'
begin
  puts "about to call bug with a fatal error"
  puts "under new-style bug handler, this will be rescued"
  puts "under old-style bug handler, this will terminate the process"
  bug(:f, 'this is a fatal error')
rescue MiriadError => e
  puts e
  puts e.backtrace.join("\n")
ensure
  puts "hello from ensure block protecting fatal bug call!"
end
puts 'if you see this, you have new-style bug handler!'
puts '-----'
begin
  bug(:f, 'this is a fatal error that will not be rescued')
rescue MiriadNonFatalError => e
  puts e
  puts e.backtrace.join("\n")
end

puts 'this should NOT be output'
