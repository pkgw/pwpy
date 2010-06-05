#!/usr/bin/python
#Mattieu de Villiers mattieu@ska.ac.za 10 May 2010
import optparse, commands, sys, numpy, pylab, pickle

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
	
#Casey's rotate to convert dra,ddec to az,el
def rotate(RAoffset,DECoffset,PARANG):
	ANG=PARANG*numpy.pi/180.0
	xx=-RAoffset*numpy.cos(ANG)+DECoffset*numpy.sin(ANG)
	yy=RAoffset*numpy.sin(ANG)+DECoffset*numpy.cos(ANG)
	return xx,yy

#counter clockwise rotation
def normalrotate(x,y,theta):
	ANG=theta*numpy.pi/180.0
	xx=x*numpy.cos(ANG)-y*numpy.sin(ANG)
	yy=x*numpy.sin(ANG)+y*numpy.cos(ANG)
	return xx,yy

def plotstokessnap(outputpath):
	[RA,DEC,RAoffset,DECoffset,AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime,freq,nant]=LoadPointingInfo(outputpath)
	[leakageX,leakageY,peakIQUV,noiseIQUV,convergeFail,nactiveAntennas,validant]=readresults(outputpath)

	PARANG=numpy.array(CHI,dtype='double')-90.0 #parang=CHI-90

	npointings=len(peakIQUV)
	ntime=len(peakIQUV[0])
	nexplodedpieces=len(peakIQUV[0][0])

	x=range(npointings)
	I=range(npointings)
	Q=range(npointings)
	U=range(npointings)
	V=range(npointings)
	nI=range(npointings)
	nQ=range(npointings)
	nU=range(npointings)
	nV=range(npointings)
	II=range(ntime*npointings)
	QQ=range(ntime*npointings)
	UU=range(ntime*npointings)
	xx=range(ntime*npointings)
	yy=range(ntime*npointings)
	dx=range(ntime*npointings)
	dy=range(ntime*npointings)
	radius=range(ntime*npointings)
	angle=range(ntime*npointings)
	vectorlength=range(ntime*npointings)
	vectorangle=range(ntime*npointings)
	colouring=['k','r','m','g','b','c','y','k']
	alphas=[1,1,1,1,1,1,1,0.5]
	cnt=0
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
			II[cnt]=Iacc
			QQ[cnt]=Qacc
			UU[cnt]=Uacc
			[xx[cnt],yy[cnt]]=rotate(RAoffset[pointing],DECoffset[pointing],PARANG[pointing][itime])
			II0=II[itime*npointings]
			QQ0=QQ[itime*npointings]
			UU0=UU[itime*npointings]
			length=pylab.sqrt((QQ[cnt]/Iacc-QQ0/II0)**2+(UU[cnt]/Iacc-UU0/II0)**2);
			posangle=0.5*numpy.arctan2(UU[cnt]/Iacc-UU0/II0,QQ[cnt]/Iacc-QQ0/II0)
#			length=pylab.sqrt((QQ[cnt]/II0-QQ0/II0)**2+(UU[cnt]/II0-UU0/II0)**2);
#			posangle=0.5*numpy.arctan2(UU[cnt]/II0-UU0/II0,QQ[cnt]/II0-QQ0/II0)

			dx[cnt]=length*numpy.cos(posangle)
			dy[cnt]=length*numpy.sin(posangle)
			pylab.figure(1)			
#			pylab.arrow(xx[cnt],yy[cnt],dx[cnt]*4000.0,dy[cnt]*4000.0,linewidth=0.5,head_width=0.5,color=colouring[itime],alpha=alphas[itime])	
#			pylab.arrow(xx[cnt],yy[cnt],dx[cnt]*16000.0,dy[cnt]*16000.0,linewidth=0.5,head_width=0.5,color=colouring[itime],alpha=alphas[itime])	
			
			newrelQ=numpy.cos(2.0*(posangle-PARANG[pointing][itime]*numpy.pi/180.0))
			newrelU=numpy.sin(2.0*(posangle-PARANG[pointing][itime]*numpy.pi/180.0))
			posangle=0.5*numpy.arctan2(newrelU,newrelQ)
			radius[cnt]=numpy.sqrt(xx[cnt]*xx[cnt]+yy[cnt]*yy[cnt])
			angle[cnt]=numpy.arctan2(yy[cnt],xx[cnt])*180.0/numpy.pi
			vectorlength[cnt]=length
			vectorangle[cnt]=posangle*180.0/numpy.pi
			
			dx[cnt]=length*numpy.cos(posangle)
			dy[cnt]=length*numpy.sin(posangle)
						
			pylab.figure(2)			
#			pylab.arrow(xx[cnt],yy[cnt],dx[cnt]*4000.0,dy[cnt]*4000.0,linewidth=0.5,head_width=0.5,color=colouring[itime],alpha=alphas[itime])	
#			pylab.arrow(xx[cnt],yy[cnt],dx[cnt]*16000.0,dy[cnt]*16000.0,linewidth=0.5,head_width=0.5,color=colouring[itime],alpha=alphas[itime])	
#				pylab.text(xx[cnt],yy[cnt],'p%dt%d'%(pointing,itime),fontsize=8,color=colouring[itime],alpha=alphas[itime])
#				pylab.text(xx[cnt],yy[cnt],'p%dt%dL%d'%(pointing,itime,PARANG[pointing][itime]),fontsize=8,color=colouring[itime],alpha=alphas[itime])
#				pylab.plot(xx[cnt], yy[cnt], marker='o', color='c', lw=0)

			cnt=cnt+1
	
	pylab.figure(1)
	pylab.axis([-1400,1400,-1100,1100])
	pylab.xlabel('Relative AZ [arcsec]')
	pylab.ylabel('Relative EL [arcsec]')
	pylab.title('%s Q,U error' % (outputpath[:-1]))
	pylab.savefig('%scoverage.png'%outputpath)
	pylab.figure(2)
	pylab.axis([-1400,1400,-1100,1100])
	pylab.xlabel('Relative AZ [arcsec]')
	pylab.ylabel('Relative EL [arcsec]')
	pylab.title('%s Q,U error, after PA correction' % (outputpath[:-1]))
	pylab.savefig('%scoveragePA.png'%outputpath)
	pylab.figure(3)
	pylab.plot(angle, vectorangle, marker='o', lw=0)
	pylab.xlabel('Relative angle [degrees]')
	pylab.ylabel('QU error angle')
	pylab.title('%s Q,U error' % (outputpath[:-1]))
	pylab.savefig('%sangleQU.png'%outputpath)
	pylab.figure(4)
	pylab.plot(numpy.array(radius)/1000.0*freq/3.140*0.5, vectorlength, marker='o', lw=0)
	pylab.ylim([0,0.03])
	pylab.xlim([0,0.51])
	pylab.xlabel('Radius [frac to half power point]')
	pylab.ylabel('QU error magnitude')
	pylab.title('%s Q,U error' % (outputpath[:-1]))
	pylab.savefig('%sradiusQU.png'%outputpath)
	
	for itime in range(ntime):
		maxparang=-1e10
		minparang=1e10
		avgparang=0
		for pointing in range(npointings):
			if (PARANG[pointing][itime]<minparang):
				minparang=PARANG[pointing][itime]
			if (PARANG[pointing][itime]>maxparang):
				maxparang=PARANG[pointing][itime]
			avgparang=avgparang+(PARANG[pointing][itime])/float(npointings)
				
		for explodedpiece in range (nexplodedpieces):
			for pointing in range(npointings):
				I[pointing]=peakIQUV[pointing][itime][explodedpiece][0]
				Q[pointing]=peakIQUV[pointing][itime][explodedpiece][1]
				U[pointing]=peakIQUV[pointing][itime][explodedpiece][2]
				V[pointing]=peakIQUV[pointing][itime][explodedpiece][3]
				nI[pointing]=noiseIQUV[pointing][itime][explodedpiece][0]
				nQ[pointing]=noiseIQUV[pointing][itime][explodedpiece][1]
				nU[pointing]=noiseIQUV[pointing][itime][explodedpiece][2]
				nV[pointing]=noiseIQUV[pointing][itime][explodedpiece][3]
		
			I=numpy.array(I,dtype='d')	
			Q=numpy.array(Q,dtype='d')	
			U=numpy.array(U,dtype='d')	
			V=numpy.array(V,dtype='d')	
			nI=numpy.array(nI,dtype='d')	
			nQ=numpy.array(nQ,dtype='d')	
			nU=numpy.array(nU,dtype='d')	
			nV=numpy.array(nV,dtype='d')	

			eQ=numpy.abs(numpy.average(Q[1:]/I[1:])-Q[0]/I[0]);
			eU=numpy.abs(numpy.average(U[1:]/I[1:])-U[0]/I[0]);
			eV=numpy.abs(numpy.average(V[1:]/I[1:])-V[0]/I[0]);
			sQ=numpy.std(Q[1:]/I[1:])
			sU=numpy.std(U[1:]/I[1:])
			sV=numpy.std(V[1:]/I[1:])
			print 'eQ=%g eU=%g eV=%g' % (eQ,eU,eV)
			print 'sQ=%g sU=%g sV=%g' % (sQ,sU,sV)

			pylab.figure(100+itime)
			if ((explodedpiece==0)&(itime==0)):
				pylab.plot(x, I, marker='x', color='c', lw=2, label=r'I')
				pylab.plot(x, Q, marker='o', color='b', lw=2,  label=r'Q')
				pylab.plot(x, U, marker='s', color='r', lw=2, label=r'U', zorder=1.9)
				pylab.plot(x,V, marker='^', color='g', lw=2, label=r'V', zorder=1.9)
			else:
				pylab.plot(x, I, marker='x', color='c', lw=2)
				pylab.plot(x, Q, marker='o', color='b', lw=2)
				pylab.plot(x, U, marker='s', color='r', lw=2)
				pylab.plot(x,V, marker='^', color='g', lw=2)

			pylab.figure(200+itime)
			if (nexplodedpieces==1):
				pylab.errorbar(x, Q, nQ, marker='o',color='b',
	         		mfc='red', mec='blue', ms=2, mew=2, label=r'Q e=%g s=%g' %(eQ,sQ))
				pylab.errorbar(x, U, nQ, marker='s',color='r',
	         		mfc='red', mec='red', ms=2, mew=2, label=r'U e=%g s=%g' %(eU,sU))
				pylab.errorbar(x, V, nV, marker='^',color='g',
	         		mfc='red', mec='green', ms=2, mew=2, label=r'V e=%g s=%g' %(eV,sV))
			elif ((explodedpiece==0)):
				pylab.errorbar(x, Q, nQ, marker='o',color='b',
	         		mfc='red', mec='blue', ms=2, mew=2, label=r'Q')
				pylab.errorbar(x, U, nQ, marker='s',color='r',
	         		mfc='red', mec='red', ms=2, mew=2, label=r'U')
				pylab.errorbar(x, V, nV, marker='^',color='g',
	         		mfc='red', mec='green', ms=2, mew=2, label=r'V')
			else:
				pylab.errorbar(x, Q, nQ, marker='o',color='b',
	         		mfc='red', mec='blue', ms=2, mew=2)
				pylab.errorbar(x, U, nQ, marker='s',color='r',
	         		mfc='red', mec='red', ms=2, mew=2)
				pylab.errorbar(x, V, nV, marker='^',color='g',
	         		mfc='red', mec='green', ms=2, mew=2)

			pylab.figure(300+itime)
			if (nexplodedpieces==1):
				pylab.errorbar(x, Q/I, nQ/I, marker='o',color='b',
			       	mfc='red', mec='blue', ms=2, mew=2, label=r'Q e=%g s=%g' %(eQ,sQ))
				pylab.errorbar(x, U/I, nQ/I, marker='s',color='r',
			    	mfc='red', mec='red', ms=2, mew=2, label=r'U e=%g s=%g' %(eU,sU))
				pylab.errorbar(x, V/I, nV/I, marker='^',color='g',
			    	mfc='red', mec='green', ms=2, mew=2, label=r'V e=%g s=%g' %(eV,sV))
			elif ((explodedpiece==0)):
				pylab.errorbar(x, Q/I, nQ/I, marker='o',color='b',
		       		mfc='red', mec='blue', ms=2, mew=2, label=r'Q')
				pylab.errorbar(x, U/I, nQ/I, marker='s',color='r',
		       		mfc='red', mec='red', ms=2, mew=2, label=r'U')
				pylab.errorbar(x, V/I, nV/I, marker='^',color='g',
			    	mfc='red', mec='green', ms=2, mew=2, label=r'V')
			else:
				pylab.errorbar(x, Q/I, nQ/I, marker='o',color='b',
		       		mfc='red', mec='blue', ms=2, mew=2)
				pylab.errorbar(x, U/I, nQ/I, marker='s',color='r',
		       		mfc='red', mec='red', ms=2, mew=2)
				pylab.errorbar(x, V/I, nV/I, marker='^',color='g',
		       		mfc='red', mec='green', ms=2, mew=2)


		pylab.figure(100+itime)
		pylab.xlim((x[0], x[-1]))
		pylab.xlabel('Pointing')
		pylab.ylabel('Brightness [Jy/beam]')
		pylab.title('%s itime=%d  %d<%d<%d' % (outputpath[:-1],itime,minparang,avgparang,maxparang))
		pylab.grid()
		pylab.legend()
		pylab.savefig('%sstokesIQUV%d.png' % (outputpath,itime))

		pylab.figure(200+itime)
		pylab.xlim((x[0], x[-1]))
		pylab.ylim(-0.4, 1.4)
		pylab.xlabel('Pointing')
		pylab.ylabel('Q,U')
		pylab.title('%s time=%d %d<%d<%d' % (outputpath[:-1],itime,minparang,avgparang,maxparang))
		pylab.grid()
		pylab.legend()
		pylab.savefig('%sstokesIQUVs%d.png' % (outputpath,itime))

		pylab.figure(300+itime)
		pylab.xlim((x[0], x[-1]))
		pylab.ylim(-0.04, 0.14)
		pylab.xlabel('Pointing')
		pylab.ylabel('Normalized by I')
		pylab.title('%s time=%d %d<%d<%d' % (outputpath[:-1],itime,minparang,avgparang,maxparang))
		pylab.grid()
		pylab.legend()
		pylab.savefig('%sstokesIQUVsNorm%d.png' % (outputpath,itime))
	
#not used
def plotstokessnapOld(outputpath):
	[RA,DEC,RAoffset,DECoffset,AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime,freq,nant]=LoadPointingInfo(outputpath)
	[leakageX,leakageY,peakIQUV,noiseIQUV,convergeFail,nactiveAntennas,validant]=readresults(outputpath)

	PARANG=numpy.array(CHI,dtype='double')-90.0 #parang=CHI-90

	npointings=len(peakIQUV)
	ntime=len(peakIQUV[0])
	nexplodedpieces=len(peakIQUV[0][0])
	
	x=range(npointings)
	I=range(npointings)
	Q=range(npointings)
	U=range(npointings)
	V=range(npointings)
	nI=range(npointings)
	nQ=range(npointings)
	nU=range(npointings)
	nV=range(npointings)

	pylab.figure(30)
	pylab.plot(AZ, EL, marker='x', color='c', lw=1)
	pylab.grid()
	pylab.savefig('%sazel.png' % (outputpath))

	
	colouring=['k','r','m','g','b','c','y','k']
	alphas=[1,1,1,1,1,1,1,0.5]
	pylab.figure(31)
	for itime in range(ntime):
		for pointing in range(npointings):
			pylab.plot(LST[pointing][itime], PARANG[pointing][itime], marker='.', color=colouring[itime],alpha=alphas[itime],lw=0)
	pylab.xlabel('LST')
	pylab.ylabel('Parallactic angle')
	pylab.savefig('%sparanglst.png' % (outputpath))
	pylab.figure(32)
	for itime in range(ntime):
		for pointing in range(npointings):
			pylab.plot(pointing, PARANG[pointing][itime], marker='.', color=colouring[itime],alpha=alphas[itime], lw=0)
	pylab.xlabel('Pointing')
	pylab.ylabel('Parallactic angle')
	pylab.savefig('%sparangpoint.png' % (outputpath))

	pylab.figure(33)
	for itime in range(ntime):
		for pointing in range(npointings):
			pylab.plot(itime, PARANG[pointing][itime], marker='.', color=colouring[itime],alpha=alphas[itime], lw=0)
	pylab.xlabel('itime')
	pylab.ylabel('Parallactic angle')
	pylab.savefig('%sparangitime.png' % (outputpath))
	
	QQ=range(ntime*npointings)
	UU=range(ntime*npointings)
	xx=range(ntime*npointings)
	yy=range(ntime*npointings)
	dx=range(ntime*npointings)
	dy=range(ntime*npointings)
	parangcheck=range(ntime*npointings)
	cnt=0
	pylab.figure(1)
	for c in range(4):
		parang=(float(c)/4.0-0.5)*90.0
		for pointing in range(npointings):
			[xx[cnt],yy[cnt]]=rotate(RAoffset[pointing],DECoffset[pointing],parang)
			pylab.plot(xx[cnt], yy[cnt], marker='o', markersize=5, color=colouring[c], lw=0)
			pylab.text(xx[cnt],yy[cnt],'p%dL%d'%(pointing,parang),color=colouring[c],alpha=alphas[c])
	pylab.axis([-1400,1400,-1100,1100])
	pylab.xlabel('Relative AZ [arcsec]')
	pylab.ylabel('Relative EL [arcsec]')
	pylab.savefig('%sazelpointing.png'%outputpath)

	#convert pointing to pRA, pDEC
	pRA=range(npointings)
	pDEC=range(npointings)
	for pointing in range(npointings):
		pDEC[pointing]=DEC[pointing]+DECoffset[pointing]/60.0/60.0
		pRA[pointing]=RA[pointing]*360.0/24.0+RAoffset[pointing]/60.0/60.0/numpy.cos(pDEC[pointing]*numpy.pi/180.0)

	print 'pRA',pRA
	print 'pDEC',pDEC
	
	print 'RA',RA
	print 'dec',DEC
	print 'RAoffset',RAoffset
	print 'decoffset',DECoffset
	print 'LST',LST
	
	
	pylab.figure(20)
	pylab.axes()
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
			QQ[cnt]=Qacc/Iacc
			UU[cnt]=Uacc/Iacc
			#ax=x
			LAT=40.81*numpy.pi/180.0
			D0=pDEC[0]
			H0=pRA[0]-LST[pointing][itime]*360.0/24.0
			D=pDEC[pointing]
			H=pRA[pointing]-LST[pointing][itime]*360.0/24.0#units!!!RA in arcsec
			#arcsec to degrees
			H0=H0*numpy.pi/180.0
			D0=D0*numpy.pi/180.0
			H=H*numpy.pi/180.0
			D=D*numpy.pi/180.0
			az=numpy.arctan2(-numpy.sin(H)*numpy.cos(D),numpy.sin(D)*numpy.cos(LAT)-numpy.cos(D)*numpy.sin(LAT)*numpy.cos(H))
			el=numpy.arcsin(numpy.sin(D)*numpy.sin(LAT)+numpy.cos(D)*numpy.cos(LAT)*numpy.cos(H))
			az0=numpy.arctan2(-numpy.sin(H0)*numpy.cos(D0),numpy.sin(D0)*numpy.cos(LAT)-numpy.cos(D0)*numpy.sin(LAT)*numpy.cos(H0))
			el0=numpy.arcsin(numpy.sin(D0)*numpy.sin(LAT)+numpy.cos(D0)*numpy.cos(LAT)*numpy.cos(H0))
			parangcheck[cnt]=180.0/numpy.pi*numpy.arctan2(numpy.sin(H)*numpy.cos(LAT),numpy.sin(LAT)*numpy.cos(D)-numpy.sin(D)*numpy.cos(LAT)*numpy.cos(H))
			xx[cnt]=(az-az0)*60.0*60.0*10#degrees to arcsec
			yy[cnt]=(el-el0)*60.0*60.0*10
			print '-========='
			print xx[cnt]
			print yy[cnt]
			#note RA=-AZ for southward pointing; but should be RA=AZ for northward pointing
			[xx[cnt],yy[cnt]]=rotate(RAoffset[pointing],DECoffset[pointing],PARANG[pointing][itime])
			if (0):
				f=float(pointing)/float(npointings)
				if (itime+1<ntime):
					nextEL=EL[0][itime+1]
					nextAZ=AZ[0][itime+1]
				else:
					nextEL=EL[0][itime]+(EL[0][itime]-EL[0][itime-1])
					nextAZ=AZ[0][itime]+(AZ[0][itime]-AZ[0][itime-1])
				xx[cnt]=AZ[pointing][itime]-(AZ[0][itime]*(1.0-f)+f*nextAZ)
				yy[cnt]=EL[pointing][itime]-(EL[0][itime]*(1.0-f)+f*nextEL)
			
				pylab.figure(20)			
				pylab.plot(xx[cnt], yy[cnt], marker='o', markersize=(QQ[cnt]-0.015)*200, color='c', lw=0)
				pylab.figure(21)
				pylab.plot(xx[cnt], yy[cnt], marker='o', markersize=(UU[cnt]-0.06)*200, color='c', lw=0)
			else:
				QQ0=QQ[itime*npointings]		
				UU0=UU[itime*npointings]
				length=pylab.sqrt((QQ[cnt]-QQ0)**2+(UU[cnt]-UU0)**2);
				posangle=0.5*numpy.arctan2(UU[cnt]-UU0,QQ[cnt]-QQ0)
				dx[cnt]=length*numpy.cos(posangle)
				dy[cnt]=length*numpy.sin(posangle)
				pylab.figure(20)
				for explodedpiece in range(nexplodedpieces):
					Iacc=peakIQUV[pointing][itime][explodedpiece][0]
					Qacc=peakIQUV[pointing][itime][explodedpiece][1]
					Uacc=peakIQUV[pointing][itime][explodedpiece][2]
					Vacc=peakIQUV[pointing][itime][explodedpiece][3]
					Qacc=Qacc/Iacc
					Uacc=Uacc/Iacc
					length=pylab.sqrt((Qacc-QQ0)**2+(Uacc-UU0)**2);
					posangle=0.5*numpy.arctan2(Uacc-UU0,Qacc-QQ0)
					#				posangle=numpy.arctan2(UU[cnt]-UU0,QQ[cnt]-QQ0)
					ddx=length*numpy.cos(posangle)
					ddy=length*numpy.sin(posangle)					
#					pylab.arrow(xx[cnt],yy[cnt],ddx*4000,ddy*4000,linewidth=0.5,head_width=10)	


#				pylab.arrow(xx[cnt],yy[cnt],dx[cnt]*4000.0,dy[cnt]*4000.0,linewidth=0.5,head_width=10,color=colouring[itime],alpha=alphas[itime])	
#				pylab.text(xx[cnt],yy[cnt],'p%dt%d'%(pointing,itime),fontsize=8,color=colouring[itime],alpha=alphas[itime])
#				pylab.text(xx[cnt],yy[cnt],'p%dt%dL%d'%(pointing,itime,PARANG[pointing][itime]),fontsize=8,color=colouring[itime],alpha=alphas[itime])
#				pylab.plot(xx[cnt], yy[cnt], marker='o', color='c', lw=0)

			cnt=cnt+1
			
	pylab.figure(19)
	pylab.plot(range(npointings*ntime),parangcheck)
	pylab.savefig('%sparangcheck'%outputpath)
	pylab.figure(20)
# 	pylab.axis('equal')
	pylab.axis([-1400,1400,-1100,1100])
	pylab.xlabel('Relative AZ [arcsec]')
	pylab.ylabel('Relative EL [arcsec]')
	pylab.title('%s QU error' % (outputpath[:-1]))
	pylab.savefig('%sFcoverage.png'%outputpath)
#	pylab.figure(21)
#	pylab.plot(xx, yy, marker='.',markersize=QQ*30, color='c', lw=0)
#	pylab.contour(xx, yy, QQ, [0.07,0.08,0.09,0.1,0.11,0.12,0.13,0.14], colors='k', linewidths=0.5)
#	pylab.savefig('%scontourcoverage.png'%outputpath)

	for itime in range(ntime):
		for explodedpiece in range (nexplodedpieces):
			for pointing in range(npointings):
				I[pointing]=peakIQUV[pointing][itime][explodedpiece][0]
				Q[pointing]=peakIQUV[pointing][itime][explodedpiece][1]
				U[pointing]=peakIQUV[pointing][itime][explodedpiece][2]
				V[pointing]=peakIQUV[pointing][itime][explodedpiece][3]
				nI[pointing]=noiseIQUV[pointing][itime][explodedpiece][0]
				nQ[pointing]=noiseIQUV[pointing][itime][explodedpiece][1]
				nU[pointing]=noiseIQUV[pointing][itime][explodedpiece][2]
				nV[pointing]=noiseIQUV[pointing][itime][explodedpiece][3]
		
			I=numpy.array(I,dtype='d')	
			Q=numpy.array(Q,dtype='d')	
			U=numpy.array(U,dtype='d')	
			V=numpy.array(V,dtype='d')	
			nI=numpy.array(nI,dtype='d')	
			nQ=numpy.array(nQ,dtype='d')	
			nU=numpy.array(nU,dtype='d')	
			nV=numpy.array(nV,dtype='d')	

			eQ=numpy.abs(numpy.average(Q[1:]/I[1:])-Q[0]/I[0]);
			eU=numpy.abs(numpy.average(U[1:]/I[1:])-U[0]/I[0]);
			eV=numpy.abs(numpy.average(V[1:]/I[1:])-V[0]/I[0]);
			sQ=numpy.std(Q[1:]/I[1:])
			sU=numpy.std(U[1:]/I[1:])
			sV=numpy.std(V[1:]/I[1:])
			print 'eQ=%g eU=%g eV=%g' % (eQ,eU,eV)
			print 'sQ=%g sU=%g sV=%g' % (sQ,sU,sV)

			pylab.figure(10+itime)
			if ((explodedpiece==0)&(itime==0)):
				pylab.plot(x, I, marker='x', color='c', lw=2, label=r'I')
				pylab.plot(x, Q, marker='o', color='b', lw=2,  label=r'Q')
				pylab.plot(x, U, marker='s', color='r', lw=2, label=r'U', zorder=1.9)
				pylab.plot(x,V, marker='^', color='g', lw=2, label=r'V', zorder=1.9)
			else:
				pylab.plot(x, I, marker='x', color='c', lw=2)
				pylab.plot(x, Q, marker='o', color='b', lw=2)
				pylab.plot(x, U, marker='s', color='r', lw=2)
				pylab.plot(x,V, marker='^', color='g', lw=2)

			pylab.figure(2+itime)
			if (nexplodedpieces==1):
				pylab.errorbar(x, Q/I, nQ/I, marker='o',color='b',
	         		mfc='red', mec='blue', ms=2, mew=2, label=r'Q e=%g s=%g' %(eQ,sQ))
				pylab.errorbar(x, U/I, nQ/I, marker='s',color='r',
	         		mfc='red', mec='red', ms=2, mew=2, label=r'U e=%g s=%g' %(eU,sU))
				pylab.errorbar(x, V/I, nV/I, marker='^',color='g',
	         		mfc='red', mec='green', ms=2, mew=2, label=r'V e=%g s=%g' %(eV,sV))
			elif ((explodedpiece==0)):
				pylab.errorbar(x, Q/I, nQ/I, marker='o',color='b',
	         		mfc='red', mec='blue', ms=2, mew=2, label=r'Q')
				pylab.errorbar(x, U/I, nQ/I, marker='s',color='r',
	         		mfc='red', mec='red', ms=2, mew=2, label=r'U')
				pylab.errorbar(x, V/I, nV/I, marker='^',color='g',
	         		mfc='red', mec='green', ms=2, mew=2, label=r'V')
			else:
				pylab.errorbar(x, Q/I, nQ/I, marker='o',color='b',
	         		mfc='red', mec='blue', ms=2, mew=2)
				pylab.errorbar(x, U/I, nQ/I, marker='s',color='r',
	         		mfc='red', mec='red', ms=2, mew=2)
				pylab.errorbar(x, V/I, nV/I, marker='^',color='g',
	         		mfc='red', mec='green', ms=2, mew=2)

		pylab.figure(2+itime)
		pylab.xlim((x[0], x[-1]))
		pylab.ylim(-0.04, 0.14)
		pylab.xlabel('Pointing')
		pylab.ylabel('Normalized by Stokes I')
		pylab.title('%s time=%d' % (outputpath[:-1],itime))
		pylab.grid()
		pylab.legend()
		pylab.savefig('%sstokesIQUVs%d.png' % (outputpath,itime))
	#pylab.plot(x, Q/I, marker='o', lw=2, label=r'Q')
	#pylab.plot(x, U/I, marker='s', lw=2, label=r'U', zorder=1.9)
	#pylab.plot(x,V/I, marker='^', lw=2, label=r'V', zorder=1.9)

		pylab.figure(10+itime)
		pylab.xlim((x[0], x[-1]))
		pylab.xlabel('Pointing')
		pylab.ylabel('Brightness [Jy/beam]')
		pylab.title('%s' % (outputpath[:-1]))
		pylab.grid()
		pylab.legend()
		pylab.savefig('%sstokesIQUV%d.png' % (outputpath,itime))

	pylab.figure(2)
	for pointing in range(npointings):
		pylab.plot(RAoffset[pointing],DECoffset[pointing], lw=1)
		pylab.text(RAoffset[pointing],DECoffset[pointing],str(pointing))

	pylab.xlabel('RA (arcsec)')
	pylab.ylabel('DEC (arcsec)')
	pylab.title('%s pointings' % (outputpath[:-1]))
	pylab.savefig('%spointings.png' % (outputpath))

def plotstokes(outputpath):
	[RA,DEC,RAoffset,DECoffset,AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime,freq,nant]=LoadPointingInfo(outputpath)
	[leakageX,leakageY,peakIQUV,noiseIQUV,convergeFail,nactiveAntennas,validant]=readresults(outputpath)

	if len(peakIQUV)>1:
		plotstokessnap(outputpath)
		return
		
	npointings=len(RA);
	nexplodedpieces=len(peakIQUV[0])

	x=range(npointings)
	I=range(npointings)
	Q=range(npointings)
	U=range(npointings)
	V=range(npointings)
	nI=range(npointings)
	nQ=range(npointings)
	nU=range(npointings)
	nV=range(npointings)

	for explodedpiece in range (nexplodedpieces):
		for pointing in range(npointings):
			I[pointing]=peakIQUV[pointing][explodedpiece][0]
			Q[pointing]=peakIQUV[pointing][explodedpiece][1]
			U[pointing]=peakIQUV[pointing][explodedpiece][2]
			V[pointing]=peakIQUV[pointing][explodedpiece][3]
			nI[pointing]=noiseIQUV[pointing][explodedpiece][0]
			nQ[pointing]=noiseIQUV[pointing][explodedpiece][1]
			nU[pointing]=noiseIQUV[pointing][explodedpiece][2]
			nV[pointing]=noiseIQUV[pointing][explodedpiece][3]
	
	
		I=numpy.array(I,dtype='d')	
		Q=numpy.array(Q,dtype='d')	
		U=numpy.array(U,dtype='d')	
		V=numpy.array(V,dtype='d')	
		nI=numpy.array(nI,dtype='d')	
		nQ=numpy.array(nQ,dtype='d')	
		nU=numpy.array(nU,dtype='d')	
		nV=numpy.array(nV,dtype='d')	

		eQ=numpy.abs(numpy.average(Q[1:]/I[1:])-Q[0]/I[0]);
		eU=numpy.abs(numpy.average(U[1:]/I[1:])-U[0]/I[0]);
		eV=numpy.abs(numpy.average(V[1:]/I[1:])-V[0]/I[0]);
		sQ=numpy.std(Q[1:]/I[1:])
		sU=numpy.std(U[1:]/I[1:])
		sV=numpy.std(V[1:]/I[1:])
		print 'eQ=%g eU=%g eV=%g' % (eQ,eU,eV)
		print 'sQ=%g sU=%g sV=%g' % (sQ,sU,sV)

		pylab.figure(1)
		if (explodedpiece==0):
			pylab.plot(x, I, marker='x', color='c', lw=2, label=r'I')
			pylab.plot(x, Q, marker='o', color='b', lw=2,  label=r'Q')
			pylab.plot(x, U, marker='s', color='r', lw=2, label=r'U', zorder=1.9)
			pylab.plot(x,V, marker='^', color='g', lw=2, label=r'V', zorder=1.9)
		else:
			pylab.plot(x, I, marker='x', color='c', lw=2)
			pylab.plot(x, Q, marker='o', color='b', lw=2)
			pylab.plot(x, U, marker='s', color='r', lw=2)
			pylab.plot(x,V, marker='^', color='g', lw=2)

		pylab.figure(2)
		if (nexplodedpieces==1):
			pylab.errorbar(x, Q/I, nQ/I, marker='o',color='b',
	         	mfc='red', mec='blue', ms=2, mew=2, label=r'Q e=%g s=%g' %(eQ,sQ))
			pylab.errorbar(x, U/I, nQ/I, marker='s',color='r',
	         	mfc='red', mec='red', ms=2, mew=2, label=r'U e=%g s=%g' %(eU,sU))
			pylab.errorbar(x, V/I, nV/I, marker='^',color='g',
	         	mfc='red', mec='green', ms=2, mew=2, label=r'V e=%g s=%g' %(eV,sV))
		elif (explodedpiece==0):
			pylab.errorbar(x, Q/I, nQ/I, marker='o',color='b',
	         	mfc='red', mec='blue', ms=2, mew=2, label=r'Q')
			pylab.errorbar(x, U/I, nQ/I, marker='s',color='r',
	         	mfc='red', mec='red', ms=2, mew=2, label=r'U')
			pylab.errorbar(x, V/I, nV/I, marker='^',color='g',
	         	mfc='red', mec='green', ms=2, mew=2, label=r'V')
		else:
			pylab.errorbar(x, Q/I, nQ/I, marker='o',color='b',
	         	mfc='red', mec='blue', ms=2, mew=2)
			pylab.errorbar(x, U/I, nQ/I, marker='s',color='r',
	         	mfc='red', mec='red', ms=2, mew=2)
			pylab.errorbar(x, V/I, nV/I, marker='^',color='g',
	         	mfc='red', mec='green', ms=2, mew=2)

	#pylab.plot(x, Q/I, marker='o', lw=2, label=r'Q')
	#pylab.plot(x, U/I, marker='s', lw=2, label=r'U', zorder=1.9)
	#pylab.plot(x,V/I, marker='^', lw=2, label=r'V', zorder=1.9)

	pylab.figure(1)
	pylab.xlim((x[0], x[-1]))
	pylab.xlabel('Pointing')
	pylab.ylabel('Brightness [Jy/beam]')
	pylab.title('%s' % (outputpath[:-1]))
	pylab.grid()
	pylab.legend()
	pylab.savefig('%sstokesIQUV.png' % (outputpath))

	pylab.figure(2)
	pylab.xlim((x[0], x[-1]))
	pylab.ylim(-0.04, 0.14)
	pylab.xlabel('Pointing')
	pylab.ylabel('Normalized by Stokes I')
	pylab.title('%s' % (outputpath[:-1]))
	pylab.grid()
	pylab.legend()
	pylab.savefig('%sstokesIQUVs.png' % (outputpath))

#	pylab.show()

def plotfreqleakage(outputpath,pointing):
	[RA,DEC,RAoffset,DECoffset,AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime,freq,nant]=LoadPointingInfo(outputpath)
	[leakageX,leakageY,peakIQUV,noiseIQUV,convergeFail,nactiveAntennas,validant]=readresults(outputpath)

	npointings=len(RA)
	nfreq=len(leakageX[0])
	nant=len(leakageX[0][0])
	
	pylab.figure(1)
	for iant in range(nant):
		fleakageX=numpy.array(range(nfreq),dtype='complex')
		fleakageY=numpy.array(range(nfreq),dtype='complex')
		firstfinitepiece=-1
		for ifreq in range(nfreq):
			fleakageX[ifreq]=leakageX[pointing][ifreq][iant];
			fleakageY[ifreq]=leakageY[pointing][ifreq][iant];
			if ((firstfinitepiece<0)&(numpy.isfinite(fleakageX[ifreq]))&(numpy.isfinite(fleakageY[ifreq]))&(~((fleakageX[ifreq]==0.0)&(fleakageY[ifreq]==0.0)))):
				firstfinitepiece=ifreq
		if (firstfinitepiece<0):
			continue
			
		#otherwise this is a calibrated antenna
#		print iant,numpy.real(fleakageX), numpy.imag(fleakageX)

		pylab.figure(1)
		pylab.plot(numpy.real(fleakageX), numpy.imag(fleakageX), marker='o', lw=1, label=r'%d' %(iant+1))
		if (firstfinitepiece>=0):
			pylab.text(numpy.real(fleakageX[firstfinitepiece]), numpy.imag(fleakageX[firstfinitepiece]),str(iant+1))
		pylab.figure(2)
		pylab.plot(numpy.real(fleakageY), numpy.imag(fleakageY), marker='o', lw=1, label=r'%d' %(iant+1))
		if (firstfinitepiece>=0):
			pylab.text(numpy.real(fleakageY[firstfinitepiece]), numpy.imag(fleakageY[firstfinitepiece]),str(iant+1))
	
	pylab.figure(1)
	pylab.xlabel('Real')
	pylab.ylabel('Imaginary')
	pylab.title('%s leakageX-p%d for %d antennas' % (outputpath[:-1],pointing,len(validant)))
	pylab.grid()
 	pylab.xlim((-0.2, 0.2))
	pylab.ylim((-0.2, 0.2))
	pylab.savefig('%sleakageX-p%d.png' % (outputpath,pointing))

	pylab.figure(2)
	pylab.xlabel('Real')
	pylab.ylabel('Imaginary')
	pylab.title('%s leakageY-p%d' % (outputpath[:-1],pointing))
	pylab.grid()
	pylab.xlim((-0.2, 0.2))
	pylab.ylim((-0.2, 0.2))
	pylab.savefig('%sleakageY-p%d.png' % (outputpath,pointing))

def plotantleakage(outputpath,iant):#iant starts at 1
	[RA,DEC,RAoffset,DECoffset,AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime,freq,nant]=LoadPointingInfo(outputpath)
	[leakageX,leakageY,peakIQUV,noiseIQUV,convergeFail,nactiveAntennas,validant]=readresults(outputpath)

	npointings=len(leakageX)
	nfreq=len(leakageX[0])
	nant=len(leakageX[0][0])
	
	print 'leakageX', leakageX
	print 'leakageY', leakageY
	
	linewidth=[1,4,3,2,1,1,2,3,4,4,3,2,1,1,2,3,4]
	markers=['o','>','>','>','>','<','<','<','<','^','^','^','^','v','v','v','v']
	colouring=['k','r','r','r','r','r','r','r','r','b','b','b','b','b','b','b','b']
#	colouring=['k','r','m','g','b','b','g','m','r','r','m','g','b','b','g','m','r']
	pylab.figure(1)
	for pointing in range(npointings):
		fleakageX=numpy.array(range(nfreq),dtype='complex')
		fleakageY=numpy.array(range(nfreq),dtype='complex')
		for ifreq in range(nfreq):
			fleakageX[ifreq]=leakageX[pointing][ifreq][iant-1];
			fleakageY[ifreq]=leakageY[pointing][ifreq][iant-1];
		
#		pylab.subplot(121)
		pylab.plot(numpy.real(fleakageX),numpy.imag(fleakageX), markersize=6,marker=markers[pointing], lw=linewidth[pointing], color=colouring[pointing])
		pylab.text(numpy.real(fleakageX[0]),numpy.imag(fleakageX[0]),str(pointing))
#		pylab.subplot(122)
#		pylab.plot(numpy.real(fleakageY),numpy.imag(fleakageY), markersize=6,marker=markers[pointing], lw=linewidth[pointing], color=colouring[pointing])
#		pylab.text(numpy.real(fleakageY[0]),numpy.imag(fleakageY[0]),str(pointing))
		
#		pylab.text(RADEC[pointing][0],RADEC[pointing][1],str(pointing))
#		pylab.plot(numpy.real(fleakageX), numpy.imag(fleakageX), marker='o', lw=1, label=r'%d' %(iant+1))
#		pylab.figure(2)
#		pylab.plot(numpy.real(fleakageY), numpy.imag(fleakageY), marker='o', lw=1, label=r'%d' %(iant+1))


	pylab.figure(1)
#	pylab.subplot(121)
	pylab.xlabel('Real')
	pylab.ylabel('Imaginary')
	pylab.title('%s leakageX-a%d, for %d pointings' % (outputpath[:-1],iant,npointings))
	pylab.grid()
#	pylab.xlim((-0.1, 0.3))
#	pylab.ylim((-0.05, 0.1))
#	pylab.subplot(122)
#	pylab.xlabel('Real')
#	pylab.ylabel('Imaginary')
#	pylab.title('%s leakageY-a%d, for %d pointings' % (outputpath[:-1],iant,npointings))
#	pylab.grid()
#	pylab.xlim((-0.1, 0.3))
#	pylab.ylim((-0.05, 0.1))
	
	pylab.savefig('%sleakageX-a%d.png' % (outputpath,iant))

	pylab.figure(2)
	for pointing in range(npointings):
		pylab.plot(RAoffset[pointing],DECoffset[pointing], marker=markers[pointing],color=colouring[pointing], lw=1)
		pylab.text(RAoffset[pointing],DECoffset[pointing],str(pointing))

	pylab.xlabel('Relative RA (arcsec)')
	pylab.ylabel('Relative DEC (arcsec)')
	pylab.title('%s pointings' % (outputpath[:-1]))
	pylab.savefig('%spointings.png' % (outputpath))
#	pylab.show()
	
#not used
def plotantradec(outputpath,iant):#iant starts at 1
	[RA,DEC,RAoffset,DECoffset,AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime,freq,nant]=LoadPointingInfo(outputpath)
	[leakageX,leakageY,peakIQUV,noiseIQUV,convergeFail,nactiveAntennas,validant]=readresults(outputpath)

	npointings=len(RADEC)
	nfreq=len(leakageX[0])
	nant=len(leakageX[0][0])
	
	linewidth=[1,4,3,2,1,1,2,3,4,4,3,2,1,1,2,3,4]
	markers=['o','>','>','>','>','<','<','<','<','^','^','^','^','v','v','v','v']
	colouring=['k','r','r','r','r','r','r','r','r','b','b','b','b','b','b','b','b']
#	colouring=['k','r','m','g','b','b','g','m','r','r','m','g','b','b','g','m','r']
	pylab.figure(1)
	for ifreq in range(nfreq):
		fleakageX=numpy.array(range(nfreq),dtype='complex')
		fleakageY=numpy.array(range(nfreq),dtype='complex')
		for pointing in range(npointings):
			fleakageX[ifreq]=leakageX[pointing][ifreq][iant-1];
			fleakageY[ifreq]=leakageY[pointing][ifreq][iant-1];
		
		subplot(211)
		pylab.plot(numpy.real(fleakageX),numpy.imag(fleakageX), markersize=6,marker=markers[pointing], lw=linewidth[pointing], color=colouring[pointing])
		pylab.text(numpy.real(fleakageX[0]),numpy.imag(fleakageX[0]),str(pointing))
		subplot(212)
		pylab.plot(numpy.real(fleakageY),numpy.imag(fleakageY), markersize=6,marker=markers[pointing], lw=linewidth[pointing], color=colouring[pointing])
		pylab.text(numpy.real(fleakageY[0]),numpy.imag(fleakageY[0]),str(pointing))
		
#		pylab.text(RADEC[pointing][0],RADEC[pointing][1],str(pointing))
#		pylab.plot(numpy.real(fleakageX), numpy.imag(fleakageX), marker='o', lw=1, label=r'%d' %(iant+1))
#		pylab.figure(2)
#		pylab.plot(numpy.real(fleakageY), numpy.imag(fleakageY), marker='o', lw=1, label=r'%d' %(iant+1))


	pylab.figure(1)
	subplot(211)
	pylab.plot(numpy.real(fleakageX),numpy.imag(fleakageX), markersize=6,marker=markers[pointing], lw=linewidth[pointing], color=colouring[pointing])
	pylab.text(numpy.real(fleakageX[0]),numpy.imag(fleakageX[0]),str(pointing))
	pylab.xlabel('Real')
	pylab.ylabel('Imaginary')
	pylab.title('%s leakageX-a%d, for %d pointings' % (outputpath[:-1],iant,npointings))
	pylab.grid()
	pylab.xlim((-0.1, 0.3))
	pylab.ylim((-0.05, 0.1))
	subplot(212)
	pylab.plot(numpy.real(fleakageX),numpy.imag(fleakageX), markersize=6,marker=markers[pointing], lw=linewidth[pointing], color=colouring[pointing])
	pylab.text(numpy.real(fleakageX[0]),numpy.imag(fleakageX[0]),str(pointing))
	pylab.xlabel('Real')
	pylab.ylabel('Imaginary')
	pylab.title('%s leakageX-a%d, for %d pointings' % (outputpath[:-1],iant,npointings))
	pylab.grid()
	pylab.xlim((-0.1, 0.3))
	pylab.ylim((-0.05, 0.1))
	pylab.savefig('%sleakageX-a%d.png' % (outputpath,iant))

	pylab.figure(2)
	for pointing in range(npointings):
		pylab.plot(RADECoffset[pointing][0],RADECoffset[pointing][1], marker=markers[pointing],color=colouring[pointing], lw=1)
		pylab.text(RADECoffset[pointing][0],RADECoffset[pointing][1],str(pointing))
	
# ================================ Main function ================================
# Parse command-line options and arguments
parser = optparse.OptionParser(usage="%prog [options] path",
                               description="Plots the calibration or performance results \
                                            stored at a given path. Either leakages are plotted at a specified\
											pointing; or leakages for different pointings for the specified antenna\
											is plotted. Without specified options, the stokes I,Q,U,V results are plotted.")
parser.set_defaults(pointing=-1, antenna=-1)
parser.add_option("-p", "--pointing", dest="pointing", type=int, \
              	help="type of plot to be drawn")
parser.add_option("-a", "--antenna", dest="antenna", type=int, \
              	help="type of plot to be drawn")
(options, args) = parser.parse_args()

if len(args) < 1:
    parser.error("Please specify path")

outputpath=ensurepathformat(args[0])

if (options.pointing>=0):
	plotfreqleakage(outputpath,options.pointing)
elif (options.antenna>0):#antenna start at 1
	plotantleakage(outputpath,options.antenna)
else:
	plotstokes(outputpath)
