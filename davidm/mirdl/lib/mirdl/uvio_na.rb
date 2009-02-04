require 'ostruct'
require 'narray'
require 'naptr'

# Routines from uvio.c

module Mirdl

  H_BYTE  = 1
  H_INT   = 2
  H_INT2  = 3
  H_REAL  = 4
  H_DBLE  = 5
  H_TXT   = 6
  H_CMPLX = 7

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

  # void uvopen_c   (int *tno, Const char *name, Const char *status);
  SYM[:uvopen] = LIBMIR_UVIO['uvopen_c', '0iSS']
  def uvopen(name, status)
    status = status.to_s
    status = case status
             when 'a', 'w+': 'append'
             when 'r': 'old'
             when 'w': 'new'
             else status
             end
    r, rs = SYM[:uvopen][0, name, status]
    rs[0]
  end
  module_function :uvopen

  # void uvclose_c  (int tno);
  SYM[:uvclose] = LIBMIR_UVIO['uvclose_c', '0I']
  def uvclose(tno)
    SYM[:uvclose][tno]
  end
  module_function :uvclose

  # void uvflush_c  (int tno);
  # void uvnext_c   (int tno);
  # void uvrewind_c (int tno);
  # void uvcopyvr_c (int tin, int tout);
  # int  uvupdate_c (int tno);
  # void uvvarini_c (int tno, int *vhan);
  # void uvvarset_c (int vhan, Const char *var);
  # void uvvarcpy_c (int vhan, int tout);
  # int  uvvarupd_c (int vhan);

  # void uvrdvr_c(int tno, int type, Const char *var, char *data, char *def, int n)
  SYM[:uvrdvr] = LIBMIR_UVIO['uvrdvr_c', '0IISppI']
  def uvrdvr(tno, type, var, defval, n=1)
    case type
    when H_BYTE
      data = DL.malloc(n)
      fmt = 'a*'
    when H_INT
      n = DL.sizeof('I')
      data = DL.malloc(n)
      fmt = 'i'
    when H_INT2
      n = DL.sizeof('S')
      data = DL.malloc(n)
      fmt = 's'
    when H_REAL
      n = DL.sizeof('F')
      data = DL.malloc(n)
      fmt = 'F'
    when H_DBLE
      n = DL.sizeof('D')
      data = DL.malloc(n)
      fmt = 'D'
    when H_CMPLX
      n = 2*DL.sizeof('F')
      data = DL.malloc(n)
      fmt = 'FF'
      defval = [defval.real, defval.imag] unless Array === defval
    else
      bug(BUGSEV_FATAL, "Type incompatiblity for variable #{var}, in UVRDVR")
    end
    defval = [defval].pack(fmt)
    r, rs = SYM[:uvrdvr][tno, type, var.to_s, data, defval, n]
    if type == H_CMPLX
      re, im = rs[3].to_s(n).unpack(fmt)
      Complex(re, im)
    else
      rs[3].to_s(n).unpack(fmt)[0]
    end
  end
  module_function :uvrdvr

  def uvrdvra(tno, var, defval, n)
    uvrdvr(tno, H_BYTE, var, defval, n)
  end
  module_function :uvrdvra

  def uvrdvrj(tno, var, defval)
    uvrdvr(tno, H_INT2, var, defval)
  end
  module_function :uvrdvrj

  def uvrdvri(tno, var, defval)
    uvrdvr(tno, H_INT, var, defval)
  end
  module_function :uvrdvri

  def uvrdvrf(tno, var, defval)
    uvrdvr(tno, H_REAL, var, defval)
  end
  module_function :uvrdvrf

  def uvrdvrd(tno, var, defval)
    uvrdvr(tno, H_DBLE, var, defval)
  end
  module_function :uvrdvrd

  def uvrdvrc(tno, var, defval)
    uvrdvr(tno, H_CMPLX, var, defval)
  end
  module_function :uvrdvrc

  # void uvgetvr_c  (int tno, int type, Const char *var, char *data, int n);

  # void uvprobvr_c (int tno, Const char *var, char *type, int *length, int *updated);
  SYM[:uvprobvr] = LIBMIR_UVIO['uvprobvr_c', '0IScii']
  def uvprobvr(tno, var)
    r, rs = SYM[:uvprobvr][tno, var.to_s, 0, 0, 0]
    (rs[2] == ' '[0]) ? nil : [rs[2].chr, rs[3], rs[4]!=0]
  end
  module_function :uvprobvr

  # void uvputvr_c  (int tno, int type, Const char *var, Const char *data, int n);
  # void uvtrack_c  (int tno, Const char *name, Const char *switches);
  # int  uvscan_c   (int tno, Const char *var);
  # void uvwrite_c  (int tno, Const double *preamble, Const float *data, Const int *flags, int n);
  # void uvwwrite_c (int tno, Const float *data, Const int *flags, int n);
  # void uvsela_c   (int tno, Const char *object, Const char *string, int datasel);
  # void uvselect_c (int tno, Const char *object, double p1, double p2, int datasel);
  # void uvset_c    (int tno, Const char *object, Const char *type, int n, double p1, double p2, double p3);

  # void uvread_c   (int tno, double *preamble, float *data, int *flags, int n, int *nread);
  SYM[:uvread] = LIBMIR_UVIO['uvread_c', '0IpppIi']
  def uvread(tno, vis)
    r, rs = SYM[:uvread][tno, vis.preamble_p, vis.data_p, vis.flags_p, vis.nchan, 0]
    vis.nread = rs[-1]
    vis
  end
  module_function :uvread

  # void uvwread_c  (int tno, float *data, int *flags, int n, int *nread);
  # void uvflgwr_c  (int tno, Const int *flags);
  # void uvwflgwr_c (int tno, Const int *flags);
  # void uvinfo_c   (int tno, Const char *object, double *data);

end
