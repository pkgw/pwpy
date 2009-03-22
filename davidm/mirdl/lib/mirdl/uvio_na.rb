#
# $Id$
#

# Functions from uvio.c

require 'ostruct'
require 'dl'
require 'narray'

module Mirdl

  class Vis < OpenStruct
    def initialize(nchan)
      super(
        :preamble => NArray.float(5),
        :data => NArray.scomplex(nchan),
        :flags => NArray.int(nchan),
        :nread => 0,
        :nchan => nchan
      )
      self.preamble_p = DL::PtrData.new(preamble.ptr, preamble.bsize)
      self.data_p = DL::PtrData.new(data.ptr, data.bsize)
      self.flags_p = DL::PtrData.new(flags.ptr, flags.bsize)
    end

    private
    def preamble=; end
    def data=; end
    def flags=; end
  end

  # void uvopen_c (int *tno, Const char *name, Const char *status);
  SYM[:uvopen] = LIBMIR_UVIO['uvopen_c', '0iSS']
  def uvopen(name, status='old')
    status = status.to_s
    status = case status
             when 'a', 'w+': 'append'
             when 'r': 'old'
             when 'w': 'new'
             else status
             end
    r, rs = SYM[:uvopen][0, name, status]
    tno = rs[0]
    if status == 'old'
      # Read in first "frame" of uv variables
      uvnext(tno)
      uvrewind(tno)
    end
    tno
  end
  module_function :uvopen

  # void uvclose_c (int tno);
  SYM[:uvclose] = LIBMIR_UVIO['uvclose_c', '0I']
  def uvclose(tno)
    SYM[:uvclose][tno]
  end
  module_function :uvclose

  # void uvflush_c (int tno);
  SYM[:uvflush] = LIBMIR_UVIO['uvflush_c', '0I']
  def uvflush(tno)
    SYM[:flush][tno]
  end
  module_function :uvflush

  # void uvnext_c (int tno);
  SYM[:uvnext] = LIBMIR_UVIO['uvnext_c', '0I']
  def uvnext(tno)
    SYM[:uvnext][tno]
  end
  module_function :uvnext

  # void uvrewind_c (int tno);
  SYM[:uvrewind] = LIBMIR_UVIO['uvrewind_c', '0I']
  def uvrewind(tno)
    SYM[:uvrewind][tno]
  end
  module_function :uvrewind

  # void uvcopyvr_c (int tin, int tout);
  SYM[:uvcopyvr] = LIBMIR_UVIO['uvcopyvr_c', '0II']
  def uvcopyvr(tin, tout)
    SYM[:uvcopyvr][tin, tout]
  end
  module_function :uvcopyvr

  # int  uvupdate_c (int tno);
  SYM[:uvupdate] = LIBMIR_UVIO['uvupdate_c', 'II']
  def uvupdate(tno)
    r, rs = SYM[:uvupdate][tno]
    r != 0
  end
  module_function :uvupdate

  # void uvvarini_c (int tno, int *vhan);
  SYM[:uvvarini] = LIBMIR_UVIO['uvvarini_c', '0Ii']
  def uvvarini(tno)
    r, rs = SYM[:uvvarini][tno, 0]
    rs[1]
  end
  module_function :uvvarini

  # void uvvarset_c (int vhan, Const char *var);
  SYM[:uvvarset] = LIBMIR_UVIO['uvvarset_c', '0IS']
  def uvvarset(vhan, var)
    SYM[:uvvarset][vhan, var.to_s]
  end
  module_function :uvvarset

  # void uvvarcpy_c (int vhan, int tout);
  SYM[:uvvarcpy] = LIBMIR_UVIO['uvvarcpy_c', '0II']
  def uvvarcpy(vhan, tout)
    SYM[:uvvarcpy][vhan, tout]
  end
  module_function :uvvarcpy

  # int  uvvarupd_c (int vhan);
  SYM[:uvvarupd] = LIBMIR_UVIO['uvvarupd_c', 'II']
  def uvvarupd(vhan)
    r, rs = SYM[:uvvarupd][vhan, 0]
    rs[1] != 0
  end
  module_function :uvvarupd

  # void uvrdvr_c(int tno, int type, Const char *var, char *data, char *def, int n)
  SYM[:uvrdvr] = LIBMIR_UVIO['uvrdvr_c', '0IISppI']
  def uvrdvr(tno, type, var, defval, n=1)
    case type
    when H_BYTE, :char, 'a'
      type = H_BYTE
      data = DL.malloc(n)
      fmt = 'A*'
    when H_INT, :int, 'i'
      type = H_INT
      data = DL.malloc(n * DL.sizeof('I'))
      fmt = 'i'
    when H_INT2, :short, 'j'
      type = H_INT2
      data = DL.malloc(n * DL.sizeof('S'))
      fmt = 's'
    when H_REAL, :float, 'r'
      type = H_REAL
      data = DL.malloc(n * DL.sizeof('F'))
      fmt = 'F'
    when H_DBLE, :double, 'd'
      type = H_DBLE
      data = DL.malloc(n * DL.sizeof('D'))
      fmt = 'D'
    when H_CMPLX, :complex, 'c'
      type = H_CMPLX
      data = DL.malloc(n * 2 * DL.sizeof('F'))
      fmt = 'FF'
      defval = [defval.real, defval.imag] unless Array === defval
    else
      bug(BUGSEV_ERROR, "Type incompatiblity for variable #{var.to_s}, in UVRDVR")
    end
    defval = [defval].pack(fmt)
    r, rs = SYM[:uvrdvr][tno, type, var.to_s, data, defval, n]
    if type == H_CMPLX
      re, im = rs[3].to_s(data.size).unpack(fmt)
      Complex(re, im)
    else
      rs[3].to_s(data.size).unpack(fmt)[0]
    end
  end
  module_function :uvrdvr

  def uvrdvra(tno, var, defval='', n=MAXSTRING)
    uvrdvr(tno, H_BYTE, var, defval, n)
  end
  module_function :uvrdvra

  def uvrdvrj(tno, var, defval=0)
    uvrdvr(tno, H_INT2, var, defval)
  end
  module_function :uvrdvrj

  def uvrdvri(tno, var, defval=0)
    uvrdvr(tno, H_INT, var, defval)
  end
  module_function :uvrdvri

  def uvrdvrf(tno, var, defval=0.0)
    uvrdvr(tno, H_REAL, var, defval)
  end
  module_function :uvrdvrf

  def uvrdvrd(tno, var, defval=0.0)
    uvrdvr(tno, H_DBLE, var, defval)
  end
  module_function :uvrdvrd

  def uvrdvrc(tno, var, defval=Complex(0,0))
    uvrdvr(tno, H_CMPLX, var, defval)
  end
  module_function :uvrdvrc

  # void uvgetvr_c  (int tno, int type, Const char *var, char *data, int n);
  SYM[:uvgetvr] = LIBMIR_UVIO['uvgetvr_c', '0IISpI']
  # Returns String for type == H_BYTE,
  # otherwise NArray if n > 1,
  # otherwise a single value
  #def uvgetvr(tno, type, var, n)
  #def uvgetvr(tno, type, var, n)
  def uvgetvr(*args)
    case args.length
    when 2
      tno, var = *args
      type, n, updated = uvprobvr(tno, var)
      return nil if type.nil?
    when 4
      tno, type, var, n = *args
    else
      raise ArgumentError.new("wrong number of arguments (#{args.length} for 2 or 4)")
    end

    case type
    when H_BYTE, :char, 'a'
      type = H_BYTE
      ptr = DL.malloc(n+1)
    when H_INT, :int, 'i'
      type = H_INT
      data = NArray.int(n)
      ptr = DL::PtrData.new(data.ptr, data.bsize)
    when H_INT2, :short, 'j'
      type = H_INT2
      data = NArray.sint(n)
      ptr = DL::PtrData.new(data.ptr, data.bsize)
    when H_REAL, :float, 'r'
      type = H_REAL
      data = NArray.sfloat(n)
      ptr = DL::PtrData.new(data.ptr, data.bsize)
    when H_DBLE, :double, 'd'
      type = H_DBLE
      data = NArray.float(n)
      ptr = DL::PtrData.new(data.ptr, data.bsize)
    when H_CMPLX, :complex, 'c'
      type = H_CMPLX
      data = NArray.scomplex(n)
      ptr = DL::PtrData.new(data.ptr, data.bsize)
    else
      bug(BUGSEV_ERROR, "Type incompatiblity for variable #{var.to_s}, in UVGETVR")
    end
    r, rs = SYM[:uvgetvr][tno, type, var.to_s, ptr, n]
    if type == H_BYTE
      data = rs[3].to_s
    else
      data = data[0] if n == 1
    end
    data
  end
  module_function :uvgetvr

  def uvgetvra(tno, var, n=MAXSTRING)
    uvgetvr(tno, H_BYTE, var, n)
  end
  module_function :uvgetvra

  def uvgetvrj(tno, var, n=1)
    uvgetvr(tno, H_INT2, var, n)
  end
  module_function :uvgetvrj

  def uvgetvri(tno, var, n=1)
    uvgetvr(tno, H_INT, var, n)
  end
  module_function :uvgetvri

  def uvgetvrr(tno, var, n=1)
    uvgetvr(tno, H_REAL, var, n)
  end
  module_function :uvgetvrr

  def uvgetvrd(tno, var, n=1)
    uvgetvr(tno, H_DBLE, var, n)
  end
  module_function :uvgetvrd

  def uvgetvrc(tno, var, n=1)
    uvgetvr(tno, H_CMPLX, var, n)
  end
  module_function :uvgetvrc

  # void uvprobvr_c (int tno, Const char *var, char *type, int *length, int *updated);
  SYM[:uvprobvr] = LIBMIR_UVIO['uvprobvr_c', '0IScii']
  def uvprobvr(tno, var)
    r, rs = SYM[:uvprobvr][tno, var.to_s, 0, 0, 0]
    case rs[2].chr
    when ' ' then nil
    when 'a' then 
      # increment length to allow for terminating nul
      [rs[2].chr, rs[3]+1, rs[4]!=0]
    else
      [rs[2].chr, rs[3], rs[4]!=0]
    end
  end
  module_function :uvprobvr

  # void uvputvr_c  (int tno, int type, Const char *var, Const char *data, int n);
  SYM[:uvputvr] = LIBMIR_UVIO['uvputvr_c', '0IISSI']
  # data can be String for type == H_BYTE, otherwise NArray or Array
  def uvputvr(tno, var, data, type=nil)
    n = data.length
    if NArray === data
      # Force type
      type = case data.typecode
             when NArray::BYTE then H_BYTE
             when NArray::INT then H_INT
             when NArray::SINT then H_INT2
             when NArray::SFLOAT then H_REAL
             when NArray::FLOAT then H_DBLE
             when NArray::SCOMPLEX then H_CMPLX
             else
               bug(BUGSEV_ERROR, "Unsupported typecode (#{data.typecode}), in UVPUTVR")
             end
      data = data.to_s
    else
      # Autodetect type?
      if type.nil?
        if String == data
          type = H_BYTE
        else
          case data[0]
          when Integer
            type = H_INT
          when Float
            type = H_DBLE
          when Complex
            type = H_CMPLX
          else
            bug(BUGSEV_ERROR, "Unsupported type (#{data.class}), in UVPUTVR")
          end
        end
      end
      # Pack data
      case type
      when H_BYTE, :char, 'a'
        type = H_BYTE
        data = data.to_s
      when H_INT, :int, 'i'
        type = H_INT
        data = data.pack('i*')
      when H_INT2, :short, 'j'
        type = H_INT2
        data = data.pack('s*')
      when H_REAL, :float, 'r'
        type = H_REAL
        data = data.pack('F*')
      when H_DBLE, :double, 'd'
        type = H_DBLE
        data = data.pack('D*')
      when H_CMPLX, :complex, 'c'
        type = H_CMPLX
        data = data.map {|z| [z.real, z.imag]}
        data = data.flatten!.pack('F*')
      else
        bug(BUGSEV_ERROR, "Type incompatiblity for variable #{var.to_s}, in UVPUTVR")
      end
    end
    SYM[:uvputvr][tno, type, var.to_s, data, n]
  end
  module_function :uvputvr

  def uvputvra(tno, var, value)
    uvputvr(tno, H_BYTE, var, value)
  end
  module_function :uvputvra

  def uvputvrj(tno, var, value)
    uvputvr(tno, H_INT2, var, value)
  end
  module_function :uvputvrj

  def uvputvri(tno, var, value)
    uvputvr(tno, H_INT, var, value)
  end
  module_function :uvputvri

  def uvputvrf(tno, var, value)
    uvputvr(tno, H_REAL, var, value)
  end
  module_function :uvputvrf

  def uvputvrd(tno, var, value)
    uvputvr(tno, H_DBLE, var, value)
  end
  module_function :uvputvrd

  def uvputvrc(tno, var, value)
    uvputvr(tno, H_CMPLX, var, value)
  end
  module_function :uvputvrc

  # void uvtrack_c  (int tno, Const char *name, Const char *switches);
  SYM[:uvtrack] = LIBMIR_UVIO['uvtrack_c', '0ISS']
  def uvtrack(tno, name, switches='u')
    SYM[:uvtrack][tno, name.to_s, switches.to_s]
  end
  module_function :uvtrack

  # int  uvscan_c   (int tno, Const char *var);
  SYM[:uvscan] = LIBMIR_UVIO['uvscan_c', 'IIS']
  def uvscan(tno, var)
    r, rs = SYM[:uvscan][tno, var.to_s]
    case r
    when -1: nil # eof
    when  0: true # found
    else false # not found
    end
  end
  module_function :uvscan

  # void uvwrite_c  (int tno, Const double *preamble, Const float *data, Const int *flags, int n);
  SYM[:uvwrite] = LIBMIR_UVIO['uvwrite_c', '0IpppI']
  def uvwrite(tno, vis, n=nil)
    n ||= vis.nchan
    SYM[:uvwrite][tno, vis.preamble_p, vis.data_p, vis.flags_p, n]
  end
  module_function :uvwrite

  # void uvwwrite_c (int tno, Const float *data, Const int *flags, int n);
  SYM[:uvwwrite] = LIBMIR_UVIO['uvwwrite_c', '0IppI']
  def uvwwrite(tno, vis, n=nil)
    n ||= vis.nchan
    SYM[:uvwwrite][tno, vis.data_p, vis.flags_p, n]
  end
  module_function :uvwwrite

  # void uvsela_c   (int tno, Const char *object, Const char *string, int datasel);
  SYM[:uvsela] = LIBMIR_UVIO['uvsela_c', '0ISSI']
  def uvsela(tno, object, string, datasel) # TODO Reorder inputs to allow defaults?
    SYM[:uvsela][tno, object.to_s, string.to_s, datasel] # TODO Test, might need (datasel ? 1 : 0)
  end
  module_function :uvsela

  # void uvselect_c (int tno, Const char *object, double p1, double p2, int datasel);
  SYM[:uvselect] = LIBMIR_UVIO['uvselect_c', 'ISDDI']
  def uvselect(tno, object, p1, p2, dataset) # TODO Reorder inputs to allow defaults?
    SYM[:uvselect][tno, object.to_s, p1, p2, dataset] # TODO Test, might need (datasel ? 1 : 0)
  end
  module_function :uvselect

  # void uvset_c    (int tno, Const char *object, Const char *type, int n, double p1, double p2, double p3);
  SYM[:uvset] = LIBMIR_UVIO['uvset_c', '0ISSIDDD']
  def uvset(tno, object, type, n, p1, p2, p3)
    SYM[:uvset][tno, object.to_s, type.to_s, n, p1, p2, p3]
  end
  module_function :uvset

  # void uvread_c   (int tno, double *preamble, float *data, int *flags, int n, int *nread);
  SYM[:uvread] = LIBMIR_UVIO['uvread_c', '0IpppIi']
  def uvread(tno, vis)
    r, rs = SYM[:uvread][tno, vis.preamble_p, vis.data_p, vis.flags_p, vis.nchan, 0]
    vis.nread = rs[-1]
    vis.nread == 0 ? nil : vis
  end
  module_function :uvread

  # void uvwread_c  (int tno, float *data, int *flags, int n, int *nread);
  SYM[:uvwread] = LIBMIR_UVIO['uvwread_c', '0IppIi']
  def uvwread()
    SYM[:uvwread][tno, vis.preamble_p, vis.data_p, vis.flags_p, vis.nchan, 0]
    vis.nread = rs[-1]
    vis.nread == 0 ? nil : vis
  end
  module_function :uvwread

  # void uvflgwr_c  (int tno, Const int *flags);
  SYM[:uvflgwr] = LIBMIR_UVIO['uvflgwr_c', '0Ip']
  def uvflgwr(tno, vis_flags)
    case vis_flags
    when Vis
      p = vis_flags.flags_p
    when NArray
      p = DL::PtrData.new(vis_flags.ptr, vis_flags.bsize)
    when Array
      p = vis_flags.pack('i*') # TODO use DL.strdup?
    end
    SYM[:uvflgwr][tno, p]
  end
  module_function :uvflgwr

  # void uvwflgwr_c (int tno, Const int *flags);
  SYM[:uvwflgwr] = LIBMIR_UVIO['uvwflgwr_c', '0Ip']
  def uvwflgwr(tno, vis_flags)
    case vis_flags
    when Vis
      p = vis_flags.flags_p
    when NArray
      p = DL::PtrData.new(vis_flags.ptr, vis_flags.bsize)
    when Array
      p = vis_flags.pack('i*') # TODO use DL.strdup?
    end
    SYM[:uvwflgwr][tno, p]
  end
  module_function :uvwflgwr

  # void uvinfo_c   (int tno, Const char *object, double *data);
  SYM[:uvinfo] = LIBMIR_UVIO['uvinfo_c', '0ISp']
  def uvinfo(tno, object, ndata)
    data = NArray.float(ndata)
    p = DL::PtrData.new(data.ptr, data.bsize)
    SYM[:uvinfo][tno, object.to_s, p]
    ndata == 1 ? data[0] : data
  end
  module_function :uvinfo

end
