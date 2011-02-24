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

# Check GrWin Library (for cygwin (and mingw32?))
#  configure options: --with-grwin
if with_config("grwin")
  #$LDFLAGS = "-Wl,--subsystem,console "+$LDFLAGS
  if RUBY_PLATFORM =~ /cygwin|mingw/
    $libs += " -mwindows"
  end
  exit unless have_library("GrWin", "GWinit")
end

# Check PGPLOT Library
$libs = append_library($libs, "pgplot")
exit unless find_library( "cpgplot", "cpgbeg", "/usr/lib", 
			  "/usr/local/lib", "/usr/local/pgplot" )

$objs = %w(rb_pgplot.o kwarg.o)

# Generate Makefile
create_makefile("pgplot")
