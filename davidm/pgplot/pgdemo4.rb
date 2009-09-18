require 'narray'
require 'pgplot'
include Pgplot
include NMath

def setvp
  pgsvp(0.0, 1.0, 0.0, 1.0)
  vpx1, vpx2, vpy1, vpy2 = pgqvp(1)
  d = [vpx2-vpx1, vpy2-vpy1].min/40.0
  vpx1 = vpx1 + 5.0*d
  vpx2 = vpx2 - 2.0*d
  vpy1 = vpy1 + 8.0*d
  vpy2 = vpy2 - 2.0*d
  pgvsiz(vpx1, vpx2, vpy1, vpy2)
end

def palett contra,bright
  rl =[-0.5, 0.0, 0.17, 0.33, 0.50, 0.67, 0.83, 1.0, 1.7]
  rr =[	0.0, 0.0,  0.0,  0.0,  0.6,  1.0,  1.0, 1.0, 1.0]
  rg =[	0.0, 0.0,  0.0,  1.0,  1.0,  1.0,  0.6, 0.0, 1.0]
  rb =[	0.0, 0.3,  0.8,  1.0,  0.3,  0.0,  0.0, 0.0, 1.0]
  pgctab(rl, rr, rg, rb)
end

exit if pgopen('?') < 1
printf "PGPLOT device type: %s\n", pgqinf('TYPE')
c1,c2 = pgqcir()
printf "Number of color indices used for image: %d\n", nc=[0,c2-c1+1].max
exit if nc<8

nx = 64
ny = 64
x = NArray.sfloat(nx,1).indgen!(1)
y = NArray.sfloat(1,ny).indgen!(1)
f = cos( sqrt(x*(80.0/nx))*0.6 - y*16.0/(3.0*ny) ) *
    cos( x*16.0/(3.0*nx) ) +
    (x/nx - y/ny) + sin(sqrt(x**2+y**2))*0.05

pgpage
setvp
pgwnad(0.0, 1.0+nx, 0.0, 1.0+ny)
bright = 0.5
contra  = 1.0
palett(contra, bright)
pgimag(f)
pgmtxt('t',1.0,0.0,0.0,'PGIMAG, PGWEDG, and PGCTAB')
pgsch(0.6)
pgbox('bcntsi',0.0,0,'bcntsiv',0.0,0)
pgmtxt('b',3.0,1.0,1.0,'pixel number')
pgwedg('BI', 4.0, 5.0, f.min,f.max, 'pixel value')
pgsch(1.0)

angle = 120.0/57.29578
c = cos(angle)
s = sin(angle)
tr = NArray[ -c-s,  2.0*c/nx, 2.0*s/ny,
	     -c+s, -2.0*s/nx, 2.0*c/ny ]

pgpage
setvp
pgwnad(-1.0, 1.0, -1.0, 1.0)
pgsci(1)
bright = 0.5
contra  = 1.0
palett(contra, bright)
pgimag(f,nil,tr)
pgsci(1)

pgcont(f,NArray.sfloat(21).indgen!*(f.max-f.min)/21+f.min, tr)
pgsls(1)
pgslw(1)
pgsci(1)
#outlin(1,mxi,1,mxj,tr)
pgmtxt('t',1.0,0.0,0.0,'PGIMAG, PGCONT and PGWEDG')
pgsch(0.6)
pgbox('bctsn',0.0,0,'bctsn',0.0,0)
pgwedg('BI', 4.0, 5.0, f.min, f.max, 'pixel value')
pgsch(1.0)

pgclos
