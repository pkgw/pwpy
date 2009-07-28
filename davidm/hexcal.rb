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

# Get dra and ddec from last vis.
tno = Mirdl.uvopen(vis[-1])
dra = Mirdl.uvrdvrd(tno, :dra)
ddec = Mirdl.uvrdvrd(tno, :ddec)
Mirdl.uvclose(tno)

# If dra and ddec of last pointing are both 0.0 then assume "old-style"
# observations where offset pointings had phase and delay centers at the offset
# pointing position.  Otherwise, assume "new-style" observations where phase
# and delay centers are always on the calibrator's actual position regardless
# of antenna pointing.
old_style = ((dra == 0.0) && (ddec == 0.0))
# Old-style observations are calibrated and fitted by...
#
# 1) [hexcal.rb] Running mfcal on center pointing with explicit flux=
# 2) [hexcal.rb] Copying gains (using gpcopy) to other 6 pointings
# 3) [hexcal.rb] Applying gains to all pointings using uvcal
# 4) [hexcal.rb] Re-running mfcal with explicit flux= on the gains-applied
#                datasets
# 5) [hex7.rb]   Fit Gaussians to the inverse gains at the offset poistions of
#                the re-mfcal'd datasets.
#
# New-style observations are calibrated and fitted by...
#
# 1) [hexcal.rb] Running mfcal with explicit flux= on all datasets
# 2) [hex7.rb]   Fit Gaussians to the ratio of central gain to offset gains at
#                offset posiitons.
#
# Note that New-style calibration is experimental.
# Might need to mfcal, apply, mfcal.
#

if old_style
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
else # new_style
  vouts = vis
  for v in vis
    # Run mfcal on v
    puts "Running mfcal on #{v}"
    out = run(:mfcal, mfcal_opts + ["vis=#{v}"])
    # TODO check for error in $? or output
    #puts out
    raise "mfcal exited with status #{$?}" unless $? == 0
  end
end

## Run hex7.rb on all vouts
#out = run('hex7.rb', :vis => vouts.join(','), :hexopts => hexopts)
# Run gpfit.rb on all vouts
out = run('gpfit.rb', :vis => vouts.join(','), :options => hexopts)
puts out
