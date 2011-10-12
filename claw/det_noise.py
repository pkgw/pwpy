#!/usr/bin/env python
# claw 11oct11
#
# script to simulate noise in complex and detected valued data

import numpy as n
import pylab as p
import random

class noise:
    def __init__(self, len=100, std=1.):
        self.std = std

        self.data = n.zeros(len, dtype='complex')
        for i in range(len):
            self.data[i] = n.complex(random.gauss(0, std), random.gauss(0, std))

    def add_source(self, flux=1+0j):
        self.data = self.data + flux

    def det(self,show=0):
        self.datadet = n.abs(self.data)

        if show:
            print 'datadet:', self.datadet
        return self.datadet

    def show(self):
        p.plot(self.data.real, self.data.imag,'.')
        p.show()

def repeat(num=351, source=0+0j, show=0):
    bglen = 1000

    # make detected visibilities on source
    nn = noise(len=num)
    nn.add_source(source)
    dmon = nn.det().mean()

    # make background detected visibilities
    dmarr = []
    for i in range(bglen):
        nnoff = noise(len=num)
        dmarr.append(nnoff.det().mean())
    dmarr = n.array(dmarr)
    meanoff = dmarr.mean()
    stdoff = dmarr.std()
    dmsig = (dmon - meanoff)/stdoff

    # make background mean visibilities and det significance
    nnoff = noise(len=bglen*num)
    meanoff = n.abs(nnoff.data.mean())
    stdoff = nnoff.data.std()/n.sqrt(num)
    nn = noise(len=num)
    nn.add_source(source)
    mdsig = (n.abs(nn.data.mean()) - meanoff)/stdoff

    intsig = n.abs(source)/nn.std
    print 'snr per int:', intsig
    print 'det then mean:', dmsig, 'sigma'
    print 'mean then det:', mdsig, 'sigma'

    return n.array([intsig, dmsig, mdsig])
