require 'narray'
require 'naptr' #unless NArray.method_defined? :ptr

# TODO Detect and adapt to FORTRAN calling conventions of loaded libraries.
# (Currently developed for gfortran)

# Routines from select.for

module Mirdl

  # void SelInput(cost char *key, float * sels, int maxsels)
  SYM[:SelInput] = LIBMIR['selinput_', '0Spi'+'I']
  def selInput(sels, key='select')
    key = key.to_s
    sels_p = DL::PtrData.new(sels.ptr, sels.bsize)
    SYM[:SelInput][key, sels_p, sels.length, key.length]
  end
  module_function :selInput

  # int SelProbe(float * sels, char * object, double * value)
  SYM[:SelProbe] = LIBMIR['selprobe_', 'IpSd'+'I']
  def selProbe(sels, object, value=0.0)
    object = object.to_s
    sels_p = DL::PtrData.new(sels.ptr, sels.bsize)
    r, rs = SYM[:SelProbe][sels_p, object, value.to_f, object.length]
    r != 0
  end
  module_function :selProbe

  # void SelApply(int tno, float * sels, int select)
  SYM[:SelApply] = LIBMIR['selapply_', '0ipi']
  def selApply(tno, sels, select=true)
    sels_p = DL::PtrData.new(sels.ptr, sels.bsize)
    SYM[:SelApply][tno, sels_p, select ? 1 : 0]
  end
  module_function :selApply

end
