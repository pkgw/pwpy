#!/usr/bin/env ruby

# $Id$
#
# Beginnings of a uvwlint effort.  Checks baseline projections.

require 'miriad'

raise "usage: #{File.basename($0)} DATASET [A1 [A2 [COUNT]]]" if ARGV.empty?

dsname = ARGV[0]
antsel1 = Integer(ARGV[1]||0) rescue 0
antsel2 = Integer(ARGV[2]||0) rescue 0
count = Integer(ARGV[3]||1) rescue 1

Miriad::Uvio.open(dsname) do |ds|
  ds.select('antennae', true, antsel1, antsel2)
  ds.select('polarization', true, Miriad::POLMAP['xx'])
  ds.select('auto',false) if antsel1 == 0 || antsel2 == 0
  count.times do
    vis = ds.read(vis)
    raise "No baselines found" if vis.nil?
    a1, a2 = ds.basant
    a1xyz, a2xyz = ds.antpos(a1, a2, :coord => :xyz, :units => :ns)
    bl = ds.baseline(:coord => :xyz, :units => :ns)
    obsra = ds[:obsra]
    obsdec = ds[:obsdec]
    lst = ds[:lst]
    azel = ds.azel
    uvw_calc = Miriad.xyz2uvw(a1xyz, a2xyz, obsra, obsdec, lst)
    uvw_vis = vis.coord
    ut = DateTime.ajd((vis.jd * 86400 * 1000).round / 1000.0)
    puts "UT is #{(24*((vis.jd+0.5)%1)).to_hmsstr}"
    puts "ant #{a1} x,y,z position is [%.3f, %.3f, %.3f] (ns)" % a1xyz
    puts "ant #{a2} x,y,z position is [%.3f, %.3f, %.3f] (ns)" % a2xyz
    puts "x,y,z baseline is [%.3f, %.3f, %.3f] (ns)" % bl
    puts "obsra is #{obsra.r2h.to_hmsstr} (hh:mm:ss.sss)"
    puts "obsdec is #{obsdec.d2h.to_hmsstr} (dd:mm:ss.sss)"
    puts "lst is #{lst.r2h} (hours)"
    puts "calculated az,el is [%.3f, %.3f] (degrees)" % azel.map {|r| r.r2d}
    puts "calculated u,v,w is [%.3f, %.3f, %.3f] (ns)" % uvw_calc
    puts "visibility u,v,w is [%.3f, %.3f, %.3f] (ns)" % uvw_vis
    if ds[:ra] == obsra && ds[:dec] == obsdec
      puts "WARNING: ra == obsra and dec == obsdec"
      puts "precessing ra/dec and recalculating azel and uvw"
      obsra, obsdec = Miriad.precess(obsra, obsdec, vis.jd)
      azel = Miriad.azel(obsra, obsdec, lst, ds[:latitud])
      uvw_calc = Miriad.xyz2uvw(a1xyz, a2xyz, obsra, obsdec, lst)
      puts "obsra is #{obsra.r2h.to_hmsstr} (hh:mm:ss.sss)"
      puts "obsdec is #{obsdec.d2h.to_hmsstr} (dd:mm:ss.sss)"
      puts "calculated az,el is [%.3f, %.3f] (degrees)" % azel.map {|r| r.r2d}
      puts "calculated u,v,w is [%.3f, %.3f, %.3f] (ns)" % uvw_calc
      puts "visibility u,v,w is [%.3f, %.3f, %.3f] (ns)" % uvw_vis
    end
    puts
  end
end
