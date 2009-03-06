#!/usr/bin/csh
# script to automate flagging of cals and targets in gcmosaictest and gc-seti observations

# set up variables
set CAL = 'mosfxc-1733-130-1640'
set CALFLUX = 5.2
set VIS1 = 'mosfxc-gc-seti2-1-1640'
set VIS2 = 'mosfxc-gc-seti2-2-1640'
set VIS3 = 'mosfxc-gc-seti2-3-1640'
set VIS4 = 'mosfxc-gc-seti2-4-1640'
set VIS5 = 'mosfxc-gc-seti2-5-1640'
set VIS6 = 'mosfxc-gc-seti2-6-1640'
set VIS7 = 'mosfxc-gc-seti2-7-1640'
set VIS8 = 'mosfxc-gc-seti2-8-1640'
set VIS9 = 'mosfxc-gc-seti2-9-1640'
set VIS10 = 'mosfxc-gc-seti2-10-1640'
set VIS11 = 'mosfxc-gc-seti2-11-1640'
set VIS12 = 'mosfxc-gc-seti2-12-1640'
set VIS13 = 'mosfxc-gc-seti2-13-1640'
set VIS14 = 'mosfxc-gc-seti2-14-1640'
set VIS15 = 'mosfxc-gc-seti2-15-1640'
set VIS16 = 'mosfxc-gc-seti2-16-1640'
set VIS17 = 'mosfxc-gc-seti2-17-1640'
set VIS18 = 'mosfxc-gc-seti2-18-1640'
set VIS19 = 'mosfxc-gc-seti2-19-1640'
set VIS20 = 'mosfxc-gc-seti2-20-1640'
set VISLIST = ($VIS2,$VIS3,$VIS4,$VIS5,$VIS6,$VIS7,$VIS8,$VIS9,$VIS10,$VIS11,$VIS12,$VIS13,$VIS14,$VIS15,$VIS16,$VIS17,$VIS18,$VIS19,$VIS20)

echo ''
echo 'Make sure everything is executable, etc.\n'
itemize
if ($? != 0) exit(1)
newrfisweep.csh
if ($? != 0) exit(1)
~/big_scr2/code/mmm/pwilliams/fancy/calctsys
if ($? != 1) exit(1)
echo 'Checking on files...\n'
if (! -e ${CAL}) exit(1)
if (! -e ${VIS2}) exit(1)

if ($#argv > 0) then
  switch ($argv[1])
    case 'flag':
      echo 'Going to flag.\n'
      goto $argv[1]
    case 'cal':
      echo 'Going to cal.\n'
      goto $argv[1]
    case 'apply':
      echo 'Going to apply.\n'
      goto $argv[1]
    default:
      echo 'Argument not recognized.  Exiting...\n'
      exit(1)
  endsw
else
    echo 'Argument needed.  Exiting...\n'
    exit(1)
endif


flag:
  echo 'Starting flagging for '${CAL}'. Also applying flags to target fields blindly.\n'

  echo 'Initial flagging of data for worst stuff.   Including short baselinse (100 lambda) during day time.\n'
  uvflag vis=${CAL},${VISLIST} line='chan,74,98,1,1' flagval=flag log=/dev/null            # big bad chunk at beginning
  uvflag vis=${CAL},${VISLIST} line='chan,174,850,1,1' flagval=flag log=/dev/null           # bad chunk also at end
  uvflag vis=${CAL},${VISLIST} line='chan,50,348,1,1' flagval=flag log=/dev/null            # bad 50 near center
  uvflag vis=${CAL},${VISLIST} select='uvrange(0.001,0.1)' flagval=flag log=/dev/null       # short baselines bad during day
#  uvflag vis=${CAL} select='pol(xx),ant(14,42,26)' flagval=flag      # high tsys 
#  uvflag vis=${CAL} select='pol(yy),ant(42,39,24,28)' flagval=flag   # high tsys

  echo 'Summarize intermediate flagged data.\n'
  uvfstats vis=${CAL}

  echo 'Now flag automatically.\n'
  newrfisweep.csh vis=${CAL} tvis=${VISLIST}

  echo 'Summarize final flagged data.\n'
  uvfstats vis=${CAL}

  echo 'Plots to inspect for remnant RFI...\n'
  smauvspec vis=${CAL} device=${CAL}_rfi.ps/cps axis=ch,bo select='pol(xx,yy),ant(1,2,3)(11,12,13,14)' nxy=4,3

#  echo 'Plots to inspect for solar interference...\n'   # not needed at the moment, since this is flagged out.
#  smauvspec device=${CAL}_solar.ps/cps axis=ch,bo select='pol(xx),uvrange(0.001,0.1)' nxy='4,3' vis=${CAL}

  exit(0)
end

cal:
  echo 'If cal field flagging ok, now calibrate.\n'
  newcalcal.csh vis=${CAL} flux=${CALFLUX}

#  echo 'Tsys calculation.  Producing new file '${CAL}.ts '\n'
#  ~/big_scr2/code/mmm/pwilliams/fancy/calctsys quant=16,1 flux=${CALFLUX} vis=${CAL} out=${CAL}.ts

  echo 'Plots to inspect phase solution...\n'
  gpplt device=${CAL}_cal.ps/cps vis=${CAL} yaxis=phase yrange='-180,180'

  exit(0)

apply:
  echo 'If cal is calibrated well, now flag and apply calibration to targets.'
  echo 'This ignores lines at 1612 and 1665/1667.'
  newrfisweep.csh vis=${VISLIST} crange='-(240,260),-(750,800)'
  newcalcal.csh vis=${CAL} flux=${CALFLUX} tvis=${VISLIST} options=insource,sefd

# in case forgotten the first time
#  uvflag vis=${VISLIST} flagval=unflag line='chan,20,240,1,1'
#  uvflag vis=${VISLIST} flagval=unflag line='chan,50,750,1,1'

# this not needed?
#  echo 'If target fields flagged well (probably not true yet!), calculate Tsys.\n'
#  foreach VIS (`echo $VISLIST`)
#    echo 'Calculating Tsys for field '${VIS} '\n'
#    ~/big_scr2/code/mmm/pwilliams/fancy/calctsys quant=16,1 vis=${VIS} out=${VIS}.ts maxtsys=1000
#    ~/big_scr2/code/mmm/pwilliams/fancy/calctsys quant=16,1 vis=${VIS} out=${VIS}.ts maxtsys=1000
#  end

  exit(0)
end
