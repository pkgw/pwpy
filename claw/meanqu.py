#!/usr/bin/env python

import sys

if len(sys.argv) < 2:
    print 'dude, give me a log file.  wtf?'
    exit(1)

import asciidata, numpy, pylab

# load files
print 'loading ', sys.argv[1]
f = asciidata.AsciiData(sys.argv[1], comment_char='#')
nu = numpy.array(f.columns[0])
q = numpy.array(f.columns[1])
u = numpy.array(f.columns[2])
err = numpy.array(f.columns[3])

# flux model for 3c286 stokes parameters
# init with 1.0 ghz index
trueq = 0.638 * (0.96/nu)**(0.337)
trueu = 1.433 * (0.96/nu)**(0.337)
ind = numpy.where((nu >= 1.39) & (nu <= 1.47))
trueq[ind] = 0.526 * (1.39/nu[ind])**(0.353)
trueu[ind] = 1.263 * (1.39/nu[ind])**(0.353)
ind = numpy.where((nu >= 1.76) & (nu <= 1.84))
trueq[ind] = 0.515 * (1.76/nu[ind])**(0.353)
trueu[ind] = 1.158 * (1.76/nu[ind])**(0.353)
ind = numpy.where((nu >= 1.97) & (nu <= 2.05))
trueq[ind] = 0.494 * (1.97/nu[ind])**(0.410)
trueu[ind] = 1.110 * (1.97/nu[ind])**(0.410)

# fluxweight = numpy.sum(q/err**2)/numpy.sum(1/err**2)
# print 1/numpy.sqrt(numpy.sum(1/err**2))
ind = numpy.where(((nu >= 0.96) & (nu <= 1.04)) | ((nu >= 1.39) & (nu <= 1.47)) | ((nu >= 1.76) & (nu <= 1.84)) | ((nu >= 1.97) & (nu <= 2.05)))
meanq = (q-trueq).mean()
meanu = (u-trueu).mean()
stdq = (q-trueq).std()/numpy.sqrt(len(ind[0]))
stdu = (u-trueu).std()/numpy.sqrt(len(ind[0]))
print 'Total:'
#print '%2.0f\pm%2.0f & %2.0f\pm%2.0f' % (1000*meanq,1000*stdq,1000*meanu,1000*stdu) 
p = numpy.sqrt(trueq[ind].mean()**2 + trueu[ind].mean()**2)
perr = numpy.sqrt(meanq**2 + meanu**2)/(p/0.095)
stdp = numpy.sqrt(stdq**2 + stdu**2)/(p/0.095)
therr = numpy.degrees(0.5*numpy.arctan2(meanu,meanq))
print '$%1.2f\pm%1.2f$ & $%3.0f$ ' % (100*perr,100*stdp,therr)

ind = numpy.where((nu >= 0.96) & (nu <= 1.04))
meanq = (q[ind]-trueq[ind]).mean()
meanu = (u[ind]-trueu[ind]).mean()
stdq = (q[ind]-trueq[ind]).std()/numpy.sqrt(len(ind[0]))
stdu = (u[ind]-trueu[ind]).std()/numpy.sqrt(len(ind[0]))
print '1000:'
#print '%2.0f\pm%2.0f & %2.0f\pm%2.0f' % (1000*meanq,1000*stdq,1000*meanu,1000*stdu) 
p = numpy.sqrt(trueq[ind].mean()**2 + trueu[ind].mean()**2)
perr = numpy.sqrt(meanq**2 + meanu**2)/(p/0.095)
stdp = numpy.sqrt(stdq**2 + stdu**2)/(p/0.095)
therr = numpy.degrees(0.5*numpy.arctan2(meanu,meanq))
print '$%1.2f\pm%1.2f$ & $%3.0f$ ' % (100*perr,100*stdp,therr)


ind = numpy.where((nu >= 1.39) & (nu <= 1.47))
meanq = (q[ind]-trueq[ind]).mean()
meanu = (u[ind]-trueu[ind]).mean()
stdq = (q[ind]-trueq[ind]).std()/numpy.sqrt(len(ind[0]))
stdu = (u[ind]-trueu[ind]).std()/numpy.sqrt(len(ind[0]))
print '1430:'
#print '%2.0f\pm%2.0f & %2.0f\pm%2.0f' % (1000*meanq,1000*stdq,1000*meanu,1000*stdu) 
p = numpy.sqrt(trueq[ind].mean()**2 + trueu[ind].mean()**2)
perr = numpy.sqrt(meanq**2 + meanu**2)/(p/0.095)
stdp = numpy.sqrt(stdq**2 + stdu**2)/(p/0.095)
therr = numpy.degrees(0.5*numpy.arctan2(meanu,meanq))
print '$%1.2f\pm%1.2f$ & $%3.0f$ ' % (100*perr,100*stdp,therr)


ind = numpy.where((nu >= 1.76) & (nu <= 1.84))
meanq = (q[ind]-trueq[ind]).mean()
meanu = (u[ind]-trueu[ind]).mean()
stdq = (q[ind]-trueq[ind]).std()/numpy.sqrt(len(ind[0]))
stdu = (u[ind]-trueu[ind]).std()/numpy.sqrt(len(ind[0]))
print '1800:'
#print '%2.0f\pm%2.0f & %2.0f\pm%2.0f' % (1000*meanq,1000*stdq,1000*meanu,1000*stdu) 
p = numpy.sqrt(trueq[ind].mean()**2 + trueu[ind].mean()**2)
perr = numpy.sqrt(meanq**2 + meanu**2)/(p/0.095)
stdp = numpy.sqrt(stdq**2 + stdu**2)/(p/0.095)
therr = numpy.degrees(0.5*numpy.arctan2(meanu,meanq))
print '$%1.2f\pm%1.2f$ & $%3.0f$ ' % (100*perr,100*stdp,therr)


ind = numpy.where((nu >= 1.97) & (nu <= 2.05))
meanq = (q[ind]-trueq[ind]).mean()
meanu = (u[ind]-trueu[ind]).mean()
stdq = (q[ind]-trueq[ind]).std()/numpy.sqrt(len(ind[0]))
stdu = (u[ind]-trueu[ind]).std()/numpy.sqrt(len(ind[0]))
print '2010:'
#print '%2.0f\pm%2.0f & %2.0f\pm%2.0f' % (1000*meanq,1000*stdq,1000*meanu,1000*stdu) 
p = numpy.sqrt(trueq[ind].mean()**2 + trueu[ind].mean()**2)
perr = numpy.sqrt(meanq**2 + meanu**2)/(p/0.095)
stdp = numpy.sqrt(stdq**2 + stdu**2)/(p/0.095)
therr = numpy.degrees(0.5*numpy.arctan2(meanu,meanq))
print '$%1.2f\pm%1.2f$ & $%3.0f$ ' % (100*perr,100*stdp,therr)


ind = numpy.where(((nu >= 1.39) & (nu <= 1.47)) | ((nu >= 1.97) & (nu <= 2.05)))
meanq = (q[ind]-trueq[ind]).mean()
meanu = (u[ind]-trueu[ind]).mean()
stdq = (q[ind]-trueq[ind]).std()/numpy.sqrt(len(ind[0]))
stdu = (u[ind]-trueu[ind]).std()/numpy.sqrt(len(ind[0]))
print '1430-2010:'
#print '%2.0f\pm%2.0f & %2.0f\pm%2.0f' % (1000*meanq,1000*stdq,1000*meanu,1000*stdu) 
p = numpy.sqrt(trueq[ind].mean()**2 + trueu[ind].mean()**2)
perr = numpy.sqrt(meanq**2 + meanu**2)/(p/0.095)
stdp = numpy.sqrt(stdq**2 + stdu**2)/(p/0.095)
therr = numpy.degrees(0.5*numpy.arctan2(meanu,meanq))
print '$%1.2f\pm%1.2f$ & $%3.0f$ ' % (100*perr,100*stdp,therr)


