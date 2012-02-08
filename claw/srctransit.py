#!/usr/bin/env python
# claw 8feb12
# Script to take ra,dec and print next rise, transit, set times
# ra,dec should be colon-delimited sexagesimal

import ephem,sys

if len(sys.argv) != 3:
    print '**Syntax**'
    print 'srctransit.py hh:mm:ss dd:mm:ss'
    exit(1)

# define stuff
telescope = 'vla'
ra = sys.argv[1]
dec = sys.argv[2]

if telescope == 'vla':
    obs = ephem.Observer()
    obs.lat = '34.'
    obs.long = '-107.5'
    obs.elevation = 4000  # guess
elif telescope == 'ata':
    obs = ephem.Observer()
    obs.lat = '40.817'
    obs.long = '-121.47'
    obs.elevation = 3000  # guess

# current 
obs.date = ephem.now()
print 'Current sidereal time:', obs.sidereal_time()

# set up source
src = ephem.FixedBody()
src._ra = ra
src._dec = dec
src.compute(obs)

# get transit properties -- note times are normally in UT!
print 'Next rising: ', ephem.localtime(obs.next_rising(src))
print 'Next transit: ', ephem.localtime(obs.next_setting(src))
print 'Next setting: ', ephem.localtime(obs.next_transit(src))
