#
# $Id$
#

# Functions from maskio.c

require 'ostruct'
require 'dl'
require 'narray'

module Mirdl

  MK_FLAGS = 1
  MK_RUNS  = 2

  # char *mkopen_c(int tno,char *name,char *status)
  SYM[:mkopen] = LIBMIR_UVIO['mkopen_c', 'pISS']
  def mkopen(tno, name, status='old')
    status = status.to_s
    status = case status
             when 'a', 'w+': 'append'
             when 'r': 'old'
             when 'w': 'new'
             else status
             end
    r, rs = SYM[:mkopen][tno, name, status]
    r.free = nil
    r
  end
  module_function :mkopen

  # void mkclose_c(char *handle)
  SYM[:mkclose] = LIBMIR_UVIO['mkclose_c', '0p']
  def mkclose(handle)
    SYM[:mkclose][handle]
  end
  module_function :mkclose

  # int mkread_c(char *handle,int mode,int *flags,int offset,int n,int nsize)
  SYM[:mkread] = LIBMIR_UVIO['mkread_c', 'IpIpIII']
  def mkread(handle, mode, flags_na, offset, n, nsize=nil)
    nsize ||= flags_na.length
    ptr = DL::PtrData.new(flags_na.ptr, flags_na.bsize)
    r, rs = SYM[:mkread][handle, mode, ptr, offset, n, nsize]
    # Translate runs from 1-based indexing to 0-based indexing
    flags_na[0...r] -= 1 if mode == MK_RUNS
    r
  end
  module_function :mkread

  # void mkwrite_c(char *handle,int mode,int *flags,int offset,int n,int nsize)
  SYM[:mkwrite] = LIBMIR_UVIO['mkwrite_c', '0pIpIII']
  def mkwrite(handle, mode, flags_na, offset, n, nsize=nil)
    nsize ||= flags_na.length
    # Translate runs from 0-based indexing to 1-based indexing
    flags_na += 1 if mode == MK_RUNS
    ptr = DL::PtrData.new(flags_na.ptr, flags_na.bsize)
    SYM[:mkwrite][handle, mode, ptr, offset, n, flags_na.length]
    # Translate runs back from 1-based indexing to 0-based indexing
    flags_na -= 1 if mode == MK_RUNS
  end
  module_function :mkwrite

  # void mkflush_c(char *handle)
  SYM[:mkflush] = LIBMIR_UVIO['mkflush_c', '0p']
  def mkflush(handle)
    SYM[:flush][handle]
  end
  module_function :mkflush

end
