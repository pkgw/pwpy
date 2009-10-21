#
# $Id$
#

# extconf.rb : Configure script for rb_tle
#
#   Copyright (c) 2009 David MacMahon <davidm@astro.berkeley.edu>
#
#   This program is free software.
#   You can distribute/modify this program
#   under the same terms as Ruby itself.
#   NO WARRANTY.
#
# usage: ruby extconf.rb [configure options]

require "mkmf"

$CFLAGS += ' -fno-builtin' if Config::CONFIG['CC'] = 'gcc'
have_func('asinh')
$CFLAGS.sub!(/ -fno-builtin$/,'') if Config::CONFIG['CC'] = 'gcc'

# Generate Makefile
create_makefile("tle_ext")
