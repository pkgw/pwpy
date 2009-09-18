require 'narray'
require 'pgplot'
include Pgplot
include NMath

n=64
ncol=32
nlev=9

pgbeg

i = NArray.sfloat(n,1).indgen!(1)
j = NArray.sfloat(1,n).indgen!(1)
f = cos(0.6*sqrt(i*2)-(0.4/3)*j) * cos((0.4/3)*i) + (i-j)/n
fmin = f.min
fmax = f.max

ia = (f-fmin)/(fmax-fmin)*(ncol-1)+16

ci1,ci2 = pgqcol
if ci2 < 15+ncol
  raise 'This program requires a device with at least %d colors'%(15+ncol)
end

pgpage
pgscr(0, 0.0, 0.3, 0.2)
pgsvp(0.05,0.95,0.05,0.95)
pgwnad(0.0, 1.0, 0.0, 1.0)

for i in 1..ncol
  r = 0.8*(i-1)/(ncol-1) + 0.2
  g = 2.0*(i-1-ncol/2)/(ncol-1)
  g = 0 if g<0
  b = 0.2 + 0.4*(ncol-i)/ncol
  pgscr(i+15, r, g, b)
end

pgpixl(ia,0,1,0,1)
pgsci(1)
pgmtxt('t',1.0,0.0,0.0,'Test of PGPIXL')
pgbox('bcnts',0.0,0,'bcnts',0.0,0)

clev = NArray.sfloat(nlev).indgen!(1) * ((fmax-fmin)/nlev) + fmin
pgcont(f, clev, NArray[-1.0, 1, 0, -1, 0, 1]/(n-1))
