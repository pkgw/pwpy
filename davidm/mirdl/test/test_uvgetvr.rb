#!/usr/bin/env ruby
$-w = true if $0 == __FILE__

require 'mirdl'
include Mirdl

tno = uvopen('test/test.mir')
d = uvgetvr(tno, :delay0)
p d
