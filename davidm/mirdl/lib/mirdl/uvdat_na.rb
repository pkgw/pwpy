#
# $Id$
#

# Suboutines and functions from uvdat.for

require 'dl'
require 'narray'

module Mirdl

  # void uvDatInp(const char *key, const char *flags)
  SYM[:uvDatInp] = LIBMIR['uvdatinp_', '0SS'+'II']
  def uvDatInp(flags, key='vis')
    SYM[:uvDatInp][key, flags, key.length, flags.length]
  end
  module_function :uvDatInp

  # void uvDatRew
  SYM[:uvDatRew] = LIBMIR['uvdatrew_', '0']
  def uvDatRew
    SYM[:uvDatRew][]
  end
  module_function :uvDatRew

  # int uvDatOpn(int *tno)
  SYM[:uvDatOpn] = LIBMIR['uvdatopn_', 'Ii']
  def uvDatOpn
    r, rs = SYM[:uvDatOpn][0]
    return nil if r == 0
    tno = rs[0]
    # Read in first "frame" of uv variables
    uvnext(tno)
    uvrewind(tno)
    tno
  end
  module_function :uvDatOpn

  # void uvDatCls()
  SYM[:uvDatCls] = LIBMIR['uvdatcls_', '0']
  def uvDatCls
    SYM[:uvDatCls][]
  end
  module_function :uvDatCls

  # void uvDatRd(double preamble[], float data[],int flags[], int *n, int *nread)
  SYM[:uvDatRd] = LIBMIR['uvdatrd_', '0pppii']
  def uvDatRd(vis)
    r, rs = SYM[:uvDatRd][vis.preamble_p, vis.data_p, vis.flags_p, vis.nchan, 0]
    vis.nread = rs[-1]
    vis.nread == 0 ? nil : vis
  end
  module_function :uvDatRd

  # void uvDatWRd(float data[], int flags[], int *n, int *nread)
  SYM[:uvDatWRd] = LIBMIR['uvdatwrd_', '0ppii']
  def uvDatWRd(vis)
    r, rs = SYM[:uvDatWRd][vis.preamble_p, vis.data_p, vis.flags_p, vis.nchan, 0]
    vis.nread = rs[-1]
    vis.nread == 0 ? nil : vis
  end
  module_function :uvDatWRd

  # void uvDatGti(const char *object, int *ival)
  SYM[:uvDatGti] = LIBMIR['uvdatgti_', '0Sp'+'I']
  def uvDatGti(object)
    object = object.to_s
    p = DL.malloc(4*DL.sizeof('I'))
    r, rs = SYM[:uvDatGti][object, p, object.length]
    if object == 'pols'
      ival = rs[1].to_s(p.size).unpack('i4')
    else
      ival = rs[1].to_s(p.size).unpack('i')[0]
    end
    ival
  end
  module_function :uvDatGti

  # void uvDatGtr(const char *object, float *rval)
  SYM[:uvDatGtr] = LIBMIR['uvdatgtr_', '0Sf'+'I']
  def uvDatGtr(object)
    object = object.to_s
    r, rs = SYM[:uvDatGtr][object, 0.0, object.length]
    rs[1]
  end
  module_function :uvDatGtr

  # void uvDatGta(const char *object, char *aval)
  SYM[:uvDatGta] = LIBMIR['uvdatgta_', '0Ss'+'II']
  def uvDatGta(object, size=128)
    object = object.to_s
    aval=DL.malloc(size)
    r, rs = SYM[:uvDatGta][object, aval, object.length, size]
    rs[1].to_s.rstrip!
  end
  module_function :uvDatGta

  # void uvDatSet(const char *object, int ival)
  SYM[:uvDatSet] = LIBMIR['uvdatset_', '0Si'+'I']
  def uvDatSet(object, value)
    object = object.to_s
    r, rs = SYM[:uvDatSet][object, value, object.length]
    rs[1]
  end
  module_function :uvDatSet

  # int uvDatPrb(const char *object, double dval)
  SYM[:uvDatPrb] = LIBMIR['uvdatprb_', '0SD'+'I']
  def uvDatPrb(object, value)
    object = object.to_s
    r, rs = SYM[:uvDatPrb][object, value, object.length]
    r != 0
  end
  module_function :uvDatPrb

end
