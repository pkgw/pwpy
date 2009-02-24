#!/usr/bin/csh
# script to automate flagging of cals and targets in gcmosaictest and gc-seti observations

# set up variables
set CAL = 'mosfxc-1733-130-1640'
set CALFLUX = 5.2
set VIS1 = 'mosfxc-gc-seti1-1-1640'
set VIS2 = 'mosfxc-gc-seti1-2-1640'
set VIS3 = 'mosfxc-gc-seti1-3-1640'
set VIS4 = 'mosfxc-gc-seti1-4-1640'
set VIS5 = 'mosfxc-gc-seti1-5-1640'
set VIS6 = 'mosfxc-gc-seti1-6-1640'
set VIS7 = 'mosfxc-gc-seti1-7-1640'
set VIS8 = 'mosfxc-gc-seti1-8-1640'
set VIS9 = 'mosfxc-gc-seti1-9-1640'
set VIS10 = 'mosfxc-gc-seti1-10-1640'
set VISLIST = ($VIS1 $VIS2 $VIS3 $VIS4 $VIS5 $VIS6 $VIS7 $VIS8 $VIS9 $VIS10)

echo 'Make sure everything is executable, etc.'
itemize
if ($? != 0) exit(1)
newrfisweep.csh
if ($? != 0) exit(1)
~/big_scr2/code/mmm/pwilliams/fancy/calctsys
if ($? != 1) exit(1)
echo 'Can find files?'
if (! -e ${CAL}) exit(1)

if ("$argv[1]" =~ 'flag') then
    echo 'Going to flag.'
else if ("$argv[1]" =~ 'cal') then
    echo 'Going to cal.'
else if ("$argv[1]" =~ 'apply') then
    echo 'Going to apply.'
else
    echo 'Argument not recognized.  Exiting.'
    exit(1)

goto $argv[1]

flag:

  echo 'Fix header problem for '${CAL}
  puthd in=${CAL}/freq value=1.640
  puthd in=${CAL}/restfreq value=1.640
  puthd in=${CAL}/sfreq value=1.5876

  echo 'Starting flagging for '${CAL}'. Also applying flags to target fields blindly.'

  echo 'Initial flagging of data for worst stuff.   Including short baselinse (100 lambda) during day time.'
  uvflag vis=${CAL},${VISLIST} line='chan,70,100,1,1' flagval=flag log=/dev/null            # big bad chunk at beginning
  uvflag vis=${CAL},${VISLIST} line='chan,124,900,1,1' flagval=flag log=/dev/null           # bad chunk also at end
  uvflag vis=${CAL},${VISLIST} line='chan,50,350,1,1' flagval=flag log=/dev/null            # bad 50 near center
  uvflag vis=${CAL},${VISLIST} select='uvrange(0.001,0.1)' flagval=flag log=/dev/null       # short baselines bad during day
#  uvflag vis=${CAL} select='pol(xx),ant(14,42,26)' flagval=flag      # high tsys 
#  uvflag vis=${CAL} select='pol(yy),ant(42,39,24,28)' flagval=flag   # high tsys

  echo 'Summarize intermediate flagged data.'
  uvflag vis=${CAL} flagval=f options=noapply

  echo 'Now flag automatically.'
  newrfisweep.csh vis=${CAL} tvis=${VISLIST}

  echo 'Summarize final flagged data.'
  uvflag vis=${CAL} flagval=f options=noapply

  echo 'Plots to inspect for remnant RFI...'
  smauvspec vis=${CAL} device=${CAL}_rfi.ps/cps axis=ch,bo select='pol(xx,yy),ant(1,2,3)(11,12,13,14)' nxy=4,3

  echo 'Plots to inspect for solar interference...'
  smauvspec device=${CAL}_solar.ps/cps axis=ch,bo select='pol(xx),uvrange(0.001,0.1)' nxy='4,3' vis=${CAL}

  exit(0)
end

cal:
  echo 'If cal field flagging ok, now calibrate.'
  newcalcal.csh vis=${CAL} flux=${CALFLUX}

  echo 'Tsys calculation.  Producing new file '${CAL}.ts
  ~/big_scr2/code/mmm/pwilliams/fancy/calctsys quant=16,1 flux=${CALFLUX} vis=${CAL} out=${CAL}.ts

  echo 'Plots to inspect phase solution...'
  gpplt device=${CAL}_cal.ps/cps vis=${CAL}.ts yaxis=phase

  exit(0)

apply:
  echo 'This stuff is not tested yet!'

  echo 'After confident use options=savedata,insource to set values (?)'
  newcalcal.csh vis=${CAL} flux=${CALFLUX} tvis=${VISLIST} options=savedata,insource

  echo 'If target fields flagged well (probably not true yet!), calculate Tsys.'
  foreach VIS (`echo $VISLIST`)
    echo 'Calculating Tsys for field '${VIS}
    ~/big_scr2/code/mmm/pwilliams/fancy/calctsys quant=16,1 vis=${VIS} out=${VIS}.ts maxtsys=1000
    ~/big_scr2/code/mmm/pwilliams/fancy/calctsys quant=16,1 vis=${VIS} out=${VIS}.ts maxtsys=1000
end

  exit(0)
end
