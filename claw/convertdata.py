#!/usr/bin/python
#fixes the pointing and source of cross17 dataset
import commands
#uvedit vis=cross17-p1-3140 ra=13,31,08.289 dec=30,30,32.945
#puthd in=cross17-p1-3140_c/object value=3c286
#puthd in=cross17-p1-3140_c/source value=3c286
for pointing in range(17):
	tmplog=commands.getstatusoutput('uvedit vis=cross17-p%d-3140 ra=13,31,08.289 dec=30,30,32.945'% (pointing))
	print tmplog[1]
	tmplog=commands.getstatusoutput('puthd in=cross17-p%d-3140_c/object value=3c286'% (pointing))
	print tmplog[1]
	tmplog=commands.getstatusoutput('puthd in=cross17-p%d-3140_c/source value=3c286'% (pointing))
	print tmplog[1]

