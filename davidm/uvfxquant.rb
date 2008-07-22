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

# Require the Ruby/PGPLOT extension and provide a more user-friendly message if
# it cannot be loaded
begin
  require 'pgplot'
rescue LoadError
  puts "ERROR: could not load the Ruby/PGPLOT extension"
  puts "Please see http://pgplot.rubyforge.org/ for installation instructions."
  exit 1
end
include Pgplot

BLACK, WHITE, RED, GREEN, BLUE, CYAN, MAGENTA, YELLOW, ORANGE, GREEN_YELLOW,
GREEN_CYAN, BLUE_CYAN, BLUE_MAGENTA, RED_MAGENTA, DARK_GRAY, LIGHT_GRAY = (0..15).to_a

do_only_one = false
chans="212,150"
pgplot_device = ENV['PGPLOT_DEV'] || '/xs'
nxy = "8,8"

while ARGV[0] && ARGV[0][0] == ?- do
    case ARGV[0][1]
        when ?1 : do_only_one = true
        when ?c : chans = ARGV[1]; ARGV.shift
        when ?d : pgplot_device = ARGV[1]; ARGV.shift
        when ?n : nxy = ARGV[1]; ARGV.shift
    end
    ARGV.shift
end

# Parse chans
nchan, schan, junk = chans.split(',',3).map {|s| s.to_i}

# Parse nxy
nx, ny, junk = nxy.split(',',3).map {|s| s.to_i}

# Insist that a dataset be given on the commad line
raise "Usage: #{File.basename $0} [-1] [-d PGPLOT_DEVICE] [-n nx,ny] DATASET [INTERVAL_MINUTES]" if ARGV.empty?

# Push default interval
ARGV << '0'

dsname = ARGV[0]
interval = ARGV[1].to_f / (24*60) # Convert minutes to days

def init_plot(pgplot_device, nx, ny)
  # Initialize pgplot device
  raise "error opening device #{pgplot_device}" if pgopen(pgplot_device) < 0
  #pgask(false)
  pgsubp(nx, ny)
  pgsch(2)
end

def plot_rms(channels, amps, scale, jd)
  # Output header
  amps.keys.sort.each do |k|
    sumspect, n = amps[k]
    meanspect = sumspect / n
    rmsspect = NMath.sqrt(meanspect/scale)

    nchan = rmsspect.length
    
    pgenv(channels[0], channels[-1], 0, 8, 0, -1)
    pgbox('ABCNST',128,4,'ABCNST',1,1)
    pglab('Channels', 'Four Bit Input RMS', DateTime.ajd(jd).to_s)
    pgsls(4)
    pgmove(channels[0],2)
    pgdraw(channels[-1],2)
    pgsls(1)

    # Add big labels
    pgsch(8)
    pgptxt(channels[0]+channels.length/16,5.5,0,0,k.join)
    pgsch(2)
    # Plot bins
    pgsci(BLUE)
    pgbin(channels, rmsspect, true)
    pgsci(WHITE)
  end
end

channels = NArray.float(nchan).indgen!(schan)

# Create Hash to store amplitude data
amps = Hash.new {|h,k| h[k] = [NArray.sfloat(nchan), 0]}

# Open the dataset and pass the object representing it into a "do...end" block.
# The dataset will be closed automatically when the block terminates.
Miriad::Uvio.open(ARGV[0]) do |ds|

  # Select the parallel-hand autocorrelations
  ds.select('polarization', true, Miriad::POLMAP['XX'])
  ds.select('polarization', true, Miriad::POLMAP['YY'])
  ds.select('auto', true)

  # Set the line
  ds.set('data','channel',nchan,schan,1,1)

  interval_end = ds[:time] + interval

  # Compute per-integration scale factor from integration time
  scale = 2*1024*100*ds[:inttime]

  # Initialze plot
  init_plot(pgplot_device, nx, ny)

  # This is a way to loop through datasets.  Note that passing vis into read
  # will cause it to be modified in place rather than having a new vis object
  # created and returned each read.  Read returns nil, which is treated as
  # false, when there are no more records (i.e. at end of file).
  while vis = ds.read(vis)

    # If we are in a new interval
    if ds[:time] > interval_end
      plot_rms(channels, amps, scale, interval_end - interval/2)
      pgpanl(nx,ny)
      exit if do_only_one
      # Clear amplitude buffer
      amps.clear
      # Re-calculate end of next interval
      interval_end = ds[:time] + interval
    end

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

  plot_rms(channels, amps, scale, interval_end - interval/2)
end
