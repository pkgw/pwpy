#!/usr/bin/python
#Mattieu de Villiers mattieu@ska.ac.za 10 May 2010
from struct import unpack
import optparse, commands, sys, numpy, pickle#, pylab

deletefiles=0

# ================================ Helper functions ================================
#execute unix command and record stdio to log file
def executelog(cmd):
	tmplog=commands.getstatusoutput(cmd)
	print tmplog[1];
	thelogfile.write(tmplog[1])
	return tmplog

#generates suitable output path name given input flags and ensure directory exists. If it does - error - user must delete directory first
def ensureoutputpath(parser):
	(options, args) = parser.parse_args()

	if len(args) < 1:
	    parser.error("Please specify dataset: eg hex7, crossa, crossc, mos1000, mos1430, mos1800, mos2010")
	dataset=args[0]
	
	outputpath=options.outputpath;
	if len(outputpath):
		commands.getstatusoutput('mkdir -p %s' % (outputpath));
		if outputpath[-1]!='/':
			outputpath+='/'
	if len(options.remant):
		sappend='s%d' % (len(options.remant.split(',')))
	else:
		sappend=''
	if (options.imagepertimepiece):
		options.npieces=options.imagepertimepiece
		fappend='T'
	elif (options.imageperpiece):
		options.npieces=options.imageperpiece
		fappend='E'
	else:
		fappend='f'
	
	outputpath+='%sp%s%s%da%d%s/'%(dataset,options.refpointing,fappend,options.npieces,options.refant,sappend)
	
	tmplog=commands.getstatusoutput('mkdir %s' % (outputpath));
	if (tmplog[0]):
#		print 'Warning: Output directory %s already exist' % (outputpath)
		parser.error('Error %s already exists' % outputpath)
	else:
		print 'Output directory %s created' % (outputpath)
			
	if ((options.refpointing=='A')|(options.refpointing=='a')):
		options.refpointing=-1# so calibrate each pointing
	else:
		options.refpointing=int(options.refpointing)

	return dataset, outputpath, options
	
#creates input file name from components, adding pointing
def forminputfilename(parser,inputpath,visfilename0,refpointing,visfilename1):
	if len(visfilename1):
		inputfilename='%s%d%s' % (visfilename0,refpointing,visfilename1)
	else:
		inputfilename='%s' % (visfilename0)
	tmplog=commands.getstatusoutput('ls %s%s' %(inputpath,inputfilename))
	if (tmplog[0]):
		parser.error('Input file %s%s not found' % (inputpath,inputfilename))
	return inputfilename	

#reads leakage values directly from miriad's binary file format
def readleakage(outputpath,pointing,piece,nant):
	leakageX=range(nant)
	leakageY=range(nant)
	f=open('%sp%df%d/leakage' % (outputpath,pointing,piece),"rb")
	unpack('>f',f.read(4))#garbage
	unpack('>f',f.read(4))#garbage
	for iant in range(nant):
		leakageX[iant]=numpy.double(unpack('>f',f.read(4))[0])
		leakageX[iant]=leakageX[iant]+numpy.double(unpack('>f',f.read(4))[0])*complex(0,1)
		leakageY[iant]=numpy.double(unpack('>f',f.read(4))[0])
		leakageY[iant]=leakageY[iant]+numpy.double(unpack('>f',f.read(4))[0])*complex(0,1)
	f.close()
	return numpy.array(leakageX,dtype='complex'), numpy.array(leakageY,dtype='complex')

#to be deleted!!
#clumsy way of obtaining leakage values (axis = 'amp' or 'phase') by calling gpplt, writing to file, reading from file...
def readgpplt(outputpath,pointing,piece,nant,axis):
	x=[];
	tmp=executelog('gpplt vis=%sp%df%d options=polarization yaxis=%s log=%sp%df%d-%s.txt' % (outputpath,pointing,piece,axis,outputpath,pointing,piece,axis));

	if (tmp[0]):
		return numpy.array([numpy.inf for x in range(nant)]),numpy.array([numpy.inf for x in range(nant)])
	f = open('%sp%df%d-%s.txt' % (outputpath,pointing,piece,axis),"r")
	for headerline in range(0,5):
		line = f.readline()		

	dataX = []
	dataY = []

	while line <> "":
		line=numpy.array(line.split(), dtype='f');
		dataX.extend(line[::2]);
		dataY.extend(line[1::2]);
		line = f.readline();
	f.close()
	return numpy.array(dataX, dtype='d'), numpy.array(dataY, dtype='d')

#interprets prthd to read the number of pixels in dirty image
#returns number of pixels for RA, DEC
def readprthd(prthdoutput):
	lines=prthdoutput[1].split('\n')
	if len(lines)<18:
		print lines
		parser.error("Error reading prthd")
		return '1000'
	for index in range(7,10):
		line=lines[index].split()
		if (len(line)>2):
			if ((line[0]=='Type')&(line[1]=='Pixels')):
				linera=lines[index+1].split()
				linedec=lines[index+2].split()
				return int(linera[1]),int(linedec[1])
	return 0,0

#interprets imfit output - extracts peak value from image
def readimfit(imfitoutput):
	lines=imfitoutput[1].split('\n')
	if len(lines)<15:
		print lines
		parser.error("Error reading imfit")
	line=lines[14].split()
	if (line[0]!='Peak'):
		line=lines[15].split()
	return line[2];

#interprets imstat output - extract noise from image
def readimstat(imstatoutput):
	lines=imstatoutput[1].split('\n')
	if len(lines)<18:
		print lines
#		parser.error("Error reading imstat")
		return '1000'
	line=lines[17]
	return line[41:51]

#reads RA,DEC,freq,nant values from input (vis) dataset using prthd
def readRADEC(inputpath,filename,outputpath,pointing):
	prthdoutput=executelog('prthd in=%s%s' % (inputpath,filename))
	if (prthdoutput[0]):
		parser.error("Error reading %s%s" % (inputpath,filename))
	lines=prthdoutput[1].split('\n')
	pointingRA=0
	pointingDEC=0
	freq=0
	for iline in range(len(lines)):
		line=lines[iline].split()
		if len(line)>2:
			if (line[0]=='J2000')&(line[1]=='Source'):
				RAdms=numpy.array(line[3].split(':'),dtype='d')
				DECdms=numpy.array(line[5].split(':'),dtype='d')
				RA=RAdms[0]+RAdms[1]/60.0+RAdms[2]/(60.0*60.0)#in hours
				DEC=DECdms[0]+DECdms[1]/60.0+DECdms[2]/(60.0*60.0)#in degrees
				freq=float(lines[iline-4].split()[4])
			elif (line[0]=='Pointing')&(line[1]=='Centre'):
				RAdms=numpy.array(line[3].split(':'),dtype='d')
				DECdms=numpy.array(line[5].split(':'),dtype='d')
				pointingRA=RAdms[0]+RAdms[1]/60.0+RAdms[2]/(60.0*60.0)#in hours
				pointingDEC=DECdms[0]+DECdms[1]/60.0+DECdms[2]/(60.0*60.0)#in degrees

	if (pointingRA==0):
		tmplog=executelog('varplt vis="%s%s" xaxis=dra yaxis=ddec log=%sp%d-draddec.txt' % (inputpath,filename,outputpath,pointing))

		if (tmplog[0]):#error, shouldnt happen
			RAoffset=0
			DECoffset=0
		else:
			f = open('%sp%d-draddec.txt' % (outputpath,pointing),"r")
			for headerline in range(0,4):
				line = f.readline()		
			[RAoffset,DECoffset]=numpy.array(line.split(), dtype='d') #in arcsec
			f.close()
	else:
		RAoffset=(pointingRA-RA)*60.0*60.0*360.0/24.0*numpy.cos(DEC*numpy.pi/180.0)#convert hours to arcsec
		DECoffset=(pointingDEC-DEC)*60.0*60.0#convert degrees to arcsec
			
	if len(lines)<18:
		print lines
		parser.error("Errorrror reading RADEC")
	line=lines[6].split()
	nant=numpy.array(line[3],dtype='i')

	return RA,DEC,RAoffset,DECoffset,freq,nant

#reads information trom visibility file: azel is 'obsaz' or 'obsel' or 'chi'
def readAZEL(inputpath,visfilename,outputpath,pointing,filestarttime,filestoptime,azel):
	print 'varplt vis=%s%s xaxis=time yaxis=%s log=%sp%d%s.txt' % (inputpath,visfilename,azel,outputpath,pointing,azel)
	varpltoutput=executelog('varplt vis=%s%s xaxis=time yaxis=%s log=%sp%d%s.txt' % (inputpath,visfilename,azel,outputpath,pointing,azel))
	if (varpltoutput[0]):
		#note that hex7 does not have obsaz
		return []
#		parser.error("Error reading %s%s" % (inputpath,visfilename))
	if (len(varpltoutput[1].split('\n'))>2):#sometimes miriad does not output to file...
		f = open('%sp%d%s.txt' % (outputpath,pointing,azel),"wt")
		f.write(varpltoutput[1])#NOTE extra first line; but reading below can cope with changing header size
		f.close()
		
	f = open('%sp%d%s.txt' % (outputpath,pointing,azel),"r")
	line = f.readline()
	line = f.readline()
	line = f.readline()
	line = f.readline()
	line = f.readline()
	itime=0
	startazel=range(len(filestarttime))
	stopazel=range(len(filestarttime))
	while line <> "":
		line=line.split()
		if ((line[0]==filestarttime[itime][0])&(line[1]==filestarttime[itime][1])):
			startazel[itime]=float(line[2])
		elif ((line[0]==filestoptime[itime][0])&(line[1]==filestoptime[itime][1])):
			stopazel[itime]=float(line[2])
			itime=itime+1
			if (itime>=len(filestarttime)):
				break
		line = f.readline();
	f.close()

	return 0.5*(numpy.array(startazel)+numpy.array(stopazel))

def makeTime(basetime,extraday,time):
	return '%s%02d:%s' %(basetime[:5],int(basetime[5:7])+int(extraday),time)
	
def readTime(inputpath,visfilename,outputpath,pointing):
	varpltoutput=executelog('varplt vis=%s%s xaxis=time yaxis=ut log=%sp%dtime.txt' % (inputpath,visfilename,outputpath,pointing))
	if (varpltoutput[0]):
		parser.error("Error reading %s%s" % (inputpath,visfilename))
		
	f = open('%sp%dtime.txt' % (outputpath,pointing),"r")
	line = f.readline()		
	line = f.readline()		
	basetime=line.split()[4].split(':')[0] #should be eg '10MAY16' ie YYMMMDD, have verified this!
	line = f.readline()		
	line = f.readline()		
	line = f.readline()		
	starttime=[]
	stoptime=[]
	utstarttime=[]
	utstoptime=[]
	filestarttime=[]
	filestoptime=[]
	lastextraday=0
	lasttime=-24
	lasthmstime=0
	while line <> "":
		line=line.split()
		extraday=line[0]
		hmstime=line[1]
		uttime=line[2]
		time=24*float(extraday)+float(uttime)
		if (time-lasttime>0.1):
			if (lasttime>=0):
				stoptime.append(makeTime(basetime,lastextraday,lasthmstime))
				filestoptime.append([lastextraday,lasthmstime])
				utstoptime.append(lasttime)
			starttime.append(makeTime(basetime,extraday,hmstime))
			filestarttime.append([extraday,hmstime])
			utstarttime.append(time)
		lasthmstime=hmstime
		lasttime=time
		lastextraday=extraday
		line = f.readline();
	f.close()
	stoptime.append(makeTime(basetime,lastextraday,lasthmstime))
	filestoptime.append([lastextraday,lasthmstime])
	utstoptime.append(lasttime)
	print starttime
	print stoptime
	AZ=readAZEL(inputpath,visfilename,outputpath,pointing,filestarttime,filestoptime,'obsaz')
	EL=readAZEL(inputpath,visfilename,outputpath,pointing,filestarttime,filestoptime,'obsel')
	CHI=readAZEL(inputpath,visfilename,outputpath,pointing,filestarttime,filestoptime,'chi')
	LST=readAZEL(inputpath,visfilename,outputpath,pointing,filestarttime,filestoptime,'lst')
	print AZ
	print EL
	print CHI
	return [AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime]

#assuming pointing info already extracted from vis files, load it
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

#combine snapshot time samples
#reduction=1 or 2 or 3 is integer
def combinesnaptime(reduction,CHI,LST,starttime,stoptime,utstarttime,utstoptime):
	newntime=(len(CHI[0])/reduction)*reduction;
	npointings=len(CHI)
	nCHI=range(npointings)
	nLST=range(npointings)
	nstarttime=range(npointings)
	nstoptime=range(npointings)
	nutstarttime=range(npointings)
	nutstoptime=range(npointings)
	for ipointing in range(npointings):
		nCHI[ipointing]=0.5*(CHI[ipointing][:newntime:reduction]+CHI[ipointing][1:newntime:reduction])
		nLST[ipointing]=0.5*(LST[ipointing][:newntime:reduction]+LST[ipointing][1:newntime:reduction])
		nstarttime[ipointing]=starttime[ipointing][:newntime:reduction]
		nstoptime[ipointing]=stoptime[ipointing][1:newntime:reduction]
		nutstarttime[ipointing]=utstarttime[ipointing][:newntime:reduction]
		nutstoptime[ipointing]=utstoptime[ipointing][1:newntime:reduction]
	nCHI=numpy.array(nCHI)
	nLST=numpy.array(nLST)
	nstarttime=numpy.array(nstarttime)
	nstoptime=numpy.array(nstoptime)
	nutstarttime=numpy.array(nutstarttime)
	nutstoptime=numpy.array(nutstoptime)
	return nCHI,nLST,nstarttime,nstoptime,nutstarttime,nutstoptime
	
def ReducePointingInfo(reduction,outputpath,RA,DEC,RAoffset,DECoffset,AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime,freq,nant):
	if (reduction>1):
		[CHI,LST,starttime,stoptime,utstarttime,utstoptime]=combinesnaptime(reduction,CHI,LST,starttime,stoptime,utstarttime,utstoptime)
	output=open('%spointinginfo' % (outputpath), 'wb')#overwrite values in local directory
	pickle.dump(RA,output)
	pickle.dump(DEC,output)
	pickle.dump(RAoffset,output)
	pickle.dump(DECoffset,output)
	pickle.dump(AZ,output)
	pickle.dump(EL,output)
	pickle.dump(CHI,output)
	pickle.dump(LST,output)
	pickle.dump(starttime,output)
	pickle.dump(stoptime,output)
	pickle.dump(utstarttime,output)
	pickle.dump(utstoptime,output)
	pickle.dump(freq,output)	
	pickle.dump(nant,output)	
	output.close()
	return RA,DEC,RAoffset,DECoffset,AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime,freq,nant
	
#tries to load pointing info if exists, else read it from vis files
def GetPointingInfo(parser,inputpath,outputpath,visfilename0,visfilename1,npointings):	
	tmplog=commands.getstatusoutput('ls %spointinginfo' % (outputpath))
	if (tmplog[0]==0):
		return LoadPointingInfo(outputpath)
	tmplog=commands.getstatusoutput('ls %spointinginfo' % (inputpath))
	if (tmplog[0]==0):#try copy from source directory
		commands.getstatusoutput('cp %spointinginfo %s' % (inputpath,outputpath))
		return LoadPointingInfo(outputpath)
	
	RA=range(npointings);
	DEC=range(npointings);
	RAoffset=range(npointings);
	DECoffset=range(npointings);
	AZ=range(npointings);
	EL=range(npointings);
	CHI=range(npointings);
	LST=range(npointings);
	starttime=range(npointings);
	stoptime=range(npointings);
	utstarttime=range(npointings);
	utstoptime=range(npointings);
	freq=0
	nant=0
	for pointing in range(npointings):# get pointings first in case refpointing is not 0
		visfilename=forminputfilename(parser,inputpath,visfilename0,pointing,visfilename1)
		[RA[pointing],DEC[pointing],RAoffset[pointing],DECoffset[pointing],freq,nant]=readRADEC(inputpath,visfilename,outputpath,pointing)
		[AZ[pointing],EL[pointing],CHI[pointing],LST[pointing],starttime[pointing],stoptime[pointing],utstarttime[pointing],utstoptime[pointing]]=readTime(inputpath,visfilename,outputpath,pointing)
		
	RA=numpy.array(RA)
	DEC=numpy.array(DEC)
	RAoffset=numpy.array(RAoffset)
	DECoffset=numpy.array(DECoffset)
	AZ=numpy.array(AZ)
	EL=numpy.array(EL)
	CHI=numpy.array(CHI)
	LST=numpy.array(LST)
#	starttime=string not numpy.array(starttime)
#	stoptime=string not numpy.array(stoptime)
	utstarttime=numpy.array(utstarttime)
	utstoptime=numpy.array(utstoptime)
	freq=numpy.array(freq)#does nothing
	nant=numpy.array(nant)#does nothing
	
	output=open('%spointinginfo' % (inputpath), 'wb')
	pickle.dump(RA,output)
	pickle.dump(DEC,output)
	pickle.dump(RAoffset,output)
	pickle.dump(DECoffset,output)
	pickle.dump(AZ,output)
	pickle.dump(EL,output)
	pickle.dump(CHI,output)
	pickle.dump(LST,output)
	pickle.dump(starttime,output)
	pickle.dump(stoptime,output)
	pickle.dump(utstarttime,output)
	pickle.dump(utstoptime,output)
	pickle.dump(freq,output)	
	pickle.dump(nant,output)	
	output.close();
	commands.getstatusoutput('cp %spointinginfo %s' % (inputpath,outputpath))
	return RA,DEC,RAoffset,DECoffset,AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime,freq,nant

#makes regions based on dirty image size
def makeregions(npixxy):
	fitmax=15 #specifies distance in pixels away from origin (in x,y direction) in which fit is performed
	noiseextra=5 #specifies extra buffer zone around fit region to avoid when determining noise
	defaultmax=50 #default region size (distance away from origin in x,y directions)
	maxx=(npixxy[0]-1)/2
	maxy=(npixxy[1]-1)/2
	if (maxx>defaultmax):
		maxx=defaultmax
	if (maxy>defaultmax):
		maxy=defaultmax
	region='relpixel,boxes(-%d,-%d,%d,%d)' % (maxx,maxy,maxx,maxy)
	fitregion='relpixel,boxes(-%d,-%d,%d,%d)' % (fitmax,fitmax,fitmax,fitmax)
	noiseregion='relpixel,boxes(-%d,-%d,%d,-%d)' % (maxx,maxy,maxx,fitmax+noiseextra)
	return region, fitregion, noiseregion

#image IQUV by combining all frequency pieces using MFS - this corresponds to option f (frequency)
def imageIQUV(outputpath,pointing,convergeFail):
	npieces=len(convergeFail)
	peakIQUV=[[[0,0,0,0]]]
	noiseIQUV=[[[0,0,0,0]]]
	stokes=['i','q','u','v']
	robust=[0,-2,-2,-2]
	niters=[400,200,200,200]
	imagingnamelist=''
	for piece in range(npieces):
		if (convergeFail[piece]):
			continue
		if len(imagingnamelist):
			imagingnamelist+=',%sp%df%d' % (outputpath,pointing,piece);
		else:
			imagingnamelist='%sp%df%d' % (outputpath,pointing,piece);
		
	for count in range(4):
		executelog('invert vis=%sp%df%d options=mfs map=%sp%df%d-%s.mp beam=%sp%df%d-%s.bm stokes=%s robust=%d' % (outputpath,pointing,piece,outputpath,pointing,piece,stokes[count],outputpath,pointing,piece,stokes[count],stokes[count],robust[count]));
		[region,fitregion,noiseregion]=makeregions(readprthd(executelog('prthd in=%sp%df%d-%s.mp' % (outputpath,pointing,piece,stokes[count]))));
		executelog('clean map=%sp%df%d-%s.mp beam=%sp%df%d-%s.bm out=%sp%df%d-%s.cl niters=%d region="%s"' % (outputpath,pointing,piece,stokes[count],outputpath,pointing,piece,stokes[count],outputpath,pointing,piece,stokes[count],niters[count],region));
		executelog('restor map=%sp%df%d-%s.mp beam=%sp%df%d-%s.bm out=%sp%df%d-%s.rm model=%sp%df%d-%s.cl' % (outputpath,pointing,piece,stokes[count],outputpath,pointing,piece,stokes[count],outputpath,pointing,piece,stokes[count],outputpath,pointing,piece,stokes[count]));
		peakIQUV[0][0][count]=readimfit(executelog('imfit in=%sp%df%d-%s.rm object=point region="%s"' % (outputpath,pointing,piece,stokes[count],fitregion)))
		noiseIQUV[0][0][count]=readimstat(executelog('imstat in=%sp%df%d-%s.rm region="%s"' % (outputpath,pointing,piece,stokes[count],noiseregion)))
		if (deletefiles):
			executelog('rm -rf "%sp%df%d-%s.mp"' % (outputpath,pointing,piece,stokes[count]));
			executelog('rm -rf "%sp%df%d-%s.bm"' % (outputpath,pointing,piece,stokes[count]));
			executelog('rm -rf "%sp%df%d-%s.cl"' % (outputpath,pointing,piece,stokes[count]));
			executelog('rm -rf "%sp%df%d-%s.rm"' % (outputpath,pointing,piece,stokes[count]));
	return numpy.array(peakIQUV, dtype='d'), numpy.array(noiseIQUV, dtype='d')
	
#image IQUV for each frequency piece individually - this corresponds to option E (for eXplode)
def imageIQUVperpiece(outputpath,pointing,convergeFail):
	npieces=len(convergeFail)
	peakIQUV =[[ [numpy.inf,numpy.inf,numpy.inf,numpy.inf] for piece in range(npieces)]]
	noiseIQUV=[[ [numpy.inf,numpy.inf,numpy.inf,numpy.inf] for piece in range(npieces)]]
	stokes=['i','q','u','v']
	robust=[0,-2,-2,-2]
	niters=[400,200,200,200]

	for piece in range(npieces):
		if (convergeFail[piece]):
			continue
		for count in range(4):
			executelog('invert vis=%sp%df%d options=mfs map=%sp%df%d-%s.mp beam=%sp%df%d-%s.bm stokes=%s robust=%d' % (outputpath,pointing,piece,outputpath,pointing,piece,stokes[count],outputpath,pointing,piece,stokes[count],stokes[count],robust[count]));
			[region,fitregion,noiseregion]=makeregions(readprthd(executelog('prthd in=%sp%df%d-%s.mp' % (outputpath,pointing,piece,stokes[count]))));
			executelog('clean map=%sp%df%d-%s.mp beam=%sp%df%d-%s.bm out=%sp%df%d-%s.cl niters=%d region="%s"' % (outputpath,pointing,piece,stokes[count],outputpath,pointing,piece,stokes[count],outputpath,pointing,piece,stokes[count],niters[count],region));
			executelog('restor map=%sp%df%d-%s.mp beam=%sp%df%d-%s.bm out=%sp%df%d-%s.rm model=%sp%df%d-%s.cl' % (outputpath,pointing,piece,stokes[count],outputpath,pointing,piece,stokes[count],outputpath,pointing,piece,stokes[count],outputpath,pointing,piece,stokes[count]));
			peakIQUV[0][piece][count]=readimfit(executelog('imfit in=%sp%df%d-%s.rm object=point region="%s"' % (outputpath,pointing,piece,stokes[count],fitregion)))
			noiseIQUV[0][piece][count]=readimstat(executelog('imstat in=%sp%df%d-%s.rm region="%s"' % (outputpath,pointing,piece,stokes[count],noiseregion)))
			if (deletefiles):
				executelog('rm -rf "%sp%df%d-%s.mp"' % (outputpath,pointing,piece,stokes[count]));
				executelog('rm -rf "%sp%df%d-%s.bm"' % (outputpath,pointing,piece,stokes[count]));
				executelog('rm -rf "%sp%df%d-%s.cl"' % (outputpath,pointing,piece,stokes[count]));
				executelog('rm -rf "%sp%df%d-%s.rm"' % (outputpath,pointing,piece,stokes[count]));
	print "----------------------------------------------------------"
	print "PEAKIQUV",peakIQUV
	print "NOISEIQUV",noiseIQUV
	return numpy.array(peakIQUV, dtype='d'), numpy.array(noiseIQUV, dtype='d')


#snapshot imaging! 
#image IQUV for each frequency piece, for each time period individually - this corresponds to option T (exploded in Time) 
def imageIQUVsnapperpiece(outputpath,pointing,convergeFail,starttime,stoptime):
	npieces=len(convergeFail)
	stokes=['i','q','u','v']
	robust=[0,-2,-2,-2]
	niters=[400,200,200,200]

	peakIQUV =[[ [numpy.inf,numpy.inf,numpy.inf,numpy.inf] for piece in range(npieces)] for itime in range(len(starttime))]
	noiseIQUV=[[ [numpy.inf,numpy.inf,numpy.inf,numpy.inf] for piece in range(npieces)] for itime in range(len(starttime))]

	for itime in range(len(starttime)):
		print "starttime",starttime[itime]
		print "stoptime",stoptime[itime]		
		for piece in range(npieces):
			print "piece %d"%(piece)
#			executelog('uvaver vis=%sp%df%d out=%sp%df%dt%d interval=0.001 select="time(%s,%s)" options=nocal,nopass,nopol' % (outputpath,pointing,piece,outputpath,pointing,piece,itime,starttime[itime],stoptime[itime]))
			executelog('uvaver vis=%sp%df%d out=%sp%df%dt%d interval=0.001 select="time(%s,%s)"' % (outputpath,pointing,piece,outputpath,pointing,piece,itime,starttime[itime],stoptime[itime]))
			if (convergeFail[piece]):
				continue
			for count in range(4):
				executelog('invert vis=%sp%df%dt%d options=mfs map=%sp%df%dt%d-%s.mp beam=%sp%df%dt%d-%s.bm stokes=%s robust=%d' % (outputpath,pointing,piece,itime,outputpath,pointing,piece,itime,stokes[count],outputpath,pointing,piece,itime,stokes[count],stokes[count],robust[count]));
				[region,fitregion,noiseregion]=makeregions(readprthd(executelog('prthd in=%sp%df%dt%d-%s.mp' % (outputpath,pointing,piece,itime,stokes[count]))));
				executelog('clean map=%sp%df%dt%d-%s.mp beam=%sp%df%dt%d-%s.bm out=%sp%df%dt%d-%s.cl niters=%d region="%s"' % (outputpath,pointing,piece,itime,stokes[count],outputpath,pointing,piece,itime,stokes[count],outputpath,pointing,piece,itime,stokes[count],niters[count],region));
				executelog('restor map=%sp%df%dt%d-%s.mp beam=%sp%df%dt%d-%s.bm out=%sp%df%dt%d-%s.rm model=%sp%df%dt%d-%s.cl' % (outputpath,pointing,piece,itime,stokes[count],outputpath,pointing,piece,itime,stokes[count],outputpath,pointing,piece,itime,stokes[count],outputpath,pointing,piece,itime,stokes[count]));
				print 'analyzing %sp%df%dt%d-%s.rm' % (outputpath,pointing,piece,itime,stokes[count])
				peakIQUV[itime][piece][count]=readimfit(executelog('imfit in=%sp%df%dt%d-%s.rm object=point region="%s"' % (outputpath,pointing,piece,itime,stokes[count],fitregion)))
				noiseIQUV[itime][piece][count]=readimstat(executelog('imstat in=%sp%df%dt%d-%s.rm region="%s"' % (outputpath,pointing,piece,itime,stokes[count],noiseregion)))
				if (deletefiles):
					executelog('rm -rf "%sp%df%dt%d-%s.mp"' % (outputpath,pointing,piece,itime,stokes[count]));
					executelog('rm -rf "%sp%df%dt%d-%s.bm"' % (outputpath,pointing,piece,itime,stokes[count]));
					executelog('rm -rf "%sp%df%dt%d-%s.cl"' % (outputpath,pointing,piece,itime,stokes[count]));
					executelog('rm -rf "%sp%df%dt%d-%s.rm"' % (outputpath,pointing,piece,itime,stokes[count]));
					
			if (deletefiles):
				executelog('rm -rf "%sp%df%dt%d"' % (outputpath,pointing,piece,itime));
				

	return numpy.array(peakIQUV, dtype='d'), numpy.array(noiseIQUV, dtype='d')
	
#do all processing for given pointing
def processpointing(inputpath,outputpath,visfilename,pointing,refpointing,npieces,imageperpiece,imagepertimepiece,refant,remant,nant,starttime,stoptime):
	# First, put data in order required by gpcal
	executelog('uvaver vis="%s%s" out="%stmp-p%d-tmp" interval=0.001 options=nocal,nopass,nopol' % (inputpath,visfilename,outputpath,pointing));

	ngroupedchannels=800/npieces
	if len(remant):
		antsel='select="-ant(%s)"'%(remant) 	#antsel='select="-ant(1,2,3)"'
	else:
		antsel=''
	leakagePiecesX=[]
	leakagePiecesY=[]
	convergeFail=range(npieces)
	nactiveAntennas=range(npieces)

	for piece in range(npieces):

		startchannel= 100+(piece)*ngroupedchannels

		# Reorder data to keep pol data in order expected by other tools.  also split in frequency

		executelog('uvaver vis="%stmp-p%d-tmp" out="%sp%df%d" line=ch,%d,%d,1,1 interval=0.001 options=nocal,nopass,nopol %s' % (outputpath,pointing,outputpath,pointing,piece,ngroupedchannels,startchannel,antsel));
		if refpointing>=0: #copy calibration parameters from calfile dataset
			executelog('gpcopy vis="%sp%df%d" out="%sp%df%d"' % (outputpath,refpointing,piece,outputpath,pointing,piece));
		else:	#calibrate this dataset
			executelog('mfcal vis="%sp%df%d" refant=%d interval=60 tol=0.0001' % (outputpath,pointing,piece,refant));
			executelog('gpcal vis="%sp%df%d" refant=%d options=xyref,polref interval=999' % (outputpath,pointing,piece,refant));
			executelog('gpcal vis="%sp%df%d" refant=%d options=xyref,polref interval=60 tol=0.000001' % (outputpath,pointing,piece,refant));

		if (1):
			[leakX,leakY]=readleakage(outputpath,pointing,piece,nant)
			convergeFail[piece]=numpy.sum((~numpy.isfinite(leakX))|(~numpy.isfinite(leakY))|(numpy.abs(leakX)>0.5)|(numpy.abs(leakY)>0.5))
			nactiveAntennas[piece]=numpy.sum((~numpy.isfinite(leakX))&(~numpy.isfinite(leakY))&(numpy.abs(leakX)<=0.5)&(numpy.abs(leakY)<=0.5)&(leakX!=0.0)&(leakY!=0.0))
			leakagePiecesX.append(leakX)
			leakagePiecesY.append(leakY)
		else:
			[leakampX,leakampY]=readgpplt(outputpath,pointing,piece,nant, 'amp');
			[leakphaseX,leakphaseY]=readgpplt(outputpath,pointing,piece,nant, 'phase');
			convergeFail[piece]=numpy.sum((~numpy.isfinite(leakampX))|(~numpy.isfinite(leakampY))|(numpy.abs(leakampX)>0.5)|(numpy.abs(leakampY)>0.5))
			nactiveAntennas[piece]=numpy.sum((~numpy.isfinite(leakampX))&(~numpy.isfinite(leakampY))&(numpy.abs(leakampX)<=0.5)&(numpy.abs(leakampY)<=0.5)&(leakampX!=0.0)&(leakampY!=0.0))
			leakagePiecesX.append(leakampX*numpy.exp(complex(0,1)*numpy.radians(leakphaseX)))
			leakagePiecesY.append(leakampY*numpy.exp(complex(0,1)*numpy.radians(leakphaseY)))	
		
	if (imagepertimepiece):
		[peakIQUV, noiseIQUV]=imageIQUVsnapperpiece(outputpath,pointing,convergeFail,starttime,stoptime)
	elif (imageperpiece):
		[peakIQUV, noiseIQUV]=imageIQUVperpiece(outputpath,pointing,convergeFail)
	else:
		[peakIQUV, noiseIQUV]=imageIQUV(outputpath,pointing,convergeFail)		

	#print leakagePiecesX
	#print leakagePiecesY
	print convergeFail
	print peakIQUV
	print noiseIQUV

	if (deletefiles):
		executelog('rm -rf "%stmp-p%d-tmp"' % (outputpath,pointing));

	return leakagePiecesX, leakagePiecesY, peakIQUV, noiseIQUV, convergeFail, nactiveAntennas

	

# ================================ Main function ================================
# Parse command-line options and arguments
parser = optparse.OptionParser(usage="%prog [options] dataset",
                               description="This program perform polarimetric calibration and write results that can be plotted\
											later using plotstokes. The visibility data files are to be pointings of a known\
											linearly polarized source. The files are assumed to be already flagged, and convertdata\
											may need to be called (eg for cross17 but not for hex7) if header information per pointing\
											indicate different pointings (J2000 Source different in each pointing file header). The \
											program divides the frequency channels into pieces which are calibrated \
                                            separately. Calibration is done for specified pointing, or all pointings. \
											Reference antenna can be specified, and antennas to be removed from the dataset\
											can be specified. Imaging is done either by re-combining the frequency pieces that have been\
											calibrated individually, or imaging can be done per frequency piece. A final option allows\
											imaging per time sample (snapshot). The stokes I,Q,U,V values and background noise is extracted\
											from the images and can be plotted using plotstokes.")
parser.set_defaults(refpointing='A', npieces=8, imageperpiece=0, imagepertimepiece=0, refant=1, remant='', outputpath='')
parser.add_option("-p", "--reference-pointing", dest="refpointing", type="string", \
				help="Reference pointing, A means calibrate all pointings")
parser.add_option("-f", "--number-pieces", dest="npieces", type="int", \
                help="Number of pieces the frequency channels are divided into. Image MFS all pieces.")
parser.add_option("-E", "--number-pieces-exploded", dest="imageperpiece", type="int", \
                help="Number of pieces the frequency channels are divided into. Image per piece.")
parser.add_option("-T", "--number-pieces-time-exploded", dest="imagepertimepiece", type="int", \
	                help="Number of pieces the frequency channels are divided into. Image per piece per snapshot.")
parser.add_option("-a", "--reference-antenna", dest="refant", type="int", \
				help="Reference antenna")
parser.add_option("-s", "--select-remove-antenna", dest="remant", type="string", \
				help="comma separated list of antennas to remove")
parser.add_option("-o", "--outputpath", dest="outputpath", type="string", \
              	help="Directory name used as base name for output files [default is none ie currentdir]")

(dataset,outputpath,options)=ensureoutputpath(parser)
	
thelogfile=open('%slogfile.txt' % (outputpath),'wt')

if (dataset=='hex7'):
	inputpath='/Users/mattieu/Berk/data/hex7/'
	visfilename0='hexc-3c138-p'
	visfilename1='-2000.uvaver'
	npointings=7
elif (dataset=='crossa'):
	inputpath='/Users/mattieu/Berk/data/crossa/'
	visfilename0='cross17-p'
	visfilename1='-3140_c'
	npointings=17
	#warning: had to fix dataset by overwriting J2000 phase center using J2000 phase center of vis data of pointing 0
	#uvedit vis=cross17-p1-3140 source=3c286 ra=13,31,08.289 dec=30,30,32.945
	#warning also overwrite source name too (mysteriously added -p1 etc to source name causing gpcal to fail and claim its an unknown source)
elif (dataset=='crossc'):
	inputpath='/Users/mattieu/Berk/data/crossc/'
	visfilename0='cross17-p'
	visfilename1='-1430_c'
	npointings=17
	#warning: had to fix dataset by overwriting J2000 phase center using J2000 phase center of vis data of pointing 0
	#uvedit vis=cross17-p1-3140 source=3c286 ra=13,31,08.289 dec=30,30,32.945
	#warning also overwrite source name too (mysteriously added -p1 etc to source name causing gpcal to fail and claim its an unknown source)	
elif (dataset=='mos1430'):
	inputpath='/Users/mattieu/Berk/data/'
	visfilename0='mosfxa-3c286-1430-100'
	visfilename1=''
	npointings=1
elif (dataset=='mos2010'):
	inputpath='/Users/mattieu/Berk/data/'
	visfilename0='mosfxc-3c286-2010-100'
	visfilename1=''
	npointings=1
elif (dataset=='mos1000'):
	inputpath='/Users/mattieu/Berk/data/'
	visfilename0='mosfxa-3c286-1000-100'
	visfilename1=''
	npointings=1
elif (dataset=='mos1800'):
	inputpath='/Users/mattieu/Berk/data/'
	visfilename0='mosfxc-3c286-1800-100'
	visfilename1=''
	npointings=1
else:
	parser.error('Dataset %s unknown' % (dataset))
#1,3,4,7,8,11,12,13,15, 17, 19, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 39, 40, 41]
#B:3,7,11,13,17,23,25,27,29,31,33,35,39,41
#A:4,8,12,15,19,24,26,28,30,32,34,36,40,41
#crossap0T8a1s14A valid antennas: [1, 3, 7, 11, 13, 17, 23, 25, 27, 29, 31, 33, 35, 39]
#crossap0T8a1s14B valid antennas: [1, 4, 8, 12, 15, 19, 24, 26, 28, 30, 32, 34, 36, 40]
#crossap0T8a1s15A #-s4,8,12,15,19,24,26,28,30,32,34,36,40,41,27
#crossap0T8a1s16A #-s4,8,12,15,19,24,26,28,30,32,34,36,40,41,27,7
#crossap0T8a1s15C #-s4,8,12,15,19,24,26,28,30,32,34,36,40,41,23
#crossap0T8a1s16C #-s4,8,12,15,19,24,26,28,30,32,34,36,40,41,23,7
#need to do tests to see if it is possible to determine individual antenna patterns using this technique
#rather than only an effective array pattern.

leakageX=range(npointings);
leakageY=range(npointings);
peakIQUV=range(npointings);
noiseIQUV=range(npointings);
convergeFail=range(npointings);
nactiveAntennas=range(npointings);

[RA,DEC,RAoffset,DECoffset,AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime,freq,nant]=GetPointingInfo(parser,inputpath,outputpath,visfilename0,visfilename1,npointings)
if (len(CHI[0])>20):
	reduction=2
	[RA,DEC,RAoffset,DECoffset,AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime,freq,nant]=ReducePointingInfo(reduction,outputpath,RA,DEC,RAoffset,DECoffset,AZ,EL,CHI,LST,starttime,stoptime,utstarttime,utstoptime,freq,nant)

#ensures the reference pointing is evaluated first, because its leakage values may be copied over to other pointings
if (options.refpointing>=0):
	pointing=options.refpointing
	visfilename=forminputfilename(parser,inputpath,visfilename0,pointing,visfilename1)
	[leakageX[pointing], leakageY[pointing], peakIQUV[pointing], noiseIQUV[pointing], convergeFail[pointing], nactiveAntennas[pointing]]=processpointing(inputpath,outputpath,visfilename,pointing,-1,options.npieces,options.imageperpiece,options.imagepertimepiece,options.refant,options.remant,nant,starttime[pointing],stoptime[pointing])

for pointing in range(npointings):
	if (pointing==options.refpointing):
		continue
	visfilename=forminputfilename(parser,inputpath,visfilename0,pointing,visfilename1)
	[leakageX[pointing], leakageY[pointing], peakIQUV[pointing], noiseIQUV[pointing], convergeFail[pointing], nactiveAntennas[pointing]]=processpointing(inputpath,outputpath,visfilename,pointing,options.refpointing,options.npieces,options.imageperpiece,options.imagepertimepiece,options.refant,options.remant,nant,starttime[pointing],stoptime[pointing])

thelogfile.close()
output=open('%sresults' % (outputpath), 'wb')
pickle.dump(leakageX,output)
pickle.dump(leakageY,output)
pickle.dump(peakIQUV,output)
pickle.dump(noiseIQUV,output)
pickle.dump(convergeFail,output)
pickle.dump(nactiveAntennas,output)
output.close();
print '%sresults written' % (outputpath)

