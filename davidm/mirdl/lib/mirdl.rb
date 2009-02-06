require 'rbconfig'
require 'dl'

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
end

require 'mirdl/bug'
require 'mirdl/key'
require 'mirdl/options'
require 'mirdl/select_na'
require 'mirdl/uvio_na'
require 'mirdl/uvdat_na'
