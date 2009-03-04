#
# $Id$
#

# Functions missing from key.c

module Mirdl
  def mkeyf(key)
    m=[]
    while f = keyf(key)
      m << f
    end
    m
  end
end
