#! /usr/bin/env python

"""= kat7vis.py - visualization of kat-7 data
& claw
: Unknown
+
 Script to load and visualize kat-7 data
--
"""

import sys, string, os, shutil
import cProfile
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


class kat7:
    def __init__(self, file, nints=1000, nskip=0, nocal=False, nopass=False):
        # initialize
        self.nchan = 625
        nchan = self.nchan
        self.chans = n.arange(10,501)
        self.nbl = 10
        nbl = self.nbl
        self.nints = nints
        initsize = nints*self.nbl   # number of integrations to read in a single chunk
        self.sfreq = 1.5498  # freq for first channel in GHz
        self.sdf = -0.000391   # dfreq per channel in GHz
        self.approxuvw = True      # flag to make template visibility file to speed up writing of dm track data
        self.baseline_pairs =[(0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3), (0, 4), (1, 4), (2, 4), (3, 4)]
# corresponding baselines ??    # poco: (1,2),(1,5),(2,5),(1,6),(2,6),(5,6),(1,3),(2,3),(3,6)] (miriad numbering)
        self.pulsewidth = 0 * n.ones(len(self.chans)) # pulse width of crab and m31 candidates
        # set dmarr
#        self.dmarr = n.arange(5,45,3)
        self.dmarr = [68.0]  # crab
#        self.tshift = 0.2     # not implemented yet
        self.nskip = int(nskip*self.nbl)    # number of iterations to skip (for reading in different parts of buffer)
        nskip = int(self.nskip)
        self.file = file

        # load data
        vis = miriad.VisData(file,)
        da = n.zeros((initsize,nchan),dtype='complex64')
        fl = n.zeros((initsize,nchan),dtype='bool')
        pr = n.zeros((initsize,5),dtype='float64')

        # read data into python arrays
        i = 0
        for inp, preamble, data, flags in vis.readLowlevel ('dsl3', False, nocal=nocal, nopass=nopass):
            # Loop to skip some data and read shifted data into original data arrays
            if i == 0:
                # get few general variables
                self.nants0 = inp.getScalar ('nants', 0)
                self.inttime0 = inp.getScalar ('inttime', 10.0)
                self.nspect0 = inp.getScalar ('nspect', 0)
                self.nwide0 = inp.getScalar ('nwide', 0)
                self.sdf0 = inp.getScalar ('sdf', self.nspect0)
                self.nschan0 = inp.getScalar ('nschan', self.nspect0)
                self.ischan0 = inp.getScalar ('ischan', self.nspect0)
                self.sfreq0 = inp.getScalar ('sfreq', self.nspect0)
                self.restfreq0 = inp.getScalar ('restfreq', self.nspect0)
                self.pol0 = inp.getScalar ('pol')

            if i < nskip:
                i = i+1
                continue 

            if (i-nskip) < initsize:
                da[i-nskip] = data
                fl[i-nskip] = flags
                pr[i-nskip] = preamble
            else:
                break     # stop at initsize

            if not (i % (nbl*1000)):
                print 'Read integration ', str(i/nbl)
            i = i+1

        if i < initsize:
            print 'Array smaller than initialized array.  Trimming.'
            da = da[0:i-nskip]
            fl = fl[0:i-nskip]
            pr = pr[0:i-nskip]

        try:
            self.rawdata = da.reshape((i-nskip)/nbl,nbl,nchan)
            self.flags = fl.reshape((i-nskip)/nbl,nbl,nchan)
            self.preamble = pr
            time = self.preamble[::nbl,3]
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

        data = (rawdata)[:,:,self.chans]
#        totallen = data[flags[:,:,self.chans]].shape[0]
#        tlen = data.shape[0]
#        chlen = len(self.chans)
#        print tlen,totallen/(tlen*chlen), chlen,totallen
#        self.data = n.reshape(data[flags[:,:,self.chans]], (tlen, totallen/(tlen*chlen), chlen)) # data is what is typically needed
        self.data = data
        self.dataph = (self.data.mean(axis=1)).real  #dataph is summed and detected to form TP beam at phase center
        self.rawdata = rawdata

        print 'Data flagged, trimmed in channels, and averaged across baselines.'
        print 'New rawdata, data, dataph shapes:'
        print self.rawdata.shape, self.data.shape, self.dataph.shape


    def spec(self, save=0):
        chans = self.chans
        reltime = self.reltime

        mean = self.dataph.mean()
        std = self.dataph.std()
#        abs = (self.dataph - mean)/std
        abs = self.dataph
        print 'Data mean, std: %f, %f' % (mean, std)

        p.figure(1)
        ax = p.imshow(n.rot90(abs), aspect='auto', origin='upper', interpolation='nearest', extent=(min(reltime),max(reltime),0,len(chans)))
        p.colorbar(ax)
        p.yticks(n.arange(0,len(self.chans),50), (self.chans[(n.arange(0,len(self.chans), 50))]))
        p.xlabel('Relative time (s)')
        p.ylabel('Channel')
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

#        logname = self.file.split('_')[0:3]
#        logname.append('fitsp.txt')
#        logname = string.join(logname,'_')
#        log = open(logname,'a')

        freq = self.sfreq + self.chans * self.sdf             # freq array in GHz

        # estimate of vis rms per channel from spread in imag space at phase center
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

        p0 = [100.,-5.]
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
#            print >> log, savename, 'Fit results: ', p1, '. obsrms: ', obsrms, '. $\Chi^2$: ', chisq
        else:
            pass
#            print >> log, self.file, 'Fit results: ', p1, '. obsrms: ', obsrms, '. $\Chi^2$: ', chisq

    def dmtrack(self, dm = 0., t0 = 0., show=0):
        """Takes dispersion measure in pc/cm3 and time offset from first integration in seconds.
        t0 defined at first (unflagged) channel. Need to correct by flight time from there to freq=0 for true time.
        Returns an array of (timebin, channel) to select from the data array.
        """

        reltime = self.reltime
        chans = self.chans
        tint = self.reltime[1] - self.reltime[0]
#        tint = self.inttime0  # could do this instead...?

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


    def tracksub(self, dmbin, tbin, bgwindow = 0):
        """Reads data along dmtrack and optionally subtracts background like writetrack method.
        Returns the difference of the data in the on and off tracks as a single integration with all bl and chans.
        Nominally identical to writetrack, but gives visibilities values off at the 0.01 (absolute) level. Good enough for now.
        """

        data = self.data

        trackon = self.dmtrack(dm=self.dmarr[dmbin], t0=self.reltime[tbin], show=0)
        if ((trackon[1][0] != 0) | (trackon[1][len(trackon[1])-1] != len(self.chans)-1)):
#            print 'Track does not span all channels. Skipping.'
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


    def setstd(self, dmbin, bgwindow=10):
        """
        Measures the observed std of the mean of the mean dedispersed spectrum. Uses the std of the imaginary part of differenced data.
        """

        obsrms = []
        for bgi in range(bgwindow, self.nints-bgwindow, self.nints/15):
            datadiff = self.tracksub(dmbin, bgi, bgwindow=bgwindow)   # arbitrary offset to measure typical noise in bg
            obsrms.append(n.std(datadiff[0].mean(axis=1).imag))          # std of imag part is std of real part

        self.obsrms = n.median(obsrms)/n.sqrt(len(datadiff[0]))
        print 'Measured observed std of mean visibility as:', self.obsrms


    def writetrack(self, dmbin, tbin, tshift=0, bgwindow=0, show=0):
        """Writes data from track out as miriad visibility file.
        Optional background subtraction bl-by-bl over bgwindow integrations. Note that this is bgwindow *dmtracks* so width is bgwindow+track width
        Optional spectrum plot with source and background dmtracks
        """

        # prep data and track
        rawdatatrim = self.rawdata[:,:,self.chans]
        track = self.dmtrack(dm=self.dmarr[dmbin], t0=self.reltime[tbin-tshift], show=0)
        if ((track[1][0] != 0) | (track[1][len(track[1])-1] != len(self.chans)-1)):
#            print 'Track does not span all channels. Skipping.'
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

        # define input metadata source and output visibility file names
        outname = string.join(self.file.split('.')[:-1], '.') + '.' + str(self.nskip/self.nbl) + '-' + 'dm' + str(dmbin) + 't' + str(tbin) + '.mir'
        shutil.rmtree(outname, ignore_errors=True)
        vis = miriad.VisData(self.file,)

        i = 0
        int0 = int(self.nskip + (track[0][len(track[0])/2] + tshift) * self.nbl)   # choose integration at center of dispersed track

        for inp, preamble, data, flags in vis.readLowlevel ('dsl3', False, nocal=True, nopass=True):
            if i == 0:
                # create output vis file
                shutil.rmtree(outname, ignore_errors=True)
                out = miriad.VisData(outname)
                dOut = out.open ('c')

                # set variables
                dOut.setPreambleType ('uvw', 'time', 'baseline')
                dOut.writeVarInt ('nants', self.nants0)
                dOut.writeVarFloat ('inttime', self.inttime0)
                dOut.writeVarInt ('nspect', self.nspect0)
                dOut.writeVarDouble ('sdf', self.sdf0)
                dOut.writeVarInt ('nwide', self.nwide0)
                dOut.writeVarInt ('nschan', self.nschan0)
                dOut.writeVarInt ('ischan', self.ischan0)
                dOut.writeVarDouble ('sfreq', self.sfreq0)
                dOut.writeVarDouble ('restfreq', self.restfreq0)
                dOut.writeVarInt ('pol', self.pol0)
#                inp.copyHeader (dOut, 'history')  # **hack**
                inp.initVarsAsInput (' ') # ???
                inp.copyLineVars (dOut)

            if i < int0:  # need to grab only integration at pulse+intoff
                i = i+1
                continue

            elif i < int0 + self.nbl:
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

#                ants = util.decodeBaseline (preamble[4])
#                print preamble[3], ants

#                dOut.write (self.preamble[i], data, flags)   # not working right here...?
                dOut.write (preamble, data, flags)
                i = i+1  # essentially a baseline*int number

            elif i >= int0 + self.nbl:
                break

        dOut.close ()
        return 1


    def writetrack2(self, dmbin, tbin, tshift=0, bgwindow=0, show=0):
        """Writes data from track out as miriad visibility file.
        Alternative to writetrack that uses stored, approximate preamble used from start of pulse, not middle.
        Optional background subtraction bl-by-bl over bgwindow integrations. Note that this is bgwindow *dmtracks* so width is bgwindow+track width
        """

        # create bgsub data
        datadiffarr = self.tracksub(dmbin, tbin, bgwindow=bgwindow)
        if n.shape(datadiffarr) == n.shape([0]):    # if track doesn't cross band, ignore this iteration
            return 0

        data = n.zeros(self.nchan, dtype='complex64')  # default data array. gets overwritten.
        data0 = n.zeros(self.nchan, dtype='complex64')  # zero data array for flagged bls
        flags = n.zeros(self.nchan, dtype='bool')

        # define output visibility file names
        outname = string.join(self.file.split('.')[:-1], '.') + '.' + str(self.nskip/self.nbl) + '-' + 'dm' + str(dmbin) + 't' + str(tbin) + '.mir'
        print outname
        vis = miriad.VisData(self.file,)

        int0 = int((tbin + tshift) * self.nbl)
        flags0 = []
        i = 0
        for inp, preamble, data, flags in vis.readLowlevel ('dsl3', False, nocal=True, nopass=True):
            if i == 0:
                # prep for temp output vis file
                shutil.rmtree(outname, ignore_errors=True)
                out = miriad.VisData(outname)
                dOut = out.open ('c')

                # set variables
                dOut.setPreambleType ('uvw', 'time', 'baseline')
                dOut.writeVarInt ('nants', self.nants0)
                dOut.writeVarFloat ('inttime', self.inttime0)
                dOut.writeVarInt ('nspect', self.nspect0)
                dOut.writeVarDouble ('sdf', self.sdf0)
                dOut.writeVarInt ('nwide', self.nwide0)
                dOut.writeVarInt ('nschan', self.nschan0)
                dOut.writeVarInt ('ischan', self.ischan0)
                dOut.writeVarDouble ('sfreq', self.sfreq0)
                dOut.writeVarDouble ('restfreq', self.restfreq0)
                dOut.writeVarInt ('pol', self.pol0)
#                inp.copyHeader (dOut, 'history')  # **hack**
                inp.initVarsAsInput (' ') # ???
                inp.copyLineVars (dOut)
            if i < self.nbl:
                flags0.append(flags.copy())
                i = i+1
            else:
                break

        l = 0
        for i in range(len(flags0)):  # iterate over baselines
            # write out track, if not flagged
            if n.any(flags0[i]):
                k = 0
                for j in range(self.nchan):
                    if j in self.chans:
                        data[j] = datadiffarr[0, l, k]
#                        flags[j] = flags0[i][j]
                        k = k+1
                    else:
                        data[j] = 0 + 0j
#                        flags[j] = False
                l = l+1
            else:
                data = data0
#                flags = n.zeros(self.nchan, dtype='bool')

            dOut.write (self.preamble[int0 + i], data, flags0[i])

        dOut.close ()
        return 1


    def makedmt0(self):
        """Integrates data at dmtrack for each pair of elements in dmarr, time.
        Not threaded.  Uses dmthread directly.
        Stores mean of detected signal after dmtrack, effectively forming beam at phase center.
        """

        dmarr = self.dmarr
#        reltime = n.arange(2*len(self.reltime))/2.  # danger!
        reltime = self.reltime
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


    def imagedmt0(self, dmbin, t0bin, tshift=0, bgwindow=10, show=0, clean=1, mode='dirty'):
        """ Makes and fits an background subtracted image for a given dmbin and t0bin.
        tshift can shift the actual t0bin earlier to allow reading small chunks of data relative to pickle.
        """

        # set up
        outroot = string.join(self.file.split('.')[:-1], '.') + '.' + str(self.nskip/self.nbl) + '-dm' + str(dmbin) + 't' + str(t0bin)
        shutil.rmtree (outroot+'.map', ignore_errors=True); shutil.rmtree (outroot+'.beam', ignore_errors=True); shutil.rmtree (outroot+'.clean', ignore_errors=True); shutil.rmtree (outroot+'.restor', ignore_errors=True)

        if self.approxuvw:
            status = self.writetrack2(dmbin, t0bin, tshift=tshift, bgwindow=bgwindow)   # output file at dmbin, trelbin
        else:
            status = self.writetrack(dmbin, t0bin, tshift=tshift, bgwindow=bgwindow)   # output file at dmbin, trelbin

        if not status:  # if writetrack fails, exit this iteration
            return 0

        try:
        # make image, clean, restor, fit point source
            print
            print 'Making dirty image for nskip=%d, dm[%d]=%.1f, and trel[%d] = %.3f.' % (self.nskip/self.nbl, dmbin, self.dmarr[dmbin], t0bin-tshift, self.reltime[t0bin-tshift])
            txt = TaskInvert (vis=outroot+'.mir', map=outroot+'.map', beam=outroot+'.beam', mfs=True, double=True, cell=70, imsize=160).snarf()  # good for m31 search
            if show:  txt = TaskCgDisp (in_=outroot+'.map', device='/xs', wedge=True, beambl=True).snarf () 
            txt = TaskImStat (in_=outroot+'.map').snarf()   # get dirty image stats

            if mode == 'clean':
#                print 'cleaning image'
                thresh = 2*float(txt[0][10][41:47])       # set thresh to 2*noise level in dirty image. hack! OMG!!
#                txt = TaskClean (beam=outroot+'.beam', map=outroot+'.map', out=outroot+'.clean', cutoff=thresh, region='relpix,boxes(-10,-10,10,10)').snarf ()   # targeted clean
                txt = TaskClean (beam=outroot+'.beam', map=outroot+'.map', out=outroot+'.clean', cutoff=thresh).snarf ()
                print 'Cleaned to %.2f Jy after %d iterations' % (thresh, int(txt[0][-4][19:]))
                txt = TaskRestore (beam=outroot+'.beam', map=outroot+'.map', model=outroot+'.clean', out=outroot+'.restor').snarf () 
                if show:  txt = TaskCgDisp (in_=outroot+'.restor', device='/xs', wedge=True, beambl=True, labtyp='hms,dms').snarf () 
                txt = TaskImFit (in_=outroot+'.restor', object='point').snarf () 

                # parse output of imfit
                # print '012345678901234567890123456789012345678901234567890123456789'
                peak = float(txt[0][16][30:36])
                epeak = float(txt[0][16][44:])
                off_ra = float(txt[0][17][28:39])
                eoff_ra = float(txt[0][18][30:39])
                off_dec = float(txt[0][17][40:])
                eoff_dec = float(txt[0][18][40:])
                print 'Fit cleaned image peak %.2f +- %.2f' % (peak, epeak)
                return peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec
            elif mode == 'dirty':
#                print 'stats of dirty image'
                peak = float(txt[0][10][50:57])       # get peak of dirty image
                epeak = float(txt[0][10][41:47])       # note that epeak is biased by any true flux
                print 'Individual dirty image peak %.2f +- %.2f' % (peak, epeak)
                if clean:
                    shutil.rmtree (outroot + '.mir', ignore_errors=True)
#                    shutil.rmtree (outroot+'.map', ignore_errors=True) 
                    shutil.rmtree (outroot+'.beam', ignore_errors=True); shutil.rmtree (outroot+'.clean', ignore_errors=True); shutil.rmtree (outroot+'.restor', ignore_errors=True)
                return peak, epeak
        except:
            print 'Something broke with imaging!'
            return 0


    def imsearch(self, dmind, tind, sig=5., show=0, edge=0, mode='dirty'):
        """
        Reproduce search result of pulse_search_image.
        """

        bgwindow = 10  # where bg subtraction is made

        if mode == 'dirty':
            # define typical dirty image noise level for this dm
            print 'For DM = %.1f, measuring median image noise level' % (self.dmarr[dmind])
            bgpeak = []; bgepeak = []
            for bgi in range(bgwindow, self.nints-bgwindow, self.nints/15):
                print 'Measuring noise in integration %d' % (bgi)
                outname = string.join(self.file.split('.')[:-1], '.') + '.' + str(self.nskip/self.nbl) + '-' + 'dm' + str(dmind) + 't' + str(bgi) + '.mir'
                shutil.rmtree (outname, ignore_errors=True); shutil.rmtree (outname+'.map', ignore_errors=True); shutil.rmtree (outname+'.beam', ignore_errors=True)
                status = self.writetrack2(dmind, bgi, bgwindow=bgwindow)   # output file at dmbin, trelbin
                try:
                    txt = TaskInvert (vis=outname, map=outname+'.map', beam=outname+'.beam', mfs=True, double=True, cell=80, imsize=250).snarf()
                    txt = TaskImStat (in_=outname+'.map').snarf()   # get dirty image stats
                    bgpeak.append(float(txt[0][10][51:61]))       # get peak of dirty image
                    bgepeak.append(float(txt[0][10][41:51]))       # note that epeak is biased by any true flux
                    shutil.rmtree (outname, ignore_errors=True)
                    shutil.rmtree (outname+'.map', ignore_errors=True)
                    shutil.rmtree (outname+'.beam', ignore_errors=True)
                except:
                    pass
                
            print 'Dirty image noises and their median', bgepeak, n.median(bgepeak)

            # now make dirty image
            results = self.imagedmt0(dmind, tind, show=show, bgwindow=bgwindow, clean=1, mode=mode)
            if mode == 'clean':
                peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec = results
            elif mode == 'dirty':  # need to develop more... needs to be ~10ms processing per int!
                peak, epeak = results
                epeak = n.median(bgepeak)
            if peak/epeak >= sig:
                print '\tDetection!'
            if mode == 'clean':
                print self.nskip/self.nbl, self.nints, (dmind, tind), 'Peak, (sig),  RA, Dec: ', peak, epeak, '(', peak/epeak, ')  ', off_ra, eoff_ra, off_dec, eoff_dec
            elif mode == 'dirty':
                print self.nskip/self.nbl, self.nints, (dmind, tind), 'Peak, (sig): ', peak, epeak, '(', peak/epeak, ')'


    def uvfitdmt0(self, dmbin, t0bin, bgwindow=10, tshift=0, show=1, mode='fit'):
        """ Makes and fits a point source to background subtracted visibilities for a given dmbin and t0bin.
        tshift can shift the actual t0bin earlier to allow reading small chunks of data relative to pickle.
        """
        
        # set up
        outroot = string.join(self.file.split('.')[:-1], '.') + '.' + str(self.nskip/self.nbl) + '-dm' + str(dmbin) + 't' + str(t0bin)
        shutil.rmtree (outroot + '.mir', ignore_errors=True)

        if self.approxuvw:
            status = self.writetrack2(dmbin, t0bin, tshift=tshift, bgwindow=bgwindow)   # output file at dmbin, trelbin
        else:
            status = self.writetrack(dmbin, t0bin, tshift=tshift, bgwindow=bgwindow)   # output file at dmbin, trelbin

        if not status:  # if writetrack fails, exit this iteration
            return 0

        if mode == 'fit':
            try:
                # fit point source model to visibilities
                print
                print 'UVfit for nskip=%d, dm[%d] = %.1f, and trel[%d] = %.3f.' % (self.nskip/self.nbl, dmbin, self.dmarr[dmbin], t0bin-tshift, self.reltime[t0bin-tshift])
                txt = TaskUVFit (vis=outroot+'.mir', object='point', select='-auto').snarf()

                # parse output of imfit
                # print '012345678901234567890123456789012345678901234567890123456789'
                peak = float(txt[0][8][30:38])
                epeak = float(txt[0][8][46:])
                off_ra = float(txt[0][9][30:38])
                eoff_ra = float(txt[0][10][31:42])
                off_dec = float(txt[0][9][40:])
                eoff_dec = float(txt[0][10][42:])
                print 'Fit peak %.2f +- %.2f' % (peak, epeak)
                shutil.rmtree (outroot + '.mir', ignore_errors=True)
                return peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec
            except:
                print 'Something broke in/after uvfit!'
                shutil.rmtree (outroot + '.mir', ignore_errors=True)
                return 0

        elif mode == 'grid':
            llen = 150
            mlen = 150
            linspl = n.linspace(-4000,4000,llen)
            linspm = n.linspace(-4000,4000,mlen)
            snrarr = n.zeros((llen, mlen))
            
            for i in range(llen):
                print 'Starting loop ', i
                for j in range(mlen):
                    try:
                        txt = TaskUVFit (vis=outroot+'.mir', object='point', select='-auto', spar='0,'+str(linspl[i])+','+str(linspm[j]), fix='xy').snarf()
#                        print txt[0][8:10]
                        peak = float(txt[0][8][30:38])
                        epeak = float(txt[0][8][46:])
                        off_ra = float(txt[0][9][30:38])
                        off_dec = float(txt[0][9][40:])
                        snrarr[i, j] = peak/epeak
                    except:
                        print 'Something broke in/after uvfit!'

            peak = n.where(snrarr == snrarr.max())
            print 'Peak: ', snrarr[peak]
            print 'Location: ', peak, (linspl[peak[0]], linspm[peak[1]])
            print
            print 'Center SNR: ', snrarr[llen/2,llen/2]

            log = open('log.txt','a')
            print >> log, outroot, snrarr[peak], peak, (linspl[peak[0]], linspm[peak[1]])
            log.close()

            ax = p.imshow(snrarr, aspect='auto', origin='lower', interpolation='nearest')
            p.colorbar()
            p.savefig(outroot + '.png')


    def uvfitdmt02 (self, dmbin, t0bin, bgwindow=10, tshift=0, show=1, mode='default'):
        """Experimental alternative function to do uvfitting of visibilities.
        Reads in data from dispersion track, then fits uv model of point source in python.
        mode defines the optimization approach.
        """

        datadiffarr = self.tracksub(dmbin, t0bin, bgwindow=bgwindow)
        int0 = int((t0bin + tshift) * self.nbl)
        meanfreq = n.mean(self.sfreq + self.sdf * self.chans )

        obsrms = self.obsrms

        if show:
            p.figure(1)
            p.plot(datadiffarr[0].mean(axis=1).real, datadiffarr[0].mean(axis=1).imag, '.')

        # get flags to help select good ants
        vis = miriad.VisData(self.file,)
        flags0 = []
        i = 0
        for inp, preamble, data, flags in vis.readLowlevel ('dsl3', False, nocal=True, nopass=True):
            if i < self.nbl:
                flags0.append(flags.copy())
                i = i+1
            else:
                break
        goodants = n.where( n.any(n.array(flags0), axis=1) == True)

        u = []; v = []; w = []
        for i in range(self.nbl):  
            u.append(self.preamble[int0 + i][0])  # in units of ns
            v.append(self.preamble[int0 + i][1])  # in units of ns
            w.append(self.preamble[int0 + i][2])  # in units of ns
        u = n.array(u); v = n.array(v); w = n.array(w)
        u = meanfreq * u[goodants]; v = meanfreq * v[goodants]; w = meanfreq * w[goodants]
        data = (datadiffarr[0]).mean(axis=1)

        print
        print 'UVfit2 for nskip=%d, dm[%d] = %.1f, and trel[%d] = %.3f.' % (self.nskip/self.nbl, dmbin, self.dmarr[dmbin], t0bin-tshift, self.reltime[t0bin-tshift])

        vi = lambda a, l, m, u, v, w: a * n.exp(-2j * n.pi * (u*l + v*m)) # + w*n.sqrt(1 - l**2 - m**2)))  # ignoring w term
        phi = lambda l, m, u, v: 2 * n.pi * (l*u + m*v)
        amp = lambda vi, l, m, u, v, w: n.mean(n.real(vi) * n.cos(phi(l, m, u, v)) + n.imag(vi) * n.sin(phi(l, m, u, v)))

        def errfunc (p, u, v, w, y, obsrms):
            a, l, m = p
            err = (y - vi(a, l, m, u, v, w))/obsrms
            return err.real + err.imag

        def errfunc2 (p, l, m, u, v, w, y):
            a = p
            err = (y - vi(a, l, m, u, v, w))
            return err.real + err.imag

        def ltoa (l):
            a = n.arcsin(l) * 180 / n.pi * 3600
            return a

        if mode == 'default':
            p0 = [100.,0.,0.]
            out = opt.leastsq(errfunc, p0, args = (u, v, w, data, obsrms), full_output=1)
            p1 = out[0]
            covar = out[1]
            print 'Fit results (Jy, arcsec, arcsec):', p1[0], ltoa(p1[1]), ltoa(p1[2])
            print 'Change in sumsq: %.2f to %.2f' % (n.sum(errfunc(p0, u, v, w, data, obsrms)**2), n.sum(errfunc(p1, u, v, w, data, obsrms)**2))

            print 'here\'s some stuff...'
            print covar
            print n.sqrt(covar[0][0])
            print n.sqrt(covar[1][1])

        elif mode =='directi':
            llen = 60
            mlen = 60
            linspl = n.linspace(-0.01,0.01,llen)   # dl=0.026 => 1.5 deg (half ra width of andromeda)
            linspm = n.linspace(-0.01,0.01,mlen)   # dl=0.01 => 0.57 deg (half dec width of andromeda)
            amparr = n.zeros((llen, mlen))
            p0 = [100.]
            
            for i in range(llen):
                for j in range(mlen):
                    out = amp(data, linspl[i], linspm[j], u, v, w)
                    amparr[i, j] = out

            maxs = n.where(amparr >= 0.9*amparr.max())
            print 'Peak: ', amparr.max()
            print 'Location: ', maxs, (ltoa(linspl[maxs[0]]), ltoa(linspm[maxs[1]]))
            print 'SNR: ', amparr.max()/obsrms

            if show:
                p.figure(2)
                ax = p.imshow(amparr, aspect='auto', origin='lower', interpolation='nearest')
                p.colorbar()
                p.show()

        elif mode =='peaki':
            llen = 60
            mlen = 60
            linspl = n.linspace(-0.01,0.01,llen)   # dl=0.026 => 1.5 deg (half ra width of andromeda)
            linspm = n.linspace(-0.01,0.01,mlen)   # dl=0.01 => 0.57 deg (half dec width of andromeda)
            amparr = n.zeros((llen, mlen))
            p0 = [100.]
            
            peak = 0.
            imax = 0
            jmax = 0
            for i in range(llen):
                for j in range(mlen):
                    aa = amp(data, linspl[i], linspm[j], u, v, w)
                    if peak < aa:
                        peak = aa
                        imax = i
                        jmax = j                    

            print 'Peak: ', peak
            print 'Location: ', ltoa(linspl[imax]), ltoa(linspm[jmax])
            print 'SNR: ', peak/obsrms

            if show:
                p.show()

        elif mode == 'map':
            p0 = [100.,0.,0.]
            out = opt.leastsq(errfunc, p0, args = (u, v, w, data, obsrms), full_output=1)
            p1 = out[0]
            covar = out[1]

            llen = 20
            mlen = 20
            sumsq = n.zeros((llen, mlen))
            linspl = n.linspace(-0.005,0.005,llen)   # dl=0.026 => 1.5 deg (half ra width of andromeda)
            linspm = n.linspace(-0.005,0.005,mlen)   # dl=0.01 => 0.57 deg (half dec width of andromeda)
            for i in range(llen):
                for j in range(mlen):
                    sumsq[i, j] = n.sum(errfunc([p1[0], linspl[i], linspm[j]], u, v, w, data, obsrms)**2)

            mins = n.where(sumsq < 1.01 * sumsq.min())
            print 'Best fit: ', p1
            print 'Red. chisq: ', sumsq[mins][0]/(9-3)
            print 'Location: ', mins, (ltoa(linspl[mins[0]])[0], ltoa(linspm[mins[1]])[0])

            if show:
                p.figure(2)
                p.plot(mins[1], mins[0], 'w.')
                p.imshow(sumsq)
                p.colorbar()
                p.show()

        elif mode == 'lsgrid':
            llen = 30
            mlen = 30
            linspl = n.linspace(-0.005,0.005,llen)   # dl=0.026 => 1.5 deg (half ra width of andromeda)
            linspm = n.linspace(-0.005,0.005,mlen)   # dl=0.01 => 0.57 deg (half dec width of andromeda)
            amparr = n.zeros((llen, mlen))
            p0 = [100.]
            
            for i in range(llen):
                for j in range(mlen):
                    out = opt.leastsq(errfunc2, p0, args = (linspl[i], linspm[j], u, v, w, data), full_output=1)
                    amparr[i, j] = out[0]

            maxs = n.where(amparr >= 0.9*amparr.max())
            print 'Peak: ', amparr.max()
            print 'Location: ', maxs, (ltoa(linspl[maxs[0]]), ltoa(linspm[maxs[1]]))
            print 'SNR: ', amparr.max()/obsrms
            print
            print 'Center: ', amparr[15,15]
            print 'Center SNR: ', amparr[15,15]/obsrms

            if show:
                p.figure(2)
                ax = p.imshow(amparr, aspect='auto', origin='lower', interpolation='nearest')
                p.colorbar()
                p.show()


    def closure(self, dmbin, bgwindow=0, show=0):
        """Calculates the closure phase or bispectrum for each integration, averaging over all channels (for now).
        Detection can be done by averaging closure phases (bad) or finding when all triples have SNR over a threshold.
        """

        triph = lambda d,i,j,k: n.mod(n.angle(d[i]) + n.angle(d[j]) - n.angle(d[k]), 2*n.pi)  # triple phase

# use triples
        bisp = lambda d,i,j,k: d[i] * d[j] * n.conj(d[k])     # bispectrum w/o normalization
        triples = [(0,7,6),(0,2,1),(0,4,3),(6,8,3),(1,5,3)]  # antenna triples for good poco data: 123, 125, 126, 136, 156 (correct! miriad numbering). 6 true triples for n=5 is 123 125 126 135 136 156
        
# option 1: triple phase average over frequency
#        triarr = n.zeros((len(triples), len(self.data)))
# option 2: triple phase no freq avg
#        triarr = n.zeros((len(self.data)-2*bgwindow-1, len(triples), len(self.data[0,0])))
# option 3: bispectrum
        bisparr = n.zeros((len(triples), len(self.data)), dtype=n.dtype('complex'))

        print 'Building closure quantity array...'
        for int in range(len(self.data)):
            diff = self.tracksub(dmbin, int, bgwindow=bgwindow)
            if len(n.shape(diff)) == 1:    # no track
                continue
            diffmean = diff[0].mean(axis=1)    # option 1, 3
            for tr in range(len(triples)):
# use triples
                (i,j,k) = triples[tr]
                bisparr[tr,int] = complex(bisp(diffmean, i, j, k))    # option 3

        bispstd = n.array( [n.sqrt((n.abs(bisparr[i]**2).mean())) for i in range(len(triples))] )
        print 'First pass, bispstd: ', bispstd  
        threesig = n.array( [n.where( bisparr[i] < 3*bisparr[i].std() )[0] for i in range(len(triples))] )
        bispstd = n.array( [n.sqrt((n.abs(bisparr[i,threesig[i]]**2).mean())) for i in range(len(triples))] )
        print 'Second pass, bispstd: ', bispstd  

        bispsnr = n.array( [2*bisparr[i].real/bispstd[i] for i in range(len(triples))] )

        # normalize SNR by average of all triples?

        bispsnr = bispsnr.mean(axis=0)
        peaks = n.where( bispsnr > 5 )   # significant pulse for bispectrum with snr > 5
#        peakswhere = n.array([], dtype='int')
#        peaksint = []
#        for i in n.unique(peaks[1]):
#            npeaks = n.where(peaks[1] == i)[0]
#            if len(npeaks) == len(triples):     # set threshold for all triples 
#                peakswhere = n.concatenate( (peakswhere,npeaks) )
#                peaksint.append(i)

        if show:
            p.figure(1)
#            p.plot(peaks[1][peakswhere],bispsnr[peaks][peakswhere],'*')
#            for i in range(len(bispsnr)):
            p.plot(bispsnr,'.')
            p.show()

# option 1 and 2
#        peakstot = n.concatenate( (peaks, peaks2) )
#        peaksstdtot = n.concatenate( (tristd[peaks], tristd2[peaks2]) )
#        return peakstot,peaksstdtot

#        return (peaks[0][peakswhere], peaks[1][peakswhere]), bispsnr[peaks][peakswhere]
        return peaks,bispsnr


    def dmlc(self, dmbin, tbin):
        """Plots lc for DM bin over range of timebins.
        In principle, should produce lightcurve as if it is a slice across dmt0 plot.
        Actually designed to test writetrack function.
        """
        pass


    def normalreim(self, prob=2.3e-4, bgwindow=0):
        """Calculates p-value of normality for real-imaginary distribution of visibilities (uses real/imag separately).
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
                        newfile = string.join(self.file.split('.')[:-1], '.') + '.' + str(self.nskip/self.nbl) + '-' + 'dm' + str(i) + 't' + str(j) + '.mir'
                        print 'Loading file', newfile
                        pv2 = poco(newfile, nints=1)
                        pv2.prep()
                        length = pv2.data.shape[1] * pv2.data.shape[2]
                        da = (pv2.data[0]).reshape((1,length))[0]
                        shutil.rmtree(newfile, ignore_errors=True)
                        dmt0arr[i,j] = min(morestats.shapiro(da.real)[1], morestats.shapiro(da.imag)[1])
                else:
                    datadiff = self.tracksub(i, j, bgwindow=bgwindow)
                    if len(n.shape(datadiff)) == 3:
                        length = datadiff.shape[1] * datadiff.shape[2]
                        datadiff = (datadiff[0]).reshape((1,length))[0]
                        dmt0arr[i,j] = min(morestats.shapiro(datadiff.real)[1], morestats.shapiro(datadiff.imag)[1])
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


    def stdreim(self, fstd=1.2, bgwindow=0, show=0):
        """Calculates standard deviation of real-imaginary distribution of visibilities. Uses baselines and channels separately. 
        fstd is threshold factor of change in std to make detection.
        Returns trials with large std change.
        """

        write = 0  # use writetrack to get bgsub visies? takes long time...
        tbuffer = 7  # number of extra iterations to trim from edge of dmt0 plot

        dmarr = self.dmarr
        reltime = self.reltime
        chans = self.chans

        dmt0arr = n.zeros((len(dmarr),len(reltime)), dtype='float64')

        for i in range(len(dmarr)):
            for j in range(len(reltime)):
                datadiff = self.tracksub(i, j, bgwindow=bgwindow)
                if len(n.shape(datadiff)) == 3:
                    dmt0arr[i,j] = n.std(datadiff)
                else:
                    continue
            print 'dedispersed for ', dmarr[i]

        # Trim data down to where dmt0 array is nonzero
        arreq0 = n.where(dmt0arr == 0)
        trimt = arreq0[1].min()
        dmt0arr = dmt0arr[:,:trimt - tbuffer]
        reltime = reltime[:trimt - tbuffer]
        print 'dmt0arr/time trimmed to new shape:  ',n.shape(dmt0arr), n.shape(reltime)

        # Detect peaks
        self.dmt0arr = dmt0arr
        self.peaks = n.where(dmt0arr > fstd * dmt0arr.mean())
        peakmax = n.where(dmt0arr == dmt0arr.max())
        print 'Least normal re-im distributions: ', self.peaks
        print 'Number of trials: ', len(dmarr) * len(reltime)

        if show:
            for i in range(len(self.peaks[1])):
                ax = p.imshow(dmt0arr, aspect='auto', origin='lower', interpolation='nearest', extent=(min(reltime),max(reltime),min(dmarr),max(dmarr)))
                p.axis((min(reltime),max(reltime),min(dmarr),max(dmarr)))
                p.plot([reltime[self.peaks[1][i]]], [dmarr[self.peaks[0][i]]], 'o', markersize=2*dmt0arr[self.peaks[0][i],self.peaks[1][i]], markerfacecolor='white', markeredgecolor='blue', alpha=0.5)

            p.xlabel('Time (s)')
            p.ylabel('DM (pc/cm3)')
            p.title('Summed Spectra in DM-t0 space')

        return self.peaks,dmt0arr[self.peaks]


    def plotreim(self, save=0):
        """Plots the visibilities in real-imaginary space. Test of pulse detection concept for uncalibrated data...
        """

        da = self.data.mean(axis=0)
        length = da.shape[0] * da.shape[1]
        da = da.reshape((1,length))[0]

        print 'Real center: %.1f +- %.1f ' % (da.real.mean(), da.real.std()/n.sqrt(len(da.real)))
        print 'Imag center: %.1f +- %.1f ' % (da.imag.mean(), da.imag.std()/n.sqrt(len(da.real)))
        print 'Normal p-value (real): ', morestats.shapiro(da.real)[1]
        print 'Normal p-value (imag): ', morestats.shapiro(da.imag)[1]

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
        fileout = open(pathout + string.join(file.split('.')[:-1], '.') + '.txt', 'a')

#        for nskip in range(0, maxints-(nints-edge), nints-edge):
        for nskip in range(0, 2000, 2000):
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
                pklout = open(pathout + string.join(file.split('.')[:-1], '.') + '.' + str(nskip) + '.pkl', 'wb')
                pickle.dump((file, nskip, nints, peaks[0], pv.dmarr[peaks[0][0]], peaks[1], peakssig), pklout)
                pklout.close()

        fileout.close


def pulse_search_closure(fileroot, pathin, pathout, nints=10000, edge=0):
    """Blind search for pulses via closure phase.
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
        fileout = open(pathout + string.join(file.split('.')[:-1], '.') + '_nocal.txt', 'a')

        for nskip in range(0, maxints-(nints-edge), nints-edge):
#        for nskip in range(0, 2000, 2000):
            print
            print 'Starting file %s with nskip %d' % (file, nskip)

            # load data
            pv = poco(pathin + file, nints=nints, nskip=nskip, nocal=True)
            pv.prep()

            # searches for closure phase dips
            peaks, peaksstd = pv.closure(0)
            print peaks, peaksstd
            print >> fileout, file, nskip, nints, peaks, peaksstd
            print

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
    for i in [0,1,2,3,4,5,6,7,8,9]:
        filelist.append(string.join(fileroot.split('.')[:-1]) + '_0' + str(i) + '.mir')
    for i in [0,1,2,6,7,8,9]:
        filelist.append(string.join(fileroot.split('.')[:-1]) + '_1' + str(i) + '.mir')
    for i in [0,1,2,3]:
        filelist.append(string.join(fileroot.split('.')[:-1]) + '_2' + str(i) + '.mir')

# for m31 154202
#    for i in [0,1,2,3,4,5,6,7,8,9]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_0' + str(i) + '.mir')
#    for i in [0,1,2,3,4,5,6]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_1' + str(i) + '.mir')

# hack to search single file for pulses
#    filelist = [fileroot]

    # loop over miriad data and time chunks
    for file in filelist:
        fileout = open(pathout + string.join(file.split('.')[:-1], '.') + '.txt', 'a')

        for nskip in range(0, maxints-(nints-edge), nints-edge):
            print
            print 'Starting file %s with nskip %d' % (file, nskip)

            # load data
            pv = poco(pathin + file, nints=nints, nskip=nskip, nocal=True, nopass=True)
            pv.prep()

            # searches at phase center  ## TO DO:  need to search over position in primary beam
            dips, dipsprob = pv.stdreim(bgwindow=bgwindow)
#            dips, dipsprob = pv.normalreim(bgwindow=bgwindow, prob=1e-7)
            print >> fileout, file, nskip, nints, dips

            # save all results (v1.0 pickle format)
            # TO DO:  think of v2.0 of pickle format
            if len(dips[0]) > 0:
                pklout = open(pathout + string.join(file.split('.')[:-1], '.') + '.' + str(nskip) + '.pkl', 'wb')
                pickle.dump((file, nskip, nints, dips[0], pv.dmarr[dips[0][0]], dips[1], dipsprob), pklout)
                pklout.close()

        fileout.close


def pulse_search_image(fileroot, pathin, pathout, nints=12000, sig=5.0, show=0, edge=0, mode='dirty', dmrange=None, nstart=0, tstop=0):
    """
    Searches for pulses by imaging dedispersed trials.
    dmrange lets outside call limit range of dms to search (good to spread jobs out in parallel).
    nstart and tstop control start integration and duration of run. useful for running on cluster.
    """

    if tstop != 0:
        import time
        t0 = time.time()
        print 'Time limited search starting at ', time.ctime()

    maxints = 131000  # biggest file in integrations
    bgwindow = 10  # where bg subtraction is made

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

    print 'Looping over filelist ', filelist, ' with dmrange, ', dmrange
    for file in filelist:
        for nskip in range(nstart, maxints-(nints-edge), nints-edge):
            print 'Starting file %s with nskip %d' % (file, nskip)

            # load data
            pv = poco(pathin + file, nints=nints, nskip=nskip)
            pv.prep()

            if dmrange == None:
                dmrange = range(len(pv.dmarr))

            fileout = open(pathout + string.join(file.split('.')[:-1], '.') + '_dm' + str(dmrange[0]) + '.txt', 'a')

            # dedisperse
            for i in dmrange:

                if mode == 'dirty':
                # define typical dirty image noise level for this dm
                    print 'For DM = %.1f, measuring median image noise level' % (pv.dmarr[i])
                    bgpeak = []; bgepeak = []
                    for bgi in range(bgwindow, nints-bgwindow, nints/15):
                        print 'Measuring noise in integration %d' % (bgi)
                        outname = string.join(pv.file.split('.')[:-1], '.') + '.' + str(pv.nskip/pv.nbl) + '-' + 'dm' + str(i) + 't' + str(bgi) + '.mir'
                        shutil.rmtree (outname, ignore_errors=True); shutil.rmtree (outname+'.map', ignore_errors=True); shutil.rmtree (outname+'.beam', ignore_errors=True)
                        status = pv.writetrack2(i, bgi, bgwindow=bgwindow)   # output file at dmbin, trelbin
                        try:
                            txt = TaskInvert (vis=outname, map=outname+'.map', beam=outname+'.beam', mfs=True, double=True, cell=80, imsize=250).snarf()
                            txt = TaskImStat (in_=outname+'.map').snarf()   # get dirty image stats
                            bgpeak.append(float(txt[0][10][51:61]))       # get peak of dirty image
                            bgepeak.append(float(txt[0][10][41:51]))       # note that epeak is biased by any true flux
                            shutil.rmtree (outname, ignore_errors=True)
                            shutil.rmtree (outname+'.map', ignore_errors=True)
                            shutil.rmtree (outname+'.beam', ignore_errors=True)
                        except:
                            pass
                    print 'Dirty image noises and their median', bgepeak, n.median(bgepeak)
                # now iterate over integrations
                for j in range(len(pv.reltime)):
                    if (tstop != 0) & ((j % 10) == 0):     # check if time limit exceeded
                        if (time.time() - t0) / 3600 > tstop:
                            print 'Time limit exceeded...'
                            fileout.close
                            return 0
                    try: 
                        results = pv.imagedmt0(i, j, show=show, bgwindow=bgwindow, clean=1, mode=mode)
                        if mode == 'clean':
                            peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec = results
                        elif mode == 'dirty':  # need to develop more... needs to be ~10ms processing per int!
                            peak, epeak = results
                            epeak = n.median(bgepeak)
                        if peak/epeak >= sig:
                            print '\tDetection!'
                            if mode == 'clean':
                                print >> fileout, file, nskip, nints, (i, j), 'Peak, (sig),  RA, Dec: ', peak, epeak, '(', peak/epeak, ')  ', off_ra, eoff_ra, off_dec, eoff_dec
                            elif mode == 'dirty':
                                print >> fileout, file, nskip, nints, (i, j), 'Peak, (sig): ', peak, epeak, '(', peak/epeak, ')'
                            # save all results (v1.0 pickle format)
                            pklout = open(pathout + string.join(file.split('.')[:-1], '.') + '.' + str(nskip) + '-dm' + str(i) + 't' + str(j) + '.pkl', 'wb')
                            pickle.dump((file, nskip, nints, n.array([i]), pv.dmarr[i], n.array([j]), n.array([peak/epeak])), pklout)
                            pklout.close()
                    except:
                        continue
                if mode == 'dirty':
                    print >> fileout, '   Finished ', file, nskip, nints, (i, j), '. Noise = ', n.median(bgepeak)

        fileout.close


def pulse_search_uvfit(fileroot, pathin, pathout, nints=2000, sig=5.0, show=0, edge=0):
    """
    Searches for pulses by imaging dedispersed trials.
    """

    maxints = 131000  # biggest file in integrations
    bgwindow = 10  # where bg subtraction is made

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
    for i in [0,1,2,3,4,5,6,7,8,9]:
        filelist.append(string.join(fileroot.split('.')[:-1]) + '_0' + str(i) + '.mir')
    for i in [0,1,2,6,7,8,9]:
        filelist.append(string.join(fileroot.split('.')[:-1]) + '_1' + str(i) + '.mir')
    for i in [0,1,2,3]:
        filelist.append(string.join(fileroot.split('.')[:-1]) + '_2' + str(i) + '.mir')

# for m31 154202
#    for i in [0,1,2,3,4,5,6,7,8,9]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_0' + str(i) + '.mir')
#    for i in [0,1,2,3,4,5,6]:
#        filelist.append(string.join(fileroot.split('.')[:-1]) + '_1' + str(i) + '.mir')

# hack to search single file for pulses
    filelist = [fileroot]
        
    print 'Looping over filelist: ', filelist
    for file in filelist:
        fileout = open(pathout + string.join(file.split('.')[:-1], '.') + '.txt', 'a')

        for nskip in [1000]:
            print 'Starting file %s with nskip %d' % (file, nskip)

            # load data
            pv = poco(pathin + file, nints=nints, nskip=nskip)
            pv.prep()

            # dedisperse
            for i in range(len(pv.dmarr)):
                pv.setstd(i)
                for j in range(len(pv.reltime)):
                    try: 
                        peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec = pv.uvfitdmt02(i,j, show=show, bgwindow=bgwindow, mode='directi')
#                        print >> fileout, file, nskip, nints, (i, j), 'Peak, RA, Dec: ', peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec

                        if peak/epeak >= sig:
                            print '\tDetection!'
                            print >> fileout, file, nskip, nints, (i, j), 'Peak, (sig),  RA, Dec: ', peak, epeak, '(', peak/epeak, ')  ', off_ra, eoff_ra, off_dec, eoff_dec
                            # save all results (v1.0 pickle format)
                            pklout = open(pathout + string.join(file.split('.')[:-1], '.') + '.' + str(nskip) + '-dm' + str(i) + 't' + str(j) + '.pkl', 'wb')
                            pickle.dump((file, nskip, nints, n.array([i]), pv.dmarr[i], n.array([j]), n.array([peak/epeak])), pklout)
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
    if snrarr[0] <= 1:  # reim mode has p-values for normality, which should be small when there is a pulse
        peaktrial = n.where(snrarr == min(snrarr))[0][0]
    else:
        peaktrial = n.where(snrarr == max(snrarr))[0][0]

    bgwindow = 10

#    name = 'poco_b0329_173027_00.mir'  # hack to force using certain file
    
    print 'Loaded pickle file for %s plot of %s' % (mode, name)
    print 'Has peaks at DM = ', dmarr, ' with sig ', snrarr
    print 'Using ', snrarr[peaktrial]

    if len(dmbinarr) >= 1:
#    if (len(dmbinarr) >= 1) & (snrarr[peaktrial] > 7.):
        print 'Grabbing %d ints at %d' % (nints, nintskip)
#        pv = poco(pathin + name, nints=nints, nskip=nintskip + tbinarr[peaktrial] - bgwindow)    # to skip a few ints...
#        pv.nskip=nintskip*pv.nbl    # to skip a few ints...
        pv = poco(pathin + name, nints=nints, nskip=nintskip)
#        pv = poco(pathin + name, nints=nints, nskip=nintskip, nocal=True, nopass=True)
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
                p.plot(pv.reltime[track[0]], track[1], 'w*')
                pv.spec(save=0)
                # now estimate obsrms
#                status = pv.writetrack(dmbinarr[peaktrial], tbinarr[peaktrial]+bgwindow, tshift=0, bgwindow=0)
#                bgname = string.join(pv.file.split('.')[:-1]) + '.' + str(pv.nskip/pv.nbl) + '-' + 'dm' + str(dmbinarr[peaktrial]) + 't' + str(tbinarr[peaktrial]+bgwindow) + '.mir'
#                pvbg = poco(bgname, nints=1)
#                pvbg.prep()
#                obsrms = n.abs(pvbg.data.mean(axis=1)[0]).std()
#                print 'obsrms first try:', obsrms
#                shutil.rmtree(bgname, ignore_errors=True)
#               newfile = string.join(pv.file.split('.')[:-1]) + '.' + str(pv.nskip/pv.nbl) + '-' + 'dm' + str(dmbinarr[peaktrial]) + 't' + str(bgwindow) + '.mir'
#
                newfile = string.join(pv.file.split('.')[:-1], '.') + '.' + str(pv.nskip/pv.nbl) + '-' + 'dm' + str(dmbinarr[peaktrial]) + 't' + str(tbinarr[peaktrial]) + '.mir'
                print 'Loading file', newfile
                pv2 = poco(newfile, nints=1)
                pv2.prep()
                pv2.fitspec(obsrms=0, save=0)
                p.show()
                shutil.rmtree(newfile, ignore_errors=True)
        elif mode == 'dmt0':
            pv.makedmt0()
            peaks, peakssig = pv.peakdmt0()
#            p.plot(pv.reltime[bgwindow], pv.dmarr[dmbinarr[peaktrial]], '*' )   # not working?
            pv.plotdmt0(save=1)
        elif mode == 'image':
            immode = 'dirty'
            results = pv.imagedmt0(dmbinarr[peaktrial], tbinarr[peaktrial], bgwindow=bgwindow, clean=1, mode=immode, show=1)
            if immode == 'clean':
                peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec = results
                print peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec
            elif immode == 'dirty':
                peak, std = results
                print peak, std
        elif mode == 'uvfit':
            uvmode = 'elsegrid'
            if uvmode == 'grid':
                pv.uvfitdmt02(dmbinarr[peaktrial], tbinarr[peaktrial], mode='lsgrid')
            else:
                uvmode = 'grid'
                results = pv.uvfitdmt0(dmbinarr[peaktrial], tbinarr[peaktrial], mode='grid')
#                peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec = results
#                print peak, epeak, off_ra, eoff_ra, off_dec, eoff_dec
        elif mode == 'dump':
            # write dmtrack data out for imaging
            pv.writetrack(track)
        elif mode == 'reim':
            datasub = pv.tracksub(dmbinarr[peaktrial], tbinarr[peaktrial], bgwindow=bgwindow)
            pv.data = datasub
            pv.plotreim()
        elif mode == 'imsearch':
            pv.imsearch(dmbinarr[peaktrial], tbinarr[peaktrial], sig=7.0)
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

    fileroot = 'tmp.mir'
#    fileroot = 'poco_b0329_173027_00.mir'
    pathin = 'data/'
    pathout = 'tst/'
#    edge = 150 # m31 search up to dm=131 and pulse starting at first unflagged channel
    edge = 35 # b0329 search at dm=28.6 and pulse starting at first unflagged channel
#    edge = 70 # Crab search at dm=56.8 and pulse starting at first unflagged channel

    if len(sys.argv) == 1:
        # if no args, search for pulses
        print 'Searching for pulses...'
        try:
#            cProfile.run('pulse_search_uvfit(fileroot=fileroot, pathin=pathin, pathout=pathout, nints=500, edge=edge)')
#            pulse_search_image(fileroot=fileroot, pathin=pathin, pathout=pathout, nints=2000, edge=edge, mode='dirty', sig=7.0)
#            pulse_search_phasecenter(fileroot=fileroot, pathin=pathin, pathout=pathout, nints=2000, edge=edge)
            cProfile.run('pulse_search_closure(fileroot=fileroot, pathin=pathin, pathout=pathout, nints=2000, edge=edge)')
#            pulse_search_reim(fileroot=fileroot, pathin=pathin, pathout=pathout, nints=2000, edge=edge)
        except AttributeError:
            exit(0)
    elif len(sys.argv) == 2:
        # if pickle, then plot data or dm search results
        print 'Assuming input file is pickle of candidate...'
        process_pickle(sys.argv[1], pathin=pathin, mode='spec')
    elif len(sys.argv) == 7:
        # if pickle, then plot data or dm search results
        print 'Time limited searching for pulses... with %s, %s, %s' % (fileroot, pathin, pathout)
        try:
            dmrange = [int(sys.argv[4])]    # only works for single dm
            nstart = int(sys.argv[5])  # start integration
            tstop = float(sys.argv[6])  # run time in hours
            pulse_search_image(fileroot=sys.argv[1], pathin=sys.argv[2], pathout=sys.argv[3], nints=20000, edge=edge, mode='dirty', sig=7.0, dmrange=dmrange, nstart=nstart, tstop=tstop)
        except AttributeError:
            exit(0)
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
