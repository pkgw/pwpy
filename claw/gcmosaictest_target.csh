#!/usr/bin/csh
# script to automate flagging and cal of targets in gcmosaictest

# set up variables
set CAL = 'mosfxc-1733-130-1640'
set VIS1 = 'mosfxc-gcmosaictest2-1640'
set VIS2 = 'mosfxc-gcmosaictest3-1640'
set VIS3 = 'mosfxc-gcmosaictest4-1640'
set VISLIST = ($VIS2 $VIS3)

# perhaps add some logical structure to control flow?
#goto flag


check:
echo 'Make sure everything is executable, etc.'
itemize
if ($? != 0) exit(1)
newrfisweep.csh
if ($? != 0) exit(1)
~/big_scr2/code/mmm/pwilliams/fancy/calctsys
if ($? != 1) exit(1)

echo 'Can find files?'
if (! -e ${CAL}) exit(1)
if (! -e ${VIS1}) exit(1)
if (! -e ${VIS2}) exit(1)
if (! -e ${VIS3}) exit(1)

foreach VIS (`echo $VISLIST`)
  if (! -e ${VIS}) exit(1)
end


fixup:

foreach VIS (`echo $VISLIST`)
  echo 'Fix header problem for '${VIS}
  puthd in=${VIS}/freq value=1.640
  puthd in=${VIS}/restfreq value=1.640
  puthd in=${VIS}/sfreq value=1.5876
end

flag:

foreach VIS (`echo $VISLIST`)
  echo 'Starting flagging for '${VIS}
  echo 'First flag data for known bad stuff, including short baselinse (100 lambda).'
  uvflag vis=${VIS} select='pol(xx),ant(14,42,26)' flagval=flag
  uvflag vis=${VIS} select='pol(yy),ant(42,39,24,28)' flagval=flag
  uvflag vis=${VIS} line='chan,210,1,1,1' flagval=flag
  uvflag vis=${VIS} line='chan,200,840,1,1' flagval=flag
  uvflag vis=${VIS} line='chan,10,320,1,1' flagval=flag
  uvflag vis=${VIS} select='uvrange(0.001,0.1)' flagval=flag

  echo 'Now flag automatically'
  newrfisweep.csh vis=${VIS}

  echo 'Inspect for bad RFI...'
#  smauvspec vis=${VIS} device=1/xs axis=ch,bo select='pol(xx,yy),ant(1,2,3)(11,12,13,14)' nxy=4,3

  echo 'Inspect for solar interference...'
#  smauvspec device=1/xs axis=ch,bo select='pol(xx),-auto,uvrange(0.001,0.1)' nxy='4,3' vis=${VIS}

end

cal:

foreach VIS (`echo $VISLIST`)
  echo 'Starting calibration for '${VIS}
  echo 'Flatten out spectra a bit for later Tsys estimate'
  uvcal options=fxcal,unflagged select='pol(xx)' vis=${VIS} out=${VIS}-xx
  uvcal options=fxcal,unflagged select='pol(yy)' vis=${VIS} out=${VIS}-yy

  echo 'Copy over calibration solutions'
  gpcopy vis=${CAL}-xx out=${VIS}-xx
  uvcat vis=${VIS}-xx out=${VIS}-xx.mf
  gpcopy vis=${CAL}-xx.ts out=${VIS}-xx.mf

  gpcopy vis=${CAL}-yy out=${VIS}-yy
  uvcat vis=${VIS}-yy out=${VIS}-yy.mf
  gpcopy vis=${CAL}-yy.ts out=${VIS}-yy.mf

  ~/big_scr2/code/mmm/pwilliams/fancy/calctsys quant=16,1 vis=${VIS}-xx.mf out=${VIS}-xx.ts maxtsys=1000
  ~/big_scr2/code/mmm/pwilliams/fancy/calctsys quant=16,1 vis=${VIS}-yy.mf out=${VIS}-yy.ts maxtsys=1000
end

image:
echo 'Image roughly'
foreach VIS (`echo $VISLIST`)
  micr.sh ${VIS}-xx.ts
  micr.sh ${VIS}-yy.ts
end
