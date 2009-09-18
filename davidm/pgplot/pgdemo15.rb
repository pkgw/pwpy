require 'narray'
require 'pgplot'
include NMath
include Pgplot
#-----------------------------------------------------------------------
# Demonstration program for PGPLOT vector field plot.
#
# Program to demonstrate the use of PGVECT along with
# PGCONB by illustrating the flow around a cylinder with circulation.
#-----------------------------------------------------------------------
      twopi = 2*Math::PI
      blank = -1.0e10
# number of points in the x and y directions
      nx = 31
      ny = 31
# cylinder radius
      a = 1.0
# circulation strength
      gamma = 2.0
# freestream velocity
      vinf = 1.0
# max and min x and y
      xmax =  3.0*a
      xmin = -3.0*a
      ymax =  3.0*a
      ymin = -3.0*a
# point spacing
      dx = (xmax-xmin)/(nx-1)
      dy = (ymax-ymin)/(ny-1)
# compute the stream function, Cp, and u and v velocities
      a2 = a**2
      x  = NArray.sfloat(nx,1).indgen!*dx + xmin
      y  = NArray.sfloat(1,ny).indgen!*dy + ymin
      r2 = x**2 + y**2
      r2[(r2.eq 0).where] = 1e-10
      psi = vinf * y * (1-a2/r2) + gamma/twopi*0.5*log(r2/a)
      u   = vinf * (1 + a2/r2 - 2*a2*(x/r2)**2) + gamma/twopi * y/r2
      v   = vinf * x * (-2*a2*y/r2**2) + gamma/twopi * x/r2
      cp  = 1 - (u**2+v**2)/vinf**2
      idx = (r2 < a2).where
      u[idx] = 
      v[idx] = blank
#
# start drawing
#
      pgbeg
      pgenv( x[0], x[-1], y[0], y[-1], 1 )
      pgiden
      pglab('X','Y','Flow About a Cylinder with Circulation')
#
# contour plot of the stream function (streamlines)
#
      tr = [ x[0]-dx, dx, 0.0, y[0]-dy, 0.0, dy ]
      level = [ 1.0, 0.5, 0.0, -0.5, -1.0 ]
      pgcont( psi, level, tr )
#
# draw cylinder
#
      pgbbuf
      pgsci(0)
      pgsfs(1)
      pgcirc(0.0, 0.0, a*1.1)
      pgsfs(2)
      pgsci(14)
      pgcirc(0.0, 0.0, a)
      pgsci(1)
      pgebuf
#
# vector plot
#
      pgsah(2, 45.0, 0.7)
      pgsch(0.3)
      tr = [ x[0], dx, 0.0, y[0], 0.0, dy ]
      pgvect( u[1..-2,1..-2], v[1..-2,1..-2], 0.0, 0, tr, -1.0e10 )
      pgsch(1.0)
#
# finish
#
