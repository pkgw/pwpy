# Subroutines and functions from select.for

require 'dl'
require 'narray'
require 'naptr' unless NArray.method_defined? :ptr

module Mirdl

  class Sels
    def initialize(maxsels=100)
      @sels = NArray.sfloat(maxsels)
    end

    def length
      @sels.length
    end

    def to_p
      DL::PtrData.new(@sels.ptr, @sels.bsize)
    end
  end

  # void SelInput(cost char *key, float * sels, int maxsels)
  SYM[:SelInput] = LIBMIR['selinput_', '0Spi'+'I']
  def selInput(sels, key='select')
    key = key.to_s
    SYM[:SelInput][key, sels.to_p, sels.length, key.length]
  end
  module_function :selInput

  # int SelProbe(float * sels, char * object, double * value)
  SYM[:SelProbe] = LIBMIR['selprobe_', 'IpSd'+'I']
  def selProbe(sels, object, value=0.0)
    object = object.to_s
    r, rs = SYM[:SelProbe][sels.to_p, object, value.to_f, object.length]
    r != 0
  end
  module_function :selProbe

  # void SelApply(int tno, float * sels, int select)
  SYM[:SelApply] = LIBMIR['selapply_', '0ipi']
  def selApply(tno, sels, select=true)
    SYM[:SelApply][tno, sels.to_p, select ? 1 : 0]
  end
  module_function :selApply

end
