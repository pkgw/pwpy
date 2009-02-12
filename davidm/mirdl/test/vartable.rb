#!/usr/bin/env ruby
$-w = true if $0 == __FILE__

require 'mirdl'
include Mirdl

# This script shows a line by line translation of a simple FORTRAN program into
# Ruby using Mirdl.  The FORTRAN example is from the Miriad Programmers Guide.
#
# The Ruby code is on the left and the corresponding FORTRAN code is a comment
# on the right.  The Ruby code goes a little further than the FORTRAN snippet
# by using the "key" routines to get the UV dataset name.
#
# Note that the Ruby code is structured to mirror the FORTRAN code as closely
# as possible; it is not intended to show off Ruby coding idioms.

# No need to declare Ruby variables.    # character var*12,name*(?)
# They spring to life when assigned.    # integer iostat,tno,item
                                        #
keyini                                  #
vis = keya('vis')                       #
bug('f', 'no visibility given') if !vis #
                                        #
tno = uvopen(vis, 'old')                # call uvopen(tno,name,'old')
item = haccess(tno, 'vartable', 'read') # call haccess(tno,item,'vartable','read',iostat)
var = hreada(item)                      # call hreada(item,var,iostat)
while var                               # dowhile(iostat.eq.0)
  puts var[2..9]                       #   call output(var(3:10))
  var = hreada(item)                    #   call hreada(item,var,iostat)
end                                     # enddo
hdaccess(item)                          # call hdaccess(item,iostat)
uvclose(tno)                            # call uvclose(tno)
