#!/usr/bin/env python
# claw, 25jun10
# script to document linear algebra for stokes error
# expresses error in leak,gain as stokes errors

from sympy import *
import numpy

# define x (chi) and y (i) symbols
x = Symbol("x")
y = Symbol("y")

# define gain and leakage error symbols
gip = Symbol("gip")
giq = Symbol("giq")
gjp = Symbol("gjp")
gjq = Symbol("gjq")
dip = Symbol("dip")
diq = Symbol("diq")
djp = Symbol("djp")
djq = Symbol("djq")

# identity matrix
I2 = Matrix([[1,0],[0,1]])

# gain and leakage error matrices
Gi = Matrix([[gip,0],[0,giq]])
Gj = Matrix([[gjp,0],[0,gjq]])
Di = Matrix([[0,dip],[-diq,0]])
Dj = Matrix([[0,djp],[-djq,0]])

# product of parallactic angle and xy-orientation matrices
PS = Matrix([[1,cos(x),-sin(x),0],[0,sin(x),cos(x),y],[0,sin(x),cos(x),-y],[1,-cos(x),sin(x),0]])

# inverse of the above
PS2 = 0.5*Matrix([[1,0,0,1],[cos(x),sin(x),sin(x),-cos(x)],[-sin(x),cos(x),cos(x),sin(x)],[0,-y,y,0]])  # y = i  (a hack)

# error matrix
dR = numpy.kron(Gi,I2) + numpy.kron(I2,Gj.conjugate()) + numpy.kron(Di,I2)+  numpy.kron(I2,Dj.conjugate())

# matrix converting stokes vector (i,q,u,v) into stokes error vector
ds = -1*(PS2 * dR * PS)

# show that for theta=0, the equation reduces to Sault et al. (1996) values
print ds.subs(x,0)

