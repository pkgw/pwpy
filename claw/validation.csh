## validation.csh - Casey Law 11July2008
## A simple script listing a few good standard checks of data quality.  Breaks down into validation of flagging, calibration, and imaging.
## Would be nice to improve visualization with 2d plots;  for now everything plotted 1d (e.g., amp vs. channel, averaged over baseline and time)

set vis="fx64a-3c286-1430_1"
set image=""

## check flagging
# vs. channel and time.  average over baselines
smauvspec vis=$vis device=/xs select='ant(15)' axis=ch,bo options=avall
# vs. channel and baseline.  average over time
smauvspec vis=$vis device=/xs select='ant(15)' axis=ch,bo interval=1000
# vs. baseline.  average over channel and time
smauvplt vis=$vis device=/xs axis=uvdistance,amp options=nobase select='-auto'
# vs. baseline.  average over time
smauvplt vis=$vis device=/xs axis=uvdistance,amp options=nobase select='-auto'

## check calibration
# cal'd data vs. baseline.  average over time, baselines
uvspec vis=$vis interval=1000 select='ant(5)' options=avall,nobase device=/xs
# gains vs. channel and antenna.  average over time
smagpplt vis=$vis device=/xs options=bandpass yaxis=amp
smagpplt vis=$vis device=/xs options=bandpass yaxis=phase
# cal'd data vs baseline
check-cal.sh big_scr2/ata080429/$vis xx
# vs. time and antenna.  avarege over channel
smagpplt vis=$vis device=/xs yaxis=amp
smagpplt vis=$vis device=/xs yaxis=phase

## check image
if (-e $image) then
  ds9 &
  sleep(5)  # wait for ds9 to load
  mirds9 $image

