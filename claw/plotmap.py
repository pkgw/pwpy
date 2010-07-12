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

def getrefpointing(outputpath):
	for ind in range((len(outputpath)-1),1,-1):
		if (outputpath[ind]=='p'):
			if ((outputpath[ind+2]=='T')|(outputpath[ind+2]=='f')|(outputpath[ind+2]=='E')):
				return int(outputpath[ind+1:ind+2])
			elif ((outputpath[ind+3]=='T')|(outputpath[ind+3]=='f')|(outputpath[ind+3]=='E')):
				return int(outputpath[ind+1:ind+3])
	return 0

#Casey's rotate to convert dra,ddec to az,el
def rotate(RAoffset,DECoffset,PARANG):
	ANG=PARANG*numpy.pi/180.0
	xx=-RAoffset*numpy.cos(ANG)+DECoffset*numpy.sin(ANG)
	yy=RAoffset*numpy.sin(ANG)+DECoffset*numpy.cos(ANG)
	return xx,yy

#period=360 or 2*pi
#unwrapped=(angle+0.5*period) % period -0.5*period

#calculate epsilon, zetas at x,y
#def solve(x,y,I_true,Q_true,U_true,V_true,I_harpoon,Q_harpoon,U_harpoon,V_harpoon,xx,yy,chi):
#assumes xx,yy in units of fraction of half power point
def solvezetaepsilon(x,y,I,Q,U,V,I_harpoon,Q_harpoon,U_harpoon,V_harpoon,xx,yy,chi,maxextent,sigma):
	ndata=len(chi)
	w=numpy.exp(-0.5*((xx-x)**2+(yy-y)**2)/(sigma)**2)
	
	m=[w[c]*numpy.array([I_harpoon[c],Q_harpoon[c],U_harpoon[c],V_harpoon[c]]) for c in range(ndata)]
	m=numpy.array(m).reshape(4*ndata,1)
	
	X=[ w[c]*numpy.array(
	[[I,Q*numpy.cos(2.0*chi[c])+U*numpy.sin(2.0*chi[c]),0,U*numpy.cos(2.0*chi[c])-Q*numpy.sin(2.0*chi[c]),0,0,-V],
	  [Q,I*numpy.cos(2.0*chi[c]),U,-I*numpy.sin(2.0*chi[c]),-V*numpy.sin(2.0*chi[c]),-V*numpy.cos(2.0*chi[c]),0],
	  [U,I*numpy.sin(2.0*chi[c]),-Q,I*numpy.cos(2.0*chi[c]),V*numpy.cos(2.0*chi[c]),-V*numpy.sin(2.0*chi[c]),0],
	  [V,0,0,0,Q*numpy.sin(2.0*chi[c])-U*numpy.cos(2.0*chi[c]),Q*numpy.cos(2.0*chi[c])+U*numpy.sin(2.0*chi[c]),-I]]) for c in range(ndata)]
	X=numpy.array(X).reshape(4*ndata,7);
		
#	[I_harpoon;Q_harpoon;U_harpoon;V_harpoon]=
#	[[I,Q*cos(2*chi)+U*sin(2*chi),0,U*cos(2*chi)-Q*sin(2*chi),0,0,-V],
#	 [Q,I*cos(2*chi),U,-I*sin(2*chi),-V*sin(2*chi),-V*cos(2*chi),0],
#	 [U,I*sin(2*chi),-Q,I*cos(2*chi),V*cos(2*chi),-V*sin(2*chi),0],
#	 [V,0,0,0,Q*sin(2*chi)-U*cos(2*chi),Q*cos(2*chi)+U*sin(2*chi),-I]]
#	[1/2*epsilon_pp+1;
#	 1/2*epsilon_np;
#	 1/2*zeta_np;
#	 1/2*zeta_pp;
#	 1/2*epsilon_nn*j;
#	 1/2*zeta_pn*j;
#	 1/2*zeta_nn*j]

	
#	m=X*u
#	u_best=pinv(X)*m
#	W*m=W*X*u;
#	u_best=pinv(W*X)*W*m
	#gathering weighting terms based on position
	#if matrix W use
	#epsilon_zeta=numpy.dot(numpy.linalg.pinv(numpy.dot(W,X)),numpy.dot(W,m))
	#if vector w, use	
	#epsilon_zeta=numpy.dot(numpy.linalg.pinv((w*X.transpose()).transpose()),(w*m))
	epsilon_zeta=numpy.dot(numpy.linalg.pinv(X),m)
#	epsilon_zeta[0]=epsilon_zeta[0]-1
	return numpy.array(epsilon_zeta).reshape(7,)


#fits epsilon zeta to smooth surface of form a[0]*x^2+a[1]*x+a[2]*x*y+a[3]*y+a[4]*y^2+a[5]
#then evaluate epsilon zetas at given location
def solvefitzetaepsilon(x,y,I,Q,U,V,I_harpoon,Q_harpoon,U_harpoon,V_harpoon,xx,yy,chi,maxextent,sigma):
	ndata=len(chi)
	w=numpy.exp(-0.5*(numpy.sqrt((xx-x)**2+(yy-y)**2))/(sigma)**2)
	
	m=[w[c]*numpy.array([I_harpoon[c],Q_harpoon[c],U_harpoon[c],V_harpoon[c]]) for c in range(ndata)]
	m=numpy.array(m).reshape(4*ndata,1)
	
	range06=numpy.array(range(0,6))
	X=numpy.zeros([4*ndata,7*ndata])
	XY=numpy.zeros([7*ndata,6*7])
	for c in range(ndata):
		X[4*c][(7*c):(7*c+7)]=w[c]*numpy.array([I,Q*numpy.cos(2.0*chi[c])+U*numpy.sin(2.0*chi[c]),0,U*numpy.cos(2.0*chi[c])-Q*numpy.sin(2.0*chi[c]),0,0,-V])
		X[4*c+1][(7*c):(7*c+7)]=w[c]*numpy.array([Q,I*numpy.cos(2.0*chi[c]),U,-I*numpy.sin(2.0*chi[c]),-V*numpy.sin(2.0*chi[c]),-V*numpy.cos(2.0*chi[c]),0])
		X[4*c+2][(7*c):(7*c+7)]=w[c]*numpy.array([U,I*numpy.sin(2.0*chi[c]),-Q,I*numpy.cos(2.0*chi[c]),V*numpy.cos(2.0*chi[c]),-V*numpy.sin(2.0*chi[c]),0])
		X[4*c+3][(7*c):(7*c+7)]=w[c]*numpy.array([V,0,0,0,Q*numpy.sin(2.0*chi[c])-U*numpy.cos(2.0*chi[c]),Q*numpy.cos(2.0*chi[c])+U*numpy.sin(2.0*chi[c]),-I])		
		XY[7*c+0][6*0+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*epp+1
		XY[7*c+1][6*1+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*enp
		XY[7*c+2][6*2+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*znp
		XY[7*c+3][6*3+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*zpp
		XY[7*c+4][6*4+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*ennj
		XY[7*c+5][6*5+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*zpnj
		XY[7*c+6][6*6+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*znnj

	X=numpy.array(X)
	XY=numpy.array(XY)
#	W*m=W*X*XY*A
#	m=X*XY*A
#   A=pinv(X*XY)*m
#a[0]*x^2+a[1]*x+a[2]*x*y+a[3]*y+a[4]*y^2+a[5]
	#A=numpy.zeros(6*7)
	#A=[a0epp,a1epp,a2epp,a3epp,a4epp,a5epp, a0enp,a1enp,a2enp,a3enp,a4enp,a5enp,  a0ezp,a1ezp,a2ezp,a3ezp,a4ezp,a5ezp,...]'
	A=numpy.dot(numpy.linalg.pinv(numpy.dot(X,XY)),m)
	#now evaluate A at x,y
	thisXY=numpy.zeros([7,6*7])
	thisXY[0][6*0+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*epp+1
	thisXY[1][6*1+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*enp
	thisXY[2][6*2+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*znp
	thisXY[3][6*3+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*zpp
	thisXY[4][6*4+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*ennj
	thisXY[5][6*5+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*zpnj
	thisXY[6][6*6+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*znnj
	epsilon_zeta=numpy.dot(thisXY,A)


#	[I_harpoon;Q_harpoon;U_harpoon;V_harpoon]=
#	[[I,Q*cos(2*chi)+U*sin(2*chi),0,U*cos(2*chi)-Q*sin(2*chi),0,0,-V],
#	 [Q,I*cos(2*chi),U,-I*sin(2*chi),-V*sin(2*chi),-V*cos(2*chi),0],
#	 [U,I*sin(2*chi),-Q,I*cos(2*chi),V*cos(2*chi),-V*sin(2*chi),0],
#	 [V,0,0,0,Q*sin(2*chi)-U*cos(2*chi),Q*cos(2*chi)+U*sin(2*chi),-I]]
#	[1/2*epsilon_pp+1;
#	 1/2*epsilon_np;
#	 1/2*zeta_np;
#	 1/2*zeta_pp;
#	 1/2*epsilon_nn*j;
#	 1/2*zeta_pn*j;
#	 1/2*zeta_nn*j]
#becomes
#mIQUV[4*ndata,1]
#[I_harpoon;Q_harpoon;U_harpoon;V_harpoon]
#[I_harpoon;Q_harpoon;U_harpoon;V_harpoon]
#[I_harpoon;Q_harpoon;U_harpoon;V_harpoon]
#=
#X[4(iquv)*ndata,7(epsilonzeta)]
#[[I,Q*cos(2*chi)+U*sin(2*chi),0,U*cos(2*chi)-Q*sin(2*chi),0,0,-V],
#	 [Q,I*cos(2*chi),U,-I*sin(2*chi),-V*sin(2*chi),-V*cos(2*chi),0],
#	 [U,I*sin(2*chi),-Q,I*cos(2*chi),V*cos(2*chi),-V*sin(2*chi),0],
#	 [V,0,0,0,Q*sin(2*chi)-U*cos(2*chi),Q*cos(2*chi)+U*sin(2*chi),-I]]
#[[I,Q*cos(2*chi)+U*sin(2*chi),0,U*cos(2*chi)-Q*sin(2*chi),0,0,-V],
#	 [Q,I*cos(2*chi),U,-I*sin(2*chi),-V*sin(2*chi),-V*cos(2*chi),0],
#	 [U,I*sin(2*chi),-Q,I*cos(2*chi),V*cos(2*chi),-V*sin(2*chi),0],
#	 [V,0,0,0,Q*sin(2*chi)-U*cos(2*chi),Q*cos(2*chi)+U*sin(2*chi),-I]]
#[[I,Q*cos(2*chi)+U*sin(2*chi),0,U*cos(2*chi)-Q*sin(2*chi),0,0,-V],
#	 [Q,I*cos(2*chi),U,-I*sin(2*chi),-V*sin(2*chi),-V*cos(2*chi),0],
#	 [U,I*sin(2*chi),-Q,I*cos(2*chi),V*cos(2*chi),-V*sin(2*chi),0],
#	 [V,0,0,0,Q*sin(2*chi)-U*cos(2*chi),Q*cos(2*chi)+U*sin(2*chi),-I]]
#
#a[0]*x^2+a[1]*x+a[2]*x*y+a[3]*y+a[4]*y^2+a[5]
#[xx x xy y yy 1]  [a0_epp,a0_enp,a0_znp,a0_zpp,a0_enn,a0_zpn,a0_znn]
#[xx x xy y yy 1]*[a1_epp,a1_enp,a1_znp,a1_zpp,a1_enn,a1_zpn,a1_znn]
#[xx x xy y yy 1] [a2_epp,a2_enp,a2_znp,a2_zpp,a2_enn,a2_zpn,a2_znn]
#[xx x xy y yy 1] [a3_epp,a3_enp,a3_znp,a3_zpp,a3_enn,a3_zpn,a3_znn]

#xxyy[4*ndata,6]*A[6,7] gives [4*ndata,7] which is [zeta epsilon values at each data point]





	
#	m=X*u
#	u_best=pinv(X)*m
#	W*m=W*X*u;
#	u_best=pinv(W*X)*W*m
	#gathering weighting terms based on position
	#if matrix W use
	#epsilon_zeta=numpy.dot(numpy.linalg.pinv(numpy.dot(W,X)),numpy.dot(W,m))
	#if vector w, use	
	#epsilon_zeta=numpy.dot(numpy.linalg.pinv((w*X.transpose()).transpose()),(w*m))
#	epsilon_zeta=numpy.dot(numpy.linalg.pinv(X),m)
	return numpy.array(epsilon_zeta).reshape(7,)

#
#fits epsilon zeta to smooth surface of form a[0]*x^2+a[1]*x+a[2]*x*y+a[3]*y+a[4]*y^2+a[5]
#then evaluate epsilon zetas at given location
def solvefitlinearzetaepsilon(x,y,I,Q,U,V,I_harpoon,Q_harpoon,U_harpoon,V_harpoon,xx,yy,chi,maxextent,sigma):
	ndata=len(chi)
	w=numpy.exp(-0.5*(numpy.sqrt((xx-x)**2+(yy-y)**2))/(sigma)**2)
	
	m=[w[c]*numpy.array([I_harpoon[c],Q_harpoon[c],U_harpoon[c],V_harpoon[c]]) for c in range(ndata)]
	m=numpy.array(m).reshape(4*ndata,1)
	
	range03=numpy.array(range(0,3))
	X=numpy.zeros([4*ndata,7*ndata])
	XY=numpy.zeros([7*ndata,3*7])
	for c in range(ndata):
		X[4*c][(7*c):(7*c+7)]=w[c]*numpy.array([I,Q*numpy.cos(2.0*chi[c])+U*numpy.sin(2.0*chi[c]),0,U*numpy.cos(2.0*chi[c])-Q*numpy.sin(2.0*chi[c]),0,0,-V])
		X[4*c+1][(7*c):(7*c+7)]=w[c]*numpy.array([Q,I*numpy.cos(2.0*chi[c]),U,-I*numpy.sin(2.0*chi[c]),-V*numpy.sin(2.0*chi[c]),-V*numpy.cos(2.0*chi[c]),0])
		X[4*c+2][(7*c):(7*c+7)]=w[c]*numpy.array([U,I*numpy.sin(2.0*chi[c]),-Q,I*numpy.cos(2.0*chi[c]),V*numpy.cos(2.0*chi[c]),-V*numpy.sin(2.0*chi[c]),0])
		X[4*c+3][(7*c):(7*c+7)]=w[c]*numpy.array([V,0,0,0,Q*numpy.sin(2.0*chi[c])-U*numpy.cos(2.0*chi[c]),Q*numpy.cos(2.0*chi[c])+U*numpy.sin(2.0*chi[c]),-I])		
		XY[7*c+0][3*0+range03]=[xx[c], yy[c], 1]#1/2*epp+1
		XY[7*c+1][3*1+range03]=[xx[c], yy[c], 1]#1/2*enp
		XY[7*c+2][3*2+range03]=[xx[c], yy[c], 1]#1/2*znp
		XY[7*c+3][3*3+range03]=[xx[c], yy[c], 1]#1/2*zpp
		XY[7*c+4][3*4+range03]=[xx[c], yy[c], 1]#1/2*ennj
		XY[7*c+5][3*5+range03]=[xx[c], yy[c], 1]#1/2*zpnj
		XY[7*c+6][3*6+range03]=[xx[c], yy[c], 1]#1/2*znnj

	X=numpy.array(X)
	XY=numpy.array(XY)
#	W*m=W*X*XY*A
#	m=X*XY*A
#   A=pinv(X*XY)*m
#a[0]*x^2+a[1]*x+a[2]*x*y+a[3]*y+a[4]*y^2+a[5]
	#A=numpy.zeros(3*7)
	#A=[a0epp,a1epp,a2epp, a0enp,a1enp,a2enp, a0ezp,a1ezp,a2ezp, ...]'
	A=numpy.dot(numpy.linalg.pinv(numpy.dot(X,XY)),m)
	#now evaluate A at x,y
	thisXY=numpy.zeros([7,3*7])
	thisXY[0][3*0+range03]=[x,y, 1]#1/2*epp+1
	thisXY[1][3*1+range03]=[x,y, 1]#1/2*enp
	thisXY[2][3*2+range03]=[x,y, 1]#1/2*znp
	thisXY[3][3*3+range03]=[x,y, 1]#1/2*zpp
	thisXY[4][3*4+range03]=[x,y, 1]#1/2*ennj
	thisXY[5][3*5+range03]=[x,y, 1]#1/2*zpnj
	thisXY[6][3*6+range03]=[x,y, 1]#1/2*znnj
	epsilon_zeta=numpy.dot(thisXY,A)
	return numpy.array(epsilon_zeta).reshape(7,)


#
#fits epsilon zeta to smooth surface of form a[0]*x^2+a[1]*x+a[2]*x*y+a[3]*y+a[4]*y^2+a[5]
#except e_nn and z_pn are modeled as planes only!
#then evaluate epsilon zetas at given location
def solvefitlesszetaepsilon(x,y,I,Q,U,V,I_harpoon,Q_harpoon,U_harpoon,V_harpoon,xx,yy,chi,maxextent,sigma):
	ndata=len(chi)
	w=numpy.exp(-0.5*(numpy.sqrt((xx-x)**2+(yy-y)**2))/(sigma)**2)
	
	m=[w[c]*numpy.array([I_harpoon[c],Q_harpoon[c],U_harpoon[c],V_harpoon[c]]) for c in range(ndata)]
	m=numpy.array(m).reshape(4*ndata,1)
	
	range06=numpy.array(range(0,6))
	range03=numpy.array(range(0,3))
	X=numpy.zeros([4*ndata,7*ndata])
	XY=numpy.zeros([7*ndata,6*7-2*3])
	for c in range(ndata):
		X[4*c][(7*c):(7*c+7)]=w[c]*numpy.array([I,Q*numpy.cos(2.0*chi[c])+U*numpy.sin(2.0*chi[c]),0,U*numpy.cos(2.0*chi[c])-Q*numpy.sin(2.0*chi[c]),0,0,-V])
		X[4*c+1][(7*c):(7*c+7)]=w[c]*numpy.array([Q,I*numpy.cos(2.0*chi[c]),U,-I*numpy.sin(2.0*chi[c]),-V*numpy.sin(2.0*chi[c]),-V*numpy.cos(2.0*chi[c]),0])
		X[4*c+2][(7*c):(7*c+7)]=w[c]*numpy.array([U,I*numpy.sin(2.0*chi[c]),-Q,I*numpy.cos(2.0*chi[c]),V*numpy.cos(2.0*chi[c]),-V*numpy.sin(2.0*chi[c]),0])
		X[4*c+3][(7*c):(7*c+7)]=w[c]*numpy.array([V,0,0,0,Q*numpy.sin(2.0*chi[c])-U*numpy.cos(2.0*chi[c]),Q*numpy.cos(2.0*chi[c])+U*numpy.sin(2.0*chi[c]),-I])		
		XY[7*c+0][6*0+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*epp+1
		XY[7*c+1][6*1+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*enp
		XY[7*c+2][6*2+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*znp
		XY[7*c+3][6*3+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*zpp
		XY[7*c+4][6*4+range03]=[xx[c], yy[c], 1]#1/2*ennj***
		XY[7*c+5][6*5-3+range03]=[xx[c], yy[c], 1]#1/2*zpnj***
		XY[7*c+6][6*6-6+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*znnj

	X=numpy.array(X)
	XY=numpy.array(XY)
#	W*m=W*X*XY*A
#	m=X*XY*A
#   A=pinv(X*XY)*m
#a[0]*x^2+a[1]*x+a[2]*x*y+a[3]*y+a[4]*y^2+a[5]
	#A=numpy.zeros(6*7)
	#A=[a0epp,a1epp,a2epp,a3epp,a4epp,a5epp, a0enp,a1enp,a2enp,a3enp,a4enp,a5enp,  a0ezp,a1ezp,a2ezp,a3ezp,a4ezp,a5ezp,...]'
	A=numpy.dot(numpy.linalg.pinv(numpy.dot(X,XY)),m)
	#now evaluate A at x,y
	thisXY=numpy.zeros([7,6*7-2*3])
	thisXY[0][6*0+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*epp+1
	thisXY[1][6*1+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*enp
	thisXY[2][6*2+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*znp
	thisXY[3][6*3+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*zpp
	thisXY[4][6*4+range03]=[x, y, 1]#1/2*ennj***
	thisXY[5][6*5-3+range03]=[x, y, 1]#1/2*zpnj***
	thisXY[6][6*6-6+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*znnj
	epsilon_zeta=numpy.dot(thisXY,A)

	return numpy.array(epsilon_zeta).reshape(7,)

#
#fits epsilon zeta to smooth surface of form a[0]*x^2+a[1]*x+a[2]*x*y+a[3]*y+a[4]*y^2+a[5]
#except e_nn and z_pn are modeled as planes only!
#then evaluate epsilon zetas at given location
def solvefitevenlesszetaepsilon(x,y,I,Q,U,V,I_harpoon,Q_harpoon,U_harpoon,V_harpoon,xx,yy,chi,maxextent,sigma):
	ndata=len(chi)
	w=numpy.exp(-0.5*(numpy.sqrt((xx-x)**2+(yy-y)**2))/(sigma)**2)
	
	m=[w[c]*numpy.array([I_harpoon[c],Q_harpoon[c],U_harpoon[c],V_harpoon[c]]) for c in range(ndata)]
	m=numpy.array(m).reshape(4*ndata,1)
	
	range06=numpy.array(range(0,6))
	range03=numpy.array(range(0,3))
	X=numpy.zeros([4*ndata,7*ndata])
	XY=numpy.zeros([7*ndata,6*7-2*5])
	for c in range(ndata):
		X[4*c][(7*c):(7*c+7)]=w[c]*numpy.array([I,Q*numpy.cos(2.0*chi[c])+U*numpy.sin(2.0*chi[c]),0,U*numpy.cos(2.0*chi[c])-Q*numpy.sin(2.0*chi[c]),0,0,-V])
		X[4*c+1][(7*c):(7*c+7)]=w[c]*numpy.array([Q,I*numpy.cos(2.0*chi[c]),U,-I*numpy.sin(2.0*chi[c]),-V*numpy.sin(2.0*chi[c]),-V*numpy.cos(2.0*chi[c]),0])
		X[4*c+2][(7*c):(7*c+7)]=w[c]*numpy.array([U,I*numpy.sin(2.0*chi[c]),-Q,I*numpy.cos(2.0*chi[c]),V*numpy.cos(2.0*chi[c]),-V*numpy.sin(2.0*chi[c]),0])
		X[4*c+3][(7*c):(7*c+7)]=w[c]*numpy.array([V,0,0,0,Q*numpy.sin(2.0*chi[c])-U*numpy.cos(2.0*chi[c]),Q*numpy.cos(2.0*chi[c])+U*numpy.sin(2.0*chi[c]),-I])		
		XY[7*c+0][6*0+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*epp+1
		XY[7*c+1][6*1+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*enp
		XY[7*c+2][6*2+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*znp
		XY[7*c+3][6*3+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*zpp
		XY[7*c+4][6*4]=1#1/2*ennj***
		XY[7*c+5][6*5-5]=1#1/2*zpnj***
		XY[7*c+6][6*6-10+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*znnj

	X=numpy.array(X)
	XY=numpy.array(XY)
#	W*m=W*X*XY*A
#	m=X*XY*A
#   A=pinv(X*XY)*m
#a[0]*x^2+a[1]*x+a[2]*x*y+a[3]*y+a[4]*y^2+a[5]
	#A=numpy.zeros(6*7)
	#A=[a0epp,a1epp,a2epp,a3epp,a4epp,a5epp, a0enp,a1enp,a2enp,a3enp,a4enp,a5enp,  a0ezp,a1ezp,a2ezp,a3ezp,a4ezp,a5ezp,...]'
	A=numpy.dot(numpy.linalg.pinv(numpy.dot(X,XY)),m)
	#now evaluate A at x,y
	thisXY=numpy.zeros([7,6*7-2*5])
	thisXY[0][6*0+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*epp+1
	thisXY[1][6*1+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*enp
	thisXY[2][6*2+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*znp
	thisXY[3][6*3+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*zpp
	thisXY[4][6*4]=1#1/2*ennj***
	thisXY[5][6*5-5]=1#1/2*zpnj***
	thisXY[6][6*6-10+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*znnj
	epsilon_zeta=numpy.dot(thisXY,A)

	return numpy.array(epsilon_zeta).reshape(7,)

#given measured IQUV values, parallactic angle and epsilon_zeta terms, calculate the true (estimated) IQUV values
#epsilon_zeta=[1/2*epsilon_pp+1;
#	 1/2*epsilon_np;
#	 1/2*zeta_np;
#	 1/2*zeta_pp;
#	 1/2*epsilon_nn*j;
#	 1/2*zeta_pn*j;
#	 1/2*zeta_nn*j]
#solves the equation:
#[I..harpoon;Q..harpoon;U..harpoon;V..harpoon]=
#[1/2*e.pp+1,1/2*(-z.pp*sin(2*chi)+e.np*cos(2*chi)),1/2*(z.pp*cos(2*chi)+e.np*sin(2*chi)),-1/2*z.nn*j;
#1/2*(-z.pp*sin(2*chi)+e.np*cos(2*chi)),1/2*e.pp+1,1/2*z.np,1/2*(-z.pn*cos(2*chi)-e.nn*sin(2*chi))*j;
#1/2*(z.pp*cos(2*chi)+e.np*sin(2*chi)),-1/2*z.np,1/2*e.pp+1,1/2*(-z.pn*sin(2*chi)+e.nn*cos(2*chi))*j;
#-1/2*z.nn*j,1/2*(z.pn*cos(2*chi)+e.nn*sin(2*chi))*j,1/2*(z.pn*sin(2*chi)-e.nn*cos(2*chi))*j,1/2*e.pp+1]
#*[I;Q;U;V]
def estimatetrueIQUV(I_harpoon,Q_harpoon,U_harpoon,V_harpoon,epsilon_zeta,chi):
	[he_pp1,he_np,hz_np,hz_pp,he_nnj,hz_pnj,hz_nnj]=epsilon_zeta
	#[1/2*e.pp+1,1/2*(-z.pp*sin(2*chi)+e.np*cos(2*chi)),1/2*(z.pp*cos(2*chi)+e.np*sin(2*chi)),-1/2*z.nn*j;
	#1/2*(-z.pp*sin(2*chi)+e.np*cos(2*chi)),1/2*e.pp+1,1/2*z.np,1/2*(-z.pn*cos(2*chi)-e.nn*sin(2*chi))*j;
	#1/2*(z.pp*cos(2*chi)+e.np*sin(2*chi)),-1/2*z.np,1/2*e.pp+1,1/2*(-z.pn*sin(2*chi)+e.nn*cos(2*chi))*j;
	#-1/2*z.nn*j,1/2*(z.pn*cos(2*chi)+e.nn*sin(2*chi))*j,1/2*(z.pn*sin(2*chi)-e.nn*cos(2*chi))*j,1/2*e.pp+1]
	EZ=numpy.array([[he_pp1,-hz_pp*numpy.sin(2.0*chi)+he_np*numpy.cos(2.0*chi),hz_pp*numpy.cos(2.0*chi)+he_np*numpy.sin(2.0*chi),-hz_nnj],
	[-hz_pp*numpy.sin(2.0*chi)+he_np*numpy.cos(2.0*chi),he_pp1,hz_np,-hz_pnj*numpy.cos(2.0*chi)-he_nnj*numpy.sin(2.0*chi)],
	[hz_pp*numpy.cos(2.0*chi)+he_np*numpy.sin(2.0*chi),-hz_np,he_pp1,-hz_pnj*numpy.sin(2.0*chi)+he_nnj*numpy.cos(2.0*chi)],
	[-hz_nnj,hz_pnj*numpy.cos(2.0*chi)+he_nnj*numpy.sin(2.0*chi),hz_pnj*numpy.sin(2.0*chi)-he_nnj*numpy.cos(2.0*chi),he_pp1]])
	IQUV_harpoon=numpy.array([I_harpoon,Q_harpoon,U_harpoon,V_harpoon]).reshape(4,1)
	IQUVestimated=numpy.dot(numpy.linalg.pinv(EZ),IQUV_harpoon)
	return IQUVestimated
	
def solvezetaepsilon6(x,y,I,Q,U,V,I_harpoon,Q_harpoon,U_harpoon,V_harpoon,xx,yy,chi,maxextent,sigma):
	ndata=len(chi)
	w=numpy.exp(-0.5*((xx-x)**2+(yy-y)**2)/(sigma)**2)
	w_for_epp1=numpy.exp(-0.5*((xx-x)**2+(yy-y)**2)/(0.1)**2)
	
#	epp1=(I_harpoon[c]*I-Q_harpoon[c]*Q-U_harpoon[c]*U-V_harpoon[c]*V)/(I**2-Q**2-U**2-V**2)
	wepp1=[w_for_epp1[c]*numpy.array((I_harpoon[c]*I-Q_harpoon[c]*Q-U_harpoon[c]*U-V_harpoon[c]*V)/(I**2-Q**2-U**2-V**2)) for c in range(ndata)]
	smoothepp1=numpy.sum(wepp1)/numpy.sum(w_for_epp1)
	
	m=[w[c]*numpy.array([I_harpoon[c]-I*(I_harpoon[c]*I-Q_harpoon[c]*Q-U_harpoon[c]*U-V_harpoon[c]*V)/(I**2-Q**2-U**2-V**2),Q_harpoon[c]-Q*(I_harpoon[c]*I-Q_harpoon[c]*Q-U_harpoon[c]*U-V_harpoon[c]*V)/(I**2-Q**2-U**2-V**2),U_harpoon[c]-U*(I_harpoon[c]*I-Q_harpoon[c]*Q-U_harpoon[c]*U-V_harpoon[c]*V)/(I**2-Q**2-U**2-V**2),V_harpoon[c]-V*(I_harpoon[c]*I-Q_harpoon[c]*Q-U_harpoon[c]*U-V_harpoon[c]*V)/(I**2-Q**2-U**2-V**2)]) for c in range(ndata)]
	m=numpy.array(m).reshape(4*ndata,1)
	
	X=[ w[c]*numpy.array(
	[[Q*numpy.cos(2.0*chi[c])+U*numpy.sin(2.0*chi[c]),0,U*numpy.cos(2.0*chi[c])-Q*numpy.sin(2.0*chi[c]),0,0,-V],
	  [I*numpy.cos(2.0*chi[c]),U,-I*numpy.sin(2.0*chi[c]),-V*numpy.sin(2.0*chi[c]),-V*numpy.cos(2.0*chi[c]),0],
	  [I*numpy.sin(2.0*chi[c]),-Q,I*numpy.cos(2.0*chi[c]),V*numpy.cos(2.0*chi[c]),-V*numpy.sin(2.0*chi[c]),0],
	  [0,0,0,Q*numpy.sin(2.0*chi[c])-U*numpy.cos(2.0*chi[c]),Q*numpy.cos(2.0*chi[c])+U*numpy.sin(2.0*chi[c]),-I]]) for c in range(ndata)]
	X=numpy.array(X).reshape(4*ndata,6);
		
#	[I_harpoon;Q_harpoon;U_harpoon;V_harpoon]=
#	[[I,Q*cos(2*chi)+U*sin(2*chi),0,U*cos(2*chi)-Q*sin(2*chi),0,0,-V],
#	 [Q,I*cos(2*chi),U,-I*sin(2*chi),-V*sin(2*chi),-V*cos(2*chi),0],
#	 [U,I*sin(2*chi),-Q,I*cos(2*chi),V*cos(2*chi),-V*sin(2*chi),0],
#	 [V,0,0,0,Q*sin(2*chi)-U*cos(2*chi),Q*cos(2*chi)+U*sin(2*chi),-I]]
#	[1/2*epsilon_pp+1;
#	 1/2*epsilon_np;
#	 1/2*zeta_np;
#	 1/2*zeta_pp;
#	 1/2*epsilon_nn*j;
#	 1/2*zeta_pn*j;
#	 1/2*zeta_nn*j]

	
#	m=X*u
#	u_best=pinv(X)*m
#	W*m=W*X*u;
#	u_best=pinv(W*X)*W*m
	#gathering weighting terms based on position
	#if matrix W use
	#epsilon_zeta=numpy.dot(numpy.linalg.pinv(numpy.dot(W,X)),numpy.dot(W,m))
	#if vector w, use	
	#epsilon_zeta=numpy.dot(numpy.linalg.pinv((w*X.transpose()).transpose()),(w*m))
	
#	epsilon_zeta=[1 numpy.dot(numpy.linalg.pinv(X),m)
	epsilon_zeta=range(7)
#	epsilon_zeta[0]=smoothepp1-1.0
	epsilon_zeta[0]=smoothepp1
	epsilon_zeta[1:]=numpy.dot(numpy.linalg.pinv(X),m)
	return numpy.array(epsilon_zeta)

#
#fits epsilon zeta to smooth surface of form a[0]*x^2+a[1]*x+a[2]*x*y+a[3]*y+a[4]*y^2+a[5]
#except e_nn and z_pn are modeled as planes only!
#then evaluate epsilon zetas at given location
def solve6fitlesszetaepsilon(x,y,I,Q,U,V,I_harpoon,Q_harpoon,U_harpoon,V_harpoon,xx,yy,chi,maxextent,sigma):
	ndata=len(chi)
	w=numpy.exp(-0.5*(numpy.sqrt((xx-x)**2+(yy-y)**2))/(sigma)**2)
	w_for_epp1=numpy.exp(-0.5*((xx-x)**2+(yy-y)**2)/(0.00001)**2)
	
#	epp1=(I_harpoon[c]*I-Q_harpoon[c]*Q-U_harpoon[c]*U-V_harpoon[c]*V)/(I**2-Q**2-U**2-V**2)
	wepp1=[w_for_epp1[c]*numpy.array((I_harpoon[c]*I-Q_harpoon[c]*Q-U_harpoon[c]*U-V_harpoon[c]*V)/(I**2-Q**2-U**2-V**2)) for c in range(ndata)]
	smoothepp1=numpy.sum(wepp1)/numpy.sum(w_for_epp1)
	
	m=[w[c]*numpy.array([I_harpoon[c]-I*(I_harpoon[c]*I-Q_harpoon[c]*Q-U_harpoon[c]*U-V_harpoon[c]*V)/(I**2-Q**2-U**2-V**2),Q_harpoon[c]-Q*(I_harpoon[c]*I-Q_harpoon[c]*Q-U_harpoon[c]*U-V_harpoon[c]*V)/(I**2-Q**2-U**2-V**2),U_harpoon[c]-U*(I_harpoon[c]*I-Q_harpoon[c]*Q-U_harpoon[c]*U-V_harpoon[c]*V)/(I**2-Q**2-U**2-V**2),V_harpoon[c]-V*(I_harpoon[c]*I-Q_harpoon[c]*Q-U_harpoon[c]*U-V_harpoon[c]*V)/(I**2-Q**2-U**2-V**2)]) for c in range(ndata)]
	m=numpy.array(m).reshape(4*ndata,1)

	range06=numpy.array(range(0,6))
	range03=numpy.array(range(0,3))
	X=numpy.zeros([4*ndata,6*ndata])
	XY=numpy.zeros([6*ndata,6*6-2*3])
	for c in range(ndata):
		X[4*c][(6*c):(6*c+6)]=w[c]*numpy.array([Q*numpy.cos(2.0*chi[c])+U*numpy.sin(2.0*chi[c]),0,U*numpy.cos(2.0*chi[c])-Q*numpy.sin(2.0*chi[c]),0,0,-V])
		X[4*c+1][(6*c):(6*c+6)]=w[c]*numpy.array([I*numpy.cos(2.0*chi[c]),U,-I*numpy.sin(2.0*chi[c]),-V*numpy.sin(2.0*chi[c]),-V*numpy.cos(2.0*chi[c]),0])
		X[4*c+2][(6*c):(6*c+6)]=w[c]*numpy.array([I*numpy.sin(2.0*chi[c]),-Q,I*numpy.cos(2.0*chi[c]),V*numpy.cos(2.0*chi[c]),-V*numpy.sin(2.0*chi[c]),0])
		X[4*c+3][(6*c):(6*c+6)]=w[c]*numpy.array([0,0,0,Q*numpy.sin(2.0*chi[c])-U*numpy.cos(2.0*chi[c]),Q*numpy.cos(2.0*chi[c])+U*numpy.sin(2.0*chi[c]),-I])		
		XY[6*c+0][6*0+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*enp
		XY[6*c+1][6*1+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*znp
		XY[6*c+2][6*2+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*zpp
		XY[6*c+3][6*3+range03]=[xx[c], yy[c], 1]#1/2*ennj***
		XY[6*c+4][6*4-3+range03]=[xx[c], yy[c], 1]#1/2*zpnj***
		XY[6*c+5][6*5-6+range06]=[xx[c]**2, xx[c], xx[c]*yy[c], yy[c], yy[c]**2, 1]#1/2*znnj

	X=numpy.array(X)
	XY=numpy.array(XY)
#	W*m=W*X*XY*A
#	m=X*XY*A
#   A=pinv(X*XY)*m
#a[0]*x^2+a[1]*x+a[2]*x*y+a[3]*y+a[4]*y^2+a[5]
	#A=numpy.zeros(6*7)
	#A=[a0epp,a1epp,a2epp,a3epp,a4epp,a5epp, a0enp,a1enp,a2enp,a3enp,a4enp,a5enp,  a0ezp,a1ezp,a2ezp,a3ezp,a4ezp,a5ezp,...]'
	A=numpy.dot(numpy.linalg.pinv(numpy.dot(X,XY)),m)
	#now evaluate A at x,y
	thisXY=numpy.zeros([6,6*6-2*3])
	thisXY[0][6*0+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*enp
	thisXY[1][6*1+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*znp
	thisXY[2][6*2+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*zpp
	thisXY[3][6*3+range03]=[x, y, 1]#1/2*ennj***
	thisXY[4][6*4-3+range03]=[x, y, 1]#1/2*zpnj***
	thisXY[5][6*5-6+range06]=[x**2, x, x*y, y, y**2, 1]#1/2*znnj

	epsilon_zeta=range(7)
	epsilon_zeta[0]=smoothepp1
	epsilon_zeta[1:]=numpy.dot(thisXY,A)

	return numpy.array(epsilon_zeta).reshape(7,)

#[0.5*e.pp+1,0.5*e.np,0.5*z.pp,-0.5*z.nn*j;
#0.5*e.np,0.5*e.pp+1,0.5*z.np,-0.5*z.pn*j;
#0.5*z.pp,-0.5*z.np,0.5*e.pp+1,0.5*e.nn*j;
#-0.5*z.nn*j,0.5*z.pn*j,-0.5*e.nn*j,0.5*e.pp+1]
#[[0,1,3,-6],[1,0,2,-5],[3,-2,0,4],[-6,5,-4,0]]
def plotMueller(title,epsilonzeta,maxextent):
	labels=['1/2*e.pp+1','1/2*e.np','1/2*z.np','1/2*z.pp','1/2*e.nn*j','1/2*z.pn*j','1/2*z.nn*j']
	mapping=[[0,1,3,-6],[1,0,2,-5],[3,-2,0,4],[-6,5,-4,0]]
	names=['I','Q','U','V']
	
	az=numpy.linspace(-maxextent,maxextent,len(epsilonzeta[0][0]))
	el=numpy.linspace(-maxextent,maxextent,len(epsilonzeta[0][0]))
	fig=plt.figure(1,dpi=100)
	plt.clf()
	plt.title('%s' % (outputpath[:-1]))
	cset=0
	vmin_=numpy.min(numpy.min(numpy.min(epsilonzeta)))
	vmax_=numpy.max(numpy.max(numpy.max(epsilonzeta)))
	for irow in range(4):
		for icol in range(4):
			a = plt.subplot(4, 4, icol+irow*4+1)				
#			a.set(xlabel='', xticks=[])
#			a.set_ylabel('I', rotation='horizontal')
			iez=numpy.abs(mapping[irow][icol])
			sg=1
			if (mapping[irow][icol]<0):
				iez=-mapping[irow][icol]
				sg=-1
			else:
				iez=mapping[irow][icol]
			cset=plotPattern('', az, el, (sg*epsilonzeta[iez]), plt)
#			plt.imshow((sg*epsilonzeta[iez]).transpose(),extent=[-maxextent,maxextent,-maxextent,maxextent],vmin=vmin_,vmax=vmax_,origin='lower')
			if (irow==3):
				a.set_xlabel(names[icol], rotation='horizontal')
			else:
				a.set(xlabel='', xticks=[])
			if (icol==0):
				a.set_ylabel(names[irow], rotation='horizontal')
			else:
				a.set(ylabel='', yticks=[])

	plt.gcf().text(0.5, 0.95, '%s Beam Mueller matrix %s' % (outputpath[:-1],title), ha='center', size='x-large')
	plt.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.9, wspace=0.05, hspace=0.05)
	if (cset):
		plt.colorbar(cset, cax=plt.axes([0.9, 0.1, 0.02, 0.8]), format='%d')
		plt.gcf().text(0.96, 0.5, 'dB')
	fig.set_size_inches((10.24, 7.68))
	plt.savefig('%smueller%s.png'%(outputpath,title))
	plt.clf()
	
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
	
def plotmap(outputpath):
	[RA,DEC,RAoffset,DECoffset,AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime,freq,nant]=LoadPointingInfo(outputpath)
	[leakageX,leakageY,peakIQUV,noiseIQUV,convergeFail,nactiveAntennas,validant]=readresults(outputpath)

	PARANG=numpy.array(CHI,dtype='double')-90.0 #parang=CHI-90

	npointings=len(peakIQUV)
	ntime=len(peakIQUV[0])
	nexplodedpieces=len(peakIQUV[0][0])
	
	x=range(npointings)
	II=[[0 for col in range(npointings)] for row in range(ntime)]
	QQ=[[0 for col in range(npointings)] for row in range(ntime)]
	UU=[[0 for col in range(npointings)] for row in range(ntime)]
	VV=[[0 for col in range(npointings)] for row in range(ntime)]
	mI=range(ntime*npointings)
	mQ=range(ntime*npointings)
	mU=range(ntime*npointings)
	mV=range(ntime*npointings)
	chi=range(ntime*npointings)
	xx=range(ntime*npointings)
	yy=range(ntime*npointings)
	dx=range(ntime*npointings)
	dy=range(ntime*npointings)
	odx=range(ntime*npointings)
	ody=range(ntime*npointings)
	e_pp=range(ntime*npointings)
	z_pp=range(ntime*npointings)
	e_np=range(ntime*npointings)
	colouring=['k','r','m','g','b','c','y','k','k','r','m','g','b','c','y','k','k','r','m','g','b','c','y','k','k','r','m','g','b','c','y','k']
	alphas=[1,1,1,1,1,1,1,0.5,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
		
	refpointing=getrefpointing(outputpath)

	I_true=0
	Q_true=0
	U_true=0
	V_true=0
	for itime in range(ntime):
		for pointing in range(npointings):
			Iacc=0
			Qacc=0
			Uacc=0
			Vacc=0			
			for explodedpiece in range(nexplodedpieces):
				Iacc=Iacc+peakIQUV[pointing][itime][explodedpiece][0]
				Qacc=Qacc+peakIQUV[pointing][itime][explodedpiece][1]
				Uacc=Uacc+peakIQUV[pointing][itime][explodedpiece][2]
				Vacc=Vacc+peakIQUV[pointing][itime][explodedpiece][3]
#				if (pointing==0):
#					print peakIQUV[pointing][itime][explodedpiece][0],peakIQUV[pointing][itime][explodedpiece][1],peakIQUV[pointing][itime][explodedpiece][2],peakIQUV[pointing][itime][explodedpiece][3]
			II[itime][pointing]=Iacc/nexplodedpieces
			QQ[itime][pointing]=Qacc/nexplodedpieces
			UU[itime][pointing]=Uacc/nexplodedpieces
			VV[itime][pointing]=Vacc/nexplodedpieces
		I_true=I_true+II[itime][0]
		Q_true=Q_true+QQ[itime][0]
		U_true=U_true+UU[itime][0]
		V_true=V_true+VV[itime][0]
#		print II[itime][0],QQ[itime][0],UU[itime][0],VV[itime][0]
	I_true=I_true/(ntime)
	Q_true=Q_true/(ntime)
	U_true=U_true/(ntime)
	V_true=V_true/(ntime)
	print 'Stokes IQUV: ',I_true,Q_true,U_true,V_true, ' f: ',freq
		
	cnt=0
	for itime in range(ntime):
		for pointing in range(npointings):
			[xx[cnt],yy[cnt]]=rotate(RAoffset[pointing],DECoffset[pointing],PARANG[pointing][itime])
			chi[cnt]=PARANG[pointing][itime]*numpy.pi/180.0
			I_harpoon=II[itime][pointing]
			Q_harpoon=QQ[itime][pointing]
			U_harpoon=UU[itime][pointing]
			V_harpoon=VV[itime][pointing]
			mI[cnt]=I_harpoon
			mQ[cnt]=Q_harpoon
			mU[cnt]=U_harpoon
			mV[cnt]=V_harpoon

			e_pp[cnt]=2.0*((I_harpoon*I_true-Q_harpoon*Q_true-U_harpoon*U_true-V_harpoon*V_true)/(I_true**2-Q_true**2-U_true**2-V_true**2)-1.0)
#			e_pp[cnt]=2.0*((I_true*I_harpoon-Q_true*Q_harpoon-U_true*U_harpoon)/(I_true**2-Q_true**2-U_true**2)-1.0)
			rad=numpy.sqrt(xx[cnt]**2+yy[cnt]**2)
	#		e_pp[cnt]=-4.0E-7*rad**2  #simple model
			e_pp_1=e_pp[cnt]/2.0+1.0;

			z_np=0
			z_pp[cnt]=(numpy.cos(2.0*chi[cnt])*(2*U_harpoon-2*(e_pp_1)*U_true+z_np*Q_true)-numpy.sin(2*chi[cnt])*(2*Q_harpoon-2*(e_pp_1)*Q_true-z_np*U_true))/I_true
			e_np[cnt]=(numpy.cos(2.0*chi[cnt])*(2*Q_harpoon-2*(e_pp_1)*Q_true-z_np*U_true)+numpy.sin(2*chi[cnt])*(2*U_harpoon-2*(e_pp_1)*U_true+z_np*Q_true))/I_true

			length=numpy.sqrt(z_pp[cnt]**2+e_np[cnt]**2)
			posangle=0.5*numpy.arctan2(z_pp[cnt],e_np[cnt])
			dx[cnt]=length*numpy.cos(posangle)
			dy[cnt]=length*numpy.sin(posangle)

			#the old way of normalizing and derotating heuristically
			length=numpy.sqrt((Q_harpoon/I_harpoon-QQ[itime][refpointing]/II[itime][refpointing])**2+(U_harpoon/I_harpoon-UU[itime][refpointing]/II[itime][refpointing])**2);
			posangle=0.5*numpy.arctan2(U_harpoon/I_harpoon-UU[itime][refpointing]/II[itime][refpointing],Q_harpoon/I_harpoon-QQ[itime][refpointing]/II[itime][refpointing])
			posangle=(posangle-chi[cnt])			
			odx[cnt]=length*numpy.cos(posangle)
			ody[cnt]=length*numpy.sin(posangle)

			cnt=cnt+1

	xx=0.5*numpy.array(xx)/1000.0*freq/3.14
	yy=0.5*numpy.array(yy)/1000.0*freq/3.14
	
	sz=50
	labels=['1/2*e.pp+1','1/2*e.np','1/2*z.np','1/2*z.pp','1/2*e.nn*j','1/2*z.pn*j','1/2*z.nn*j']
	purelabels=['e.pp','e.np','z.np','z.pp','e.nn*j','z.pn*j','z.nn*j']
	
	maxextent=max(max(xx),max(yy))
	xax=numpy.linspace(-maxextent,maxextent,sz)
	yax=numpy.linspace(-maxextent,maxextent,sz)
	cset=0
#	method='7'
#	method='6'
#	method='fitlinear'
#	method='fit'
#	method='fitless'
#	method='fitevenless'
	method='6fitless'
	if 1:
		factor=0.5
		sigma=maxextent*factor
#		epsilonzeta6=[numpy.array(numpy.zeros([sz,sz])) for c in range(7)]
		epsilonzetacnt=[numpy.array(numpy.zeros(len(xx))) for c in range(7)]
		estIQUV=[numpy.array(numpy.zeros(len(xx))) for c in range(4)]
		mIQUV=[numpy.array(numpy.zeros(len(xx))) for c in range(4)]
		derotmIQUV=[numpy.array(numpy.zeros(len(xx))) for c in range(4)]
		for cnt in range(len(xx)):
			if (method=='7'):
				rv=solvezetaepsilon(xx[cnt],yy[cnt],I_true,Q_true,U_true,V_true,mI,mQ,mU,mV,xx,yy,chi,maxextent,sigma)
			elif (method=='6'):
				rv=solvezetaepsilon6(xx[cnt],yy[cnt],I_true,Q_true,U_true,V_true,mI,mQ,mU,mV,xx,yy,chi,maxextent,sigma)
			elif (method=='fitlinear'):
				rv=solvefitlinearzetaepsilon(xx[cnt],yy[cnt],I_true,Q_true,U_true,V_true,mI,mQ,mU,mV,xx,yy,chi,maxextent,sigma)
			elif (method=='fit'):
				rv=solvefitzetaepsilon(xx[cnt],yy[cnt],I_true,Q_true,U_true,V_true,mI,mQ,mU,mV,xx,yy,chi,maxextent,sigma)
			elif (method=='fitless'):
				rv=solvefitlesszetaepsilon(xx[cnt],yy[cnt],I_true,Q_true,U_true,V_true,mI,mQ,mU,mV,xx,yy,chi,maxextent,sigma)
			elif (method=='fitevenless'):
				rv=solvefitevenlesszetaepsilon(xx[cnt],yy[cnt],I_true,Q_true,U_true,V_true,mI,mQ,mU,mV,xx,yy,chi,maxextent,sigma)
			elif (method=='6fitless'):
				rv=solve6fitlesszetaepsilon(xx[cnt],yy[cnt],I_true,Q_true,U_true,V_true,mI,mQ,mU,mV,xx,yy,chi,maxextent,sigma)
			else:
				exit('unknown method')

			rvest=estimatetrueIQUV(mI[cnt],mQ[cnt],mU[cnt],mV[cnt],rv,chi[cnt])
			mIQUV[0][cnt]=mI[cnt]
			mIQUV[1][cnt]=mQ[cnt]
			mIQUV[2][cnt]=mU[cnt]
			mIQUV[3][cnt]=mV[cnt]
			derotmIQUV[0][cnt]=mI[cnt]
			derotmIQUV[1][cnt]=mQ[cnt]#mQ[cnt]*numpy.cos(2.0*chi[cnt])+mU[cnt]*numpy.sin(2.0*chi[cnt])
			derotmIQUV[2][cnt]=mU[cnt]#-mQ[cnt]*numpy.sin(2.0*chi[cnt])+mU[cnt]*numpy.cos(2.0*chi[cnt])
			derotmIQUV[3][cnt]=mV[cnt]
			for iq in range(4):
				estIQUV[iq][cnt]=rvest[iq]
			for iez in range(7):
				epsilonzetacnt[iez][cnt]=rv[iez]
		xgrid=maxextent*numpy.linspace(-1,1,200)
		ygrid=maxextent*numpy.linspace(-1,1,200)
		
		fig=plt.figure(1)
		fig.set_size_inches(5.5,4)
		zgrid=mygriddata(xx,yy,(numpy.array(epsilonzetacnt[0])),xgrid,ygrid)
#		plt.imshow(zgrid,extent=[-maxextent,maxextent,-maxextent,maxextent],vmin=numpy.min(numpy.min(zgrid)),vmax=numpy.max(numpy.max(zgrid)),origin='lower')
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

		fig=plt.figure(3)
		plt.clf()
		iqlabel=['I','Q','U','V']
		trueIQUV=[I_true,Q_true,U_true,V_true]
		
		erroption=0
		for iq in range(4):
			if (erroption==0):
				zcnt=estIQUV[iq]-trueIQUV[iq]
			elif (erroption==1):
				zcnt=derotmIQUV[iq]/derotmIQUV[0]*trueIQUV[0]-trueIQUV[iq]
			else:
				zcnt=derotmIQUV[iq]-trueIQUV[iq]# but one should really derotate Q,U too
			zgrid=mygriddata(xx,yy,zcnt,xgrid,ygrid)
			a=plt.subplot(1,4,iq+1)
			cset=plotPattern('', xgrid, ygrid, zgrid.transpose(), plt)
			for tick in a.xaxis.majorTicks:
				tick.label.set_fontsize('small')			
#			plt.title('%s m=%f s=%f' % (iqlabel[iq],zcnt.mean(),zcnt.std()),fontsize=8)
			plt.title('%s rms=%f' % (iqlabel[iq],numpy.sqrt((zcnt**2).mean())),fontsize=8)
			a.set(xlabel='az (hpp)')
			if (iq>0):
				a.set(ylabel='', yticks=[])
			else:
				a.set(ylabel='el (hpp)')
				for tick in a.yaxis.majorTicks:
					tick.label.set_fontsize('small')			

				
		plt.subplots_adjust(left=0.07, right=0.9, bottom=0.02, top=0.9, wspace=0.05, hspace=0.05)
		if (cset):
			plt.colorbar(cset, cax=plt.axes([0.92, 0.1, 0.02, 0.8]), format='%d')
			plt.gcf().text(0.97, 0.5, 'dB')
		fig.set_size_inches(9,2.8)
		if (erroption==0):
			plt.gcf().text(0.5, 0.9, '%s remaining error, %s, f=%g' % (outputpath[:-1],method,factor), ha='center', size='x-large')
			plt.savefig('%smaperr%s_%.2f.png'%(outputpath,method,factor))
		elif (erroption==1):
			plt.gcf().text(0.5, 0.9, '%s remaining error (simple normalization)' % (outputpath[:-1]), ha='center', size='x-large')
			plt.savefig('%smaperr_norm.png'%(outputpath))
		else:
			plt.gcf().text(0.5, 0.9, '%s remaining error (no correction)' % (outputpath[:-1]), ha='center', size='x-large')
			plt.savefig('%smaperr_nocor.png'%(outputpath))
			
	if 0:
		epsilonzeta6=[numpy.array(numpy.zeros([sz,sz])) for c in range(7)]
		for ix in range(sz):
			for iy in range(sz):
				rv=solvezetaepsilon6(xax[ix],yax[iy],I_true,Q_true,U_true,V_true,mI,mQ,mU,mV,xx,yy,chi,maxextent,1)
				for iez in range(7):
					epsilonzeta6[iez][ix][iy]=rv[iez]
		for iez in range(7):
			plt.figure(1)
			plt.imshow(epsilonzeta6[iez].transpose(),extent=[-maxextent,maxextent,-maxextent,maxextent],vmin=numpy.min(numpy.min(epsilonzeta6[iez])),vmax=numpy.max(numpy.max(epsilonzeta6[iez])),origin='lower')
			plt.colorbar()
			plt.xlabel('Relative AZ [Beam HPP]')
			plt.ylabel('Relative EL [Beam HPP]')
			plt.title('%s %s' % (outputpath[:-1],labels[iez]))
			plt.savefig('%smapimage6_%d.png'%(outputpath,iez))
			plt.clf()
		plotMueller('6',epsilonzeta6,maxextent)
		
	if 0:
		epsilonzeta=[numpy.array(numpy.zeros([sz,sz])) for c in range(7)]
		for ix in range(sz):
			for iy in range(sz):
				rv=solvezetaepsilon(xax[ix],yax[iy],I_true,Q_true,U_true,V_true,mI,mQ,mU,mV,xx,yy,chi,maxextent)
				for iez in range(7):
					epsilonzeta[iez][ix][iy]=rv[iez]
		for iez in range(7):
			plt.figure(1)
			plt.imshow(epsilonzeta[iez].transpose(),extent=[-maxextent,maxextent,-maxextent,maxextent],vmin=numpy.min(numpy.min(epsilonzeta[iez])),vmax=numpy.max(numpy.max(epsilonzeta[iez])),origin='lower')
			plt.colorbar()
			plt.xlabel('Relative AZ [Beam HPP]')
			plt.ylabel('Relative EL [Beam HPP]')
			plt.title('%s %s' % (outputpath[:-1],labels[iez]))
			plt.savefig('%smapimage_%d.png'%(outputpath,iez))
			plt.clf()
		plotMueller('',epsilonzeta,maxextent)
	
	plt.figure(1)
	plt.quiver(xx,yy,dx,dy,headlength=0,headwidth=1,pivot='middle')
	plt.axis([-maxextent*1.4,maxextent*1.4,-maxextent*1.2,maxextent*1.2])
	plt.xlabel('Relative AZ [Beam HPP]')
	plt.ylabel('Relative EL [Beam HPP]')
	plt.title('%s z_pp vs e_np z_np=%f' % (outputpath[:-1],z_np))
	plt.savefig('%smap_posangle%f.png'%(outputpath,z_np))

	plt.figure(2)
	plt.quiver(xx,yy,odx,ody,headlength=0,headwidth=1,pivot='middle')
	plt.axis([-maxextent*1.4,maxextent*1.4,-maxextent*1.2,maxextent*1.2])
	plt.xlabel('Relative AZ [Beam HPP]')
	plt.ylabel('Relative EL [Beam HPP]')
	plt.title('%s e_pp' % (outputpath[:-1]))
	plt.savefig('%smap_posangleOld.png'%outputpath)
	
	#plot e_pp
	xgrid=maxextent*numpy.linspace(-1,1,200)
	ygrid=maxextent*numpy.linspace(-1,1,200)
	zgrid=mygriddata(xx,yy,(numpy.array(e_pp)),xgrid,ygrid)
	plt.figure(3)
	plt.imshow(zgrid,extent=[-maxextent,maxextent,-maxextent,maxextent],origin='lower',vmin=-0.5,vmax=0)
	plt.colorbar()
	plt.xlabel('Relative AZ [Beam HPP]')
	plt.ylabel('Relative EL [Beam HPP]')
	plt.title('%s e_pp' % (outputpath[:-1]))
	plt.savefig('%smapimage_e_pp.png'%outputpath)
	#plot z_pp
	zgrid=mygriddata(xx,yy,(numpy.array(z_pp)),xgrid,ygrid)
	plt.figure(4)
	plt.imshow(zgrid,extent=[-maxextent,maxextent,-maxextent,maxextent],origin='lower',vmin=-0.05,vmax=0.05)
	plt.colorbar()
	plt.xlabel('Relative AZ [Beam HPP]')
	plt.ylabel('Relative EL [Beam HPP]')
	plt.title('%s z_pp' % (outputpath[:-1]))
	plt.savefig('%smapimage_z_pp.png'%outputpath)
	#plot e_np
	zgrid=mygriddata(xx,yy,(numpy.array(e_np)),xgrid,ygrid)
	plt.figure(5)
	plt.imshow(zgrid,extent=[-maxextent,maxextent,-maxextent,maxextent],origin='lower',vmin=-0.05,vmax=0.05)
	plt.colorbar()
	plt.xlabel('Relative AZ [Beam HPP]')
	plt.ylabel('Relative EL [Beam HPP]')
	plt.title('%s e_np' % (outputpath[:-1]))
	plt.savefig('%smapimage_e_np.png'%outputpath)
	
#	parser.exit('exiting')
	fig=plt.figure(4)
	plt.clf()

	#predict data
	cnt=0
	for itime in range(ntime):
		pcnt=0
		predI=range(npointings)
		normI=range(npointings)
		dataI=range(npointings)
		predQ=range(npointings)
		normQ=range(npointings)
		dataQ=range(npointings)
		predU=range(npointings)
		normU=range(npointings)
		dataU=range(npointings)
		predV=range(npointings)
		normV=range(npointings)
		dataV=range(npointings)
		for pointing in range(npointings):
			chi=PARANG[pointing][itime]
			I_harpoon=II[itime][pointing]
			Q_harpoon=QQ[itime][pointing]
			U_harpoon=UU[itime][pointing]
			V_harpoon=VV[itime][pointing]

			e_pp_1=e_pp[cnt]+1.0;
			dataI[pcnt]=I_harpoon
			predI[pcnt]=estIQUV[0][cnt]#II0*e_pp_1+QQ0*(-z_pp[cnt]*numpy.sin(2.0*chi)+e_np[cnt]*numpy.cos(2.0*chi))+UU0*(z_pp[cnt]*numpy.cos(2.0*chi)+e_np[cnt]*numpy.sin(2.0*chi))
#			normI[pcnt]=I_harpoon/I_harpoon*II[itime][0]
			normI[pcnt]=I_harpoon/I_harpoon*I_true
			dataQ[pcnt]=Q_harpoon
#			normQ[pcnt]=Q_harpoon/I_harpoon*II[itime][0]
			normQ[pcnt]=Q_harpoon/I_harpoon*I_true
			predQ[pcnt]=estIQUV[1][cnt]#QQ0*e_pp_1+II0*(-z_pp[cnt]*numpy.sin(2.0*chi)+e_np[cnt]*numpy.cos(2.0*chi))
			dataU[pcnt]=U_harpoon
#			normU[pcnt]=U_harpoon/I_harpoon*II[itime][0]
			normU[pcnt]=U_harpoon/I_harpoon*I_true
			predU[pcnt]=estIQUV[2][cnt]#QQ0*e_pp_1+II0*(-z_pp[cnt]*numpy.sin(2.0*chi)+e_np[cnt]*numpy.cos(2.0*chi))
			dataV[pcnt]=V_harpoon
#			normV[pcnt]=V_harpoon/I_harpoon*II[itime][0]
			normV[pcnt]=V_harpoon/I_harpoon*I_true
			predV[pcnt]=estIQUV[3][cnt]#QQ0*e_pp_1+II0*(-z_pp[cnt]*numpy.sin(2.0*chi)+e_np[cnt]*numpy.cos(2.0*chi))
			
			pcnt=pcnt+1
			cnt=cnt+1
		a = plt.subplot(2, 1, 1)				
#		plt.clf()
##		plt.plot(range(npointings),numpy.array(normI),color='y')
		plt.plot(range(npointings),dataI,color='r')
		plt.plot(range(npointings),numpy.array(predI),color='k')
#		plt.title('%s pred_I' % (outputpath[:-1]))
#		plt.savefig('%spred_I_%d.png'%(outputpath,itime))
		a = plt.subplot(2, 1, 2)
#		plt.clf()
##		plt.plot(range(npointings),numpy.array(normQ),color='y')
		plt.plot(range(npointings),dataQ,color='r')
		plt.plot(range(npointings),numpy.array(predQ),color='k')
#		plt.axis([0,npointings,-0.1,1])
#		plt.title('%s pred_Q' % (outputpath[:-1]))
#		plt.savefig('%spred_Q_%d.png'%(outputpath,itime))
#		plt.figure(4)
#		plt.clf()
##		plt.plot(range(npointings),numpy.array(normU),color='y')
		plt.plot(range(npointings),dataU,color='r')
		plt.plot(range(npointings),numpy.array(predU),color='k')
#		plt.axis([0,npointings,-0.1,1])
#		plt.title('%s pred_U' % (outputpath[:-1]))
#		plt.savefig('%spred_U_%d.png'%(outputpath,itime))
#		plt.figure(5)
#		plt.clf()
##		plt.plot(range(npointings),numpy.array(normV),color='y')
		plt.plot(range(npointings),dataV,color='r')
		plt.plot(range(npointings),numpy.array(predV),color='k')
#		plt.axis([0,npointings,-0.1,1])
#		plt.title('%s pred_V' % (outputpath[:-1]))
#		plt.savefig('%spred_V_%d.png'%(outputpath,itime))

	a = plt.subplot(2, 1, 1)				
	a.axis([0,npointings-1,7.5,10])
	a.set_ylabel('I')
	a = plt.subplot(2, 1, 2)
	a.axis([0,npointings-1,-0.2,1.2])
	a.set_xlabel('Pointing')
	a.set_ylabel('Q,U,V')
	plt.gcf().text(0.5, 0.95, '%s predicted IQUV, %s, f=%g' % (outputpath[:-1],method,factor), ha='center', size='x-large')
	plt.gcf().text(0.5, 0.91, '(red=uncorrected, black=%s f=%g)'%(method,factor), ha='center')
	plt.gcf().text(0.5, 0.01, 'Lines are for different time intervals (different parallactic angles), averaged over frequency.', ha='center')
	plt.subplots_adjust(left=0.1, right=0.95, bottom=0.1, top=0.9, wspace=0.05, hspace=0.1)
	fig.set_size_inches(8,8)
	plt.savefig('%spred_IQUV_%s_%.2f.png'%(outputpath,method,factor))

# ================================ Main function ================================
# Parse command-line options and arguments
parser = optparse.OptionParser(usage="%prog [options] path",
                               description="Plots the calibration or performance results \
                                            stored at a given path. Either leakages are plotted at a specified\
											pointing; or leakages for different pointings for the specified antenna\
											is plotted. Without specified options, the stokes I,Q,U,V results are plotted.")
(options, args) = parser.parse_args()

if len(args) < 1:
    parser.error("Please specify path")

outputpath=ensurepathformat(args[0])

plotmap(outputpath)
