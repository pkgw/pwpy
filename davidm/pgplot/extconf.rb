# extconf.rb : Configure script for Ruby/PGPLOT
#
#   Copyright (c) 2000,2001 Masahiro TANAKA <masa@ir.isas.ac.jp>
#
#   This program is free software.
#   You can distribute/modify this program
#   under the same terms as Ruby itself.
#   NO WARRANTY.
#
# usage: ruby extconf.rb [configure options]

# Narray is now Gem based, so require rubygems
# so that we can use Gem to find narray.
require 'rubygems'
require "mkmf"

#$DEBUG = true

# configure options:
#  --with-x11-dir=path
#  --with-x11-include=path
#  --with-x11-lib=path
dir_config("x11")

# configure options:
#  --with-pgplot-dir=path
#  --with-pgplot-include=path
#  --with-pgplot-lib=path
dir_config("pgplot")

# Otherwise you can also specify:
#  --with-opt-dir=path
#  --with-opt-include=path
#  --with-opt-lib=path

# Check PGPLOT Header
exit unless have_header("cpgplot.h")

# Check NArray
na_gemspec=Gem.searcher.find('narray')
na_dir=File.join(na_gemspec.full_gem_path, na_gemspec.require_path)
$CPPFLAGS = " -I#{na_dir} "+$CPPFLAGS
exit unless have_header("narray.h")
if RUBY_PLATFORM =~ /cygwin|mingw/
  $LDFLAGS = " -L#{CONFIG['sitearchdir']} "+$LDFLAGS
  exit unless have_library("narray","na_make_object")
end

# Check FORTRAN Libraries
#
# SUN WorkShop FORTRAN 77 compiler ver5.0
# configure options: --with-sunws
if with_config("sunws")
  $libs = "-lM77 -lsunmath "+$libs
  exit unless find_library("F77", "f77_init", "/opt/SUNWspro/lib")
  $defs.push "-DSPARC_FORTRAN"
#
# GNU FORTRAN v4
elsif have_library("gfortran")
  $CFLAGS = "-Wall "+$CFLAGS
  $defs.push "-DGNU_FORTRAN"
#
# GNU FORTRAN v3
elsif have_library("g77")
  $CFLAGS = "-Wall "+$CFLAGS
  $defs.push "-DGNU_FORTRAN"
# G2C
elsif have_library("g2c", "G77_getenv_0")
  $CFLAGS = "-Wall "+$CFLAGS
  $defs.push "-DGNU_FORTRAN"
else
  puts "failed"
  exit
end

# Check GrWin Library (for cygwin (and mingw32?))
#  configure options: --with-grwin
if with_config("grwin")
  #$LDFLAGS = "-Wl,--subsystem,console "+$LDFLAGS
  if RUBY_PLATFORM =~ /cygwin|mingw/
    $libs += " -mwindows"
  end
  exit unless have_library("GrWin", "GWinit")
end
#
# Check X11 Library
have_library("X11", "XOpenDisplay")

# Check PNG Library
libs_save = $libs
$libs = append_library($libs, "z")
if !have_library("png","png_create_write_struct")
  $libs = libs_save
end

# Check PGPLOT Library
$libs = append_library($libs, "pgplot")
exit unless find_library( "cpgplot", "cpgbeg", "/usr/lib", 
			  "/usr/local/lib", "/usr/local/pgplot" )

$objs = %w(rb_pgplot.o kwarg.o)

# Generate Makefile
create_makefile("pgplot")
