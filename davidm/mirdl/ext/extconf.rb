#
# $Id$
#

# extconf.rb : Configure script for mirdl
#
#   Copyright (c) 2009 David MacMahon <davidm@astro.berkeley.edu>
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

# This is an attempt to work around an incompatibility between Mac gcc
# CFLAGS/LDFLAGS and MacPorts gcc CFLAGS/LDFLAGS.
$CFLAGS.gsub!(/(^|\s+)-arch\s+\w+/,'')
$LDFLAGS.gsub!(/(^|\s+)-arch\s+\w+/,'')

# Check NArray
na_gemspec=Gem.searcher.find('narray')
if na_gemspec
  na_dir=File.join(na_gemspec.full_gem_path, na_gemspec.require_path)
  $CPPFLAGS = " -I#{na_dir} "+$CPPFLAGS
else
  $CPPFLAGS = " -I#{CONFIG['sitearchdir']} -I#{CONFIG['archdir']} " + $CPPFLAGS
end
exit unless have_header("narray.h")
if RUBY_PLATFORM =~ /cygwin|mingw/
  $LDFLAGS = " -L#{CONFIG['sitearchdir']} "+$LDFLAGS
  exit unless have_library("narray","na_make_object")
end

# Check miriad.h
dir_config('miriad')

d = ENV['MIRINC']
$CPPFLAGS << " -I#{d} " if test ?d, d
d += '/../miriad-c'
$CPPFLAGS << " -I#{d} " if test ?d, d
exit unless have_header("miriad.h")

# Check mir_uvio library
d = ENV['MIRLIB']
$LDFLAGS << " -L#{d} " if test ?d, d
exit unless have_library('mir_uvio', 'bug_c')

# Check for new MIRIAD bug handler function
have_func('bughandler_c', 'miriad.h')

# Check mir library (also requires mir_linpack and pgplot libraries)
exit unless have_library('mir_linpack', 'sdot_')
exit unless have_library('pgplot', 'pgpt_')
exit unless have_library('mir', 'options_')

# Generate Makefile
create_makefile("mirdl")
