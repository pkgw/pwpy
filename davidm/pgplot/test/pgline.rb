require 'narray'
require 'pgplot'
include Pgplot

n = 100
x = NArray.sfloat(n).indgen!/10
y = NMath.sin(x)

pgbeg()

pgenv 0, n/10, -1, 1
pglab "(x)", "(y)", "PGPLOT Example 1: y = x\\u2\\d"
pgline x, y
