#! /usr/bin/env python

"""= pocovis.py - visualization of poco data
& claw
: Unknown
+
 Script to load and visualize poco data
--
"""

import sys, string
#import mirtask
#from mirtask import uvdat, keys, util
import miriad, pickle
import numpy as n
import pylab as p
import scipy.optimize as opt
#from threading import Thread
#from matplotlib.font_manager import fontManager, FontProperties
#font= FontProperties(size='x-small');


class poco:
    def __init__(self,file,nints=1000,nskip=0):
        # initialize
        self.nchan = 64
        self.chans = n.arange(6,58)
        self.nbl = 36
        initsize = nints*self.nbl   # number of integrations to read in a single chunk
        self.sfreq = 0.718  # freq for first channel in GHz
        self.sdf = 0.104/self.nchan   # dfreq per channel in GHz
        self.baseline_order = n.array([ 257, 258, 514, 261, 517, 1285, 262, 518, 1286, 1542, 259, 515, 773, 774, 771, 516, 1029, 1030, 772, 1028, 1287, 1543, 775, 1031, 1799, 1544, 776, 1032, 1800, 2056, 260, 263, 264, 519, 520, 1288])   # second iteration of bl nums
        self.autos = []
        self.noautos = []
        self.dmarr = n.arange(52,63,1)       # dm trial range in pc/cm3
#        self.tshift = 0.2     # not implemented yet
        self.nskip = nskip*self.nbl    # number of iterations to skip (for reading in different parts of buffer)
        nskip = self.nskip
        self.usedmmask = False    # algorithm for summing over dm track.  'dmmask' is data-shaped array with True/False values, else is 2xn array where track is.
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
        vis = miriad.VisData(file)

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

        self.rawdata = da.reshape((i-nskip)/nbl,nbl,nchan)
        self.flags = fl.reshape((i-nskip)/nbl,nbl,nchan)
        self.time = ti[::nbl]
        self.reltime = 24*3600*(self.time - self.time[0])      # relative time array in seconds
        print
        print 'Data read!'
        print 'Shape of raw data, flags, time:'
        print self.rawdata.shape, self.flags.shape, self.time.shape
        print 


    def prep(self):
        self.data = (self.rawdata * self.flags)[:,self.noautos].mean(axis=1)
        self.data = self.data[:,self.chans] 
        self.rawdata = (self.rawdata * self.flags)[:,:,self.chans]

        print 'Data flagged, trimmed in channels, and averaged across baselines.'
        print 'New shape:'
        print self.data.shape


    def spec(self, save=0):
        chans = self.chans
        reltime = self.reltime
        data = self.data

# does not account for noise bias.  assumes lots of flux in the field
        print 'Renormalizing the data.  No noise bias correction.'
        abs = n.abs(data)
        mean = abs.mean()
        std = abs.std()
        abs = (abs - mean)/std

        print 'Plotting spectrgram.'
        p.figure(1)
        ax = p.imshow(n.rot90(abs), aspect='auto', origin='upper', interpolation='nearest', extent=(min(reltime),max(reltime),min(chans),max(chans)))
        p.colorbar(ax)
        p.xlabel('Relative time (s)')
        p.ylabel('Channel ')
        if save:
            savename = self.file.split('.')[:-1]
            savename.append(str(self.nskip/self.nbl) + '.spec.png')
            savename = string.join(savename,'.')
            p.savefig(savename)


    def dmmask(self, dm = 0., t0 = 0., show=0,):
        """Takes dispersion measure in pc/cm3 and time offset from first integration in seconds.
        Returns a mask to be multiplied by the data array.
        Not typically used now, since dmtrack is faster.
        """

        reltime = self.reltime
        if self.data.shape[1] == len(self.chans):
            chans = self.chans
        else:
            chans = n.arange(nchan)

        # initialize mask (false=0)
        mask = n.zeros((self.data.shape[0],self.data.shape[1]),dtype=bool)   # could get clever here.  use integer code to stack dm masks in unique way
        freq = self.sfreq + chans * self.sdf             # freq array in GHz

        # given freq, dm, dfreq, calculate pulse time and duration
        pulset = 4.2e-3 * dm * freq**(-2) + t0  # time in seconds
        pulsedt = 8.3e-6 * dm * (1000*self.sdf) * freq**(-3)   # dtime in seconds

        for ch in range(mask.shape[1]):
            ontime = n.where(((pulset[ch] + pulsedt[ch]/2.) >= reltime) & ((pulset[ch] - pulsedt[ch]/2.) <= reltime))
#            print ontime
            mask[ontime, ch] = True

        if show:
            ax = p.imshow(mask, aspect='auto', interpolation='nearest')
            p.axis([-0.5,len(chans)+0.5,max(reltime),min(reltime)])
            p.colorbar(ax)

        return mask


    def dmtrack(self, dm = 0., t0 = 0., show=0):
        """Takes dispersion measure in pc/cm3 and time offset from first integration in seconds.
        Returns an array of (time, channel) to select from the data array.
        Faster than dmmask.
        """

        reltime = self.reltime
        if self.data.shape[1] == len(self.chans):  # related to preparing of data?
            chans = self.chans
        else:
            chans = n.arange(self.nchan)
        nchan = len(chans)

        freq = self.sfreq + chans * self.sdf             # freq array in GHz

        # given freq, dm, dfreq, calculate pulse time and duration
        pulset = 4.2e-3 * dm * freq**(-2) + t0  # time in seconds
        pulsedt = 8.3e-6 * dm * (1000*self.sdf) * freq**(-3)   # dtime in seconds

        timebin = []
        chanbin = []
        for ch in range(nchan):
            ontime = n.where(((pulset[ch] + pulsedt[ch]/2.) >= reltime) & ((pulset[ch] - pulsedt[ch]/2.) <= reltime))
#            print ontime[0], ch
            timebin = n.concatenate((timebin, ontime[0]))
            chanbin = n.concatenate((chanbin, (ch * n.ones(len(ontime[0]), dtype=int))))

        track = (list(timebin), list(chanbin))
#        print 'timebin, chanbin:  ', timebin, chanbin

        if show:
            p.plot(track[1], track[0])

        return track


    def dedisperse(self):
        """Integrates over data*dmmask or data at dmtrack for each pair of elements in dmarr, time.
        Not threaded.  Uses dmmask or dmthread directly.
        """

        dmarr = self.dmarr
        reltime = self.reltime
        minintersect = len(self.chans)

        dmt0arr = n.zeros((len(dmarr),len(reltime)), dtype='float64')
#        accummask = n.zeros(self.data.shape, dtype='bool')
        if self.data.shape[1] == len(self.chans):
            chans = self.chans
        else:
            chans = n.arange(self.nchan)

        for i in range(len(dmarr)):
            for j in range(len(reltime)):
                if self.usedmmask:    # slower by factor of 2 than dmtracks
                    dmmask = self.dmmask(dm=dmarr[i], t0=reltime[j])
                    if dmmask.sum() >= minintersect:               # ignore tiny, noise-dominated tracks
                        dmt0arr[i,j] = n.mean(n.abs (self.data * dmmask)[n.where(dmmask == True)])
#                   accummask = accummask + dmmask
                else:
                    dmtrack = self.dmtrack(dm=dmarr[i], t0=reltime[j])
                    if len(dmtrack[0]) >= minintersect:               # ignore tiny, noise-dominated tracks
                        dmt0arr[i,j] = n.mean(n.abs (self.data[dmtrack[0],dmtrack[1]]))
            print 'dedispersed for ', dmarr[i]

        self.dmt0arr = dmt0arr


    def writetrack(self, track):
        """Wries data from track out as miriad visibility file.
        Assumes a template file is "template.mir" and has same baseline order, chans, etc..
        """

        # template and output miriad visibility file names
        inname = 'template.mir'
        outname = string.join(self.file.split('.')[:-1]) + '.' + str(self.nskip/self.nbl) + '.mir'

        # generate output new single-int visibility file

        vis = miriad.VisData(inname)
        out = miriad.VisData(outname)

        dOut = out.open ('c')
        dOut.setPreambleType ('uvw', 'time', 'baseline')

        i = 0
        for inp, preamble, data, flags in vis.readLowlevel ('dsl3', False):
            # since template has only one int, this loop gets spectra by iterating over baselines.

            if i < self.nbl:
                if i == 0:
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

                # prep data (and check that it matches expected?)
                for j in range(self.nchan):
                    if j in self.chans:
                        matches = n.where( (j - min(self.chans)) == n.array(track[1]) )[0]   # hack, since chans are from 0-64, but track is in trimmed chan space
                        raw = self.rawdata[track[0], i, track[1]][matches]   # all baselines for the known pulse
                        raw = raw.mean(axis=0)   # create spectrum for each baseline by averaging over time
                        data[j] = raw
                    else:
                        data[j] = 0. + 0.j

                dOut.write (preamble, data, flags)

            elif i >= self.nbl: 
                break

            i = i+1  # essentially a baseline number

        dOut.close ()


    def plotdmt0(self, sig=5., save=0):
        """calculates rms noise in dmt0 space, then plots circles for each significant point
        save=1 means plot to file.
        """
        dmarr = self.dmarr
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
        arr = (arr - mean)/std

        # Detect peaks
        peaks = n.where(arr > sig)   # this is probably biased
        peakmax = n.where(arr == arr.max())
        print 'peaks:  ', peaks

        # Plot
        p.clf()
        ax = p.imshow(arr, aspect='auto', origin='lower', interpolation='nearest', extent=(min(reltime),max(reltime),min(dmarr),max(dmarr)))
        p.colorbar()

        if len(peaks[0]) > 0:
            print 'Peak of %f sigma at DM=%f, t0=%f' % (arr.max(), dmarr[peakmax[0][0]], reltime[peakmax[1][0]])

            for i in range(len(peaks[1])):
                ax = p.imshow(arr, aspect='auto', origin='lower', interpolation='nearest', extent=(min(reltime),max(reltime),min(dmarr),max(dmarr)))
                p.axis((min(reltime),max(reltime),min(dmarr),max(dmarr)))
                p.plot([reltime[peaks[1][i]]], [dmarr[peaks[0][i]]], 'o', markersize=2*arr[peaks[0][i],peaks[1][i]], markerfacecolor='white', markeredgecolor='blue', alpha=0.5)

        p.xlabel('Time (s)')
        p.ylabel('DM (pc/cm3)')
        p.title('Signal to Noise Ratio of Dedispersed Pulse')
        if save:
            savename = self.file.split('.')[:-1]
            savename.append(str(self.nskip/self.nbl) + '.png')
            savename = string.join(savename,'.')
            p.savefig(savename)

        return peaks,arr[peaks]


    def dedisperse2(self):
        """Integrates over data*dmmask or data at dmtrack for each pair of elements in dmarr, time.
        Uses threading.  SLOWER than serial.
        """

        dmarr = self.dmarr
        reltime = self.reltime

        self.dmt0arr = n.zeros((len(dmarr),len(reltime)), dtype='float64')
#        accummask = n.zeros(self.data.shape, dtype='bool')
        if self.data.shape[1] == len(self.chans):
            chans = self.chans
        else:
            chans = n.arange(self.nchan)

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
        """Integrates over data*dmmask or data at dmtrack for each pair of elements in dmarr, time.
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
#        mec.push(dict(data=self.data, reltime=reltime))
#        mec.execute('import numpy as n')
#        mec.push_function(dict(dmtrack2 = dmtrack2))    # set up function for later

        pr_list = []
        iarr = []; jarr = []
        for i in range(len(dmarr)):
            for j in range(len(reltime)):
#                iarr.append(i)
#                jarr.append(j)
#                k = (j + len(reltime) * i) % len(ids)   # queue each iter amongst targets
                st = client.StringTask('dmt0 = dmtrack2(data, reltime, %f, %f)' % (dmarr[i], reltime[j]), pull='dmt0', push=dict(data = self.data,reltime = reltime))
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


def dmtrack2(data, reltime, dm = 0., t0 = 0.):
    """Takes dispersion measure in pc/cm3 and time offset from first integration in seconds.
    Returns an product of data with array of (time, channel) to select from the data array.
    Used by ipython-parallelized dedisperse3.
    """

    chans = n.arange(6,58)
    nchan = len(chans)
    sfreq = 0.718  # freq for first channel in GHz
    sdf = 0.104/nchan   # dfreq per channel in GHz
    freq = sfreq + chans * sdf             # freq array in GHz
    minintersect = len(chans)

    # given freq, dm, dfreq, calculate pulse time and duration
    pulset = 4.2e-3 * dm * freq**(-2) + t0  # time in seconds
    pulsedt = 8.3e-6 * dm * (1000*sdf) * freq**(-3)   # dtime in seconds
    
    timebin = []
    chanbin = []
    for ch in range(nchan):
        ontime = n.where(((pulset[ch] + pulsedt[ch]/2.) >= reltime) & ((pulset[ch] - pulsedt[ch]/2.) <= reltime))
    #        print ontime[0], ch
        timebin = n.concatenate((timebin, ontime[0]))
        chanbin = n.concatenate((chanbin, (ch * n.ones(len(ontime[0]), dtype=int))))

    track = (list(timebin), list(chanbin))
        
    if sum(track[0]) >= minintersect:               # ignore tiny, noise-dominated tracks
        dmt0 = n.mean(n.abs (data[track[0],track[1]]))
    else:
        dmt0 = 0.
        
    return dmt0


if __name__ == '__main__':
    # default stuff
    print 'Greetings, human.'
    print ''
    dedisperse = 0

    if len(sys.argv) == 2:
# if pickle, then plot data or dm search results
        print 'Assuming input file is pickle of candidate...'
#    To Do:  need to also use pickle to select data in raw format for imaging.

        file = open(sys.argv[1], 'rb')
        dump = pickle.load(file)
        print 'Loaded pickle file for %s' % (dump[0])
        print 'Has peaks at DM = ', dump[4]
        if len(dump[4]) >= 1:
            print 'Grabbing 10000 ints at %d' % (dump[1])
            pv = poco(dump[0], nints=10000, nskip=dump[1])    # format defined by pickle dump below
            pv.prep()

            midtrial = len(dump[4])/2   # guess at peak snr
            track = pv.dmtrack(dm=dump[4][midtrial], t0=pv.reltime[dump[5][midtrial]], show=0)  # needs to be shifted by -1 bin in reltime?
            int0 = track[0][len(track[0])-1]
#            print track, int0

            if dedisperse == 0:  # just show spectrum
                raw = pv.rawdata[n.array(track[0], dtype='int'), :, track[1]]   # all baselines for the known pulse
                raw = n.abs(raw[:, pv.noautos]).mean(axis=1)   # create array of all time,freq bins containing pulse
                print 'Mean, std in mean: %f, %f' % (raw.mean(), raw.std()/n.sqrt(len(raw)))
                pv.data = pv.data[int0:int0+100,:]
                pv.reltime = pv.reltime[int0:int0+100]
#                print track[0][len(track[0])-1] - int0, int0, pv.reltime[track[0][len(track[0])-1] - int0]
                p.plot(pv.reltime[n.array(track[0]-int0, dtype='int')], pv.chans[track[1]], ',')
                pv.spec(save=1)
            elif dedisperse == 1:
                pv.dedisperse()
                peaks, peakssig = pv.plotdmt0(save=1)
                file.close()
            else:
                # write dmtrack data out for imaging
                pv.writetrack(track)

        else:
            print 'No significant detection.  Moving on...'
    else:
# else search for pulses
        nints = 10000
        fileroot = 'poco_crab_201103.mir'
        filelist = []
        for i in range(0,11):
            filelist.append(string.join(fileroot.split('.')[:-1]) + '_' + str(i) + '.mir')

        filelist.reverse()  # get the last one first for testing purposes
        print 'Looping over filelist: ', filelist

# loop over miriad data and time chunks
        for file in filelist:
            for nskip in range(0,nints*9,nints*0.7):
                print 'Starting file %s with nskip %d' % (file, nskip)
                fileout = open(string.join(file.split('.')[:-1]) + '.txt', 'a')
                pklout = open(string.join(file.split('.')[:-1]) + '.' + str(nskip) + '.pkl', 'wb')

                pv = poco(file, nints=nints, nskip=nskip)
                pv.prep()
                pv.dedisperse()
                peaks, peakssig = pv.plotdmt0(save=0)
                print >> fileout, file, nskip, nints, peaks

                pickle.dump((file, nskip, nints, peaks[0], pv.dmarr[peaks[0]], peaks[1], peakssig), pklout)
                pklout.close()

        fileout.close
