require 'narray'
require 'pgplot'
include Pgplot

n = 100
x = NArray.sfloat(n,1).indgen!/10
y = NArray.sfloat(1,n).indgen!/10
a = NMath.sin(x) * NMath.cos(y)

pgbeg

pgenv  0,(n+1)/10.0, 0,(n+1)/10.0, 1 # scales of X and Y are equal
pglab  "(x)", "(y)", "PGGRAY Demo: sin(x)*cos(y)"
pgscir 16,64
pggray a, -1..1, [0,0.1,0,0,0,0.1]

pgenv  0,(n+1)/10.0, 0,(n+1)/10.0    # independent scales
pglab  "(x)", "(y)", "PGIMAG Demo: sin(x)*cos(y)"
pgscir 16,64
pgctab [0,1],[0,1],[0,1],[0,1]
pgimag a, -1..1, [0,0.1,0,0,0,0.1]
