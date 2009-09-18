require 'narray'
require 'pgplot'
include Pgplot
include NMath

def main
  exit unless pgbeg('?',1,1)
  print " Routine PGCONT\n"
  pgex31
  print " Routine PGCONS\n"
  pgex32
  print " Routine PGCONB\n"
  pgex33
  print " Routine PGCONT with PGCONL labels\n"
  pgex36
  #print " Routine PGCONX with arrow labels\n"
  #pgex37
  #print " Routine PGCONX\n"
  #pgex34
  print " Routine PGCONF\n"
  pgexx1
  pgend
end

# ====== Utility ======

class PgLinestyle
  attr_accessor :width
  attr_accessor :color
  attr_accessor :style

  def initialize(opt=nil)
    @width = 1
    @color = 1
    @style = 1
    if opt.is_a?(Hash)
      @width = opt[:width]  || @width
      @width = opt['width'] || @width
      @color = opt[:color]  || @color
      @color = opt['color'] || @color
      @style = opt[:style]  || @style
      @style = opt['style'] || @style
    end
  end

  def set
    pgslw @width
    pgsci @color
    pgsls @style
  end
end # class PgLinestyle

NC=21
Pgline_default = PgLinestyle.new
$sty = (1..NC).collect{|i|
  if i<10
    x = PgLinestyle.new(:width =>1, :color =>2, :style =>2)
  else
    x = PgLinestyle.new(:width =>1, :color =>3, :style =>1)
  end
  if i%5==0
    x.width = 5
  end
  x
}
i = NArray.sfloat(40,1).indgen!(1)
j = NArray.sfloat(1,40).indgen!(1)
$f = cos( 0.3*sqrt(i*2)-0.4*j/3 ) * cos( 0.4*i/3 ) + (i-j)/40.0
$lv = NArray.sfloat(NC).indgen!*($f.max-$f.min)/NC+$f.min
#NArray.span($f.minmax,NC)

# ====== Exsample routine ======

def pgex31
  pgpage
  pgsvp(0.05,0.95,0.05,0.95)
  pgswin(1.0,40.0,1.0,40.0)
  pgbox('bcts',0.0,0,'bcts',0.0,0)
  pgmtxt('t',1.0,0.0,0.0,'Contouring using PGCONT')
  pgbbuf
  for i in 0...NC
    $sty[i].set
    pgcont $f, $lv[i]
  end
  Pgline_default.set
  pgebuf
end

def pgex32
  pgpage
  pgsvp(0.05,0.95,0.05,0.95)
  pgswin(1.0,40.0,1.0,40.0)
  pgbox('bcts',0.0,0,'bcts',0.0,0)
  pgmtxt('t',1.0,0.0,0.0,'Contouring using PGCONS')
  pgbbuf
  for i in 0...NC
    $sty[i].set
    pgcons $f, $lv[i]
  end
  Pgline_default.set
  pgebuf
end

def pgex33
  pgpage
  pgsvp(0.05,0.95,0.05,0.95)
  pgswin(1.0,40.0,1.0,40.0)
  pgbox('bcts',0.0,0,'bcts',0.0,0)
  pgmtxt('t',1.0,0.0,0.0,'Contouring using PGCONB')
  pgbbuf

  blank = -65536.0

  f = $f.dup
  i = NArray.sfloat(40,1).indgen!(1)
  j = NArray.sfloat(1,40).indgen!(1)
  r = sqrt((i-20.5)**2 + (j-20.5)**2)
  idx = ((r>20).or(r<3.0)).where
  f[idx] = blank
  pgsci 1
  pgpt( (i+NArray.int(1,40))[idx], (j+NArray.int(40,1))[idx], 1 )

  for i in 0...NC
    $sty[i].set
    pgconb f, $lv[i], blank
  end
  Pgline_default.set
  pgebuf
end

def pgex36
  pgpage
  pgsvp(0.05,0.95,0.05,0.95)
  pgswin(1.0,40.0,1.0,40.0)
  pgbox('bcts',0.0,0,'bcts',0.0,0)
  pgmtxt('t',1.0,0.0,0.0,'Contouring using PGCONT and PGCONL labels')
  pgbbuf

  for i in 0...NC
    $sty[i].set
    pgcons $f, $lv[i]
  end
  pgslw 1
  pgsls 1
  1.step(20,2) {|i|
    pgsci $sty[i].color
    pgconl $f,$lv[i],"%2i"%(i+1),16,8
  }
  Pgline_default.set
  pgebuf
end

def pgexx1
  nx=ny=51
  c = [3.0, 3.2, 3.5, 3.6, 3.766413, 4.0 ,5.0, 10.0, 100.0]
  xmin =-2.0
  xmax = 2.0
  ymin =-2.0
  ymax = 2.0
  mu = 0.3
  dx = (xmax-xmin)/(nx-1)                                      
  dy = (ymax-ymin)/(ny-1)
  tr = [xmin-dx, dx, 0.0, ymin-dy, 0.0, dy]
  x = tr[0] + NArray.sfloat(nx,1).indgen!(1)*tr[1]
  y = tr[3] + NArray.sfloat(1,ny).indgen!(1)*tr[5]
  z = (1.0-mu)*(2.0/sqrt((x-mu)**2+y**2)+(x-mu)**2+y**2) +
       mu*(2.0/sqrt((x+1.0-mu)**2+y**2)+(x+1.0-mu)**2+y**2)      

  pgpage
  pgvstd
  pgwnad(xmin, xmax, ymin, ymax)
  pgsfs(1)
  for i in 0..c.size-2
    r = 0.5+0.5*(i-1)/(c.size-1)
    pgscr(i+10, r, r, r)
    pgsci(i+10)
    pgconf(z,c[i]..c[i+1],tr)
  end
  pgsci(3)
  pgcont(z,c,tr)
  pgsci(1)
  pgsch(0.6)
  pgbox('bctsin',1.0,10,'bctsinv',1.0,10)
  pgsch(1.0)
  pgmtxt('t',1.0,0.0,0.0,'Contour filling using PGCONF')
end

main
