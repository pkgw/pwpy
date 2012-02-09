#!/usr/bin/env python
#
# Usage: timeorder.py images
# images must be in MIRIAD format

from sys import argv
import os
from operator import itemgetter

allimr = []
allimrs = []
eps = {}

for im in argv[1:]:
	pjd = os.popen("gethd in="+im+"/obstime").read()
	eps[im] = pjd.rstrip()
allimrsa = sorted(eps.iteritems(), key=lambda (k,v):(v,k))
allimrs = allimrs + map(itemgetter(0),allimrsa)
print ' '.join(allimrs)
