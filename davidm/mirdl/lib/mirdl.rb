require 'rbconfig'

# Require the mirdl shared library
mirdl_shared_lib = 'mirdl.' + Config::CONFIG['DLEXT']
require mirdl_shared_lib
require 'mirdl_gem' if false # Fake out RDoc

module Mirdl

  # Use miriad libraries from MIRLIB if it is set int he environment.
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
end

require 'mirdl/select_na'
require 'mirdl/uvio_na'
require 'mirdl/uvdat_na'
