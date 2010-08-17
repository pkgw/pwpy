#!/usr/bin/env python

"""
claw, 13oct09
Script to plot RM values from catalog in Hammer-Aitoff (equal area), all-sky projection.
Note that projection is flipped in longitude by multiplying by -1 and relabeling.
"""

import numpy as n
import pylab as p
import asciidata

cat = asciidata.AsciiData('/indirect/big_scr3/claw/data/ata/nvss-rm-best/RM-hires-join3-namelb.txt')
name = n.array(cat.columns[0])
l = n.array(cat.columns[1])
b = n.array(cat.columns[2])
rm = n.array(cat.columns[7])

#center = n.where(abs(rm) <= 600)
#rm = rm[center]
#l = l[center]
#b = b[center]

# cat = asciidata.AsciiData('/Users/claw/data/nvss-rm/RMCatalogue.txt')
#pol = n.array(cat.columns[15])
#good = n.where(pol > 200)[0]
#rm = n.array(cat.columns[21])[good]
#l = n.array(cat.columns[10])[good]
#b = n.array(cat.columns[11])[good]

p.subplot(111, projection="hammer")
p.grid()
p.xticks(n.radians(n.arange(-150,180,30)),('150','120','90','60','30','0','-30','-60','-90','-120','-150','-180'))

for i in range(len(rm)):
    print l[i], b[i], rm[i]
    if rm[i] > 0.0:
        p.plot(n.radians([-1*l[i]]), n.radians([b[i]]), 'o', markersize=3+(abs(rm[i]/5.)), color='red', alpha=0.7)
    else:
        p.plot(n.radians([-1*l[i]]), n.radians([b[i]]), 'x', markersize=3+(abs(rm[i]/5.)), color='blue', alpha=1.0)

p.show()
