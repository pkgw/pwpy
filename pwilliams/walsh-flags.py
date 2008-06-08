#! /usr/bin/env python

import sys, os.path

vis = sys.argv[1]
hist = file (os.path.join (vis, 'history'), 'r')

print '# walsh/ADC conflict flags generated from %s' % vis

prevIbob = None
bypol = {}

for l in hist:
    if 'Walsh' not in l: continue

    a = l.strip ().replace ('|', ' ').replace (':', ' ').split ()
    #print a

    antpol = a[5]
    ant = int (antpol[:-1])
    pol = antpol[-1]
    walsh = int (a[7])
    adc = int (a[3][2])
    ibob = a[2]

    if prevIbob is not None:
        if ibob == prevIbob and walsh == prevWalsh:
            if (prevAdc == 0 and adc == 1) or \
               (prevAdc == 2 and adc == 3):
                a1, p1, a2, p2 = prevAnt, prevPol, ant, pol
                
                if ant < prevAnt:
                    a1, p1, a2, p2 = a2, p2, a1, p1

                pol = p1 + p2
                a1, a2 = int (a1), int (a2)

                if pol not in bypol: bypol[pol] = []

                bypol[pol].append ((a1, a2))

    prevIbob, prevWalsh, prevAdc, prevAnt, prevPol = ibob, walsh, adc, ant, pol

for pol, bls in bypol.iteritems ():
    print 'pol=%s bl=%s' % (pol, ','.join ('%d-%d' % x for x in bls))

