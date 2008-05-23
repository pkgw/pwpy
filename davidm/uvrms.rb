#!/usr/bin/env ruby
$-w = true if $0 == __FILE__ # Turn on warnings

# $Id$

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

  # Select the parallel-hand autocorrelations
  ds.select('polarization', true, Miriad::POLMAP['XX'])
  ds.select('polarization', true, Miriad::POLMAP['YY'])
  ds.select('auto', true)

  # Setup channel averaging to get one datum per spectrum
  # Other examples
  #ds.set('data','channel', 1, 256, 1, 1) # Channel 256 only
  #ds.set('data','channel', 1, 256, 100, 1) # Average 100 channels starting at 256
  #ds.set('data','channel', 1, 256, 4, 5) # Average channels 200, 205, 210, 215
  # Somewhat specific to current ATA datat catcher
  if ds[:nchan] == 1024
    # Full ATA band, all but end 100 channels
    nchan = 824
    schan = 101
  elsif ds[:sfreq] == ds[:freq]
    # Second half of ATA band, all but first 1 and last 100 channels
    nchan = 411
    schan = 2
  else
    # First half of ATA band, all but first 100 channels
    nchan = 412
    schan = 101
  end
  ds.set('data','channel', nchan, schan, 1, 1)

  # Compute scale factor from integration time
  scale = 2*1024*100*ds[:inttime]

  # Create Hash to store amplitude data
  amps = Hash.new {|h,k| h[k] = [NArray.sfloat(nchan), 0]}

  # This is a way to loop through datasets.  Note that passing vis into read
  # will cause it to be modified in place rather than having a new vis object
  # created and returned each read.  Read returns nil, which is treated as
  # false, when there are no more records (i.e. at end of file).
  while vis = ds.read(vis)
    # Get the antennas from the current visibility
    a1, a2 = vis.basant

    # Get the string representation of the current value of the 'pol' uv
    # variable.  Use "|| '--'" to provide default value in case pol is undefined
    # in dataset.
    pol = ds.polstr || '--'

    # Add the amp value to antpol's data in Hash
    key = [a1, pol[0,1]]
    data = amps[key]
    data[0] += vis.data.abs
    data[1] += 1
  end

  # Output header
  printf "Ant     [Four bit RMS, %4d chan]\n", nchan
  printf "Pol     Mean      Std    Norm-Std\n"
  amps.keys.sort.each do |k|
    sumspect, n = amps[k]
    meanspect = sumspect / n
    rmsspect = NMath.sqrt(meanspect/scale)
    meanrms = rmsspect.mean
    stdrms = rmsspect.stddev
    normstdrms = rmsspect.stddev / meanrms
    mean1 = meanspect.mean
    rms1 = Math.sqrt(mean1/n/scale)
    # Output the record
    printf("%3s   %7.4f   %7.4f   %7.4f\n", k.join, meanrms, stdrms, normstdrms)
  end
end
