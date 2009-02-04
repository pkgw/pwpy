# TODO Detect and adapt to FORTRAN calling conventions of loaded libraries.
# (Currently developed for gfortran)

# Routines from options.for

module Mirdl

  # void Options(const char *key, const char *opts[nopt], int present[nopts], int *nopt)
  SYM[:options] = LIBMIR['options_', '0SSpi'+'II']
  def options(opts, key='options')
    # Find max option length (opts is Array of Strings and/or Symbols)
    maxoptlen = opts.max{|a,b| a.to_s.length <=> b.to_s.length}.to_s.length
    # Pad opts out to max length and join into one long string
    optary = opts.map{|o| o.to_s.ljust(maxoptlen)}.join
    # Create buffer for present flags
    psize = opts.length*DL.sizeof('I')
    present = DL.malloc(psize)
    r, rs = SYM[:options][key, optary, present, opts.length, key.length, maxoptlen]
    flags = rs[2].to_s(psize).unpack('I*')
    h = {}
    opts.each_index {|i| h[opts[i].to_sym] = (flags[i] != 0)}
    h
  end
  module_function :options

end
