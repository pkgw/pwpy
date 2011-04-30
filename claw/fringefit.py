#!/usr/bin/env python
import numpy as n
import pylab as p
import scipy.optimize as opt

freq = n.array([520, 687, 687.4, 688, 700, 710, 718, 720, 722, 724, 730, 740, 750, 790, 890])
# arrays made from angle change between last 19... and first 20... crab gain phase solution
# value is phase change +300 mod 360 (could have just done mod 360...)
a2 = n.array([105, 318, 323, 330, 140, 285, 40,  70,  90, 130, 210, 350, 120, 340, 324])
a3 = n.array([100, 323, 315, 304, 90, 270, 130,  90,  50,  10, 270,  90, 270, 260, 255])
a5 = n.array([309, 325, 316, 303, 40, 200,  30, 330, 294, 255, 130, 268,  50, 270, 288])
a6 = n.array([120, 307, 311, 318, 90, 170, 250, 270, 288, 306,   0, 100, 200, 230, 120])

allfreq = n.arange(100,20000)/10.

line = lambda a, b, x: n.mod(a + b*(x-687), 360)
fitfunc = lambda p, x:  line(p[0], p[1], x)
errfunc = lambda p, x, y: (y - fitfunc(p, x))**2

# a2
p0 = [318, 14.2]
p2, success = opt.leastsq(errfunc, p0[:], args = (freq, a2))
p.plot(freq, a2, 'b.')
p.plot(allfreq, fitfunc(p2, allfreq), 'b--')
print p2

# a3
p0 = [323, -18.1]
p3, success = opt.leastsq(errfunc, p0[:], args = (freq, a3))
p.plot(freq, a3, 'r.')
p.plot(allfreq, fitfunc(p3, allfreq), 'r--')
print p3

# a5
p0 = [325, -21.5]
p5, success = opt.leastsq(errfunc, p0[:], args = (freq, a5))
p.plot(freq, a5, 'g.')
p.plot(allfreq, fitfunc(p5, allfreq), 'g--')
print p5

# a6
p0 = [307, 9.7]
p6, success = opt.leastsq(errfunc, p0[:], args = (freq, a6))
p.plot(freq, a6, 'y.')
p.plot(allfreq, fitfunc(p6, allfreq), 'y--')
print p6

print
print 'intersections...'
round = 30
print allfreq[n.where( (n.rint(fitfunc(p2, allfreq)/round) == n.rint(fitfunc(p3, allfreq)/round)) & (n.rint(fitfunc(p2, allfreq)/round) == n.rint(fitfunc(p5, allfreq)/round)) & (n.rint(fitfunc(p2, allfreq)/round) == n.rint(fitfunc(p6, allfreq)/round)))]

p.show()
