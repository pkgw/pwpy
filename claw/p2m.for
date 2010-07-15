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
c@ inttime
c	Integration time for each record. Also used as the time increment
c	for each record written. default  inttime=26.21571072 seconds.
c	N+1 frames/period * 128 spectra/frame * 1024 sample/spectrum / 100 MHz
c
c@ nints
c	Total number of integrations in file.  Probably a smarter way to do
c	this, but hey...
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
	integer*4 nwide,munit,nvis,nave,nints
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
	real baseline_order(36)/ 257, 258, 514, 259, 515,
	* 771, 260, 516, 772, 1028, 261, 517, 773, 1029,
        * 1285, 518, 774, 1030, 1286, 1542, 775, 1031, 
        * 1287, 1543, 1799, 1032, 1288, 1544, 1800, 2056, 
        * 262, 263, 264, 519, 520, 776 /
	double precision sinha,cosha,HA,tpi,phase
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
	real sind,cosd,sinl,cosl
	double precision along,alat,ra,dec,sra,sdec,obsra,obsdec
	double precision jd2000,lst,timeout,sfreq,bandwidth
 
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
	call keyi('pol',ipol,-1)
	if (ipol .eq. -1) 
     *    call bug('f','A polarization must be selected (1,2)')

	call keyr('baseunit',baseunit,1.0)

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
	if (timeout.le.1)
     *    call dayjul('06JUN17.00',timeout)

!       06jun19 - dcb - exact value of inttime from Aaron
	call keyr('inttime',inttime,0.001)
	call keyi('nints',nints,100)
	call keyd('freq',sfreq,0.700d0)
	write(*,*) 'Start time = Julian day ',timeout
	call keyd('freq',bandwidth,0.100d0)
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
        do i = 1, nrfi
	   do c = rfi(1,i), rfi(2,i)
	      rfiflags(c) = .false.
          enddo
        enddo
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
	open(unit=20,file=sfile,form='unformatted',status='old',
	* access='direct', recl=18436)

! Loop over integrations
	do ns = 2, nints    ! skip first int (always?)
	   read(20,rec=ns) pkt_num, vis
 	   print *, ns, ': read pkt_num ', pkt_num

! Reorder data into chan,baseline order
	   do cs = 1,4
	      do bl = 1,maxbase
		 do cg = 1,16
		    do ri= 1,2
		       print *, cs,bl,cg,ri
		       ivis(ri,cs+(cg-1)*4,bl) = 
		       * vis(ri,cs+4*(bl-1)+(cg-1)*4*36)
		    enddo
		 enddo
	      enddo
	   enddo

! Define output visibilities	   
	   times(ns) = timeout + (ns-1)*inttime/24./3600.
	   preamble(4) = times(ns)
	   call Jullst(preamble(4),along,lst)
!       Apparent RA and DEC of phase center at time of observation.
	   call precess(jd2000,ra,dec,preamble(4),obsra,obsdec) 
!       put this info out in header
	   call uvputvrd(munit,'ra',ra,1)
	   call uvputvrd(munit,'dec',dec,1)
	   call uvputvrr(munit,'epoch',2000.,1)
	   call uvputvrd(munit,'obsra',obsra,1)
	   call uvputvrd(munit,'obsdec',obsdec,1)
	   call uvputvrd(munit,'lst',lst,1)
	   call uvputvrd(munit,'longitu',along,1)
	   HA = lst - obsra
	   if (ns .eq. 1) write(*,*) ' LST,OBSRA,OBSDEC:',lst,obsra,
	   * obsdec
	   
!       setting  HA = lst-obsra = 0. makes phase tracking center at zenith
	   sinha = sin(HA)
	   cosha = cos(HA)
	   sind = sin(obsdec)
	   cosd = cos(obsdec)

	   do b = 1,maxbase
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

! Write out data and flags
	      do c=1,maxchan
		 xvis(c) = cmplx(ivis(1,c,b), ivis(2,c,b))
		 xflags(c) = .true.

		 if (sra .ne. 0.) then
!  Rotate phases to RA DEC if given by user
! n.b., GHz & ns mix ok here..not SI, of course
		    phase = tpi * (sfreq+(c-1)*sdf) * (preamble(3) +
     &            delay(bs(1,b)) - delay(bs(2,b)))
		    phase = dmod(phase,tpi)
		    xvis(c) = xvis(c) * cmplx(dcos(phase),-dsin(phase))
!		 else		! just apply delays
! n.b., GHz & ns mix ok here..not SI, of course
!		    phase = tpi * (sfreq+(c-1)*sdf) * 
!     &           (delay(bs(1,b)) - delay(bs(2,b)))
!		    phase = dmod(phase,tpi)
!		    xvis(c) = xvis(c) * cmplx(dcos(phase),-dsin(phase))
		 endif
		 print *, 'xvis(',c,',',b,') ',xvis(c)
	      enddo		!c

	      call uvwrite(munit,preamble,xvis,xflags,maxchan)
	      nvis = nvis + 1

	   enddo		!b
	enddo    !ns
	close(20)

! Tidy up and close Miriad file
	write(line,'(i9,a)')  ns-1,' records read from P2M'
	call output(line)
	umsg = 'P2M: '//line
	call hiswrite(munit, umsg )
	write(line,'(i9,a)')  nvis,' records written to Miriad '
	call output(line)
	umsg = 'P2M: '//line
	call hiswrite(munit, umsg )

	call hisclose(munit)
	call uvclose(munit)

	goto 10000       ! jump to end


c Can skip stats calculation.  Not needed for PoCoBI work.(?)

!================================================================
! READ DATA done, now GENERATE STATS via sorted amp-selected data
!================================================================
      n16 = nsbc * 0.165
      n50 = nsbc * 0.50
      n67 = nsbc * 0.667
      n84 = nsbc * 0.835
      nsd = n67 - n16 + 1
!     write(*,*) '#  numbers:',ns,nsbc,n16,n50,n67,n84
!      do b = 1, MAXBASE
! only need acf stats for threshold testing (for now)
!        if (bs(1,b) .eq. bs(2,b)) then
!          do c = 1, maxchan
! do stats here: select time sequence of chan,base; sort; then stats
!            do t = 1, maxrec
!              selcb(t) = cabs(vis(c,b,t))
!            enddo
!            call sort(nsbc,selcb)
!            s = 0.0
!            ss = 0.0
!            do t = n16, n67
!              s = s + selcb(t)
!              ss = ss + selcb(t)*selcb(t)
!            enddo
!            s = s / nsd
!            ss = sqrt(ss/nsd - s*s)
! create threshold for use in BIAS determination
! 05jun13 -- set thresh down to + 4 sigma
!            thresh(c,b) = (s + 4.0*ss)
!           if (c .eq. 153) write(*,*) ' threshold for ch',c,
!    &        ' and baseline',b,':',thresh(c,b),s,ss
!         if ((c/32)*32 .eq. c) write(*,*) ' threshold for ch',c,
!    &      ' and baseline',b,':',thresh(c,b)
!          enddo !c
!        endif !acf
!      enddo !b

!================================================================
! STATS done, now FIND BIAS spectra
!================================================================
!      write(*,*) ' BIAS'
!      do t = 1, nsbc
! set all flags to false
!        do b = 1, MAXBASE
!          do c = 1, maxchan
!            flags(c,b,t) = .false.
!          enddo
!        enddo
! go through all ccfs
!        do a1 = 1, MAXANT-1
!          do a2 = a1+1, MAXANT
! form baseline index 
!            b = 256*(a1) + a2
! now increment bias spectrum if total powers are above mean(n16:n67) + N*sigm
!            do c = 1, maxchan
! require both acfs to pass threshold test; n.b., thresholds of acfs are scaled by 100
!             if (c.eq.2 .and. b_1.eq.1) write(*,*) t,thresh(c,b_1)
!              if (cabs(vis(c,b_1,t)) .lt. thresh(c,b_1) .and.
!     &            cabs(vis(c,b_2,t)) .lt. thresh(c,b_2)) then
!             if (c .eq. 153) write(*,*) t,a1,a2,cabs(vis(c,b_1,t)),
!    &            thresh(c,b_1), cabs(vis(c,b_2,t)),thresh(c,b_2)
!                bias(c,b) = bias(c,b) + vis(c,b,t)
!                num(c,b) = num(c,b) + 1
! while we are in this loop, set ccf/acf data valid flags for MIRIAD
!                flags(c,b,t) = .true.
! a little redundancy in acf flagging here as we go through all cases
!                flags(c,b_1,t) = .true.
!                flags(c,b_2,t) = .true.
!              endif
!            enddo !c
!          enddo !a2
!        enddo !a1
!      enddo !t

! Normalize
!      do b = 1, MAXBASE
!        do c = 1, maxchan
!          if (num(c,b) .gt. 0) then
!            bias(c,b) = bias(c,b)/num(c,b)
!           write(*,*) b,c,bias(c,b),num(c,b)
!          else
!            bias(c,b) = (0.,0.)
!          endif
!        enddo !c
!      enddo !b

!================================================================
!  working with DATA as individual visibilities
!================================================================

!	do b = 1,MAXBASE

! create wide band data
!          wide = (0.,0.)
!          nave = 0
!          wflags = .false.
!          do c = 1, maxchan
!            if (flags(c,b,t)) then
!              wide = wide + vis(c,b,t)
!              nave = nave+1
!            endif
!          enddo
!          if (nave .gt. 0) then
!            wide = wide/nave
!            wflags = .true.
!          endif
c         write(*,*) ' wide =',wide,' for ',nave,' good data pts',t,b
 
! remove bias, limit amplitude and flag, transfer to 1D arrays
!          count = 0
!          do c = 1, maxchan
!            xvis(c) = vis(c,b,t) - bias(c,b)
!            xflags(c) = flags(c,b,t)
! fringe rotation
!	      if (ra .ne. 0.) then
!		 phase = tpi * wfreq * (preamble(3) +
!     &            delay(bs(1,b)) - delay(bs(2,b)))
!		 wide = wide * cmplx(dcos(phase),-dsin(phase))
!	      else
!		 phase = tpi * wfreq * (delay(bs(1,b)) - delay(bs(2,b)))
!		 wide = wide * cmplx(dcos(phase),-dsin(phase))
! may not be necessary with acf scaling, but strong correlation could still come in
! ok, so do this; check on real & imag separately.  
! 05jun11 - add in channel-based rfiflags check
!            if (abs(real(xvis(c))) .gt. 32000.0 
!     &         .or. abs(imag(xvis(c))) .gt. 32000.0
!     &         .or. (.not. rfiflags(c))) then
!              xvis(c) = cmplx(0.,0.)
!              xflags(c) = .false.
!            endif
!            if (.not. xflags(c)) count = count + 1
!          enddo
! dump whole spectrum if count exceeds maxcount (probably should be all baselines too)
!          if (count .gt. maxcount) then
!            do c = 1, maxchan
!              xvis(c) = cmplx(0.,0.)
!              xflags(c) = .false.
!            enddo
!          endif


C DEBUGGGGGGGGGGGGGGGGGGGGG
c     if (t .ge. 75 .and. t .le. 80) then
c       do c=1,maxchan
c         write(10,*) ' t',t,' b',b,' c',c,xvis(c)/1000.0,xflags(c),
c    &      thresh(c,b)/1000.0
c       enddo
c     endif
C DEBUGGGGGGGGGGGGGGGGGGGGG
c       do c=1,maxchan
c         if (.not.xflags(c)) write(10,*) ' t',t,' b',b,' c',c
c       enddo

c Write Miriad data
c          call uvwwrite(munit,wide,wflags,nwide)

!        enddo			!b

10000	continue
	end

c********1*********2*********3*********4*********5*********6*********7*c
      SUBROUTINE SORT(N,RA)
      DIMENSION RA(N)
      L=N/2+1
      IR=N
10    CONTINUE
        IF(L.GT.1)THEN
          L=L-1
          RRA=RA(L)
        ELSE
          RRA=RA(IR)
          RA(IR)=RA(1)
          IR=IR-1
          IF(IR.EQ.1)THEN
            RA(1)=RRA
            RETURN
          ENDIF
        ENDIF
        I=L
        J=L+L
20      IF(J.LE.IR)THEN
          IF(J.LT.IR)THEN
            IF(RA(J).LT.RA(J+1))J=J+1
          ENDIF
          IF(RRA.LT.RA(J))THEN
            RA(I)=RA(J)
            I=J
            J=J+J
          ELSE
            J=IR+1
          ENDIF
        GO TO 20
        ENDIF
        RA(I)=RRA
      GO TO 10
      END
