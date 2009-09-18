require 'narray'
require 'pgplot'
include Pgplot

n = 10
x = NArray.sfloat(n).indgen!
y = NMath.sin(NArray.sfloat(n).indgen!)*3+n/2

pgbeg
pgenv 0, 10, 0, 10
pglab '','','Demo of PGLCUR'

n = pglcur(x,y,n/2)
p x[0...n], y[0...n]
