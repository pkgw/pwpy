#! /usr/bin/env python

"""= pocovis.py - a skeleton task
& claw
: Unknown
+
 Script to load and visualize poco data
--
"""

import sys
#import mirtask
#from mirtask import uvdat, keys, util
import miriad
import numpy as n
import pylab as p
import scipy.optimize as opt
#from matplotlib.font_manager import fontManager, FontProperties
#font= FontProperties(size='x-small');


class poco:
    def __init__(self,file):
        # initialize'
        self.nchan = 64
        self.chans = n.arange(30,50)
        self.nbl = 36
        self.sfreq = 0.77  # freq for first channel in GHz
        self.sdf = 0.104/self.nchan   # dfreq per channel in GHz
        self.baseline_order = n.array([ 257, 258, 514, 261, 517, 1285, 262, 518, 1286, 1542, 259, 515, 773, 774, 771, 516, 1029, 1030, 772, 1028, 1287, 1543, 775, 1031, 1799, 1544, 776, 1032, 1800, 2056, 260, 263, 264, 519, 520, 1288])   # second iteration of bl nums
        self.autos = []
        self.noautos = []
        self.dmarr = n.arange(10,200,10)       # dm trial range in pc/cm3
        self.tarr = n.arange(-500.,500)/1000.   # time trial range in seconds
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
        initsize=50000
        da = n.zeros((initsize,nchan),dtype='complex64')
        fl = n.zeros((initsize,nchan),dtype='bool')
        ti = n.zeros((initsize),dtype='float64')

        # read data
        # You can pass traditional Miriad UV keywords to readLowlevel as keyword arguments
        for inp, preamble, data, flags, nread in vis.readLowlevel (False):
#        for inp, preamble, data, flags, nread in uvdat.readAll ():
            # Reduce these arrays to the correct size
            data = data[0:nread]
            flags = flags[0:nread]

    # Decode the preamble
    #        u, v, w = preamble[0:3]
            time = preamble[3]
    #        baseline = util.decodeBaseline (preamble[4])

    #    pol = uvdat.getPol ()
    
            if i < initsize:
                ti[i] = time
                da[i] = data
                fl[i] = flags
            else:
                da = n.concatenate((da,[data]))
                ti = n.concatenate((ti,[time]))
                fl = n.concatenate((fl,[flags]))
        #            bl = n.concatenate((bl,[baseline]))
            i = i+1

        if i <= initsize:
            print 'Array smaller than initialized array.  Trimming.'
            da = da[0:i]
            fl = fl[0:i]
            ti = ti[0:i]

        self.data = da.reshape(i/nbl,nbl,nchan)
        self.flags = fl.reshape(i/nbl,nbl,nchan)
        self.time = ti[::nbl]
        print
        print 'Data read!'
        print 'Shape of Data, Flags, Time:'
        print self.data.shape, self.flags.shape, self.time.shape
        print 


    def prep(self):
        self.data = (self.data * self.flags)[:,self.noautos].mean(axis=1)
        self.data = self.data[:,self.chans] 
        print 'Data flagged, trimmed in channels, and averaged across baselines.'
        print 'New shape:'
        print self.data.shape


    def spec(self):
        noautos = self.noautos
        autos = self.autos
        chans = self.chans
        time = self.time
        data = self.data

#reorganize into dimensions of integration, baseline, channel
        print 'Plotting spectrgram.'
        abs = n.abs(data[:,chans])

        p.figure(1)
        day0 = int(time[0])
        ax = p.imshow(abs, aspect='auto', interpolation='nearest')
#    ax = p.imshow(abs, aspect='auto', extent=(0,max(chans),max(time-day0),min(time-day0)))
#    p.axis([-0.5,len(chans)+0.5,100,0])
        p.colorbar(ax)


    def dmmask(self, dm = 0., t0 = 0., show=0):
        """Takes dispersion measure in pc/cm3 and time offset from first integration in seconds.
        """

        sfreq = self.sfreq
        sdf = self.sdf
        if self.data.shape[1] == len(self.chans):
            chans = self.chans
        else:
            chans = n.arange(nchan)

        # initialize mask (false=0)
        mask = n.zeros((self.data.shape[0],self.data.shape[1]),dtype=bool)   # could get clever here.  use integer code to stack dm masks in unique way
        time = 24*3600*(self.time - self.time[0])     # relative time array in seconds
        freq = sfreq + chans * sdf             # freq array in GHz

        # given freq, dm, dfreq, calculate pulse time and duration
        pulset = 4.2e-3 * dm * freq**(-2) + t0  # time in seconds
        pulsedt = 8.3e-6 * dm * (1000*sdf) * freq**(-3)   # dtime in seconds

        for ch in range(mask.shape[1]):
            ontime = n.where(((pulset[ch] + pulsedt[ch]/2.) >= time) & ((pulset[ch] - pulsedt[ch]/2.) <= time))
#            print ontime
            mask[ontime, ch] = True

        if show:
            ax = p.imshow(mask, aspect='auto', interpolation='nearest')
            p.axis([-0.5,len(chans)+0.5,max(time),min(time)])
            p.colorbar(ax)

        return mask


    def dedisperse(self):
        """Integrates over data*dmmask for each pair of elements in dmarr, tarr.
        """

        dmarr = self.dmarr
        tarr = self.tarr

        time = 24*3600*(self.time - self.time[0])     # relative time array in seconds
        dmt0arr = n.zeros((len(dmarr),len(tarr)), dtype='float64')
#        accummask = n.zeros(self.data.shape, dtype='bool')
        if self.data.shape[1] == len(self.chans):
            chans = self.chans
        else:
            chans = n.arange(self.nchan)

        for i in range(len(dmarr)):
            for j in range(len(tarr)):
                dmmask = self.dmmask(dm=dmarr[i], t0=tarr[j])
                if dmmask.sum() >= 5:
                    dmt0arr[i,j] = n.mean(n.abs (self.data * dmmask))/n.sum(dmmask)
#                accummask = accummask + dmmask
                
            print 'Dedispersed for ', dmarr[i]

        self.dmt0arr = dmt0arr

#        ax = p.imshow(accummask, aspect='auto')
#        p.axis([-0.5,len(chans)+0.5,max(time),min(time)])


    def plotdmt0(self, sig=5.):
        """Calculates rms noise in dmt0 space, then plots circles for each significant point
        """
        tarr = self.tarr
        dmarr = self.dmarr
        arr = self.dmt0arr
        ind0c = arr.shape[0]/2
        ind1c = arr.shape[1]/2
        mean = arr[ind0c-5:ind0c+5, ind1c-100:ind1c+100].mean()   # need to fix this!  sometimes falls in empty area!
        std = arr[ind0c-5:ind0c+5, ind1c-100:ind1c+100].std()

        time = 24*3600*(self.time - self.time[0])     # relative time array in seconds

        if sig:
            peaks = n.where(arr > (mean + sig*std))   # this is probably biased
            scaling = std*sig

            for i in range(len(peaks[1])):
                p.plot(tarr[peaks[1][i]], dmarr[peaks[0][i]], 'bo', markersize=arr[peaks[0][i],peaks[1][i]]/scaling)

        else:
            ax = p.imshow(arr, aspect='auto', interpolation='nearest', extent=(min(tarr),max(tarr),max(dmarr),min(dmarr)))


if __name__ == '__main__':
    # default stuff
    print 'Greetings, human.'
    print ''

    pv = poco()
    pv.load('poco_crab_candpulse.mir')
    pv.flag()
    pv.vis()
