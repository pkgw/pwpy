require 'narray'
require 'pgplot'
include Pgplot

n = 10
x = NArray.sfloat(n).indgen!
y = NArray.sfloat(n).indgen!

pgbeg
pgenv 0, 10, 0, 10
pglab '','','Demo of PGOLIN'

n = pgolin(x,y,2,n/2)
p x[0...n], y[0...n]
