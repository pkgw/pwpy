#
# $Id$
#

require 'rbconfig'
require 'dl'
require 'narray'

# Require the mirdl shared library
mirdl_shared_lib = 'mirdl.' + Config::CONFIG['DLEXT']
require mirdl_shared_lib
require 'mirdl_gem' if false # Fake out RDoc

module Mirdl

  # Use miriad libraries from MIRLIB if it is set in the environment.
  # If it is not set, libraries from LD_LIBRARY_PATH (etc) will be used.
  MIRLIB = ENV['MIRLIB'].dup
  MIRLIB << "/" if !MIRLIB.empty? && MIRLIB !~ %r{/$}
  MIRLIB.freeze

  # On MacOSX, dynamic libraries can have .bundle or .dylib extensions.
  # Miriad libs are ".dylib", Ruby's libs could be ".bundle".
  DLEXT = case RUBY_PLATFORM
          when /darwin/: 'dylib'.freeze
          else Config::CONFIG['DLEXT'].freeze
          end

  def dlopen(lib)
    DL.dlopen("#{MIRLIB}lib#{lib}.#{DLEXT}")
  end
  module_function :dlopen

  LIBMIR = dlopen("mir")
  LIBMIR_UVIO = dlopen("mir_uvio")
  undef dlopen

  SYM = {}

  MAXSTRING = 4096

  # Map bug severity to string
  BUGSEV = {
    'i' => 'Informational', 'I' => 'Informational',
    'w' => 'Warning',       'W' => 'Warning',
    'e' => 'Error',         'E' => 'Error',
    'f' => 'Fatal',         'F' => 'Fatal'
  }

  # Bug severity codes
  BUGSEV_INFO  = 'i'
  BUGSEV_WARN  = 'w'
  BUGSEV_ERROR = 'e'
  BUGSEV_FATAL = 'f'

  # hio typecodes
  H_BYTE  = 1
  H_INT   = 2
  H_INT2  = 3
  H_REAL  = 4
  H_DBLE  = 5
  H_TXT   = 6
  H_CMPLX = 7

  # POLMAP is a hash that can be used to map polarization codes to strings and
  # strings (or symbols) to codes.  Code to string always returns uppercase.
  # String (or symbol) to code accepts string (or symbol) in all uppercase or
  # all lowercase (NO mixed case).
  POLMAP = {
    +1 => 'I',
    +2 => 'Q',
    +3 => 'U',
    +4 => 'V',
    -1 => 'RR',
    -2 => 'LL',
    -3 => 'RL',
    -4 => 'LR',
    -5 => 'XX',
    -6 => 'YY',
    -7 => 'XY',
    -8 => 'YX',
  }
  POLMAP.merge!(POLMAP.invert)
  POLMAP.keys.grep(/[A-Z]/).each do |k|
    POLMAP[k.to_sym] = POLMAP[k]
    POLMAP[k.downcase] = POLMAP[k]
    POLMAP[k.downcase.to_sym] = POLMAP[k]
  end
end

require 'mirdl/version'
require 'mirdl/basant'
require 'mirdl/ephem'
require 'mirdl/key'
require 'mirdl/select_na'
require 'mirdl/maskio_na'
require 'mirdl/uvio_na'
require 'mirdl/uvdat_na'
require 'mirdl/gains'
require 'mirdl/bandpass'
require 'mirdl/astroutil'
require 'mirdl/task'
