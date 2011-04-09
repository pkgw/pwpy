from __future__ import with_statement
import numpy as np
import corr
from matplotlib import pyplot as plt
import socket
import struct
import time
import os
from threading import Thread, Lock

def permutations(iterable, r=None):
    # permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC
    # permutations(range(3)) --> 012 021 102 120 201 210
    pool = tuple(iterable)
    n = len(pool)
    r = n if r is None else r
    if r > n:
        return
    indices = range(n)
    cycles = range(n, n-r, -1)
    yield tuple(pool[i] for i in indices[:r])
    while n:
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i+1:] + indices[i:i+1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                yield tuple(pool[i] for i in indices[:r])
                break
        else:
            return
        
def combinations(iterable, r):
    pool = tuple(iterable)
    n = len(pool)
    for indices in permutations(range(n), r):
        if sorted(indices) == list(indices):
            yield tuple(pool[i] for i in indices)

triangles = [k for k in combinations(range(8), 3)]
bls = [corr.sim_cn_data.bl2ij(i) for i in corr.sim_cn_data.get_bl_order(8)]

class Poco():
    def __init__(self,u,nch=64):
        self.u = u
        self.nch = nch
    def seteq(self,quant,vals):
        valreg = 'quant%d_val' % quant
        addrreg = 'quant%d_addr' % quant
        
        for n,v in enumerate(vals):
            self.u.write_int(addrreg,n)
            self.u.write_int(valreg,v)
            
    def getspec(self):
        nint = self.u.read_int('sync_gen_sync_period_var')/128.0
        res = np.zeros((4,128))
        d0m = np.fromstring(self.u.read('spec_bram1',128*4),dtype='>i4')
        d0l = np.fromstring(self.u.read('spec_bram0',128*4),dtype='>i4')
        d1m = np.fromstring(self.u.read('spec1_bram1',128*4),dtype='>i4')
        d1l = np.fromstring(self.u.read('spec1_bram0',128*4),dtype='>i4')
        res[0,:] = d0m
        res[1,:] = d0l
        res[2,:] = d1m
        res[3,:] = d1l
        res = np.roll(res,2,1)
        spec = np.zeros((8,64))
        mset = [0,1,4,5]
        for k in range(4):
            spec[mset[k],:] = res[k,:64]
            spec[mset[k]+2,:] = res[k,64:]
#        spec[0,:] = res[0,:64]
#        spec[2,:] = res[0,64:]
#        spec[1,:] = res[1,:64]
        return np.sqrt(spec/nint/2.0)
    
    def plotspec(self,frqs=np.arange(64),db=True):
        spec = self.getspec()
        f = plt.figure()
        for k in range(8):
            ax = f.add_subplot(2,4,k+1)
            if db:
                s = 20*np.log10(spec[k,:]+1e-1)
            else:
                s = spec[k,:]
            ax.plot(frqs,s)
            ax.text(10,1,'ADC #%d' % k,size='small')
            ax.set_xlim(frqs.min(),frqs.max())
            
    
    def getadc(self):
        self.u.write_int('snap64_ctrl',0)
        self.u.write_int('snap64_ctrl',7)
        m = np.fromstring(self.u.read('snap64_bram_msb',4*2048),dtype='int8')
        l = np.fromstring(self.u.read('snap64_bram_lsb',4*2048),dtype='int8')
        res = np.zeros((8,2048))
        for k in range(4):
            res[k,:] = m[k::4]
            res[k+4,:] = l[k::4]
        return res
        
    def getadchist(self):
        hst = np.zeros((8,256))
        for n in range(8):
            adcs = self.getadc()
            for k in range(8):
                h,b = np.histogram(adcs[k,:],bins=np.arange(-128.5,128,1),new=True)
                hst[k,:] = hst[k,:] + h
        x = (b[:-1]+b[1:])/2.0
        return (x,hst,adcs)
        
    def printpps(self, n = 2):
        for k in range(n):
            st = self.u.read_int('ppscount')
            while True:
                b4 = time.time()
                pc2 = self.u.read_int('ppscount')
                if st != pc2:
                    aft = time.time()
                    break
            print "before:",b4,"after:",aft,"ncyc:",(pc2-st),pc2,st

    def plotadc(self):
        x,hst,adcs = self.getadchist()
        f = plt.figure()
        for k in range(8):
            ax = f.add_subplot(2,4,k+1)
            ax.semilogy(x,hst[k,:],'.')
            ax.set_xlim(-128,128)
            #ax.text(-100,200,'std:%.3f' % adcs[k,:].std(),size='small')
            #ax.text(-120,300,'ADC #%d' % k,size='small')
            ax.set_title('%d: std:%.3f' % (k,adcs[k,:].std()),size='small')
        f.suptitle('ADC histograms @ '+time.ctime())
        
            
    def setup(self,tge=True,period = 819200000):
        self.u.write_int('sync_gen_sync_period_var',period)
        self.u.write_int('sync_gen_sync_period_sel',1)
        self.u.write_int('sync_gen_sync',0)
        self.u.write_int('sync_gen_sync',3)
        if tge:
            self.u.tap_stop('mytap')
            self.u.write_int('ip',0x0A000001)
            self.u.write_int('port',58123)
            self.u.write_int('pktlen',574)
            try:
                self.u.tap_start('mytap','tenge',0x021283737326,0x0A000023,58899)
            except:
                self.u.tap_start('tenge',0x021283737326,0x0A000023,58899)
            
    def arm(self):
        self.u.write_int('sync_gen_sync',0)
        self.u.write_int('ctrl', 3)
        self.u.write_int('ctrl', 1)
        self.u.write_int('ctrl',0)
        
    def startpps(self):
        while True:
            t = time.time()
            if np.fmod(t,1) > 0.3 and np.fmod(t,1) < 0.5:
                break
        print "arming at:",time.time(),
        self.u.write_int('sync_gen_sync',4)
        print "  finished at:",time.time()
        pc = self.u.read_uint('ppscount')
        while True:
            pc2 = self.u.read_uint('ppscount')
            if pc != pc2:
                aft = time.time()
                break
        print "PPS arrived at:",aft,"  ",time.ctime(aft)
        cpp = pc2 - pc
        if cpp < 0:
            cpp += 2**32
        print "Cycles per pps:",cpp
        
    def start(self):
        self.u.write_int('sync_gen_sync',3)
            
    def reset(self,tvg=False,sn=7):
        self.u.write_int('sync_gen_sync',0)
        if tvg:
            val = 4
        else:
            val = 0
        self.u.write_int('ctrl',3+val)
        self.u.write_int('snap_10gbe_tx_ctrl',0)
        self.u.write_int('snap_10gbe_tx_ctrl',sn)
        self.u.write_int('corrout_ctrl',0)
        self.u.write_int('corrout_ctrl',1)
        self.u.write_int('ctrl',1+val)
        self.u.write_int('ctrl',0+val)
        self.u.write_int('sync_gen_sync',3)
        #self.u.write_int('sync_gen_sync',0)


        
        
    
    def stop_tap(self):
        self.u.tap_stop('mytap')
        
    def get_registers(self):
        regnames = self.u.listdev()
        regnames.remove('tenge')
        regs = {}
        for reg in regnames:
            if reg.find('bram') < 0:
                regs[reg] = self.u.read_int(reg)
        return regs
        
    def getcorr(self):
        self.u.write_int('corr0_ctrl',0)
        self.u.write_int('corr1_ctrl',0)
        self.u.write_int('corr0_ctrl',1)
        self.u.write_int('corr1_ctrl',1)
        done = False
        while not done:
            a = self.u.read_int('corr0_addr')
            b = self.u.read_int('corr1_addr')
            if a > 0 and b > 0:
                done = True
        depth = 36*3*self.nch/4
        l0 = np.fromstring(self.u.read('corr0_bram_lsb',depth*4),dtype='int16').byteswap().astype('float')
        l0 = l0[::2] + l0[1::2]*1j
        m0 = np.fromstring(self.u.read('corr0_bram_msb',depth*4),dtype='int16').byteswap().astype('float')
        m0 = m0[::2] + m0[1::2]*1j
        l1 = np.fromstring(self.u.read('corr1_bram_lsb',depth*4),dtype='int16').byteswap().astype('float')
        l1 = l1[::2] + l1[1::2]*1j
        m1 = np.fromstring(self.u.read('corr1_bram_msb',depth*4),dtype='int16').byteswap().astype('float')
        m1 = m1[::2] + m1[1::2]*1j
        
        c = np.zeros((3,36,self.nch),dtype='complex')
        for k in range(36):
            s = np.zeros((3*self.nch,),dtype='complex')
            s[0::4] = m0[k::36]
            s[1::4] = l0[k::36]
            s[2::4] = m1[k::36]
            s[3::4] = l1[k::36]
            for t in range(3):
                c[t,k,:] = s[(t*self.nch):((t+1)*self.nch)]
        return c
    def plotc(self,c):
        
        fig = plt.figure()
        mx = np.abs(c).max()
        for k in range(36):
            bl = bls[k]
            ax = fig.add_subplot(8,8,bl[0]+8*bl[1]+1)
            ax.plot(np.angle(c[k,:]),'.')
            m = np.abs(c[k,:])
            ax.plot(3*m/mx)
            
    def plotclosure(self,c):
        fig = plt.figure()
        for k in range(56):
            tr = triangles[k]
            i0 = bls.index((tr[0],tr[1]))
            i1 = bls.index((tr[1],tr[2]))
            i2 = bls.index((tr[0],tr[2]))
            cp = np.fmod(np.angle(c[i0,:])+np.angle(c[i1,:])+np.angle(c[i2,:]),3.14159)
            ax = fig.add_subplot(8,7,k+1)
            ax.plot(cp,'.')
            ax.text(5,3,'%d,%d,%d' % tr,size='xx-small')
            ax.set_ylim(-4,4)
            
            
def loadfile(fname,datatype='float32',count=-1): #i2
    a = np.fromfile(fname,dtype=np.dtype([('pktn','u4'),('data',datatype,36*64*2)]),count=count)
    pktn = a['pktn']
    d = a['data'][:,::2]+1j*a['data'][:,1::2]
    d = np.rollaxis(d.reshape((d.shape[0],16,36,4)),2,1).reshape((d.shape[0],36,64))
    return pktn,d
    
def getlast(fname,datatype='float32'):
    dt = np.dtype([('pktn','u4'),('data',datatype,36*64*2)])
    sz = os.stat(fname).st_size
    last = sz/(dt.itemsize)
    fh = open(fname,'rb')
    fh.seek((last-1)*dt.itemsize)
    a = np.fromfile(fh,dtype=dt,count=1)
    fh.close()
    pktn = a['pktn']
    d = a['data'][:,::2]+1j*(a['data'][:,1::2].astype('float'))
    d = np.rollaxis(d.reshape((d.shape[0],16,36,4)),2,1).reshape((d.shape[0],36,64))
    return pktn,d

def unpack(pkt):
    hdr = np.fromstring(pkt[:4],dtype='>u4')
    cnt = np.fromstring(pkt[4:8],dtype='>u4')
    dat = np.fromstring(pkt[8:],dtype='>i2')
    return dict(hdr=hdr,cnt=cnt,dat = (dat[::2]+1j*dat[1::2]))
class Receiver(Thread):
    def __init__(self,addr = ('10.0.0.1',58123)):
        super(Receiver,self).__init__()
        self.setDaemon(True)
        self.lock = Lock()
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(addr)
        self.last = 0
        self.data = None
        self.missing = 0
        self._running = False
    def quit(self):
        self._running = False
    def get(self):
        with self.lock:
            d = self.data.copy()
        d = np.rollaxis(d.reshape((16,36,4)),1,0).reshape((36,64))
        return d
    def run(self):
        self._running = True
        while self._running:
            try:
                d = self.sock.recv(10000)
            except:
                d = ''
            if len(d):
                try:
                    p = unpack(d)
                    if p['cnt'] & 0x01 == 0:
                        d = self.sock.recv(10000)
                        p2 = unpack(d)
                        if p['cnt'] + 1 == p2['cnt']:
                            if p['cnt'] != self.last and self.last != 0:
                                self.missing += (p['cnt']-self.last)
                            self.last = p['cnt']+2
                            ev = p
                            od = p2
                            dlen = ev['dat'].shape[0]
                            dat = np.zeros((dlen*2,),dtype='complex128')
                            dat[:dlen] = ev['dat']
                            dat[dlen:] = od['dat']
                            with self.lock:
                                self.data = dat
                except Exception, e:
                    print e
    def getone(self):
        p1 = unpack(self.sock.recv(8192))
        p2 = unpack(self.sock.recv(8192))
        p3 = unpack(self.sock.recv(8192))
        print "counters:",p1['cnt'],p2['cnt'],p3['cnt']
        ev = None
        od = None
        if p1['cnt'] % 2 == 0:
            if p2['cnt'] == p1['cnt']+1:
                ev = p1
                od = p2
        if p2['cnt'] % 2 == 0:
            if p3['cnt'] == p2['cnt']+1:
                ev = p2
                od = p3
        if ev is None or od is None:
            print "not found!"
            return
        dlen = ev['dat'].shape[0]
        dat = np.zeros((dlen*2,),dtype='complex128')
        dat[:dlen] = ev['dat']
        dat[dlen:] = od['dat']
        return dat


def calcPLL(f):
    if f > 1125:
        print "Frequency must be less than 1125 MHz"
        return None
    finaldiv = 1
    while f*finaldiv < 291:
        finaldiv *= 2
    if finaldiv > 32:
        print "That frequency would require a final divider of ",finaldiv
        return None
    forig = f
    f = f*finaldiv
    if f >=875 and f <=1125:
        VCOdiv = 2
    elif f >=583 and f <= 750:
        VCOdiv = 3
    elif f >= 438 and f <= 562:
        if finaldiv < 32:
            f*=2
            finaldiv *= 2
            VCOdiv = 2
        else:
            VCOdiv = 4
    elif f >= 350 and f <= 450:
        VCOdiv = 5
    elif f >= 291 and f <= 375:
        if finaldiv < 32:
            finaldiv *= 2
            f*=2
            VCOdiv = 3
        else:
            VCOdiv = 6
    else:
        print "That frequency seems to be unreachable"
        print "forig: ",forig," f:",f,"finaldiv: ",finaldiv
        return None
    (b,a) = divmod(f*VCOdiv,8)
    print "forig: ",forig," f:",f,"finaldiv: ",finaldiv
    print "VCOdiv: ",VCOdiv,"b: ",b,"a: ",a, "VCO:",f*VCOdiv
    output = (b*8+a)/VCOdiv/finaldiv
    print "Expected output:",output
    return dict(VCOdiv=VCOdiv,b=b,a=a,finaldiv=finaldiv,VCO=f,output=output)
