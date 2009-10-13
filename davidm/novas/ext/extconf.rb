require 'mkmf'
require 'fileutils'
include FileUtils

novas_dir = 'novas-c201'

novas_files = %w{
  novas.c
  novas.h
  novascon.c
  novascon.h
  readeph0.c
  solarsystem.h
  solsys3.c
}

novas_files.each {|f| cp("#{novas_dir}/#{f}",'.',:preserve => true)}

create_makefile('novas_ext')
