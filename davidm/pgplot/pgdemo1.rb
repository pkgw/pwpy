require 'narray'
require 'pgplot'
include Pgplot
include NMath
PI    = Math::PI
TWOPI = PI*2
BLACK,WHITE,RED,GREEN,BLUE,CYAN,MAGENT,YELLOW = (0..7).to_a
FULL,DASH,DOTDSH,DOTTED,FANCY = (1..5).to_a
NORMAL,ROMAN,ITALIC,SCRIPT = (1..4).to_a
SOLID,HOLLOW = (1..2).to_a

# ====== Utility function ======

def indgen arg
  if arg.kind_of?(Range)
    return NArray.sfloat(arg.size).indgen!(arg.first)
  elsif arg.kind_of?(Numeric)
    return NArray.sfloat(arg).indgen!
  else
    raise ArgumentError, "invalid argument"
  end
end

def randomn n=1
  rr = NArray.sfloat(n)
  xx = NArray.sfloat(n)
  idx= NArray.int(n).indgen!
  i  = 0
  while i<n
    x = NArray.sfloat(n*4/3).random!(1) * 2 - 1
    y = NArray.sfloat(n*4/3).random!(1) * 2 - 1
    r = x**2 + y**2
    idx = (r<1).where
    siz = [n-i,idx.size-1].min
    rr[i] = r[idx[0...siz]]
    xx[i] = x[idx[0...siz]]
    #printf "i=%d,siz=%d,idx.size=%d\n",i,siz,idx.size
    i += siz
  end
  return xx * sqrt(-2*log(rr)/rr)
end

# ====== Demo function ======

def pgex0
  %w(
    version
    state
    user
    now
    device
    file
    type
    dev/type
    hardcopy
    terminal
    cursor
  ).each{|i| print " ",i," = ",pgqinf(i),"\n"}

  x1,x2,y1,y2 = pgqvsz(1)
  x = x2-x1
  y = y2-y1
  printf " Plot dimensions (x,y; inches): %9.2f, %9.2f
                          (mm): %9.2f, %9.2f\n",x, y, x*25.4, y*25.4
end

def pgex1
  pgenv 0, 10, 0, 20, 0, 1
  pglab '(x)', '(y)', 'PGPLOT Example 1:  y = x\u2'

  xs = [1.0,2.0,3.0,4.0,5.0]
  ys = [1.0,4.0,9.0,16.0,25.0]
  pgpt xs,ys,9

  n = 60
  xr = indgen(n)*0.1
  yr = xr**2
  pgline xr, yr
end

def pgex2
  pgenv -2.0,10.0,-0.4,1.2, 0,1
  pglab '(x)', 'sin(x)/x', 'PGPLOT Example 2:  Sinc Function'

  xr = (indgen(100)-20.5)/6.0
  yr = sin(xr)/xr
  pgline xr, yr
end

def pgex3
  pgenv 0.0,720.0,-2.0,2.0, 0,-2
  pgsave
  pgsci 14
  pgbox 'G',30.0, 0,'G', 0.2, 0
  pgsci 5
  pgbox 'ABCTSN',90.0, 3,'ABCTSNV', 0.0,0
  pgsci 3
  pglab 'x (degrees)','f(x)','PGPLOT Example 3'

  xr = indgen(360) * 2
  arg= xr/180*PI
  yr = sin(arg) + cos(arg*2)*0.5 + cos(arg*1.5+PI/3)*0.5

  pgsci 6
  pgsls 2
  pgslw 3
  pgline xr, yr
  pgunsa
end

def pgex4
  seed = -5678921
  data = randomn(1000)
  pgsave
  pghist data, 31, -3.1..3.1, 0
  data = randomn(200)*0.5 + 1 
  pgsci 15
  pghist data, 31, -3.1..3.1, 3
  pgsci 0
  pghist data, 31, -3.1..3.1, 1
  pgsci 1
  pgbox 'BST', 0.0, 0, ' ', 0.0, 0

  pglab 'Variate', ' ','PGPLOT Example 4:  Histograms (Gaussian)'

  x = indgen(620)*0.01 - 3.1
  y = exp(-(x**2)*0.5) * (0.2*1000/sqrt(2*PI))

  pgline x,y
  pgunsa
end

def pgex5
  np=15
  freq = NArray[ 26.0, 38.0, 80.0, 160.0, 178.0, 318.0, 365.0, 408.0,
                 750.0, 1400.0, 2695.0, 2700.0, 5000.0, 10695.0, 14900.0 ]
  flux = NArray[ 38.0, 66.4, 89.0, 69.8, 55.9, 37.4, 46.8, 42.4, 27.0,
		 15.8, 9.09, 9.17, 5.35, 2.56, 1.73 ]
  err  = NArray[ 6.0, 6.0, 13.0, 9.1, 2.9, 1.4, 2.7, 3.0, 0.34, 0.8,
		 0.2, 0.46, 0.15, 0.08, 0.01 ]
  pgsave
  pgsci CYAN
  pgenv -2.0,2.0,-0.5,2.5,1,30
  pglab 'Frequency, \gn (GHz)',
        'Flux Density, S\d\gn\u (Jy)',
        'PGPLOT Example 5:  Log-Log plot'
  x = indgen(100)*0.03 + 1.3
  xp = x-3
  yp = -x*1.15 - exp(-x)*7.72 + 5.18
  pgsci RED
  pgline xp,yp

  xp = log10(freq)-3.0
  yp = log10(flux)
  pgsci GREEN
  pgpt xp,yp,17

  yhi = log10(flux+2*err)
  ylo = log10(flux-2*err)
  pgerry xp,ylo,yhi
  pgunsa
end

def pgex6
  twopi = PI*2
  npol = 6

  n1 = [ 0, 3, 4, 5, 5, 6, 8 ]  # index-0 is dummy
  n2 = [ 0, 1, 1, 1, 2, 1, 3 ]
  lab = [ '', 'Fill style 1 (solid)',
	  'Fill style 2 (outline)',
          'Fill style 3 (hatched)',
          'Fill style 4 (cross-hatched)']
  pgbbuf
  pgsave
  pgpage
  pgsvp 0.0, 1.0, 0.0, 1.0
  pgwnad 0.0, 10.0, 0.0, 10.0
  pgsci 1
  pgmtxt 'T', -2.0, 0.5, 0.5, 
    'PGPLOT fill area: routines PGPOLY, PGCIRC, PGRECT'

  for k in 1..4
    pgsci 1
    y0 = 10.0 - 2.0*k
    pgtext 0.2, y0+0.6, lab[k]
    pgsfs k
    for i in 1..npol
      pgsci i
      angle = indgen(n1[i])*(n2[i]*twopi/n1[i])
      x = cos(angle)*0.5 + i
      y = sin(angle)*0.5 + y0
      pgpoly x,y
    end
    pgsci 7
    pgcirc 7.0, y0, 0.5
    pgsci 8
    pgrect 7.8, 9.5, y0-0.5, y0+0.5
  end
  pgunsa
  pgebuf
end

def pgex7
  pgbbuf
  pgsave
  pgsci 1
  pgenv 0.0,5.0, -0.3,0.6, 0,1
  pglab '\fix', '\fiy', 'PGPLOT Example 7: scatter plot'

  xs = NArray.sfloat(300).random!(1.0)*5
  ys = randomn(300)*0.05 + xs*exp(-xs)

  pgsci 3
  pgpt xs[0..99],ys[0..99], 3
  pgpt xs[100..199],ys[100..199], 17
  pgpt xs[200..299],ys[200..299], 21

  xr = indgen(101)*0.05
  yr = xr*exp(-xr)
  pgsci 2
  pgline xr,yr

  xp = xs[100]
  yp = ys[100]
  xsig = 0.2
  ysig = 0.1
  pgsci 5
  pgsch 3.0
  pgerr1 5, xp, yp, xsig, 1.0
  pgerr1 6, xp, yp, ysig, 1.0
  pgpt1 xp,yp,21
  pgunsa
  pgebuf
end

def pgex8
  pgpage
  pgbbuf
  pgsave
  pgsvp(0.1,0.6,0.1,0.6)
  pgswin(0.0, 630.0, -2.0, 2.0)
  pgsci(CYAN)
  pgbox('ABCTS', 90.0, 3, 'ABCTSV', 0.0, 0)
  pgsci(RED)
  pgbox('N',90.0, 3, 'VN', 0.0, 0)
  xr = indgen(360)*2
  yr = sin(xr/57.29577951)
  pgsci(MAGENT)
  pgsls(DASH)
  pgline(xr,yr)
  pgswin(90.0, 720.0, -2.0, 2.0)
  pgsci(YELLOW)
  pgsls(DOTTED)
  pgline(xr,yr)
  pgsls(FULL)
  pgsvp(0.45,0.85,0.45,0.85)
  pgswin(0.0, 180.0, -2.0, 2.0)
  pgsci(0)
  pgrect(0.0, 180.0, -2.0, 2.0)
  pgsci(BLUE)
  pgbox('ABCTSM', 60.0, 3, 'VABCTSM', 1.0, 2)
  pgsci(WHITE)
  pgsls(DASH)
  pgline(xr,yr)
  pgunsa
  pgebuf
end

def pgex9
  pgbbuf
  pgsave
  pgsci(5)
  #pgfunt(fx,fy,360,0.0,TWOPI,0)  # pgfunt is not implemented
  t = indgen(361)/360*TWOPI
  x = sin(t*5)
  y = sin(t*4)
  pgenv -1,1,-1,1
  pgline x,y
  pgsci(3)
  pglab('x','y','PGPLOT Example 9:  routine PGFUNT')
  pgunsa
  pgebuf
end

def bessel_j0 arg

  r = NArray.sfloat(arg.size)
  x = arg.abs
  idx1,idx2 = (x<=3).where2
  if idx1.size>0 then
    xo3 = x[idx1]/3.0
    t   = xo3**2
    r[idx1] = 1.0 +
	t*(-2.2499997 +
	t*( 1.2656208 +
	t*(-0.3163866 +
	t*( 0.0444479 +
	t*(-0.0039444 +
	t*( 0.0002100))))))
  end
  if idx2.size>0 then
    xx = x[idx2]
    t  = 3.0/xx
    f0 = 0.79788456 +
	t*(-0.00000077 + 
	t*(-0.00552740 +
	t*(-0.00009512 +
	t*( 0.00137237 +
	t*(-0.00072805 +
	t*( 0.00014476))))))
    theta0 = xx - 0.78539816 +
      	t*(-0.04166397 +
      	t*(-0.00003954 +
      	t*( 0.00262573 +
      	t*(-0.00054125 +
      	t*(-0.00029333 +
      	t*( 0.00013558))))))
    r[idx2] = f0*cos(theta0)/sqrt(xx)
  end
  return r
end

def bessel_j1 arg
  r = NArray.sfloat(arg.size)
  x = arg.abs
  idx1,idx2 = (x<=3).where2
  if idx1.size>0 then
    xo3 = x[idx1]/3.0
    t = xo3**2
    f = 0.5 + t*(-0.56249985 +
	t*( 0.21093573 +
	t*(-0.03954289 +
	t*( 0.00443319 +
	t*(-0.00031761 +
	t*( 0.00001109))))))
    r[idx1] = f * arg[idx1]
  end
  if idx2.size>0 then
    xx = x[idx2]
    t  = 3.0/xx
    f1 = 0.79788456 +
        t*( 0.00000156 +
	t*( 0.01659667 + 
        t*( 0.00017105 +
        t*(-0.00249511 +
        t*( 0.00113653 + 
        t*(-0.00020033))))))
    theta1 = xx - 2.35619449 + 
        t*( 0.12499612 +
        t*( 0.00005650 +
        t*(-0.00637879 +
        t*( 0.00074348 +
        t*( 0.00079824 +
        t*(-0.00029166))))))
    r[idx2] = f1*cos(theta1)/sqrt(xx)
  end
  idx = (arg<0).where
  #p idx
  #p r[idx]
  r[idx] = -r[idx] if idx.size>0
  return r
end

def pgex10
  pgbbuf
  pgsave
  pgsci(YELLOW)
  # PGFUNX(PGBSJ0,500,0.0,10.0*PI,0)
  x = indgen(500)/50*PI
  y = bessel_j0(x)
  pgenv 0,PI*10, y.min,y.max
  pgline x,y
  pgsci(RED)
  pgsls(DASH)
  # PGFUNX(PGBSJ1,500,0.0,10.0*PI,1)
  pgline x, bessel_j1(x)
  pgsci(GREEN)
  pgsls(FULL)
  pglab('\fix', '\fiy',
        '\frPGPLOT Example 10: routine PGFUNX')
  pgmtxt('T', -4.0, 0.5, 0.5,
	 '\frBessel Functions')
  pgarro(8.0, 0.7, 1.0, bessel_j0(NArray[1.0])[0])
  pgarro(12.0, 0.5, 9.0, bessel_j1(NArray[9.0])[0])
  pgstbg(GREEN)
  pgsci(0)
  pgptxt(8.0, 0.7, 0.0, 0.0, ' \fiy = J\d0\u(x)')
  pgptxt(12.0, 0.5, 0.0, 0.0, ' \fiy = J\d1\u(x)')
  pgunsa
  pgebuf
end

# ====== Demo start ======

raise "device not found" if pgopen<0

pgex0
pgex1
pgex2
pgex3
pgsubp 2,1
pgex4
pgex5
pgsubp 1,1
pgex6
pgex7
pgex8
pgex9
pgex10

pgclos
exit

