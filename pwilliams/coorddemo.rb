#!/usr/bin/env ruby
$-w = true if $0 == __FILE__ # Turn on warnings

# UVW Coordinate demo

# Require the RubyGems extension and provide a more user-friendly message if it
# cannot be loaded
begin
  require 'rubygems'
rescue LoadError
  puts "ERROR: could not load the RubyGems extension"
  puts "Please see http://www.rubygems.org/ for installation instructions."
  exit 1
end

# Require the MIRIAD-Ruby extension and provide a more user-friendly message if
# it cannot be loaded
begin
  require 'miriad'
rescue LoadError
  puts "ERROR: could not load the MIRIAD-Ruby extension"
  puts "Please see http://miriad.rubyforge.org/ for installation instructions."
  exit 1
end

# Insist that a dataset be given on the commad line
raise "Usage: #{File.basename $0} DATASET" if ARGV.empty?

# Open the dataset and pass the object representing it into a "do...end" block.
# The dataset will be closed automatically when the block terminates.
Miriad::Uvio.open(ARGV[0]) do |ds|
  ds.select('auto', false)
  vis = ds.read(nil)
  u, v, w = vis.coord
  printf "%25.10f %15.10f %15.10f %15.10f\n", vis.jd, u, v, w
end
