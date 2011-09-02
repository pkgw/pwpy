#!/usr/bin/env ruby

require 'date'
require 'narray'
require 'pgplot'; include Pgplot
require 'socket'

BACK, FORE, RED, GREEN, BLUE, CYAN, MAGENTA, YELLOW, ORANGE, GREEN_YELLOW,
GREEN_CYAN, BLUE_CYAN, BLUE_MAGENTA, RED_MAGENTA, DARK_GRAY, LIGHT_GRAY = (0..15).to_a

## Default nx and ny values
#N    0 1 2 3 4 5 6 7 8 9 10
NX = [1,1,1,2,2,2,2,3,3,3,3]
NY = [1,1,2,2,2,3,3,3,3,3,4]

# Columns in peer file are:
# 
#   MJD
#   seconds.fract (since midnight UTC)
#   peer IP
#   peer status (4 digit hex)
#   time offset (seconds)
#   delay (seconds)
#   dispersion (seconds)
#   RMS jitter (seconds)
#
# This script assumes that all records in a file have the same MJD and that
# the records appear in chronological order.
#
# Every column except the peer_ip column ends up as a column in a 2-dimensional
# NArray.  The hash defined here maps symbols (i.e. names) to column index in
# an attempt to make the code more readable.

COL = {
  :mjd    => 0,
  :secs   => 1,
  :status => 2,
  :offset => 3,
  :delay  => 4,
  :disp   => 5,
  :jitter => 6
}

# Symbols to use for the eight possible "peer selection" status values
STATUS_SYMBOL = [
  17, # reject (solid square)
  -3, # falsetick (solid triangle)
  16, # excess (solid dot)
   0, # outlyer (square)
  11, # candidate (diamond)
  12, # selected (star)
   4, # sys.peer (circle)
   8  # pps.peer (circle with plus)
]

nxy="0,0"
opt_plot = true
pgplot_device = ENV['PGPLOT_DEV'] || '/xs'

while ARGV[0] && ARGV[0][0] == ?- do
    case ARGV[0][1]
        when ?d : pgplot_device = ARGV[1]; ARGV.shift
        when ?n : nxy = ARGV[1]; ARGV.shift
        else
            printf STDERR, "Unrecongized option #{ARGV[0]}\n"
            #printf STDERR, "#{usage}\n"
            exit 1
    end
    ARGV.shift
end

nx, ny, junk = nxy.split(',',3).map {|s| s.to_i}
opt_plot = false if %r{/null$}i =~ pgplot_device

peer_file = ARGV[0] || '/var/log/ntpstats/peers'

min_secs = nil
max_secs = nil
peers = {}
File.new(peer_file).readlines.each do |l|
  w = l.split
  peer_ip = w.slice!(2,1)[0]    # Slice out the peer_ip column
  max_secs = w[COL[:secs]].to_f # Assume secs are monotonically increasing
  min_secs ||= max_secs         # Assume first secs value is minimum
  w[COL[:status]] = w[COL[:status]].to_i(16)
  peers[peer_ip] ||= []
  peers[peer_ip].push(w.map {|s| s.to_f})
end

num_peers = peers.length
raise "{peer_file} seems empty" if num_peers == 0
raise "Too many peers (#{num_peers})" if num_peers > 10

nx = NX[num_peers] if nx == 0
ny = NY[num_peers] if ny == 0

if /\.\d+$/.match(peer_file)
  # Calculate x range based on full 24 hours
  xxmin = 0
  xxmax = 24*60*60
else
  # Calculate x range based on even hours
  xxmin = 3600 * (min_secs/3600).to_i
  xxmax = 3600 * ((max_secs+3599)/3600).to_i
end

raise "error opening device #{pgplot_device}" if pgopen(pgplot_device) < 0
pgsubp(nx, ny)
# Plot black on white, and darken green
pgscr(FORE,0,0,0)
pgscr(BACK,1,1,1)
pgscr(GREEN,0,0.7,0)

peers_name2ip = {}
peers.each_key do |peer_ip|
  begin
    peer_name = Socket.getaddrinfo(peer_ip,nil)[0][2]
    peers_name2ip[peer_name] = peer_ip
  rescue
    peers_name2ip[peer_ip] = peer_ip
  end
end

peers_name2ip.keys.sort.each do |peer_name|

  peer_ip = peers_name2ip[peer_name]

  # peer will be a two dimensional NArray indexed as [col,row], where col and
  # row describe the elements per-peer location in the loop_file, excluding the
  # peer_ip column.
  peer = NArray.to_na(peers[peer_ip])

  mjd    = peer[COL[:mjd],0]
  xx  = peer[COL[:secs  ],true]
  yy  = peer[COL[:offset],true] * 1e3 # Convert to ms
  dy1 = peer[COL[:disp  ],true] * 1e3 # Convert to ms
  dy2 = peer[COL[:jitter],true] * 1e3 # Convert to ms

  dymax = [dy1.max, dy2.max].max
  yymin = yy.min
  yymax = yy.max

  text = "Peer: #{peer_name}"

  # Recalculate y range based on max error bars
  yymin -= dymax
  yymax += dymax
  yymid = (yymax + yymin) / 2
  yyrng = 1.1 * (yymax - yymin) / 2
  yymin = yymid - yyrng
  yymax = yymid + yyrng

  date = Date.jd(Date.mjd_to_jd(mjd))
  title="NTP Peer Statistics from #{peer_file}"

  pgenv(xxmin, xxmax, yymin, yymax, 0, -1)
  # Box and x axis are in foreground color
  pgsci(FORE)
  # Draw box and label X axis
  pgtbox('ABHNSTXYZ',0,0,'',0,0)
  pglab("#{date} UTC", '', title)
  pgmtxt('T',0.5,0.5,0.5,text)

  # Draw time offset Y axis and plot it in blue
  pgsci(BLUE)
  # Draw y axis on left for time offset
  pgaxis(xxmin,yymin,xxmin,yymax,yymin,yymax,:opt=>'N',#:step=>0,
         :tickl=>0,:tickr=>0.5,:frac=>0.5,
         :disp=>-0.5,:orient=>0)
  # Label magnitude axis
  pgmtxt('L',2.2,0.5,0.5,'Time Offset (ms) \(2233) RMS Jitter (dotted), \(2233) Dispersion (dashed)')
  pgline(xx, yy)
  pgsls(2) # Dashed
  #pgerry(xx,yy+dy1,yy-dy1)
  pgline(xx,yy+dy1)
  pgline(xx,yy-dy1)
  pgsls(4) # Dotted
  #pgerry(xx,yy+dy2,yy-dy2)
  pgline(xx,yy+dy2)
  pgline(xx,yy-dy2)
  pgsls(1) # Full

  # Setup to plot delay
  status = (peer[COL[:status],true].to_i & 0x700) / 256
  yy = peer[COL[:delay],true] * 1e3 # Convert to ms
  yymin = yy.min
  yymax = yy.max
  yymid = (yymax + yymin) / 2
  yyrng = 1.1 * (yymax - yymin) / 2
  yymin = yymid - yyrng
  yymax = yymid + yyrng

  # Freq offset is green
  pgsci(GREEN)
  # Change window's world coordinates
  pgswin(xxmin,xxmax,yymin,yymax)
  # Draw y axis on right for phase
  pgaxis(xxmax,yymin,xxmax,yymax,yymin,yymax,:opt=>'N',
         :tickl=>0.5,:tickr=>0,:frac=>0.5,
         :disp=>0.3,:orient=>0)
         #:step=>45,:nsub=>3,
  # Label phase axis
  pgmtxt('R',2.7,0.5,0.5,'Delay (ms)')
  # Plot line points
  pgline(xx, yy)
  # Plot points using symbols to reflect "peer selection" status
  prev_symbol = nil
  xx.total.times do |i|
    x = xx[i]
    y = yy[i]
    symbol = STATUS_SYMBOL[status[i]] || -4 # Solid diamond means invalid "peer selection" status
    pgsch(3) if symbol != prev_symbol
    pgpt1(x, y, symbol)
    prev_symbol = symbol
    pgsch(1)
  end
end
