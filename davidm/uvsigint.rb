#!/usr/bin/env ruby
$-w = true if $0 == __FILE__ # Turn on warnings

# $Id$
#
# Plot several integrations and their sum to see how the integration build up.

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

nints = 25
chans="212,150"
nx, ny = 4, 4
pgplot_device = ENV['PGPLOT_DEV'] || '/xs'

while ARGV[0] && ARGV[0][0] == ?- do
    case ARGV[0][1]
        when ?c : chans = ARGV[1]; ARGV.shift
        when ?d : pgplot_device = ARGV[1]; ARGV.shift
        when ?i : nints = Integer(ARGV[1]); ARGV.shift
        when ?n : ny = Integer(ARGV[1]); ARGV.shift
    end
    ARGV.shift
end

# Parse chans
schan, nchan, junk = chans.split(',',3).map {|s| s.to_i}

# Insist that a dataset and two ants and a pol be given on the commad line
raise "Usage: #{File.basename $0} [-c nchan,schan] [-d PGPLOT_DEVICE] [-i nints] [-n nx,ny] DATASET A1 A2" if ARGV.length < 3

dsname = ARGV[0]
a1 = ARGV[1].to_i
a2 = ARGV[2].to_i

#raise "antenna numbers must be different" if a1 == a2
a1, a2 = a2, a1 if a2 < a1

def init_plot(pgplot_device, nx, ny)
  # Initialize pgplot device
  raise "error opening device #{pgplot_device}" if pgopen(pgplot_device) < 0
  #pgask(false)
  pgsubp(nx, ny)
  #pgsch(2)
end

def plot_data(channels, data, caption)
  # Plot
  abssum = data.abs.sum(1)
  sumabs = data.sum(1).abs
  ratio = sumabs / abssum
  mean_ratio = ratio[abssum.ne(0)].mean
  ratio[abssum.eq(0)] = 0

  max = [abssum.max, sumabs.max].max
  ymax = max*1.05
    
  pgenv(channels[0], channels[-1], 0, ymax, 0, -2)
  #pgbox('ABCNST',0,0,'ABCNST',0,0)
  pglab('Channel', 'Amplitude', caption)
  # Draw bottom and top axes
  pgaxis(channels[0],0,channels[-1],0,channels[0],channels[-1],:opt=>'N',
         :step=>0,:nsub=>0,
         :tickl=>0.5,:tickr=>0,:frac=>0.5,
         :disp=>0.5,:orient=>0)
  pgaxis(channels[0],ymax,channels[-1],ymax,channels[0],channels[-1],
         :step=>0,:nsub=>0,
         :tickl=>0,:tickr=>0.5,:frac=>0.5,
         :disp=>0.5,:orient=>0)

  # Draw y axis on left for magnitudes
  pgaxis(channels[0],0,channels[0],ymax,0,ymax,:opt=>'N',:step=>0,
         :tickl=>0,:tickr=>0.5,:frac=>0.5,
         :disp=>-0.5,:orient=>0)

  # Plot individual dumps
  #pgsls(4)
  #4.times do |i|
  #  pgsci(RED+i)
  #  #pgbin(channels, 4*data[true,i].abs, true)
  #  pgline(channels, 4*data[true,i].abs)
  #end

  # Plot scalar-averaged amplitude
  pgsls(1)
  pgsci(RED)
  pgline(channels, abssum)

  # Plot vector-averaged amplitude
  pgsls(1)
  pgsci(BLUE)
  #pgbin(channels, sum.abs, true)
  pgline(channels, sumabs)

  # Setup second axis
  pgsci(WHITE)
  # Change window's world coordinates
  pgswin(channels[0],channels[-1],0,1)
  # Draw y axis on right for ratio
  pgaxis(channels[-1],0,channels[-1],1,0,1,:opt=>'N',
         :step=>0.5,:nsub=>5,
         :tickl=>0.5,:tickr=>0,:frac=>0.5,
         :disp=>0.3,:orient=>0)
  # Label ratio axis
  pgmtxt('R',2.7,0.5,0.5,'Ratio (vector/scalar)')
  # Plot ratio
  pgpt(channels, ratio, 3)#channels.total > 100 ? 1 : 3)
  #pgbin(channels, sumabs / abssum, true)
  #pgbin(channels, sumabs / abssum)

  # Plot mean ratio
  pgsci(GREEN)
  pgsls(3)
  pgmove(channels[0], mean_ratio)
  pgdraw(channels[-1], mean_ratio)
  pgsls(1)

  # Plot 1/sqrt(N) line
  n = data.shape[1] || 1
  if n > 1
    n = 1/Math.sqrt(n)
    pgsls(4)
    pgmove(channels[0],n)
    pgdraw(channels[-1],n)
    pgsls(1)
  end
  pgsci(WHITE)
end

channels = NArray.float(nchan).indgen!(schan)

# Create Hash to store vis data
data = Hash.new {|h,k| h[k] = NArray.scomplex(nchan,nints)}

# Open the dataset and pass the object representing it into a "do...end" block.
# The dataset will be closed automatically when the block terminates.
Miriad::Uvio.open(ARGV[0]) do |ds|

  # Select a1-a2 baseline
  ds.select('antennae', true, a1, a2)

  # Set the line
  ds.set('data','channel',nchan,schan,1,1)

  # Initialze plot
  init_plot(pgplot_device, nx, ny)

  vis = ds.read(vis)
  first = [ds.basant, (ds.polstr || '--')]
  ds.rewind
  i = -1

  while vis = ds.read(vis)

    blkey = [ds.basant, (ds.polstr || '--')]

    if blkey == first
      i += 1
      break if i >= nints
    end

    # Add the visdata to data
    data[blkey][true,i] = vis.data
  end
  
  numpan = nx * ny
  pan = 0
  data.keys.sort.each do |blkey|
    case blkey[1]
    when 'XX': mod = 0
    when 'XY': mod = 1
    when 'YX': mod = 2
    when 'YY': mod = 3
    end

    # Advance until (pan - 1) % 4 = (mod - 1) % 4
    while (pan - 1) % 4 != (mod - 1) % 4
      pgpage
      pan = (pan + 1) % numpan
    end
    plot_data(channels, data[blkey], "%s %d-%d %s (N=%d)" %
              [File.basename(dsname), blkey, nints].flatten)
    pan = (pan + 1) % numpan
  end
end
