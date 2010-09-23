c***********************************************************************
	program  P2M
	implicit none
c
c= P2M - Convert PoCoBI-8 correlator data to Miriad.
c& mchw
c: uv analysis
c+
c	P2M is a MIRIAD task to convert PoCoBI-8 correlator data to Miriad.
c@ in
c	The name of PoCoBI-8 file written by Glenn's "pocorx"
c
c@ out
c	This gives the name of the output Miriad uvdata file. 
c
c@ ant
c   The name of a text file containing the position of the antennas.
c   There is no default. Each line of the text file gives three values,
c   being the x, y and z location of an antenna.
c   The antenna positions can be given in either a right handed
c   equatorial system or as a local ground based coordinates measured to the
c   north, east and in elevation. See the "baseunit" parameter to
c   specify the coordinate system. Some standard antenna configurations
c   can be found in $MIRCAT/*.ant for ATCA, BIMA and VLA telescopes.
c   The BIMA and VLA antenna tables, use with baseunit=1, whereas for
c   the ATCA, use baseunit=-51.0204.
c
c   The text file is free-format, with commas or blanks used to separate
c   the values. Comments (starting with #) can be included in the file.
c
c@ baseunit
c   This specifies the coordinate system used in the antenna file.
c   A positive value for "baseunit" indicates an equatorial system,
c   whereas a negative value indicates a local system. The magnitude of
c   "baseunit" gives the conversion factor between the baseline units
c   used in the antenna file, and nanoseconds. The default value is +1,
c   which means that the antenna file gives the antenna position in an
c   equatorial system measured in nanoseconds.
c   E.g.    baseunit=-1 for topocentric coordinates in nanosecs,
c       baseunit=3.33564 for geocentric coordinates in meters.
c
c@ longlat
c   Longitude and Latitude of array phase center. hh:mm:ss,dd:mm:ss format, 
c   or as decimal hours and degrees.  Default is ATA at HCRO
c	-121:28:18.49,40:49:02.50 (no spaces). Coordinates for some other 
c	telescopes can be obtained from Miriad telepar task.
c
c@ radec
c   Source right ascension and declination. These can be given in
c   hh:mm:ss,dd:mm:ss format, or as decimal hours and decimal
c   degrees. The default is to set RA = LST, and DEC = latitude for
c	a transit observation.  Setting RA and DEC will change the phase
c	center to the RA and DEC specified.
c
c@ time
c   Start time of the observation.  This is in the form
c     yymmmdd.ddd
c   or
c     yymmmdd:hh:mm:ss.s
c   The default is 04DEC23.00 
c   With the unix date command you can use
c                date +%y%b%d:%H:%M:%S | tr '[A-Z]' '[a-z]'
c
c@ time0
c   Time of delay cal of the observation.  This is in the form
c     yymmmdd.ddd
c   or
c     yymmmdd:hh:mm:ss.s
c
c   If set, all geometric delays are zero at this time.
c
c@ inttime
c	Integration time for each record. Also used as the time increment
c	for each record written. default  inttime=26.21571072 seconds.
c	N+1 frames/period * 128 spectra/frame * 1024 sample/spectrum / 100 MHz
c
c@ nints
c	Total number of integrations in file.  Probably a smarter way to do
c	this, but hey...
c
c@ int0
c	Starting integration to write to file.  Default is 2, since first
c	integration not guaranteeed to have all data.
c
c@ freq
c   Frequency and Bandwidth in GHz.  Default 0.200,-0.05 GHz.
c	The first spectral channel is centered at frequency. The spectral channel 
c	increment is Bandwidth/nchan. nchan is taken from the input data. 
c	Set the bandwidth to a negative value to reverse the spectrum.
c--
c
c  History:
c    nov04 mchw  new task to convert correlator data to Miriad.
c    dec04 mchw  Added parameter for antenna positions.
c    22dec04 mchw suppress RFI so scaling to 16-bit integers is OK
c    23dec04 mchw improved doc.
c    24dec04 mchw Rotate phases to RA DEC if given by user
c    03jan05 mchw Added inttime parameter and antpos to output file.
c    06jan05 mchw Added offsets for channels 153 158 163.
c    07jan05 mchw reverse signs for offsets for channels 153 158 163.
c    21may05 dcb many changes: rfi; bias removal; dosun option
c    11jun05 dcb add rfi channel list - zero & flag
c    17jun06 dcb 3.0: convert from fx.for --> c2m.for; FITS input for CASPER/8 correlator
c      jul06 dcb 3.1: insert conj fixit for 6 antenna --> remove for 26jul06
c    30jul06 dcb 3.2: back to conjugating for 8 ant; a1=1,2,3,4; a2>4,5,6,7, resp.
c    08jul10 cjl 1.0:  convert to p2m, script for reading PoCoBI data and applying fringe rotation
c------------------------------------------------------------------------
	character version*(*)
	parameter(version = 'P2M: ver 1.0 10jul08')

	include 'maxnax.h'
	include 'mirconst.h'
 
c  Externals.
	integer*4 tinNext

c these belong in .h file
	parameter (MAXREC=10000000,MAXRFI=100,maxchan=64,
	* maxbase=36,maxant=8)

c PoCoBI data format
	integer pkt_num, bnum
c	integer*2 vis(2,64,36)      ! maybe works for 16b data?
	real vis(2,maxchan*maxbase)          ! works for 32b data!
	real ivis(2,maxchan,maxbase)          ! works for 32b data!

	logical flags(MAXCHAN,MAXBASE),wflags
	logical xflags(2*MAXCHAN), rfiflags(MAXCHAN)
	integer*4 nwide,munit,nvis,nave,nints,int0
	integer*4 i,j,n,nant,nrfi
	integer*4 b,c,d,t,a1,a2,b_1,b_2,count,maxcount
	integer*4 num(MAXCHAN,MAXBASE)
	integer*4 ns,nsbc,n16,n50,n67,n84,nsd
	integer*4 bs(2,MAXBASE),rfi(2,MAXRFI)
	integer*4 cs,bl,cg,ri
	real inttime,x,z,wfreq,wwidth
	real selcb(MAXREC),s,ss,thresh(MAXCHAN,MAXBASE)
	real delay(MAXANT)
	double precision bxx,byy,bzz
	real baseline_order(36)/ 257, 258, 514, 261, 517,
	* 1285, 262, 518, 1286, 1542, 259, 515, 773,
        * 774, 771, 516, 1029, 1030, 772, 1028, 1287,
        * 1543, 775, 1031, 1799, 1544, 776, 1032, 1800,
        * 2056, 260, 263, 264, 519, 520, 1288 /
c wrong order used first!
c	real baseline_order(36)/ 257, 258, 514, 259, 515,
c	* 771, 260, 516, 772, 1028, 261, 517, 773, 1029,
c        * 1285, 518, 774, 1030, 1286, 1542, 775, 1031, 
c        * 1287, 1543, 1799, 1032, 1288, 1544, 1800, 2056, 
c        * 262, 263, 264, 519, 520, 776 /
	double precision sinha,cosha,HA,tpi,phase
	double precision sinha0,cosha0,HA0,delayref
	double precision preamble(5),sdf,times(MAXREC)
	complex wide
	complex bias(MAXCHAN,MAXBASE)
c       make copy for miriad call
	complex xvis(MAXCHAN)

c       setup now for CASPER/8
	data tpi/6.283185307d0/
c       set all true to pass all data
	data rfiflags/MAXCHAN*.true./
	
c       Parameters from the user.
	character sfile*80,outfile*80,antfile*80,rfifile*80
c       define/setup abase array for CASPER/8 correlator
	character umsg*80,line*80,cbase*2,chant*8,abase(36)*2
	integer ipol
	real baseunit
	real b1(MAXANT),b2(MAXANT),b3(MAXANT)
	double precision sind,cosd,sinl,cosl,sind0,cosd0
	double precision along,alat,ra,dec,sra,sdec,obsra,obsdec
	double precision jd2000,lst,timeout,timerel,time0,lst0
	double precision sfreq,bandwidth
 
!================================================================
!  Get command line arguments.
!================================================================

	call output( version )
	call keyini

	call keya('in',sfile,' ')
	if (sfile .eq. ' ') call bug('f','An input file must be given')
	call keya('out',outfile,' ')
	if (outfile .eq. ' ')
     *	  call bug('f','Output file must be given')
	call keya('ant',antfile,' ')
	if (antfile .eq. ' ') 
     *    call bug('f','An antenna table must be given')

	call keyr('baseunit',baseunit,-3.33564)  ! ata default is topocentric in meters

!       10jul08 update to ATA at HCRO: -121:28:18.49,40:49:02.50
	call keyt('longlat',along,'dms',-2.1200829068d0)
	call keyt('longlat',alat,'dms',0.71239734336d0)
	call keyt('radec',sra,'hms',0.d0)
	call keyt('radec',sdec,'dms',alat)
	write(*,*) 'SRA,SDEC:',sra,sdec

!       06jun18 - dcb - require rfi file; bug
	call keya('rfi',rfifile,' ')
	write(*,'(1x,a80)') rfifile

!       get start time (GMT=UTC from paper0 cpu clock --> filename)
!       06jun18 - dcb - input starttime of first integration "time="
	call keyt('time',timeout,'atime',0.d0)
	call keyt('time0',time0,'atime',0.d0)
	if (timeout.le.1) then
	   call dayjul('06JUN17.00',timeout)
	   call dayjul('06JUN17.00',time0)
	endif

!       06jun19 - dcb - exact value of inttime from Aaron
	call keyr('inttime',inttime,0.001)
	call keyi('nints',nints,1)
	call keyi('int0',int0,2)
	call keyd('freq',sfreq,0.718d0)
	write(*,*) 'Start time = Julian day ',timeout
	write(*,*) 'Ref time = Julian day ',time0
	call keyd('freq',bandwidth,0.104d0)
	write(*,*) 'Freq, Bandwidth ',sfreq, bandwidth
	call keyfin
 
!       convert inputs to useful parameters
	sinl = sin(alat)
	cosl = cos(alat)
 
!================================================================
!  Read the antenna positions and cable delays file.
!================================================================
	call output('Antenna positions/cable delays:')
	nant = 0
	call tinOpen(antfile,' ')
	do while (tinNext() .gt. 0)
	   nant = nant + 1
	   if (nant .gt. MAXANT) call bug('f','Too many antennas')
	   call tinGetr(b1(nant),0.0)
	   call tinGetr(b2(nant),0.0)
	   call tinGetr(b3(nant),0.0)
	   call tinGetr(delay(nant),0.0)
 
!       Convert to equatorial coordinates.
	   if (baseunit .lt. 0.) then
	      x = b1(nant)
	      z = b3(nant)
	      b1(nant) = -x * sinl + z * cosl
	      b3(nant) =  x * cosl + z * sinl
	   endif

!       Convert to nanosecs.
	   if (baseunit .ne. 0.) then
	      b1(nant) = abs(baseunit) * b1(nant)
	      b2(nant) = abs(baseunit) * b2(nant)
	      b3(nant) = abs(baseunit) * b3(nant)
	   endif
	   write(line,'(a,4f15.4)') 'Equatorial b(ns):',
     *              b1(nant),b2(nant),b3(nant),delay(nant)
	   call output(line)
	enddo
	call tinClose		!antenna file

! Get RFI channels to delete if file exists.
! 06jun18 - dcb - this may not work?? i.e., must have rfifile
	if (rfifile .ne. ' ') then
	   call output('RFI Channels:')
	   nrfi = 0
	   call tinOpen(rfifile,' ')
	   do while (tinNext() .gt. 0)
	      nrfi = nrfi + 1
	      if (nrfi .gt. MAXRFI) call bug('f','Too many rfi channels
	      * for deletion')
           call tinGeti(rfi(1,nrfi),0)
           call tinGeti(rfi(2,nrfi),0)
	   if (rfi(2,nrfi) .eq. 0) rfi(2,nrfi)=rfi(1,nrfi)
	   write(*,*) nrfi,rfi(1,nrfi),rfi(2,nrfi)
        enddo
        call tinClose		!rfi file

! now setup rfiflags logical file.
!        do i = 1, nrfi
!	   do c = rfi(1,i), rfi(2,i)
!	      rfiflags(c) = .false.
!          enddo
!        enddo
!       do c = 1, rfi(2,nrfi)
!         write(*,*) c,rfiflags(c)
!       enddo

	endif			!rfi file exists

!================================================================
!  Open the output dataset
!================================================================
	call uvopen(munit,outfile,'new')
	call uvset(munit,'preamble','uvw/time/baseline',0,0.,0.,0.)

	call hisopen(munit,'write')
	call hiswrite(munit,'P2M: Miriad '//version)
	call hisinput(munit,'P2M')
 
c  Write some header information and uvvariables to describe the data .
	call wrhda(munit,'obstype','crosscorrelation')
	call uvputvra(munit,'source',sfile)
	call uvputvra(munit,'operator','P2M')
	call uvputvra(munit,'version',version)
	call uvputvra(munit,'telescop','ATA')
c  frequency
	call uvputvrd(munit,'freq',sfreq,1)
	call uvputvrd(munit,'freqif',0.d0,1)

	call uvputvrr(munit,'inttime',inttime,1)
	call uvputvrr(munit,'vsource',0.,1)
	call uvputvrr(munit,'veldop',0.,1)
	call uvputvri(munit,'nants',nant,8)

c Spectral channels; nchan & maxcount ought to be in .h file!!
c 10jul08 - cjl - PoCoBI-8 correlator: hardwire 64 chan
	maxcount = 0.8 * maxchan
	sdf = bandwidth/maxchan
	call uvputvri(munit,'nchan',maxchan,1)
	call uvputvri(munit,'nspect',1,1)
	call uvputvrd(munit,'sfreq',sfreq,1)
	call uvputvrd(munit,'sdf',sdf,1)
	call uvputvri(munit,'ischan',1,1)
	call uvputvri(munit,'nschan',maxchan,1)
	call uvputvrd(munit,'restfreq',sfreq,1)

! Wideband channels
	nwide = 1
	wfreq = sfreq + bandwidth/2.
	wwidth = abs(bandwidth)
	call uvputvri(munit,'nwide',nwide,1)
	call uvputvrr(munit,'wfreq',wfreq,nwide)
	call uvputvrr(munit,'wwidth',wwidth,nwide)

	call uvputvri(munit,'npol',1,1)
	call uvputvri(munit,'pol',1,1)

!================================================================
! READ IN pocorx data
!================================================================
! Initialize number of spectra counter in file
 
! Open and read the input pocorx file.  recl=18436 for 32b data, 9220 for 16b
	write(*,*) 'Opening Pocorx file, ',sfile
	write(*,*) 'Reading from int ',int0,' a total of ',nints,' ints'
	open(unit=20,file=sfile,form='unformatted',status='old',
	* access='direct', recl=18436)

! Loop over integrations
	do ns = int0, int0+nints-1
	   read(20,rec=ns) pkt_num, vis
! 	   print *, ns, ': read pkt_num ', pkt_num

! Reorder data into chan,baseline order
	   do cs = 1,4
	      do bl = 1,maxbase
		 do cg = 1,16
		    do ri= 1,2
! conj error for 7, 32, 33, 34, 35, 27?
c		       if (((bl .eq. 7) .or. (bl .eq. 27) .or. 
c		       * (bl .ge. 32 .and. bl .le. 35 )) .and. ri .eq. 
c		       * 2) then
c			  ivis(ri,cs+(cg-1)*4,bl) = 
c		       * -vis(ri,cs+4*(bl-1)+(cg-1)*4*36)
c		       else
c or conj error for 31-36?		      
		       if (bl .ge. 31 .and. ri .eq. 2) then
			  ivis(ri,cs+(cg-1)*4,bl) = 
		       * -vis(ri,cs+4*(bl-1)+(cg-1)*4*36)
		       else if (bl .ge. 13 .and. bl .le. 14 .and. 
			  * ri .eq. 2) then
			  ivis(ri,cs+(cg-1)*4,bl) = 
		       * -vis(ri,cs+4*(bl-1)+(cg-1)*4*36)
		    else if (bl .ge. 17 .and. bl .le. 18 .and. 
                          * ri .eq. 2) then
			  ivis(ri,cs+(cg-1)*4,bl) = 
		       * -vis(ri,cs+4*(bl-1)+(cg-1)*4*36)
c or no conj error?
		       else
			  ivis(ri,cs+(cg-1)*4,bl) = 
		       * vis(ri,cs+4*(bl-1)+(cg-1)*4*36)
		       endif
		    enddo
		 enddo
	      enddo
	   enddo

! Define output visibilities	   
	   times(ns) = timeout + (ns-1)*inttime/24./3600.

	   preamble(4) = times(ns)
	   call Jullst(preamble(4),along,lst)
           call dayjul('00jan01.00',jd2000)
!       Apparent RA and DEC of phase center at time of observation.
	   call precess(jd2000,sra,sdec,preamble(4),obsra,obsdec) 
!       put this info out in header
	   call uvputvrd(munit,'ra',ra,1)
	   call uvputvrd(munit,'dec',dec,1)
	   call uvputvrr(munit,'epoch',2000.,1)
	   call uvputvrd(munit,'obsra',obsra,1)
	   call uvputvrd(munit,'obsdec',obsdec,1)
	   call uvputvrd(munit,'lst',lst,1)
	   call uvputvrd(munit,'longitu',along,1)

	   if (ns .eq. int0 .and. time0 .ne. 0) then
	      print *, 'int0=0 and time0!=0.'
	      call Jullst(time0,along,lst0)
	      HA0 = lst0 - obsra
	      sinha0 = sin(HA0)
	      cosha0 = cos(HA0)
	      sind0 = sin(obsdec)
	      cosd0 = cos(obsdec)
	   endif

	   do b = 1,maxbase
	      HA = lst - obsra
	      if (ns .eq. int0 .and. b .eq. 1) then
		 write(*,*) ' LST,OBSRA,OBSDEC,HA, pre(4):'
		 * ,lst,obsra, obsdec, HA, preamble(4)
	      endif
	   
	      sinha = sin(HA)
	      cosha = cos(HA)
	      sind = sin(obsdec)
	      cosd = cos(obsdec)

	      preamble(5) = baseline_order(b)
	      call basant(preamble(5),a1,a2)
	      bxx = b1(a1) - b1(a2)
	      byy = b2(a1) - b2(a2)
	      bzz = b3(a1) - b3(a2)
!	      print *, 'a1,a2,b,preamble(5),bxx,byy,bzz',a1, a2, b
!	      * , preamble(5), bxx, byy, bzz
!  get u,v,w
	      preamble(1) =  bxx * sinha + byy * cosha
	      preamble(2) = -(bxx * cosha - byy * sinha)*sind + bzz*cosd
	      preamble(3) = (bxx * cosha - byy * sinha)*cosd + bzz*sind
	      preamble(5) = 256*a1 + a2

	      if (time0 .ne. 0) then
		 delayref = (bxx * cosha0 - byy * sinha0)*cosd0 + bzz
     &           *sind0
		 if (ns .eq. int0) then
		    print *, 'a1, a2, ns, p(3), delayref', a1, a2, ns, 
     &       	       preamble(3), delayref
		 endif
	      endif

! Write out data and flags
	      do c=1,maxchan
		 xvis(c) = cmplx(ivis(1,c,b), ivis(2,c,b))
		 xflags(c) = .true.

		 if (sra .ne. 0.) then
!  Rotate phases to RA DEC if given by user
! n.b., GHz & ns mix ok here..not SI, of course
		    if (time0 .ne. 0) then
		       phase = tpi * (sfreq+(c-1)*sdf) * (preamble(3) -
     &                    delayref + delay(a1) - delay(a2))
		    else
		       phase = tpi * (sfreq+(c-1)*sdf) * (preamble(3) +
     &                    delay(a1) - delay(a2))
		    endif
		 else		! just apply delays
! n.b., GHz & ns mix ok here..not SI, of course
		    phase = tpi * (sfreq+(c-1)*sdf) * 
     &           (delay(a1) - delay(a2))
!		    print *, 'phase ', phase, sfreq, sdf, delay(a1)
!     &	     ,delay(a2), a1, a2
		 endif
		 phase = dmod(phase,tpi)
		 xvis(c) = xvis(c) * cmplx(dcos(phase),-dsin(phase))
!		 print *, 'xvis(',c,',',b,') ',xvis(c)
	      enddo		!c
!	      if (a1 .eq. 1) then
!		 print *, 'a1, a2, delayref, pre(3)', a1, a2, 
!		 * delayref, preamble(3)
!	      endif

! write out data
	      call uvwrite(munit,preamble,xvis,xflags,maxchan)
!             call uvwwrite(munit,wide,wflags,nwide)
	      nvis = nvis + 1

	   enddo		!b
	enddo    !ns
	close(20)      ! finished reading pocorx file

! Tidy up and close Miriad file
	write(line,'(i9,a)')  ns-int0,' records read and written'
	call output(line)
	umsg = 'P2M: '//line
	call hiswrite(munit, umsg )

	call hisclose(munit)
	call uvclose(munit)

	end
