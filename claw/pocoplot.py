
#!/usr/bin/env python
"""
Quick script for plotting and fitting distributions of PoCo pulses.
claw, 7apr11
"""

import asciidata, pickle, string
import pylab as p
import numpy as n
import scipy.optimize as opt


#filename = 'crab_fixdm_ph/poco_crab_fitsp.txt'
filename = 'b0329_fixdm_ph/poco_b0329_173027_fitsp.txt'
filename2 = 'b0329_fixdm_uv/poco_b0329_173027_fitsp.txt'
filename3 = 'b0329_fixdm_im2/poco_b0329_173027_fitsp.txt'
mode='flux'

f = asciidata.AsciiData(filename)
name = n.array(f.columns[0])
amp = n.array(f.columns[3])
ind = n.array(f.columns[4])
rms = n.array(f.columns[6])
f = asciidata.AsciiData(filename2)
name2 = n.array(f.columns[0])
amp2 = n.array(f.columns[3])
ind2 = n.array(f.columns[4])
rms2 = n.array(f.columns[6])
f = asciidata.AsciiData(filename3)
name3 = n.array(f.columns[0])
amp3 = n.array(f.columns[3])
ind3 = n.array(f.columns[4])
rms3 = n.array(f.columns[6])

plaw = lambda a, b, x: a * (x/x[0])**b
freqs = 0.718 + 0.104/64. * n.array([ 3,  4,  5,  6,  7,  8,  9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 37, 38, 40, 44, 45, 46, 47, 48])

meanflux = []; meanflux2 = []; meanflux3 = []
for i in range(len(amp)):
    meanflux.append(plaw(amp[i],ind[i],freqs).mean())
for i in range(len(amp2)):
    meanflux2.append(plaw(amp2[i],ind2[i],freqs).mean())
for i in range(len(amp3)):
    meanflux3.append(plaw(amp3[i],ind3[i],freqs).mean())

meanflux = n.array(meanflux); meanflux2 = n.array(meanflux2); meanflux3 = n.array(meanflux3)
sig = meanflux/(n.sqrt(len(freqs)) * n.array(rms)); sig2 = meanflux2/(n.sqrt(len(freqs)) * n.array(rms2)); sig3 = meanflux3/(n.sqrt(len(freqs)) * n.array(rms3))

nint = []; nskip = []; chunk = []
nint2 = []; nskip2 = []; chunk2 = []; pnn2 = []; detsig2 = []
nint3 = []; nskip3 = []; chunk3 = []; pnn3 = []; detsig3 = []
for nn in name:
    nskip.append(int((nn.split('.'))[1].split('-')[0]))
    nint.append(int((nn.split('-dm0t'))[1].split('.')[0]))
#    chunk.append(int((nn.split('_173027_'))[1].split('.')[0]))
    chunk.append(int((nn.split('_'))[3].split('.')[0]))
for nn in name2:
    nskip2.append(int((nn.split('.'))[1].split('-')[0]))
    nint2.append(int((nn.split('-dm0t'))[1].split('.')[0]))
    chunk2.append(int((nn.split('_173027_'))[1].split('.')[0]))
    tmp = (nn.split('/')[1].split('.')[0:2])
    tmp.append('pkl')
    tmp[0] = 'b0329_fixdm_uv/' + tmp[0]
    pklname = string.join(tmp, '.')
    pnn2.append(pklname)
    pkl = pickle.load(open(pklname))
    detsig2.append(pkl[6][0])
for nn in name3:
    nskip3.append(int((nn.split('.'))[1].split('-')[0]))
    nint3.append(int((nn.split('-dm0t'))[1].split('.')[0]))
    chunk3.append(int((nn.split('_173027_'))[1].split('.')[0]))
    tmp = (nn.split('/')[1].split('.')[0:2])
    tmp.append('pkl')
    tmp[0] = 'b0329_fixdm_im2/' + tmp[0]
    pklname = string.join(tmp, '.')
    pnn3.append(pklname)
    pkl = pickle.load(open(pklname))
    detsig3.append(pkl[6][0])


ntot = n.array(chunk)*131000 + n.array(nskip) + n.array(nint)
ntot2 = n.array(chunk2)*131000 + n.array(nskip2) + n.array(nint2)
ntot3 = n.array(chunk3)*131000 + n.array(nskip3) + n.array(nint3)

dtype1 = [('ntot', int), ('flux', float)]
dtype2 = [('ntot', int), ('flux', float), ('detsig', float)]
sortar = []; sortar2 = []; sortar3 = []
for i in range(len(ntot)):
    sortar.append( (ntot[i], meanflux[i], ind[i]) )
#    sortar.append( (ntot[i], meanflux[i]) )
for i in range(len(ntot2)):
    sortar2.append( (ntot2[i], meanflux2[i], detsig2[i]) )
for i in range(len(ntot3)):
    sortar3.append( (ntot3[i], meanflux3[i], detsig3[i]) )

sortar = n.array(sortar, dtype=dtype2)
#sortar = n.array(sortar, dtype=dtype1)
sortar2 = n.array(sortar2, dtype=dtype2)
sortar3 = n.array(sortar3, dtype=dtype2)
newsortar = n.sort(sortar, order=['ntot'])
newsortar2 = n.sort(sortar2, order=['ntot'])
newsortar3 = n.sort(sortar3, order=['ntot'])

# print out integration number of each pulse
#ff = open('tmp.txt','a')
#tt = n.array( newsortar.tolist())
#for i in range(len(tt)):
#    print >> ff, tt[i,0], tt[i,1]
#ff.close()

ntotdiff = []; ntotdiff2 = []; ntotdiff3 = []
for i in range(len(newsortar)-1):
    ntotdiff.append(newsortar[i+1][0] - newsortar[i][0])
for i in range(len(newsortar2)-1):
    ntotdiff2.append(newsortar2[i+1][0] - newsortar2[i][0])
for i in range(len(newsortar3)-1):
    ntotdiff3.append(newsortar3[i+1][0] - newsortar3[i][0])
ntotdiff.append(0)
ntotdiff2.append(0)
ntotdiff3.append(0)
ntotdiff = n.array(ntotdiff) ; ntotdiff2 = n.array(ntotdiff2); ntotdiff3 = n.array(ntotdiff3)

good1 = n.where(n.array(newsortar.tolist())[:,1] > 0.)[0]
good2 = n.where( (ntotdiff2 > 0) & (n.array(newsortar2.tolist())[:,2] > 5.6) )[0]
good3 = n.where( (n.array(newsortar3.tolist())[:,2] > 7.0) & (n.array(newsortar3.tolist())[:,1] > 0.) & (ntotdiff3 > 0))[0]
print 'lengths (orig, new): ', len(ntotdiff), len(good1), len(ntotdiff2), len(good2), len(ntotdiff3), len(good3)

meanflux = (n.array( newsortar.tolist())[:,1] )[good1]
meanflux2 = (n.array( newsortar2.tolist())[:,1] )[good2]
meanflux3 = (n.array( newsortar3.tolist())[:,1] )[good3]

#p.figure(1)
#p.hist(ntotdiff, bins=[-1,0,1,2,5,10,20,30,40,50,60,70,80,90,100,110])
#p.figure(2)
#p.hist(ntotdiff2, bins=[-1,0,1,2,5,10,20,30,40,50,60,70,80,90,100,110])
#p.figure(3)
#p.hist(ntotdiff3, bins=[-1,0,1,2,5,10,20,30,40,50,60,70,80,90,100,110])
#p.show()

if mode == 'flux':
    plaw = lambda a, b, x: a * (x/100.)**b
    fitfunc = lambda p, x:  plaw(p[0], p[1], x)
    errfunc = lambda p, x, y, rms: ((y - fitfunc(p, x))/rms)**2
    p0 = [100,-4.5]

    hist = p.hist(meanflux, align='mid', bins=n.arange(-200,1000,10), label='Observed', color='b')
    centers = n.array([(hist[1][i+1] + hist[1][i])/2 for i in range(len(hist[1])-1)])
    errs = 1+(n.sqrt(hist[0] + 0.75))
    p.errorbar(centers,hist[0],yerr=errs,fmt=None,ecolor='b', capsize=0)
    fitignore = n.where(hist[1] >= 80)[0].min()
    print 'ignore, ', fitignore
    p1,success = opt.leastsq(errfunc, p0[:], args = (centers[fitignore:], hist[0][fitignore:], errs[fitignore:]))
    print p1
#    p.clf()

    p.plot(centers,fitfunc(p1[:],centers), 'y', linewidth=2.5, label='Fit powerlaw slope=%.1f' % p1[1])
    p.xlabel('Flux (Jy)')
    p.ylabel('Number of pulses')
    p.legend()
    p.axis([-170,430,0,500])
    p.show()

    hist = p.hist(meanflux, align='mid', histtype='bar', bins=hist[1], label='Beamforming', color='b')
    hist2 = p.hist(meanflux2, align='mid', histtype='step', linewidth=2.5, bins=hist[1], label='UV fit', color='y')
    centers2 = n.array([(hist2[1][i+1] + hist2[1][i])/2 for i in range(len(hist2[1])-1)])
    errs2 = 1+(n.sqrt(hist2[0] + 0.75))
    p.errorbar(centers2,hist2[0],yerr=errs2,fmt=None,ecolor='y', capsize=0)
    p12,success = opt.leastsq(errfunc, p0[:], args = (centers2[fitignore:], hist2[0][fitignore:], errs2[fitignore:]))

    hist3 = p.hist(meanflux3, align='mid', histtype='step', linewidth=2.5, bins=hist[1], label='Dirty Image', color='r')
    centers3 = n.array([(hist3[1][i+1] + hist3[1][i])/2 for i in range(len(hist3[1])-1)])
    errs3 = 1+(n.sqrt(hist3[0] + 0.75))
    p.errorbar(centers3,hist3[0],yerr=errs3,fmt=None,ecolor='r', capsize=0)
    p13,success = opt.leastsq(errfunc, p0[:], args = (centers3[fitignore:], hist3[0][fitignore:], errs3[fitignore:]))

    print 'bin center, completeness 1, 2, 3:'
    for i in range(len(centers)):
        print centers[i], hist[0][i]/fitfunc(p1[:],centers)[i], hist2[0][i]/fitfunc(p1[:],centers)[i], hist3[0][i]/fitfunc(p1[:],centers)[i]

#    p.plot(centers,fitfunc(p1[:],centers), 'y', label='Fit powerlaw slope=%.1f' % p1[1])
#    p.plot(centers2,fitfunc(p12[:],centers2), 'g', label='Best fit slope2=%.1f' % p12[1])
#    p.plot(centers3,fitfunc(p13[:],centers3), 'g', label='Best fit slope3=%.1f' % p13[1])
    p.xlabel('Flux (Jy)')
    p.ylabel('Number of pulses')
    p.legend()
    p.axis([-170,430,0,500])
    p.show()

elif mode == 'index':
    gauss = lambda amp, x, x0, sigma: amp * n.exp(-1./(2.*sigma**2)*(x-x0)**2)
    fitfunc = lambda p, x:  gauss(p[0], x, p[1], p[2])
    errfunc = lambda p, x, y, rms: ((y - fitfunc(p, x))/rms)**2
    p0 = [10,0,10]

    ind = (n.array( newsortar.tolist() )[:,2] )[good1]   # to select limited set of pulses
    print len(ind)
    hist = p.hist(ind, align='mid',bins=n.arange(-50,50,2))
    p.clf()
    centers = n.array([(hist[1][i+1] + hist[1][i])/2 for i in range(len(hist[1])-1)])
    errs = 1+(n.sqrt(hist[0] + 0.75))

    p1,success = opt.leastsq(errfunc, p0[:], args = (centers, hist[0], errs))
    print 'model', p1

    hist = p.hist(ind, align='mid', bins=hist[1], label='Observed')
    p.errorbar(centers,hist[0],yerr=errs,fmt=None,ecolor='b', capsize=0)
    p.plot(centers,fitfunc(p1[:],centers), 'y', linewidth=2.5, label='Best-fit Gaussian')
    p.legend()
    p.xlabel('Spectral index')
    p.ylabel('Number of pulses')
    p.show()
