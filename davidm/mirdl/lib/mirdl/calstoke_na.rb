#
# calstoke_na.rb
#
# Suboutines and functions from calstoke.for

require 'dl'
require 'narray'

module Mirdl

  # void calstoke(const char *source, const char *stokes, double *freq, double *flux, int nchan, int ierr)
  SYM[:calstoke] = LIBMIR['calstoke_', '0SSSpii'+'II']
  def calstoke(source, stokes, freq)
    source = source.to_s; source.upcase!
    stokes = stokes.to_s; stokes.downcase!
    ## Make sure we pass an NArray
    #freq_p = (NArray === freq) ? freq : NArray.to_na(freq)
    #freq_p = freq_na.to_type(NArray::FLOAT) unless freq_na.typecode == NArray::FLOAT
    ## Create flux if not passed in
    #flux_na = (NArray === flux) ? flux : NArray.float(freq.length)
    #flux_na = flux_na.to_type(NArray::FLOAT) unless flux_na.typecode == NArray::FLOAT
    # Create pointers
    nchan = freq.length
    if NArray === freq
      if freq.typecode == NArray::FLOAT
        freq_p = freq.to_s
      else
        freq_p = freq.to_type(NArray::FLOAT).to_s
      end
    else
      freq_p = NArray === freq ? freq.to_s : freq.pack('D*')
    end
    flux_p = DL.malloc(nchan * DL.sizeof('F'))
    ierr = 2
    r, rs = SYM[:calstoke][source, stokes, freq_p, flux_p, nchan, ierr, source.length, stokes.length]
    ierr = rs[5]
    raise 'No match found' unless (0..1) === ierr
    if ierr == 1
      warn("extrapolation performed for some of %s %s [%.3g to %.3g]" %
           [source, stokes.upcase, freq.min, freq.max])
    end
    NArray.to_na(rs[3].to_s(flux_p.size),NArray::SFLOAT)
  end
  module_function :calstoke

end
