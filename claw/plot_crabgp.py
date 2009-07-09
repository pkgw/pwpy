# claw, 9jul09
# script to plot the rate of crab giant pulses visible to ata-256 as a function of distance
# see McLaughlin & Cordes 2008, astro-ph

import pylab,numpy

flux = numpy.arange(50.)/10. + 2
rate = (24/70.)*10**11.1*(10**flux)**(-2.5)  # cumulative number with S > "flux" per day
dist812 = 0.85 * (26/5.)**(-1/2.) * (500/10.)**(1/4.) * ((10.**flux)/(10.**5))**(1/2.)  # BW=500 MHz, Ssys=26Jy, dt=0.1ms, SNR=5, 2pols, 812 MHz
dist500 = 0.85 * (26/5.)**(-1/2.) * (500/10.)**(1/4.) * ((((500/812.)**(-4.4))*10.**flux)/(10.**5))**(1/2.)  # BW=500 MHz, Ssys=26Jy, dt=0.1ms, SNR=5, 2pols, 500 MHz
# the distance estimate also assumes dedispersion and/or matched filter detection (i.e., idealized)

l1 = pylab.loglog(dist812,rate, label='1 Crab @ 812 MHz')  # plot for 1 Crab at 812 MHz
l2 = pylab.loglog(dist812,10*rate, label='10 Crabs @ 812 MHz')  # plot for 10 Crabs at 812 MHz
l3 = pylab.loglog(dist500,10*rate, label='10 Crabs @ 500 MHz')  # plot for 10 Crabs at 500 MHz

top = 3e5
pylab.loglog([0.78,0.78],[0.1*top,top],'b--',label='M31')
pylab.text(0.78,0.1*top,'M31',rotation='vertical')
pylab.loglog([0.86,0.86],[0.1*top,top],'b--',label='M33')
pylab.text(0.86,0.1*top,'M33',rotation='vertical')
pylab.loglog([0.1,0.1],[0.1*top,top],'b--',label='UMa I')
pylab.text(0.1,0.1*top,'UMa I',rotation='vertical')
pylab.loglog([0.06,0.06],[0.1*top,top],'b--',label='UMi')
pylab.text(0.06,0.1*top,'UMi',rotation='vertical')
pylab.loglog([0.09,0.09],[0.1*top,top],'b--',label='Sextans I')
pylab.text(0.09,0.1*top,'Sextans I',rotation='vertical')

# pretty up
pylab.legend(('1 Crab @ 812 MHz','10 Crabs @ 812 MHz', '10 Crabs @ 500 MHz'))
pylab.axis([0.05,10,1e-1,top])
pylab.title('Rate of Detectable Crab-like GPs')
pylab.ylabel('Rate (>D; per day)')
pylab.xlabel('Distance visible to ATA-256 (Mpc)')
