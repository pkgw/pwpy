#
# $Id$
#

# Routines to deal with the  baseline <-> antennae pair translations (from
# basant.for)

require 'dl'

module Mirdl

  # subroutine basants(baseline, ant1, ant2, check)
  # NB: Ruby method 'basant' calls miriad method 'basants'
  SYM[:basant] = LIBMIR['basants_', '0diii']
  def basant(baseline, check=false)
    r, rs = SYM[:basant][baseline.to_f, 0, 0, (check ? 1 : 0)]
    rs[1,2]
  end
  module_function :basant

	# double precision function antbas(i1,i2)
  SYM[:antbas] = LIBMIR['antbas_', 'dii']
  def antbas(a1, a2)
    a1, a2 = a2, a1 if a1 > a2
    r, rs = SYM[:antbas][a1, a2]
    r
  end
  module_function :antbas

end
