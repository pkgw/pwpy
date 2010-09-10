#!/usr/bin/python
#Mattieu de Villiers mattieu@ska.ac.za 10 May 2010
import sys
import commands
import optparse
import pickle
import numpy
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab


# ================================ Helper functions ================================
def ensurepathformat(outputpath):
	if len(outputpath):
		if outputpath[-1]!='/':
			outputpath+='/'
	return outputpath

#loads pointing information
def LoadPointingInfo(outputpath):
	tmplog=commands.getstatusoutput('ls %spointinginfo' % (outputpath))
	if (tmplog[0]):
		return []
	results=open('%spointinginfo' % (outputpath), 'rb')
	RA=pickle.load(results)
	DEC=pickle.load(results)
	RAoffset=pickle.load(results)
	DECoffset=pickle.load(results)
	AZ=pickle.load(results)
	EL=pickle.load(results)
	CHI=pickle.load(results)
	LST=pickle.load(results)
	starttime=pickle.load(results)
	stoptime=pickle.load(results)
	utstarttime=pickle.load(results)
	utstoptime=pickle.load(results)
	freq=pickle.load(results)
	nant=pickle.load(results)
	results.close()
	return RA,DEC,RAoffset,DECoffset,AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime,freq,nant

#loads leakages and IQUV results
def readresults(outputpath):
	results=open('%sresults' % (outputpath), 'rb')
	leakageX=pickle.load(results)
	leakageY=pickle.load(results)
	peakIQUV=pickle.load(results)
	noiseIQUV=pickle.load(results)
	convergeFail=pickle.load(results)
	nactiveAntennas=pickle.load(results)
	
	npointings=len(leakageX)
	nfreq=len(leakageX[0])
	nant=len(leakageX[0][0])
	
	validant=[];
	maxleakant=[];
	avgabsleakant=[];
	for iant in range(nant):
		fleakageX=numpy.array(range(nfreq),dtype='complex')
		fleakageY=numpy.array(range(nfreq),dtype='complex')
		firstfinitepiece=-1
		for ifreq in range(nfreq):
			fleakageX[ifreq]=leakageX[0][ifreq][iant];
			fleakageY[ifreq]=leakageY[0][ifreq][iant];
			if ((firstfinitepiece<0)&(numpy.isfinite(fleakageX[ifreq]))&(numpy.isfinite(fleakageY[ifreq]))&(~((fleakageX[ifreq]==0.0)&(fleakageY[ifreq]==0.0)))):
				firstfinitepiece=ifreq
		if (firstfinitepiece<0):
			continue
		validant.append(iant+1)
		maxleakant.append(max([max(abs(fleakageX)),max(abs(fleakageY))]))
		avgabsleakant.append(numpy.mean([numpy.mean(abs(fleakageX)),numpy.mean(abs(fleakageY))]))
		
	print "Valid antennas: ",validant
	print "Max abs leakage:",maxleakant
	print "Mean abs leakage:",avgabsleakant
	if len(maxleakant):
		print "Max abs leakage:",max(maxleakant)
	else:
		print "Max abs leakage: inf"
	print "Mean abs leakage:",numpy.mean(avgabsleakant)
	npointingswithfailures=0
	npieceswithfailures=[]
	for point in range(npointings):
		if (numpy.sum(convergeFail[point])>0):
			npieceswithfailures.append(numpy.sum(numpy.array(convergeFail[point])>0))
	
	print "Number of pointings with calibration failures: %d" %(len(npieceswithfailures))
	if (len(npieceswithfailures)==0):
		print "Maximum pieces per pointing failed: %d" % (0)
		print "Total pieces failed: %d" % (0)
	else:
		print "Maximum pieces per pointing failed: %d" % (numpy.max(npieceswithfailures))
		print "Total pieces failed: %d" % (numpy.sum(npieceswithfailures))
	return leakageX, leakageY, peakIQUV, noiseIQUV, convergeFail, nactiveAntennas, validant


def readepsilonzeta(outputpath):
	results=open('%sepsilonzeta' % (outputpath), 'rb')
	xx=pickle.load(results)
	yy=pickle.load(results)
	epsilonzeta=pickle.load(results)
	results.close()
	return xx,yy,epsilonzeta	

def plotPattern(title, az, el, E, plt, useSinCoords=False, addLines=True, levels=None):
    """Plot beam pattern as filled contour plot in dBs.
    
    The beam pattern should be real-valued, but may contain negative parts.
    These are indicated by dashed contours. This function can therefore plot
    generic single-dish Stokes parameters. To plot voltage patterns, let E be
    the squared magnitude of the pattern.
    
    Parameters
    ----------
    title : string
        Figure title
    az : real array, shape (numPixels)
        Vector of azimuth coordinates, in degrees
    el : real array, shape (numPixels)
        Vector of elevation coordinates, in degrees
    E : real array, shape (numPixels, numPixels)
        Beam pattern (in units of power) as a function of (az, el)
    useSinCoords : bool
        True if coordinates should be converted to sine values
    addLines : bool, optional
        True if contour lines should be added to plot
    levels : sequence of floats, optional
        Contour levels to plot, in dB below the peak beam response (default
        is -60 dB to 0 dB in 3 dB steps, i.e. ``np.linspace(-60., 0., 21)``)

    """
    np=numpy
    # Crude corner cutouts to indicate region outside spherical projection
    quadrant = np.linspace(0.0, np.pi / 2.0, 401)
    corner_az = np.concatenate([np.cos(quadrant), [1.0, 1.0]])
    corner_el = np.concatenate([np.sin(quadrant), [1.0, 0.0]])
    if not useSinCoords:
        corner_az, corner_el = 90.0 * corner_az, 90.0 * corner_el
    if useSinCoords:
        x, y = np.sin(az * np.pi / 180.0), np.sin(el * np.pi / 180.0)
    else:
        x, y = az, el
    if levels is None:
#        levels = np.linspace(-60.0, 0.0, 21)
		levels = np.linspace(-40.0, 0.0, 17)
#    	levels = np.linspace(-40.0, -10.0, 16)
    # Transpose the data for plotting purposes, so that rows of E correspond to y and columns of E correspond to x
    E = E.transpose()
    E_dB = 10.0 * np.log10(np.abs(E))
    # Remove -infs (keep above lowest contour level to prevent white patches in contourf)
    E_dB[E_dB < levels.min() + 0.01] = levels.min() + 0.01
    # Also keep below highest contour level for the same reason
    E_dB[E_dB > levels.max() - 0.01] = levels.max() - 0.01
    
    cset = plt.contourf(x, y, E_dB, levels)
    matplotlib.rc('contour', negative_linestyle='solid')
    if addLines:
        # Positive beam patterns are straightforward
        if E.min() >= 0.0:
            plt.contour(x, y, E_dB, levels, colors='k', linewidths=0.5)
        else:
            # Indicate positive parts with solid contours
            E_dB_pos = E_dB.copy()
            E_dB_pos[E < 0.0] = levels.min() + 0.01
            plt.contour(x, y, E_dB_pos, levels, colors='k', linewidths=0.5)
            # Indicate negative parts with dashed contours
            E_dB_neg = E_dB.copy()
            E_dB_neg[E > 0.0] = levels.min() + 0.01
            matplotlib.rc('contour', negative_linestyle='dashed')
            plt.contour(x, y, E_dB_neg, levels, colors='k', linewidths=0.5)
    if useSinCoords:
        plt.xlabel(r'sin $\theta$ sin $\phi$')
        plt.ylabel(r'sin $\theta$ cos $\phi$')
    else:
        plt.xlabel('az (deg)')
        plt.ylabel('el (deg)')
    for ticklabel in plt.xticks()[1] + plt.yticks()[1]:
        ticklabel.set_size('small')
    plt.title(title)
    plt.axis('image')
    plt.fill(corner_az, corner_el, facecolor='w')
    plt.fill(-corner_az, corner_el, facecolor='w')
    plt.fill(-corner_az, -corner_el, facecolor='w')
    plt.fill(corner_az, -corner_el, facecolor='w')
    return cset

#
def mygriddata(xx,yy,zz,xgrid,ygrid):
	if 1:
		org=mlab.find((xx==0.0) & (yy==0.0))
		norg=len(org)
		if (norg):
			corg=mlab.find(((xx!=0.0) | (yy!=0.0)))
			ndata=len(xx)
			nz=range(ndata-norg+1);
			nx=range(ndata-norg+1);
			ny=range(ndata-norg+1);
			nz[0]=zz[org].mean()
			nx[0]=0
			ny[0]=0
			nz[1:]=zz[corg]
			nx[1:]=xx[corg]
			ny[1:]=yy[corg]
			return mlab.griddata(nx,ny,nz,xgrid,ygrid)
			
#	return mlab.griddata(xx+0.000001*numpy.random.rand(len(xx)),yy+0.000001*numpy.random.rand(len(xx)),zz,xgrid,ygrid)
	return mlab.griddata(xx,yy,zz,xgrid,ygrid)


# ================================ Main function ================================
# Parse command-line options and arguments
parser = optparse.OptionParser(usage="%prog [options] path",
                               description="Plots the calibration or performance results \
                                            stored at a given path. Either leakages are plotted at a specified\
											pointing; or leakages for different pointings for the specified antenna\
											is plotted. Without specified options, the stokes I,Q,U,V results are plotted.")
parser.set_defaults(freqchannels=-1)
parser.add_option("-f", "--frequency", dest="freqchannels", type=int, \
              	help="frequency channel, default is all")
(options, args) = parser.parse_args()

#if len(args) < 1:
#	parser.error("Please specify path")

#outputpath=ensurepathformat(args[0])
#plotmap(outputpath,options.freqchannels)
[xx,yy,ez]=readepsilonzeta('crossap0T8a1/')
[xx,yy,ezs7]=readepsilonzeta('crossap0T8a1s1_7/')
[xx,yy,ezs23]=readepsilonzeta('crossap0T8a1s1_23/')
[xx,yy,ezs7_23]=readepsilonzeta('crossap0T8a1s2_7_23/')
[xx,yy,ezs14]=readepsilonzeta('crossap0T8a1s14A/') #valid antennas:[1, 3, 7, 11, 13, 17, 23, 25, 27, 29, 31, 33, 35, 39]
[xx,yy,ezs15]=readepsilonzeta('crossap0T8a1s15A/') #valid antennas:[1, 3, 7, 11, 13, 17, 23, 25, 29, 31, 33, 35, 39]
[xx,yy,ezs16]=readepsilonzeta('crossap0T8a1s16A/') #Valid antennas:[1, 3, 11, 13, 17, 23, 25, 29, 31, 33, 35, 39]
[xx,yy,ezs15C]=readepsilonzeta('crossap0T8a1s15C/')#Valid antennas:[1, 3, 7, 11, 13, 17, 25, 27, 29, 31, 33, 35, 39]
[xx,yy,ezs16C]=readepsilonzeta('crossap0T8a1s16C/')#Valid antennas:[1, 3, 11, 13, 17, 25, 27, 29, 31, 33, 35, 39]

nant=28
ez7=ez*nant-ezs7*(nant-1)
ez23=ez*nant-ezs23*(nant-1)
testez=(ezs7_23*(nant-2)+ez7+ez23)/(nant)
test7_23=(ez*nant-ezs7-ez23)/(nant-2)

#tests15=ezs14*14+ezs
ez7_h=ezs15*13.0-ezs16*12.0
ez23_C=ezs14*14.0-ezs15C*13.0
ez7_C=ezs15C*13.0-ezs16C*12.0

#epsilonzetacnt=testez
epsilonzetacnt=ez7_C
purelabels=['e.pp','e.np','z.np','z.pp','e.nn*j','z.pn*j','z.nn*j']
method='fitevenless'
factor=10
maxextent=max(max(xx),max(yy))
xgrid=maxextent*numpy.linspace(-1,1,200)
ygrid=maxextent*numpy.linspace(-1,1,200)
outputpath='antenna7_C/'
fig=plt.figure(1)
fig.set_size_inches(5.5,4)
zgrid=mygriddata(xx,yy,(numpy.array(epsilonzetacnt[0])),xgrid,ygrid)
plt.imshow(zgrid,extent=[-maxextent,maxextent,-maxextent,maxextent],vmin=numpy.min(numpy.min(zgrid)),vmax=numpy.max(numpy.max(zgrid)),origin='lower')
plt.imshow(zgrid,extent=[-maxextent,maxextent,-maxextent,maxextent],vmin=0.7,vmax=1,origin='lower')
plt.colorbar()
plt.title('%s e.pp, %s, f=%g'%(outputpath[:-1],method,factor))
a=plt.gca()
a.set(xlabel='az (hpp)',ylabel='el (hpp)')
plt.savefig('%smap%s_epp_%.2f.png'%(outputpath,method,factor))

fig=plt.figure(2)
plt.clf()
for iez in range(6):
	zgrid=mygriddata(xx,yy,(numpy.array(epsilonzetacnt[iez+1])),xgrid,ygrid)
	zgrid=zgrid*2
	plt.figure(2)
	a=plt.subplot(1,6,iez+1)
#			plt.imshow(zgrid,extent=[-maxextent,maxextent,-maxextent,maxextent],vmin=numpy.min(numpy.min(zgrid)),vmax=numpy.max(numpy.max(zgrid)),origin='lower')
#			plt.colorbar()
			
	cset=plotPattern('', xgrid, ygrid, zgrid.transpose(), plt)
	for tick in a.xaxis.majorTicks:
		tick.label.set_fontsize('small')			
	plt.title('%s' % (purelabels[iez+1]))
	a.set(xlabel='az (hpp)')
	if (iez>0):
		a.set(ylabel='', yticks=[])
	else:
		a.set(ylabel='el (hpp)')
		for tick in a.yaxis.majorTicks:
			tick.label.set_fontsize('small')			
plt.gcf().text(0.5, 0.9, '%s epsilon zeta maps, %s, f=%g' % (outputpath[:-1],method,factor), ha='center', size='x-large')
plt.subplots_adjust(left=0.07, right=0.9, bottom=0.02, top=0.9, wspace=0.05, hspace=0.05)
if (cset):
	plt.colorbar(cset, cax=plt.axes([0.92, 0.1, 0.02, 0.8]), format='%d')
	plt.gcf().text(0.97, 0.5, 'dB')
fig.set_size_inches(10,2.5)
plt.savefig('%smap%s_%.2f.png'%(outputpath,method,factor))

