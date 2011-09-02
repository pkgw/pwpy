#!/usr/bin/env ruby

require 'date'
require 'narray'
require 'pgplot'; include Pgplot

BACK, FORE, RED, GREEN, BLUE, CYAN, MAGENTA, YELLOW, ORANGE, GREEN_YELLOW,
GREEN_CYAN, BLUE_CYAN, BLUE_MAGENTA, RED_MAGENTA, DARK_GRAY, LIGHT_GRAY = (0..15).to_a

# Columns in loop file are:
# 
#   MJD
#   seconds.fract (since midnight UTC)
#   time offset (seconds)
#   frequency offset (PPM)
#   RMS jitter (seconds)
#   Allan deviation (PPM)
#   Clock discipline time constant (log2(polling interval in seconds))
#
# This script assumes that all records in a file have the same MJD and that
# the records appear in chronological order.

opt_plot = true
pgplot_device = ENV['PGPLOT_DEV'] || '/xs'

while ARGV[0] && ARGV[0][0] == ?- do
    case ARGV[0][1]
        when ?d : pgplot_device = ARGV[1]; ARGV.shift
        else
            printf STDERR, "Unrecongized option #{ARGV[0]}\n"
            #printf STDERR, "#{usage}\n"
            exit 1
    end
    ARGV.shift
end

opt_plot = false if %r{/null$}i =~ pgplot_device

loop_file = ARGV[0] || '/var/log/ntpstats/loops'

loops_a=File.new(loop_file).readlines.map do |l|
  l.split.map {|n| n.to_f}
end

# Loops will be a two dimensional NArray indexed as [col,row],
# where col and row describe the elements location in the loop_file.
loops = NArray.to_na(loops_a)

mjd    = loops[0,true]
secs   = loops[1,true]
offset = loops[2,true] * 1e3 # Convert to millisecs
froff  = loops[3,true]
jitter = loops[4,true] * 1e3 # Convert to millisecs
allan  = loops[5,true]
poll   = 2 ** loops[6,true]

#xx = secs
xx = (mjd-mjd[0])*86400+secs
yy = offset
yymin = yy.min
yymax = yy.max

text = "%s: min=%.3f mean=%.3f max=%.3f std=%.3f" %
  ['Time offset (ms)', yymin, yy.mean, yymax, yy.stddev]

if /\.\d+.*\d*$/.match(loop_file)
  # Calculate x range based on greater of full 24 hours and timestamp range
  xxmin = [0, xx[0]].min
  xxmax = [24*60*60, xx[-1]].max
else
  # Calculate x range based on even hours
  xxmin = 3600 * (secs[0]/3600).to_i
  xxmax = 3600 * ((secs[-1]+3599)/3600).to_i
end

# Recalculate y range based on jitter error bars
yymin = (offset-jitter).min
yymax = (offset+jitter).max
yymid = (yymax + yymin) / 2
yyrng = 1.1 * (yymax - yymin) / 2
yymin = yymid - yyrng
yymax = yymid + yyrng

date = Date.jd(Date.mjd_to_jd(mjd[0]))
title="NTP Loop Statistics from #{loop_file}"

raise "error opening device #{pgplot_device}" if pgopen(pgplot_device) < 0
# Plot black on white, and darken green
pgscr(FORE,0,0,0)
pgscr(BACK,1,1,1)
pgscr(GREEN,0,0.7,0)
pgask(false)
pgenv(xxmin, xxmax, yymin, yymax, 0, -1)
# Draw box and label X axis
pgtbox('ABHNSTZ',0,0,'',0,0) # Was ABHNSTXYZ, but removed XY
pglab("#{date} UTC", '', title)
pgmtxt('T',0.5,0.5,0.5,text)

# Only do detailed plots (i.e. error bars and points) if we have fewer than
# 1000 points.
detailed = (xx.length < 1000)

# Draw time offset Y axis and plot it in blue
pgsci(BLUE)
# Draw y axis on left for time offset
pgaxis(xxmin,yymin,xxmin,yymax,yymin,yymax,:opt=>'N',#:step=>0,
       :tickl=>0,:tickr=>0.5,:frac=>0.5,
       :disp=>-0.5,:orient=>0)
# Label magnitude axis
ylabel = 'Time Offset (ms)'
ylabel += ' \(2233) RMS Jitter (ms)' if detailed
pgmtxt('L',2.2,0.5,0.5,ylabel)
pgline(xx, yy)
if detailed
  pgpt(xx, yy, 21)
  pgerry(xx,offset+jitter,offset-jitter)
end

# Setup to plot frequency offset
yy = froff
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
pgmtxt('R',2.7,0.5,0.5,'Freq Offset (PPM)')
# Plot line points
pgline(xx, yy)
# Plot line points
pgpt(xx, yy, 3) if detailed
