#! /usr/bin/env python

import sys

def read (log):
    res = {}
    
    for l in log:
        a = l.strip ().split ()
        ibob = a[1]
        inp = a[2]
        setting = float (a[3])

        if 'too low' in l:
            rms = float (a[13])
            desired = float (a[16])
            flag = 'low'
        else:
            rms = float (a[7])
            desired = float (a[10])
            flag = 'ok'

        name = '%s %s' % (ibob, inp)
        res[name] = (setting, rms, desired, flag)

    return res

tabs = {}

for fn in sys.argv[1:]:
    tabs[fn] = read (file (fn, 'r'))

all = set ()
for tab in tabs.itervalues ():
    all = all.union (tab.iterkeys ())

sall = sorted (all)
sfiles = sorted (sys.argv[1:])

for name in sall:
    print '%s:' % name
    
    for fn in sfiles:
        tab = tabs[fn]
        if name not in tab: continue

        setting, rms, desired, flag = tab[name]
        print '   %20s: %6.1f %6.1f %6.1f %s' % (fn, setting, rms, desired, flag)
