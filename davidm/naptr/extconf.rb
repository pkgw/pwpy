# extconf.rb : Configure script for naptr
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

# Generate Makefile
create_makefile("naptr")
