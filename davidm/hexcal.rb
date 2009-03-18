#!/usr/bin/env ruby
$-w = true if $0 == __FILE__

require 'mirdl'
include Mirdl::Task

require 'fileutils'
include FileUtils

# Get vis list from command line and sort it
viskey = ARGV.grep(/^vis[-=]/)[-1]
raise 'No vis files given (use vis=...)' unless viskey
kw, vis = viskey.split(/[-=]/, 2)
vis = vis.split(',')
vis = vis.map {|v| Dir.glob(v)}
vis.flatten!
vis.sort!

# Easier way to refer to central pointing
cvis = vis[0]

# mfcal opts are all opts minus the vis and hexopts keywords
mfcal_opts = ARGV.grep(/^(?!vis[-=])/).grep(/^(?!hexopts[-=])/)
# uvcal opts are only select=
uvcal_opts = ARGV.grep(/^select[-=]/)
# Get hexopts from command line
hexopts = ARGV.grep(/^hexopts[-=]/)[-1]
# Strip 'hexopts=' part
hexopts = hexopts.sub(/^hexopts[-=]/,'') if hexopts

# Insert placeholder flux for mfcal
mfcal_opts.unshift 'flux=1'

# Run mfcal on central pointing
puts "Running mfcal on central pointing (#{cvis})"
out = run(:mfcal, mfcal_opts + ["vis=#{cvis}"])
# TODO grep for error message in output
#puts out
raise "mfcal exited with status #{$?}" unless $? == 0

# Run gpcopy to copy gains from central pointing to other pointings
for v in vis[1..-1]
  puts "Running gpcopy to copy gains from central pointing (#{cvis}) to #{v}"
  out = run(:gpcopy, :vis => cvis, :out => v)
  # TODO check for error in $? or output
  #puts out
end

# Apply gains and recalibrate
vouts = []
for v in vis
  vouts << (vout = "#{v}.hexcal")
  rm_rf(vout, :verbose => true)

  puts "Running uvcal to apply gains to #{v}"
  out = run(:uvcal, uvcal_opts + ["vis=#{v}", "out=#{vout}", '2>&1'])
  # TODO check for error in $? or output
  #puts out

  # Run mfcal on vout
  puts "Running mfcal on #{vout}"
  out = run(:mfcal, mfcal_opts + ["vis=#{vout}"])
  # TODO check for error in $? or output
  #puts out
end

# Run hex7.rb on all vouts
out = run('hex7.rb', :vis => vouts.join(','), :hexopts => hexopts)
puts out
