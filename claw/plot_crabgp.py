# claw, 9jul09
# script to plot the rate of crab giant pulses visible to ata-256 as a function of distance
# see McLaughlin & Cordes 2008, astro-ph

import pylab as p
import numpy as n

flux = n.arange(50.)/10. + 2
alpha = -3.4

mode = 'f'  # plot flux vs. frequency
#mode = 'd'  # plot flux vs. distance

if mode == 'd':
    # the distance estimate also assumes dedispersion and/or matched filter detection (i.e., idealized)
    rate = (24/70.)*10**11.1*(10**flux)**(-2.5)  # cumulative number with S > "flux" per day for rate in McLaughlin & Cordes 2003
    dist812 = 0.85 * (26/5.)**(-1/2.) * (286/10.)**(1/4.) * ((10.**flux)/(10.**5))**(1/2.)  # BW=60 MHz, Ssys=26Jy, dt=0.1ms, SNR=5, 2pols, bottom at 800 MHz, weighted mean at 812 MHz (as in Lundgren)
    dist632 = 0.85 * (26/5.)**(-1/2.) * (500/10.)**(1/4.) * ((((632/812.)**alpha)*10.**flux)/(10.**5))**(1/2.)  # BW=30 MHz, Ssys=26Jy, dt=0.1ms, SNR=5, 2pols, bottom at 500 MHz, weighted mean at 514 MHz
    dist527 = 0.85 * (26/5.)**(-1/2.) * (60/10.)**(1/4.) * ((((527.5/812.)**alpha)*10.**flux)/(10.**5))**(1/2.)  # BW=60 MHz, Ssys=26Jy, dt=0.1ms, SNR=5, 2pols, bottom at 500 MHz, weighted mean at 527 MHz
    dist588 = 0.85 * (26/5.)**(-1/2.) * (60/10.)**(1/4.) * ((((588/812.)**alpha)*10.**flux)/(10.**5))**(1/2.)  # BW=60 MHz, Ssys=26Jy, dt=0.1ms, SNR=5, 2pols, bottom at 560 MHz, weighted mean at 588 MHz
    dist1614 = 0.85 * (26/5.)**(-1/2.) * (500/10.)**(1/4.) * ((((1614/812.)**alpha)*10.**flux)/(10.**5))**(1/2.)  # BW=500 MHz, Ssys=26Jy, dt=0.1ms, SNR=5, 2pols, bottom at 1420 MHz, weighted mean at 1614 MHz
#dist501_qb = 0.85 * (26/5.)**(-1/2.) * (15/10.)**(1/4.) * ((((501/812.)**alpha)*10.**flux)/(10.**5))**(1/2.)  # BW=60 MHz, Ssys=26Jy, dt=0.1ms, SNR=5, 2pols, bottom at 500 MHz, weighted mean at 502 MHz

    # alt numbers for 10 ms time resolution.  assumes GPs are underresolved by factor of three (1.5 ms integration/10 ms burst), but gains in noise and bandwidth
    flux = n.arange(50,100000,5.)
    ratealt = (24/70.)*10**11.1*(flux*3*(10/1.5))**(-2.5)  # cumulative number with S > "flux" per day for rate in Lundgren et al. 1995 averaged from 1.5 ms down to 10 ms
    dist812alt = 0.85 * (156/5.)**(-1/2.) * (600/10. * 10/0.1)**(1/4.) * (flux/(10.**5))**(1/2.)  # BW=60 MHz, Ssys=26Jy, dt=0.1ms, SNR=5, 2pols, bottom at 800 MHz, weighted mean at 812 MHz (as in Lundgren)
    dist674alt = 0.85 * (156/5.)**(-1/2.) * (600/10. * 10/0.1)**(1/4.) * ((((674/812.)**alpha)*flux)/(10.**5))**(1/2.)  # BW=30 MHz, Ssys=26Jy, dt=0.1ms, SNR=5, 2pols, bottom at 500 MHz, weighted mean at 514 MHz
    dist1624alt = 0.85 * (156/5.)**(-1/2.) * (600/10. * 10/0.1)**(1/4.) * ((((1624/812.)**alpha)*flux)/(10.**5))**(1/2.)  # BW=500 MHz, Ssys=26Jy, dt=0.1ms, SNR=5, 2pols, bottom at 1420 MHz, weighted mean at 1624 MHz

#l1 = p.loglog(dist812alt,ratealt, label='1 Crab @ 812 MHz')  # plot for 1 Crab at 812 MHz
    l1 = p.loglog(dist674alt,ratealt, label='1 Crab @ 674 MHz')
    l1 = p.loglog(dist674alt,10*ratealt, label='10 Crab @ 674 MHz')
#l1 = p.loglog(dist1624alt,10*ratealt, label='10 Crab @ 1624 MHz')
#l1 = p.loglog(dist812,rate, label='1 Crab @ 812 MHz')  # plot for 1 Crab at 812 MHz
#l2 = p.loglog(dist812,10*rate, label='10 Crabs @ 812 MHz')
#l3 = p.loglog(dist527,10*rate, label='10 Crabs @ 527 MHz')
#l4 = p.loglog(dist632,10*rate, label='10 Crabs @ 632 MHz')
#l4 = p.loglog(dist588,10*rate, label='10 Crabs @ 588 MHz')
#l5 = p.loglog(dist1614,10*rate, label='10 Crabs @ 1614 MHz')
#l6 = p.loglog(dist527,1000*rate, label='1000 Crabs @ 527 MHz')
#l6 = p.loglog(dist501_qb,10*rate, label='10 Crabs @ 501 MHz (quarter band)')

    top = 6e3
#p.loglog([0.78,0.78],[0.1*top,top],'b--',label='M31')
    p.text(0.78,top,'M31 ',rotation='vertical',verticalalignment='top',horizontalalignment='center')
#p.loglog([0.86,0.86],[0.1*top,top],'b--',label='M33')
    p.text(0.86,top,'M33 ',rotation='vertical',verticalalignment='top',horizontalalignment='center')
#p.loglog([0.1,0.1],[0.1*top,top],'b--',label='UMa I')
    p.text(0.1,top,'UMa I ',rotation='vertical',verticalalignment='top',horizontalalignment='center')
#p.loglog([0.06,0.06],[0.1*top,top],'b--',label='UMi, Bootes')
    p.text(0.06,top,'UMi, Bootes ',rotation='vertical',verticalalignment='top',horizontalalignment='center')
#p.loglog([0.09,0.09],[0.1*top,top],'b--',label='Sextans I')
    p.text(0.09,top,'Sextans I ',rotation='vertical',verticalalignment='top',horizontalalignment='center')
#p.loglog([0.08,0.08],[0.1*top,top],'b--',label='Draco')
    p.text(0.08,top,'Draco ',rotation='vertical',verticalalignment='top',horizontalalignment='center')
#p.loglog([0.25,0.25],[0.1*top,top],'b--',label='Leo I')
    p.text(0.25,top,'Leo I ',rotation='vertical',verticalalignment='top',horizontalalignment='center')
#p.loglog([0.21,0.21],[0.1*top,top],'b--',label='Leo II')
    p.text(0.21,top,'Leo II ',rotation='vertical',verticalalignment='top',horizontalalignment='center')
#p.loglog([0.5,0.5],[0.1*top,top],'b--',label='NGC 6822')
    p.text(0.5,top,'NGC 6822 ',rotation='vertical',verticalalignment='top',horizontalalignment='center')
#p.loglog([18,18],[0.1*top,top],'b--',label='Virgo Cl.')
#p.text(18,0.1*top,'Virgo Cl.',rotation='vertical')

# pretty up

    p.legend(('1 Crab @ 674 MHz','10 Crab @ 674 MHz'),loc=3)
#p.legend(('10 Crabs @ 527 MHz','10 Crabs @ 588 MHz','10 Crabs @ 1614 MHz','1000 Crabs @ 527 MHz'),loc=4)
#p.legend(('1 Crab @ 812 MHz','10 Crabs @ 812 MHz','10 Crabs @ 527 MHz','10 Crabs @ 588 MHz'),loc=3)
#p.legend(('10 Crabs @ 527 MHz','10 Crabs @ 632 MHz'),loc=3)
    p.axis([0.055,0.91,1e-2,top])
    p.title('Rate of Detectable Crab-like GPs (for BW=600 MHz, dt=10 ms)')
#p.title('Rate of Detectable Crab-like GPs (for DM=50 pc cm-3, dt=0.1 ms)')
    p.ylabel('Rate (>D; per day)')
    p.xlabel('Distance visible to ATA-42 (Mpc)')
    p.show()

elif mode == 'f':
    freqs = n.arange(5,100)/10.
    rate = lambda flux,alpha,freq,fsc,tmin: 1/(24*60.)* 5e10 * ((freq/0.812)**(alpha) * (8/2.)**2 * ( n.sqrt((10*tmin)**2 + (100*(fsc/freq)**4.4)**2) ) * flux)**(-2.5)

    # limits and rates of number of pulses from a single gc crab pulsar
#    p.plot(freqs, 10*rate(0.0065, freqs, 17., 10 ))  # macquart et al. 2010 pulsars in central 50" for 10 hours (single pulse search)
    p.plot(freqs, 29*rate(0.0065, 3.4, freqs, 3.5, 100), 'g--', label='D09 limit') # deneva pulsars in 5.8' beam at 2 ghz for 29x1 hours
    p.plot(freqs, 6*12*rate(0.035/n.sqrt(10), 3.4, freqs, 3.5, 10 ), 'b', label='Proposed')  # evla proposal including survey speed 6x better than d09
