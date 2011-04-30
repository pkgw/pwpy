#! /usr/bin/env python

"""= pocovis.py - visualization of poco data
& claw
: Unknown
+
 Script to load and visualize poco data
--
"""

import sys, string, os
from os.path import join
#import mirtask
#from mirtask import uvdat, keys, util
from mirexec import TaskInvert, TaskClean, TaskRestore, TaskImFit, TaskCgDisp, TaskImStat, TaskUVFit
import miriad, pickle
import numpy as n
import pylab as p
import scipy.optimize as opt
import scipy.stats.morestats as morestats
#from threading import Thread
#from matplotlib.font_manager import fontManager, FontProperties
#font= FontProperties(size='x-small');


class poco:
    def __init__(self,file,nints=1000,nskip=0):
        # initialize
        self.nchan = 64
#        self.chans = n.arange(6,58)
#        li = range(4,23) + range(37,49)   # must match flagging range; miriad 1-4, 24-38, 50-64
#        li = range(2,10) + range(11,23) + range(37,39) + range(40,41) + range(44,49)   # must match flagging range; miriad 1-2, 11, 24-37, 40, 42-44, 50-64
        li = range(3,10) + range(11,23) + range(37,39) + range(40,41) + range(44,49)   # must match flagging range; miriad 1-2, 11, 24-37, 40, 42-44, 50-64
        self.chans = n.array(li)
        self.nbl = 36
        initsize = nints*self.nbl   # number of integrations to read in a single chunk
        self.sfreq = 0.718  # freq for first channel in GHz
        self.sdf = 0.104/self.nchan   # dfreq per channel in GHz
        self.baseline_order = n.array([ 257, 258, 514, 261, 517, 1285, 262, 518, 1286, 1542, 259, 515, 773, 774, 771, 516, 1029, 1030, 772, 1028, 1287, 1543, 775, 1031, 1799, 1544, 776, 1032, 1800, 2056, 260, 263, 264, 519, 520, 1288])   # second iteration of bl nums
        self.autos = []
        self.noautos = []
#        self.pulsewidth = 0.0066 * n.ones(len(self.chans)) # pulse width of b0329+54
        self.pulsewidth = 0 * n.ones(len(self.chans)) # pulse width of crab
        # set dmarr
#        self.dmarr = [26.8]  # b0329+54
        self.dmarr = [56.8]  # crab
#        self.dmarr = n.arange(53,131,3.1)       # dm trials for m31. spacing set for 50% efficiency for band from 722-796 MHz, 1.2 ms integrations
#        self.tshift = 0.2     # not implemented yet
        self.nskip = nskip*self.nbl    # number of iterations to skip (for reading in different parts of buffer)
        nskip = self.nskip
        self.file = file
        for a1 in range(1,9):             # loop to adjust delays
            for a2 in range(a1,9):
                self.blindex = n.where(self.baseline_order == a1*256 + a2)[0][0]
                if a1 == a2:
                    self.autos.append(self.blindex)
                else:
                    self.noautos.append(self.blindex)

# load data
#
# slick way, but hard to hack for interactive use
#        sys.argv.append('vis='+file)
#        keys.doUvdat ('dsl3', True)
#        opts = keys.process ()

# poor man's way
        vis = miriad.VisData(file,)

        # initialize parameters
        nchan = self.nchan
        nbl = self.nbl
        i = 0
        da = n.zeros((initsize,nchan),dtype='complex64')
        fl = n.zeros((initsize,nchan),dtype='bool')
        ti = n.zeros((initsize),dtype='float64')

        # read data
        # You can pass traditional Miriad UV keywords to readLowlevel as keyword arguments
        for inp, preamble, data, flags in vis.readLowlevel ('dsl3', False):

            # Loop to skip some data and read shifted data into original data arrays
            if i < nskip:
                i = i+1
                continue 

            # Reduce these arrays to the correct size
#            data = data[0:nread]
#            flags = flags[0:nread]

    # Decode the preamble
    #        u, v, w = preamble[0:3]
            time = preamble[3]
    #        baseline = util.decodeBaseline (preamble[4])

    #    pol = uvdat.getPol ()
    
            if (i-nskip) < initsize:
                ti[i-nskip] = time
                da[i-nskip] = data
                fl[i-nskip] = flags
            else:
                break     # test to stop at initsize
#                da = n.concatenate((da,[data]))
#                ti = n.concatenate((ti,[time]))
#                fl = n.concatenate((fl,[flags]))
#                bl = n.concatenate((bl,[baseline]))
            if not (i % (nbl*1000)):
                print 'Read integration ', str(i/nbl)
            i = i+1

        if i < initsize:
            print 'Array smaller than initialized array.  Trimming.'
            da = da[0:i-nskip]
            fl = fl[0:i-nskip]
            ti = ti[0:i-nskip]

        try:
            self.rawdata = da.reshape((i-nskip)/nbl,nbl,nchan)
            self.flags = fl.reshape((i-nskip)/nbl,nbl,nchan)
            time = ti[::nbl]
            self.reltime = 24*3600*(time - time[0])      # relative time array in seconds
            print
            print 'Data read!'
            print 'Shape of raw data, flags, time:'
            print self.rawdata.shape, self.flags.shape, self.reltime.shape
            print 
        except ValueError:
            print 'Could not reshape data arrays. Incomplete read?'


    def prep(self):
        """
        Reshapes data for usage by other functions.
        Note that it assumes that any integration with bad data has an entire baseline flagged.
        """
        rawdata = self.rawdata
        flags = self.flags

        data = ((rawdata * flags)[:,self.noautos])[:,:,self.chans]
        totallen = data[flags[:,self.noautos][:,:,self.chans]].shape[0]
        tlen = data.shape[0]
        chlen = len(self.chans)
        self.data = n.reshape(data[flags[:,self.noautos][:,:,self.chans]], (tlen, totallen/(tlen*chlen), chlen)) # data is what is typically needed
        self.dataph = (self.data.mean(axis=1)).real  #dataph is summed and detected to form TP beam at phase center
        self.rawdata = (rawdata * flags)

        print 'Data flagged, trimmed in channels, and averaged across baselines.'
        print 'New rawdata, data, dataph shapes:'
        print self.rawdata.shape, self.data.shape, self.dataph.shape


    def spec(self, save=0):
        chans = self.chans
        reltime = self.reltime

# does not account for noise bias.  assumes lots of flux in the field
        mean = self.dataph.mean()
        std = self.dataph.std()
        abs = (self.dataph - mean)/std
#        abs = self.dataph
        print 'Data mean, std: %f, %f' % (mean, std)

        p.figure(1)
        ax = p.imshow(n.rot90(abs), aspect='auto', origin='upper', interpolation='nearest', extent=(min(reltime),max(reltime),0,len(chans)))
#        ax = p.imshow(n.rot90(abs), aspect='auto', origin='upper', interpolation='nearest', extent=(min(reltime),max(reltime),min(chans),max(chans)))
        p.colorbar(ax)
        p.xlabel('Relative time (s)')
        p.ylabel('Channel (flagged data removed)')
        if save:
            savename = self.file.split('.')[:-1]
            savename.append(str(self.nskip/self.nbl) + '.spec.png')
            savename = string.join(savename,'.')
            print 'Saving file as ', savename
            p.savefig(savename)
        else:
            p.show()
            

    def fitspec(self, obsrms=0, save=0):
        """
        Fits a powerlaw to the mean spectrum at the phase center.
        Returns fit parameters.
        """

        if save:
            logname = self.file.split('_')[0:2]
            logname.append('fitsp.txt')
            logname = string.join(logname,'_')
            log = open(logname,'a')

        freq = self.sfreq + self.chans * self.sdf             # freq array in GHz

        # estimage of vis rms per channel from spread in imag space at phase center
        if obsrms == 0:
            print 'estimating obsrms from imaginary part of data...'
#            obsrms = n.std((((self.data).mean(axis=1)).mean(axis=0)).imag)/n.sqrt(2)  # sqrt(2) scales it to an amplitude error. indep of signal.
            obsrms = n.std((((self.data).mean(axis=1)).mean(axis=0)).imag)      # std of imag part is std of real part
#        spec = n.abs((((self.data).mean(axis=1))).mean(axis=0))
        spec = ((((self.data).mean(axis=1))).mean(axis=0)).real
        print 'obsrms = %.2f' % (obsrms)

        plaw = lambda a, b, x: a * (x/x[0]) ** b
#        fitfunc = lambda p, x, rms:  n.sqrt(plaw(p[0], p[1], x)**2 + rms**2)   # for ricean-biased amplitudes
#        errfunc = lambda p, x, y, rms: ((y - fitfunc(p, x, rms))/rms)**2
        fitfunc = lambda p, x:  plaw(p[0], p[1], x)              # for real part of data
        errfunc = lambda p, x, y, rms: ((y - fitfunc(p, x))/rms)**2

        p0 = [50.,0.]
        p1, success = opt.leastsq(errfunc, p0[:], args = (freq, spec, obsrms))
        print 'Fit results: ', p1
        chisq = errfunc(p1, freq, spec, obsrms).sum()/(len(freq) - 2)
        print 'Reduced chisq: ', chisq

        p.figure(2)
        p.errorbar(freq, spec, yerr=obsrms*n.ones(len(spec)), fmt='.')
        p.plot(freq, fitfunc(p1, freq), label='Fit: %.1f, %.2f. Noise: %.1f, $\chi^2$: %.1f' % (p1[0], p1[1], obsrms, chisq))
        p.xlabel('Frequency')
        p.ylabel('Flux Density (Jy)')
        p.legend()
        if save == 1:
            savename = self.file.split('.')[:-1]
            savename.append(str(self.nskip/self.nbl) + '.fitsp.png')
            savename = string.join(savename,'.')
            print 'Saving file as ', savename
            p.savefig(savename)
            print >> log, savename, 'Fit results: ', p1, '. obsrms: ', obsrms, '. $\Chi^2$: ', chisq
        else:
            p.show()


    def dmtrack(self, dm = 0., t0 = 0., show=0):
        """Takes dispersion measure in pc/cm3 and time offset from first integration in seconds.
        t0 defined at first (unflagged) channel. Need to correct by flight time from there to freq=0 for true time.
        Returns an array of (timebin, channel) to select from the data array.
        """

        reltime = self.reltime
        chans = self.chans
        tint = self.reltime[1] - self.reltime[0]

        freq = self.sfreq + chans * self.sdf             # freq array in GHz

        # given freq, dm, dfreq, calculate pulse time and duration
        pulset_firstchan = 4.2e-3 * dm * freq[len(freq)-1]**(-2)   # used to start dmtrack at highest-freq unflagged channel
        pulset = 4.2e-3 * dm * freq**(-2) + t0 - pulset_firstchan  # time in seconds
        pulsedt = n.sqrt( (8.3e-6 * dm * (1000*self.sdf) * freq**(-3))**2 + self.pulsewidth**2)   # dtime in seconds

        timebin = []
        chanbin = []

        for ch in range(len(chans)):
#            ontime = n.where(((pulset[ch] + pulsedt[ch]/2.) >= reltime) & ((pulset[ch] - pulsedt[ch]/2.) <= reltime))
            ontime = n.where(((pulset[ch] + pulsedt[ch]/2.) >= reltime - tint/2.) & ((pulset[ch] - pulsedt[ch]/2.) <= reltime + tint/2.))
            timebin = n.concatenate((timebin, ontime[0]))
            chanbin = n.concatenate((chanbin, (ch * n.ones(len(ontime[0]), dtype=int))))

        track = (list(timebin), list(chanbin))
#        print 'timebin, chanbin:  ', timebin, chanbin

        if show:
            p.plot(track[1], track[0])

        return track


    def writetrack(self, dmbin, tbin, output='c', tshift=0, bgwindow=0, show=0):
        """Writes data from track out as miriad visibility file.
        Optional background subtraction bl-by-bl over bgwindow integrations. Note that this is bgwindow *dmtracks* so width is bgwindow+track width
        Optional spectrum plot with source and background dmtracks
        Output parameter says whether to 'c'reate a new file or 'a'ppend to existing one. **not tested**
        """

        rawdatatrim = self.rawdata[:,:,self.chans]

        track = self.dmtrack(dm=self.dmarr[dmbin], t0=self.reltime[tbin-tshift], show=0)

#        if len(track[1]) < minintersect:
        if ((track[1][0] != 0) | (track[1][len(track[1])-1] != len(self.chans)-1)):
            print 'Track does not span all channels. Skipping.'
            return 0

        twidths = []
        for i in track[1]:
            twidths.append(len(n.array(track)[0][list(n.where(n.array(track[1]) == i)[0])]))

        if bgwindow > 0:
            bgrange = range(-bgwindow/2 - max(twidths) + tbin - tshift, -max(twidths) + tbin - tshift) + range(max(twidths) + tbin - tshift, max(twidths) + bgwindow/2 + tbin - tshift + 1)
#            bgrange = range(int(-bgwindow/2.) + tbin - tshift, int(bgwindow/2.) + tbin - tshift + 1)
#            bgrange.remove(tbin - tshift); bgrange.remove(tbin - tshift + 1); bgrange.remove(tbin - tshift - 1); bgrange.remove(tbin - tshift + 2); bgrange.remove(tbin - tshift - 2); bgrange.remove(tbin - tshift + 3); bgrange.remove(tbin - tshift - 3)
            for i in bgrange:     # build up super track for background subtraction
                if bgrange.index(i) == 0:   # first time through
                    trackbg = self.dmtrack(dm=self.dmarr[dmbin], t0=self.reltime[i], show=0)
                else:    # then extend arrays by next iterations
                    tmp = self.dmtrack(dm=self.dmarr[dmbin], t0=self.reltime[i], show=0)
                    trackbg[0].extend(tmp[0])
                    trackbg[1].extend(tmp[1])
        else:
            print 'Not doing any background subtraction.'

        if show:
            # show source and background tracks on spectrum
            p.figure(1)
            p.plot(self.reltime[track[0]], track[1], 'w.')
            if bgwindow > 0:
                p.plot(self.reltime[trackbg[0]], trackbg[1], 'r.')
            self.spec(save=0)

#                print 'trackbg'
#            print self.rawdata[:,:,self.chans][trackbg[0], 1, trackbg[1]]
#        print 'track'
#        print self.rawdata[:,:,self.chans][track[0], 1, track[1]]

        # define input metadata source and output visibility file names
        inname = self.file
        outname = string.join(self.file.split('.')[:-1]) + '.' + str(self.nskip/self.nbl) + '-' + 'dm' + str(dmbin) + 't' + str(tbin) + '.mir'

        vis = miriad.VisData(inname)
        out = miriad.VisData(outname)

        dOut = out.open (output)
        dOut.setPreambleType ('uvw', 'time', 'baseline')

        i = 0
        int0 = self.nskip + (track[0][len(track[0])/2] + tshift) * self.nbl   # choose integration at center of dispersed track

        for inp, preamble, data, flags in vis.readLowlevel ('dsl3', False):
            # since template has only one int, this loop gets spectra by iterating over baselines.

            if i < int0:  # need to grab only integration at pulse+intoff
                i = i+1
                continue

            elif i < int0 + self.nbl:
                if i == int0:
                    nants = inp.getVarFirstInt ('nants', 0)
                    inttime = inp.getVarFirstFloat ('inttime', 10.0)
                    nspect = inp.getVarFirstInt ('nspect', 0)
                    nwide = inp.getVarFirstInt ('nwide', 0)
                    sdf = inp.getVarDouble ('sdf', nspect)
                    inp.copyHeader (dOut, 'history')
                    inp.initVarsAsInput (' ') # ???

                    dOut.writeVarInt ('nants', nants)
                    dOut.writeVarFloat ('inttime', inttime)
                    dOut.writeVarInt ('nspect', nspect)
                    dOut.writeVarDouble ('sdf', sdf)
                    dOut.writeVarInt ('nwide', nwide)
                    dOut.writeVarInt ('nschan', inp.getVarInt ('nschan', nspect))
                    dOut.writeVarInt ('ischan', inp.getVarInt ('ischan', nspect))
                    dOut.writeVarDouble ('sfreq', inp.getVarDouble ('sfreq', nspect))
                    dOut.writeVarDouble ('restfreq', inp.getVarDouble ('restfreq', nspect))
                    dOut.writeVarInt ('pol', inp.getVarInt ('pol'))
                    
                    inp.copyLineVars (dOut)

                # write out track, if not flagged
                if n.any(flags):
                    bgarr = []
                    for j in range(self.nchan):
                        if j in self.chans:
                            matches = n.where( j == n.array(self.chans[track[1]]) )[0]   # hack, since chans are from 0-64, but track is in trimmed chan space
                            raw = rawdatatrim[track[0], i-int0, track[1]][matches]   # all baselines for the known pulse
                            raw = raw.mean(axis=0)   # create spectrum for each baseline by averaging over time
                            if bgwindow > 0:   # same as above, but for bg
                                matchesbg = n.where( j == n.array(self.chans[trackbg[1]]) )[0]
                                rawbg = rawdatatrim[trackbg[0], i-int0, trackbg[1]][matchesbg]
                                rawbg = rawbg.mean(axis=0)
                                bgarr.append(rawbg)
                                data[j] = raw - rawbg
                            else:
                                data[j] = raw
                        else:
                            flags[j] = False

#                    print 'BG spectrum std =', (n.abs(bgarr)).std()

#                ants = util.decodeBaseline (preamble[4])
#                print preamble[3], ants
                dOut.write (preamble, data, flags)
                i = i+1  # essentially a baseline*int number


            elif i >= int0 + self.nbl:
                break

        dOut.close ()
        return 1


    def dmlc(self, dmbin, tbin, nints = 50):
        """Plots lc for DM bin over range of timebins.
        In principle, should produce lightcurve as if it is a slice across dmt0 plot.
        Actually designed to test writetrack function.
        """

        # define input metadata source and output visibility file names
        inname = self.file
        vis = miriad.VisData(inname)

        rawdatatrim = self.rawdata[:,:,self.chans]
        lc = []
        for tbintrial in range(tbin, tbin+nints):

            # shift track integrations by intoff
            track = self.dmtrack(dm=self.dmarr[dmbin], t0=self.reltime[tbintrial], show=0)  # needs to be shifted by -1 bin in reltime?

            dataarr = []
            i = 0
            for inp, preamble, data, flags in vis.readLowlevel ('dsl3', False):
                # since template has only one int, this loop gets spectra by iterating over baselines.

                if i < (track[0][len(track[0])/2]) * self.nbl:  # need to grab only integration at pulse+intoff
                    i = i+1
                    continue
                elif i == (track[0][len(track[0])/2]) * self.nbl:     # start counting with int0
                    int0 = i

                if i < int0 + self.nbl:   # for one integration starting at int0
                    # prep data (and check that it matches expected?)
                    for j in range(self.nchan):
                        if j in self.chans:
                            matches = n.where( (j - min(self.chans)) == n.array(track[1]) )[0]   # hack, since chans are from 0-64, but track is in trimmed chan space
                            raw = rawdatatrim[track[0], i-int0, track[1]][matches]   # all baselines for the known pulse
                            raw = raw.mean(axis=0)   # create spectrum for each baseline by averaging over time
                            data[j] = raw
                        else:
                            data[j] = 0. + 0.j

                elif i >= int0 + self.nbl: 
                    break

                dataarr.append(n.array(data))
                i = i+1  # essentially a baseline*int number

            dataarr = n.abs((n.array(dataarr))[self.noautos, :])
            lc.append(dataarr.mean())

        return n.array(lc)


    def makedmt0(self):
        """Integrates data at dmtrack for each pair of elements in dmarr, time.
        Not threaded.  Uses dmthread directly.
        Stores mean of detected signal after dmtrack, effectively forming beam at phase center.
        """

        dmarr = self.dmarr
#        reltime = n.arange(2*len(self.reltime))/2.  # danger!
        reltime = self.reltime
#        minintersect = len(self.chans)  # not needed anymore
        chans = self.chans

        dmt0arr = n.zeros((len(dmarr),len(reltime)), dtype='float64')

        for i in range(len(dmarr)):
            for j in range(len(reltime)):
                dmtrack = self.dmtrack(dm=dmarr[i], t0=reltime[j])
                if ((dmtrack[1][0] == 0) & (dmtrack[1][len(dmtrack[1])-1] == len(self.chans)-1)):   # use only tracks that span whole band
#                    dmt0arr[i,j] = n.abs((((self.data).mean(axis=1))[dmtrack[0],dmtrack[1]]).mean())
                    dmt0arr[i,j] = ((((self.data).mean(axis=1))[dmtrack[0],dmtrack[1]]).mean()).real    # use real part to detect on axis, but keep gaussian dis'n
            print 'dedispersed for ', dmarr[i]

        self.dmt0arr = dmt0arr


    def plotdmt0(self, save=0):
        """calculates rms noise in dmt0 space, then plots circles for each significant point
        save=1 means plot to file.
        """
        dmarr = self.dmarr
        arr = self.dmt0arr
        reltime = self.reltime
        peaks = self.peaks
        tbuffer = 7  # number of extra iterations to trim from edge of dmt0 plot

        # Trim data down to where dmt0 array is nonzero
        arreq0 = n.where(arr == 0)
        trimt = arreq0[1].min()
        arr = arr[:,:trimt - tbuffer]
        reltime = reltime[:trimt - tbuffer]
        print 'dmt0arr/time trimmed to new shape:  ',n.shape(arr), n.shape(reltime)

        mean = arr.mean()
        std = arr.std()
        arr = (arr - mean)/std
        peakmax = n.where(arr == arr.max())

        # Plot
#        p.clf()
        ax = p.imshow(arr, aspect='auto', origin='lower', interpolation='nearest', extent=(min(reltime),max(reltime),min(dmarr),max(dmarr)))
        p.colorbar()

        if len(peaks[0]) > 0:
            print 'Peak of %f at DM=%f, t0=%f' % (arr.max(), dmarr[peakmax[0][0]], reltime[peakmax[1][0]])

            for i in range(len(peaks[1])):
                ax = p.imshow(arr, aspect='auto', origin='lower', interpolation='nearest', extent=(min(reltime),max(reltime),min(dmarr),max(dmarr)))
                p.axis((min(reltime),max(reltime),min(dmarr),max(dmarr)))
                p.plot([reltime[peaks[1][i]]], [dmarr[peaks[0][i]]], 'o', markersize=2*arr[peaks[0][i],peaks[1][i]], markerfacecolor='white', markeredgecolor='blue', alpha=0.5)

        p.xlabel('Time (s)')
        p.ylabel('DM (pc/cm3)')
        p.title('Summed Spectra in DM-t0 space')
        if save:
            savename = self.file.split('.')[:-1]
            savename.append(str(self.nskip/self.nbl) + '.dmt0.png')
            savename = string.join(savename,'.')
            p.savefig(savename)


    def peakdmt0(self, sig=5.):
        """ Method to find peaks in dedispersed data (in dmt0 space).
        Clips noise, also.
        """
        arr = self.dmt0arr
        reltime = self.reltime
        tbuffer = 7  # number of extra iterations to trim from edge of dmt0 plot

        # Trim data down to where dmt0 array is nonzero
        arreq0 = n.where(arr == 0)
        trimt = arreq0[1].min()
        arr = arr[:,:trimt - tbuffer]
        reltime = reltime[:trimt - tbuffer]
        print 'dmt0arr/time trimmed to new shape:  ',n.shape(arr), n.shape(reltime)

        # single iteration of sigma clip to find mean and std, skipping zeros
        mean = arr.mean()
        std = arr.std()
        print 'initial mean, std:  ', mean, std
        cliparr = n.where((arr < mean + 5*std) & (arr > mean - 5*std))
        mean = arr[cliparr].mean()
        std = arr[cliparr].std()
        print 'final mean, sig, std:  ', mean, sig, std

        # Recast arr as significance array
#        arr = n.sqrt((arr-mean)**2 - std**2)/std   # PROBABLY WRONG
        arr = (arr-mean)/std   # for real valued trial output (gaussian dis'n)

        # Detect peaks
        self.peaks = n.where(arr > sig)
        peakmax = n.where(arr == arr.max())
        print 'peaks:  ', self.peaks

        return self.peaks,arr[self.peaks]


    def imagedmt0(self, dmbin, t0bin, tshift=0, bgwindow=5, show=1, clean=1):
        """ Makes and fits an background subtracted image for a given dmbin and t0bin.
        tshift can shift the actual t0bin earlier to allow reading small chunks of data relative to pickle.
        """

        minintersect = len(self.chans)
        
        # set up
        outroot = string.join(self.file.split('.')[:-1]) + '.' + str(self.nskip/self.nbl) + '-dm' + str(dmbin) + 't' + str(t0bin)
        removefile (outroot+'.map'); removefile (outroot+'.beam'); removefile (outroot+'.clean'); removefile (outroot+'.restor')
        removefile (outroot + '.mir')

        # make dm trial and image
        dmtrack = self.dmtrack(dm=self.dmarr[dmbin], t0=self.reltime[t0bin-tshift])

        if len(dmtrack[0]) >= minintersect:               # ignore tiny, noise-dominated tracks
            print
            self.writetrack(dmbin, t0bin, 'c', tshift=tshift, bgwindow=bgwindow)   # output file at dmbin, trelbin

            # make image, clean, restor, fit point source
            print
## this could be made more efficient. image only center? underresolve beam?            
            print 'Making dirty image at dm[%d] = %.1f and trel[%d] = %.3f.' % (dmbin, self.dmarr[dmbin], t0bin-tshift, self.reltime[t0bin-tshift])
            txt = TaskInvert (vis=outroot+'.mir', map=outroot+'.map', beam=outroot+'.beam', mfs=True, double=True, cell=80, rob=0).snarf()
            if show:  txt = TaskCgDisp (in_=outroot+'.map', device='/xs', wedge=True, beambl=True).snarf () 
            txt = TaskImStat (in_=outroot+'.map').snarf()
            # get noise level in image
            thresh = 2*float(txt[0][10][41:47])    # OMG!!
            txt = TaskClean (beam=outroot+'.beam', map=outroot+'.map', out=outroot+'.clean', cutoff=thresh).snarf () 
            print
            print 'Cleaned to %.2f Jy after %d iterations' % (thresh, int(txt[0][-4][19:]))
            txt = TaskRestore (beam=outroot+'.beam', map=outroot+'.map', model=outroot+'.clean', out=outroot+'.restor').snarf () 
            if show:  txt = TaskCgDisp (in_=outroot+'.restor', device='/xs', wedge=True, beambl=True).snarf () 
            txt = TaskImFit (in_=outroot+'.restor', object='point').snarf () 

            try:
                # parse output of imfit
                # print '012345678901234567890123456789012345678901234567890123456789'
                # print txt[0][14]

                peak = float(txt[0][14][30:36])
                epeak = float(txt[0][14][44:])
                off_ra = float(txt[0][15][28:39])
                eoff_ra = float(txt[0][16][30:39])
                off_dec = float(txt[0][15][40:])
                eoff_dec = float(txt[0][16][40:])

                print 'Fit peak %.2f +- %.2f' % (peak, epeak)
                if clean:
                    removefile (outroot + '.mir')
                    removefile (outroot+'.map'); removefile (outroot+'.beam'); removefile (outroot+'.clean'); removefile (outroot+'.restor')
                return peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec
            except:
                print
                print 'Something broke in/after imfit!'
                if clean:
                    removefile (outroot + '.mir')
                    removefile (outroot+'.map'); removefile (outroot+'.beam'); removefile (outroot+'.clean'); removefile (outroot+'.restor')


    def uvfitdmt0(self, dmbin, t0bin, tshift=0, show=1):
        """ Makes and fits a point source to background subtracted visibilities for a given dmbin and t0bin.
        tshift can shift the actual t0bin earlier to allow reading small chunks of data relative to pickle.
        """
        
        minintersect = len(self.chans)
        
        # set up
        outroot = string.join(self.file.split('.')[:-1]) + '.' + str(self.nskip/self.nbl) + '-dm' + str(dmbin) + 't' + str(t0bin)
        removefile (outroot+'.map'); removefile (outroot+'.beam'); removefile (outroot+'.clean'); removefile (outroot+'.restor')
        removefile (outroot + '.mir')

        # make dm trial and image
        dmtrack = self.dmtrack(dm=self.dmarr[dmbin], t0=self.reltime[t0bin-tshift])

        if len(dmtrack[0]) >= minintersect:               # ignore tiny, noise-dominated tracks
            print
            self.writetrack(dmbin, t0bin, 'c', tshift=tshift, bgwindow=5)   # output file at dmbin, trelbin

            # make image, clean, restor, fit point source
            print
            print 'Fitting source for dm[%d] = %.1f and trel[%d] = %.3f.' % (dmbin, self.dmarr[dmbin], t0bin-tshift, self.reltime[t0bin-tshift])
            txt = TaskUVFit (vis=outroot+'.mir', object='point', select='-auto').snarf()

            try:
                # parse output of imfit
                # print '012345678901234567890123456789012345678901234567890123456789'
                # print txt[0][14]

                peak = float(txt[0][8][30:38])
                epeak = float(txt[0][8][46:])
                off_ra = float(txt[0][9][30:38])
                eoff_ra = float(txt[0][10][31:42])
                off_dec = float(txt[0][9][40:])
                eoff_dec = float(txt[0][10][42:])

                print 'Fit peak %.2f +- %.2f' % (peak, epeak)
                removefile (outroot + '.mir')
                return peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec
            except:
                print
                print 'Something broke in/after uvfit!'
                removefile (outroot + '.mir')


    def normalreim(self, prob=2.3e-4, bgwindow=0):
        """Calculates p-value of normality for real-imaginary distribution of visibilities. **Does not use both parts of complex values! Only real.**
        Uses baselines and channels separately. prob is the false positive rate (actually non-normal p-value); default is 230/1e6 => 5sigma.
        Returns least likely normal trials
        """

        write = 0  # use writetrack to get bgsub visies? takes long time...
        tbuffer = 7  # number of extra iterations to trim from edge of dmt0 plot

        dmarr = self.dmarr
        reltime = self.reltime
        chans = self.chans

        dmt0arr = n.zeros((len(dmarr),len(reltime)), dtype='float64')

        for i in range(len(dmarr)):
            for j in range(len(reltime)):
                if write:
                    # use writetrack to get bgsub visibilities
                    status = self.writetrack(i, j, tshift=0, bgwindow=bgwindow)
                    if status:
                        newfile = string.join(self.file.split('.')[:-1]) + '.' + str(self.nskip/self.nbl) + '-' + 'dm' + str(i) + 't' + str(j) + '.mir'
                        print 'Loading file', newfile
                        pv2 = poco(newfile, nints=1)
                        pv2.prep()
                        length = pv2.data.shape[1] * pv2.data.shape[2]
                        da = (pv2.data[0]).reshape((1,length))[0]
                        removefile(newfile)
                    
                        dmt0arr[i,j] = morestats.shapiro(da)[1]
                else:
                    datadiff = self.tracksub(i, j, bgwindow=bgwindow)
                    if len(n.shape(datadiff)) == 3:
                        length = datadiff.shape[1] * datadiff.shape[2]
                        datadiff = (datadiff[0]).reshape((1,length))[0]
                        dmt0arr[i,j] = morestats.shapiro(datadiff)[1]
                    else:
                        continue
            print 'dedispersed for ', dmarr[i]

        # Trim data down to where dmt0 array is nonzero
        arreq0 = n.where(dmt0arr == 0)
        trimt = arreq0[1].min()
        dmt0arr = dmt0arr[:,:trimt - tbuffer]
        reltime = reltime[:trimt - tbuffer]
        print 'dmt0arr/time trimmed to new shape:  ',n.shape(dmt0arr), n.shape(reltime)

        # Detect dips
        self.dmt0arr = dmt0arr
        self.dips = n.where(dmt0arr < prob)
        dipmin = n.where(dmt0arr == dmt0arr.min())
        print 'Least normal re-im distributions: ', self.dips
        print 'Number of trials: ', len(dmarr) * len(reltime)

        return self.dips,dmt0arr[self.dips]


    def tracksub(self, dmbin, tbin, bgwindow = 0):
        """Reads data along dmtrack and optionally subtracts background like writetrack method.
        Returns the difference of the data in the on and off tracks as a single integration with all bl and chans.
        Nominally identical to writetrack, but gives visibilities values off at the 0.01 (absolute) level. Good enough for now.
        """

        data = self.data

        trackon = self.dmtrack(dm=self.dmarr[dmbin], t0=self.reltime[tbin], show=0)
        if ((trackon[1][0] != 0) | (trackon[1][len(trackon[1])-1] != len(self.chans)-1)):
            print 'Track does not span all channels. Skipping.'
            return [0]

        dataon = data[trackon[0], :, trackon[1]]

        # set up bg track
        if bgwindow:
            # measure max width of pulse (to avoid in bgsub)
            twidths = [] 
            for k in trackon[1]:
                twidths.append(len(n.array(trackon)[0][list(n.where(n.array(trackon[1]) == k)[0])]))

            bgrange = range(-bgwindow/2 - max(twidths) + tbin, -max(twidths) + tbin) + range(max(twidths) + tbin, max(twidths) + bgwindow/2 + tbin + 1)
            for k in bgrange:     # build up super track for background subtraction
                if bgrange.index(k) == 0:   # first time through
                    trackoff = self.dmtrack(dm=self.dmarr[dmbin], t0=self.reltime[k], show=0)
                else:    # then extend arrays by next iterations
                    tmp = self.dmtrack(dm=self.dmarr[dmbin], t0=self.reltime[k], show=0)
                    trackoff[0].extend(tmp[0])
                    trackoff[1].extend(tmp[1])

            dataoff = data[trackoff[0], :, trackoff[1]]

        # compress time axis, then subtract on and off tracks
        for ch in n.unique(trackon[1]):
            indon = n.where(trackon[1] == ch)

            if bgwindow:
                indoff = n.where(trackoff[1] == ch)
                datadiff = dataon[indon].mean(axis=0) - dataoff[indoff].mean(axis=0)
            else:
                datadiff = dataon[indon].mean(axis=0)

            if ch == 0:
                datadiffarr = [datadiff]
            else:
                datadiffarr = n.append(datadiffarr, [datadiff], axis=0)

        datadiffarr = n.array([datadiffarr.transpose()])

        return datadiffarr


    def plotreim(self, save=0):
        """Plots the visibilities in real-imaginary space. Test of pulse detection concept for uncalibrated data...
        """

        da = self.data.mean(axis=0)
        length = da.shape[0] * da.shape[1]
        da = da.reshape((1,length))[0]

        print 'Real center: %.1f +- %.1f ' % (da.real.mean(), da.real.std()/n.sqrt(len(da.real)))
        print 'Imag center: %.1f +- %.1f ' % (da.imag.mean(), da.imag.std()/n.sqrt(len(da.real)))
        print 'Normal p-value: ', morestats.shapiro(da)[1]

        if save:
            savename = self.file.split('.')[:-1]
            savename.append(str(self.nskip/self.nbl) + '.reim.png')
            savename = string.join(savename,'.')
            p.savefig(savename)
        else:
            p.plot(da.real,da.imag, '.')
            p.show()


    def dedisperse2(self):
        """Integrates over data at dmtrack for each pair of elements in dmarr, time.
        Uses threading.  SLOWER than serial.
        """

        dmarr = self.dmarr
        reltime = self.reltime
        chans = self.chans

        self.dmt0arr = n.zeros((len(dmarr),len(reltime)), dtype='float64')
#        accummask = n.zeros(self.dataph.shape, dtype='bool')

        threadlist = []
        for i in range(len(dmarr)):
            for j in range(len(reltime)):
                proc = worker(self, i, j)
                threadlist.append(proc)
                proc.start()
            print 'submitted for dm= ', dmarr[i]
        for proc in threadlist:
            proc.join()


    def dedisperse3(self):
        """Integrates over data at dmtrack for each pair of elements in dmarr, time.
        Uses ipython.
        """
        from IPython.kernel import client

        dmarr = self.dmarr
        reltime = self.reltime
        dmt0arr = n.zeros((len(dmarr),len(reltime)), dtype='float64')

        # initialize engines
        tc = client.TaskClient()
        mec = client.MultiEngineClient()
        ids = mec.get_ids()
        print 'Got engines: ', ids
#        mec.push_function(dict(dmtrack2 = dmtrack2))    # set up function for later
#        mec.push(dict(data=self.dataph, reltime=reltime))
#        mec.execute('import numpy as n')
#        mec.push_function(dict(dmtrack2 = dmtrack2))    # set up function for later

        pr_list = []
        iarr = []; jarr = []
        for i in range(len(dmarr)):
            for j in range(len(reltime)):
#                iarr.append(i)
#                jarr.append(j)
#                k = (j + len(reltime) * i) % len(ids)   # queue each iter amongst targets
                st = client.StringTask('dmt0 = dmtrack2(data, reltime, %f, %f)' % (dmarr[i], reltime[j]), pull='dmt0', push=dict(data = self.dataph,reltime = reltime))
                pr_list.append(tc.run(task=st))
                if len(pr_list) == len(ids):     # wait until node queue is full
                    for l in range(len(pr_list)):
                        tc.barrier(pr_list)         # then wait for all processes to finish
                        dmt0 = tc.get_task_result(pr_list[l])
                        print dmt0
#                        dmt0arr[iarr[l],jarr[l]] = dmt0[l]
#            iarr = []; jarr = []
            print 'dedispersed for ', dmarr[i]

        self.dmt0arr = dmt0arr


def removefile (file):
    """ Shortcut to remove a miriad file.
    """
    if not os.path.exists(file): return

    for e in os.listdir (file):
        os.remove (join (file, e))
    os.rmdir (file)


def pulse_search_phasecenter(fileroot, pathin, pathout, nints=10000, edge=0):
    """Blind search for pulses at phase center.
    TO DO:  improve handling of edge times and ignoring data without complete DM track?
    """

    maxints = 131000

    filelist = []
# for crab 201103
#    for i in [0,1,4,5,6,7,8,9]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_0' + str(i) + '.mir')
#    for i in range(0,8):
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_1' + str(i) + '.mir')

# for crab 190348
#    for i in [0,1,2,3,4,5,6,7,8,9]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_0' + str(i) + '.mir')
#    for i in [1,3,4,5,6,7,8,9]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_1' + str(i) + '.mir')
#    for i in [0,1,2,3]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_2' + str(i) + '.mir')

# for b0329 173027
#    for i in [0,1,2,3,4,5,6,7,8,9]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_0' + str(i) + '.mir')
#    for i in [0,1,2,6,7,8,9]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_1' + str(i) + '.mir')
#    for i in [0,1,2,3]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_2' + str(i) + '.mir')

# for m31 154202
#    for i in [0,1,2,3,4,5,6,7,8,9]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_0' + str(i) + '.mir')
#    for i in [0,1,2,3,4,5,6]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_1' + str(i) + '.mir')

# hack to search single file for pulses
    filelist = [fileroot]

    # loop over miriad data and time chunks
    for file in filelist:
        fileout = open(pathout + string.join(file.split('.')[:-1]) + '.txt', 'a')

        for nskip in range(0, maxints-(nints-edge), nints-edge):
            print
            print 'Starting file %s with nskip %d' % (file, nskip)

            # load data
            pv = poco(pathin + file, nints=nints, nskip=nskip)
            pv.prep()

            # searches at phase center  ## TO DO:  need to search over position in primary beam
            pv.makedmt0()
            peaks, peakssig = pv.peakdmt0()
            print >> fileout, file, nskip, nints, peaks

            # save all results (v1.0 pickle format)
            # TO DO:  think of v2.0 of pickle format
            if len(peaks[0]) > 0:
                pklout = open(pathout + string.join(file.split('.')[:-1]) + '.' + str(nskip) + '.pkl', 'wb')
                pickle.dump((file, nskip, nints, peaks[0], pv.dmarr[peaks[0][0]], peaks[1], peakssig), pklout)
                pklout.close()

        fileout.close


def pulse_search_reim(fileroot, pathin, pathout, nints=10000, edge=0):
    """Blind search for pulses based on real-imaginary distribution of visibilities
    """

    maxints = 131000
    bgwindow = 10
    filelist = []

# for crab 201103
#    for i in [0,1,4,5,6,7,8,9]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_0' + str(i) + '.mir')
#    for i in range(0,8):
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_1' + str(i) + '.mir')

# for crab 190348
#    for i in [0,1,2,3,4,5,6,7,8,9]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_0' + str(i) + '.mir')
#    for i in [1,3,4,5,6,7,8,9]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_1' + str(i) + '.mir')
#    for i in [0,1,2,3]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_2' + str(i) + '.mir')

# for b0329 173027
#    for i in [0,1,2,3,4,5,6,7,8,9]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_0' + str(i) + '.mir')
#    for i in [0,1,2,6,7,8,9]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_1' + str(i) + '.mir')
#    for i in [0,1,2,3]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_2' + str(i) + '.mir')

# for m31 154202
#    for i in [0,1,2,3,4,5,6,7,8,9]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_0' + str(i) + '.mir')
#    for i in [0,1,2,3,4,5,6]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_1' + str(i) + '.mir')

# hack to search single file for pulses
    filelist = [fileroot]

    # loop over miriad data and time chunks
    for file in filelist:
        fileout = open(pathout + string.join(file.split('.')[:-1]) + '.txt', 'a')

        for nskip in range(0, maxints-(nints-edge), nints-edge):
            print
            print 'Starting file %s with nskip %d' % (file, nskip)

            # load data
            pv = poco(pathin + file, nints=nints, nskip=nskip)
            pv.prep()

            # searches at phase center  ## TO DO:  need to search over position in primary beam
            dips, dipsprob = pv.normalreim(bgwindow=bgwindow)
            print >> fileout, file, nskip, nints, dips

            # save all results (v1.0 pickle format)
            # TO DO:  think of v2.0 of pickle format
            if len(dips[0]) > 0:
                pklout = open(pathout + string.join(file.split('.')[:-1]) + '.' + str(nskip) + '.pkl', 'wb')
                pickle.dump((file, nskip, nints, dips[0], pv.dmarr[dips[0][0]], dips[1], dipsprob), pklout)
                pklout.close()

        fileout.close


def pulse_search_image(fileroot, pathin, pathout, nints=12000, sig=5.0, show=1, edge=0):
    """
    Searches for pulses by imaging dedispersed trials.
    """

    maxints = 131000  # biggest file in integrations
    bgwindow = 5  # where bg subtraction is made

    filelist = []
    for i in [0,1,4,5,6,7,8,9]:
        filelist.append(string.join(fileroot.split('.')[:-1]) + '_0' + str(i) + '.mir')
    for i in range(0,8):
        filelist.append(string.join(fileroot.split('.')[:-1]) + '_1' + str(i) + '.mir')
        
    print 'Looping over filelist: ', filelist
    for file in filelist:
        fileout = open(pathout + string.join(file.split('.')[:-1]) + '.txt', 'a')

        for nskip in range(0, maxints-(nints-edge), nints-edge):
            print 'Starting file %s with nskip %d' % (file, nskip)

            # load data
            pv = poco(pathin + file, nints=nints, nskip=nskip)
            pv.prep()

            # dedisperse
            for i in range(len(pv.dmarr)):
                for j in range(len(pv.reltime)):
                    try: 
                        peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec = pv.imagedmt0(i,j, show=show, bgwindow=bgwindow, clean=1)
                        print >> fileout, file, nskip, nints, (i, j), 'Peak, RA, Dec: ', peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec

                        if peak/epeak >= sig:
                            print '\tDetection!'
                            # save all results (v1.0 pickle format)
                            pklout = open(pathout + string.join(file.split('.')[:-1]) + '.' + str(nskip) + '-dm' + str(i) + 't' + str(j) + '.pkl', 'wb')
                            pickle.dump((file, nskip, nints, [i], pv.dmarr[i], [j], peak/epeak), pklout)
                            pklout.close()
                    except:
                        continue
        fileout.close


def pulse_search_uvfit(fileroot, pathin, pathout, nints=12000, sig=5.0, show=1, edge=0):
    """
    Searches for pulses by fitting visibilities of dedispersed trials.
    """

    maxints = 131000  # biggest file in integrations

    filelist = []
    for i in [0,1,4,5,6,7,8,9]:
        filelist.append(string.join(fileroot.split('.')[:-1]) + '_0' + str(i) + '.mir')
    for i in range(0,8):
        filelist.append(string.join(fileroot.split('.')[:-1]) + '_1' + str(i) + '.mir')
        
    print 'Looping over filelist: ', filelist
    for file in filelist:
        fileout = open(pathout + string.join(file.split('.')[:-1]) + '.txt', 'a')

        for nskip in range(0, maxints-(nints-edge), nints-edge):
            print 'Starting file %s with nskip %d' % (file, nskip)

            # load data
            pv = poco(pathin + file, nints=nints, nskip=nskip)
            pv.prep()

            # dedisperse
            for i in range(len(pv.dmarr)):
                for j in range(len(pv.reltime)):
                    try: 
                        peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec = pv.uvfitdmt0(i,j, show=show)
                        print >> fileout, file, nskip, nints, (i, j), 'Peak, RA, Dec: ', peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec

                        if peak/epeak >= sig:
                            print '\tDetection!'
                            # save all results (v1.0 pickle format)
                            pklout = open(pathout + string.join(file.split('.')[:-1]) + '.' + str(nskip) + '-dm' + str(i) + 't' + str(j) + '.pkl', 'wb')
                            pickle.dump((file, nskip, nints, [i], pv.dmarr[i], [j], peak/epeak), pklout)
                            pklout.close()
                    except:
                        continue
        fileout.close


def process_pickle(filename, pathin, mode='image'):
    """Processes a pickle file to produce a spectrum of a candidate pulse.
    mode tells whether to produce dmt0 plot ('dmt0'), a spectrogram ('spec'), 
    image the dm track ('image'), or write visibilities to a file ('dump')
    TO DO:  (maybe) modify format of pickle file.
    """

    file = open(filename, 'rb')
    dump = pickle.load(file)
    name = dump[0]
    nints = dump[2]
    nintskip = dump[1]
    dmbinarr = dump[3]
    dmarr = dump[4]
    tbinarr = dump[5]
    snrarr = dump[6]
    if mode == 'reim':  # reim mode has p-values for normality, which should be small when there is a pulse
        peaktrial = n.where(snrarr == min(snrarr))[0][0]
    else:
        peaktrial = n.where(snrarr == max(snrarr))[0][0]

    bgwindow = 10

#    name = 'poco_crab_201103_tst.mir'  # hack to force using certain file
    
    print 'Loaded pickle file for %s' % (name)
    print 'Has peaks at DM = ', dmarr
    print 'Significance of ', snrarr
    if len(dmbinarr) >= 1:
#    if (len(dmbinarr) >= 1) & (snrarr[peaktrial] > 7.):
        print 'Grabbing %d ints at %d' % (nints, nintskip)
#        pv = poco(pathin + name, nints=nints, nskip=nintskip + tbinarr[peaktrial] - bgwindow)    # to skip a few ints...
        pv = poco(pathin + name, nints=nints, nskip=nintskip)    # format defined by pickle dump below
#        pv.nskip=nintskip*pv.nbl    # to skip a few ints...
        pv.prep()
#        track = pv.dmtrack(dm=pv.dmarr[dmbinarr[peaktrial]], t0=pv.reltime[bgwindow], show=0)  # to skip a few ints...
        track = pv.dmtrack(dm=pv.dmarr[dmbinarr[peaktrial]], t0=pv.reltime[tbinarr[peaktrial]], show=0)

        if mode == 'spec':  # just show spectrum
            # write out bg-subbed track, read back in to fit spectrum
#            pv.writetrack(dmbinarr[peaktrial], bgwindow, tshift=0, bgwindow=bgwindow)  # to skip a few ints...
            status = pv.writetrack(dmbinarr[peaktrial], tbinarr[peaktrial], tshift=0, bgwindow=bgwindow)
            if status:
               # plot track and spectrogram
                p.figure(1)
                p.plot(pv.reltime[track[0]], track[1], 'w.')
                pv.spec(save=0)
                # now estimate obsrms
#                status = pv.writetrack(dmbinarr[peaktrial], tbinarr[peaktrial]+bgwindow, tshift=0, bgwindow=0)
#                bgname = string.join(pv.file.split('.')[:-1]) + '.' + str(pv.nskip/pv.nbl) + '-' + 'dm' + str(dmbinarr[peaktrial]) + 't' + str(tbinarr[peaktrial]+bgwindow) + '.mir'
#                pvbg = poco(bgname, nints=1)
#                pvbg.prep()
#                obsrms = n.abs(pvbg.data.mean(axis=1)[0]).std()
#                print 'obsrms first try:', obsrms
#                removefile(bgname)
#               newfile = string.join(pv.file.split('.')[:-1]) + '.' + str(pv.nskip/pv.nbl) + '-' + 'dm' + str(dmbinarr[peaktrial]) + 't' + str(bgwindow) + '.mir'
                newfile = string.join(pv.file.split('.')[:-1]) + '.' + str(pv.nskip/pv.nbl) + '-' + 'dm' + str(dmbinarr[peaktrial]) + 't' + str(tbinarr[peaktrial]) + '.mir'
                print 'Loading file', newfile
                pv2 = poco(newfile, nints=1)
                pv2.prep()
                pv2.fitspec(obsrms=0, save=0)
                removefile(newfile)
        elif mode == 'dmt0':
            pv.makedmt0()
            peaks, peakssig = pv.peakdmt0()
#            p.plot(pv.reltime[bgwindow], pv.dmarr[dmbinarr[peaktrial]], '*' )   # not working?
            pv.plotdmt0(save=1)
        elif mode == 'image':
            peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec = pv.imagedmt0(dmbinarr[peaktrial], bgwindow, bgwindow=bgwindow)
            print peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec
        elif mode == 'uvfit':
            peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec = pv.uvfitdmt0(dmbinarr[peaktrial], bgwindow)
            print peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec
        elif mode == 'dump':
            # write dmtrack data out for imaging
            pv.writetrack(track)
        elif mode == 'reim':
            datasub = pv.tracksub(dmbinarr[peaktrial], tbinarr[peaktrial], bgwindow=bgwindow)
            pv.data = datasub
            pv.plotreim()
        else:
            print 'Mode not recognized'
    else:
        print 'No significant detection.  Moving on...'

    file.close()


if __name__ == '__main__':
    """From the command line, pocovis can either load pickle of candidate to interact with data, or
    it will search for pulses blindly.
    """

    print 'Greetings, human.'
    print ''

    fileroot = 'poco_crab_201103_tst.mir'  
    pathin = 'data/'
    pathout = 'crab_tst2/'
#    edge = 150 # m31 search up to dm=131 and pulse starting at first unflagged channel
#    edge = 35 # b0329 search at dm=28.6 and pulse starting at first unflagged channel
    edge = 70 # Crab search at dm=56.8 and pulse starting at first unflagged channel
#    edge = 360  # Crab DM of 56.8 and for DM track starting at freq=0

    if len(sys.argv) == 1:
        # if no args, search for pulses
        print 'Searching for pulses...'
        try:
#            pulse_search_image(fileroot=fileroot, pathin=pathin, pathout=pathout, nints=2000, show=0)
#            pulse_search_phasecenter(fileroot=fileroot, pathin=pathin, pathout=pathout, nints=2000, edge=edge)
            pulse_search_reim(fileroot=fileroot, pathin=pathin, pathout=pathout, nints=500, edge=edge)
        except AttributeError:
            exit(0)
    elif len(sys.argv) == 2:
        # if pickle, then plot data or dm search results
        print 'Assuming input file is pickle of candidate...'
        process_pickle(sys.argv[1], pathin=pathin, mode='reim')
    elif len(sys.argv) == 6:
        # if full spec of trial, image it
        print 'Imaging DM trial...'
        file = sys.argv[1]
        nskip = int(sys.argv[2])
        nints = int(sys.argv[3])
        dmbin = int(sys.argv[4])
        t0bin = int(sys.argv[5])
        pv = poco(file, nints=nints, nskip=nskip)
        pv.prep()
        peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec = pv.imagedmt0(dmbin, t0bin, show=1)
        print file, nskip, nints, (dmbin, t0bin), '::Peak, RA, Dec:: ', peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec
