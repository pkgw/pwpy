# naptr.rb : naptr loader
#
#   Copyright (c) 2009 David MacMahon <davidm@astro.berkeley.edu>
#
#   This program is free software.
#   You can distribute/modify this program
#   under the same terms as Ruby itself.
#   NO WARRANTY.

require 'rbconfig'
require 'rubygems'
require 'narray'
naptr_shared_lib = 'naptr.' + Config::CONFIG['DLEXT']
require naptr_shared_lib
require 'naptr_gem' if false # Fake out RDoc

class NArray
  def byte_size
    self.element_size * self.total
  end
  alias :bsize :byte_size
end
