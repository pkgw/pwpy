# atapipe_pkw.csh - Casey Law 11July2008
# Script to put together a few steps from Peter's data reduction system (see Cookbook.txt)
# Does total intensity calibration only.

## Set parameters for observation
set SRC = 'atat-0001'
set CAL = '3c286'
set FREQ = '1430'
set VIS = fx64a-${SRC}-${FREQ}
set CALVIS = fx64a-${CAL}-${FREQ}
set VIS2 = ${SRC}-${FREQ}
set CALVIS2 = ${CAL}-${FREQ}
set REFANT = 21
# for REFANT, use 'listobs vis=${VIS}_1' to find antenna near center of array

## Start with miscellaneous data preparation/correction
# put the correlator halves together
ataglue.py vis=${VIS}_1,${VIS}_2 out=${VIS}
ataglue.py vis=${CALVIS}_1,${CALVIS}_2 out=${CALVIS}

# check for "bad C data"
#smauvspec device=1/xs axis=ch,bo select='pol(xx,yy),-auto' nxy=5,3 vis=${VIS}_2
#smauvspec device=1/xs axis=ch,bo select='pol(xx,yy),-auto' nxy=5,3 vis=${CALVIS}_2

# if pkw's "amprfi" does not work, use garrett's rfisweep here
#rfisweep.csh fx64a -3c286-1430 1430 normal flag

# rough correction for time smearing.  shouldn't be necessary after fringe tracking is done.
fringefix.py maxscale=2 vis=${VIS} out=${VIS}.ff
fringefix.py maxscale=2 vis=${CALVIS} out=${CALVIS}.ff

# check results of fringefix.  first one shows some amp drop at large u distance
uvplt vis=${VIS} select='pol(xx,yy),-auto' options=nobase axis=uu,amp device=1/xs
# yrange=0,3000 (may need to adjust range)
uvplt vis=${VIS}.ff select='pol(xx,yy),-auto' options=nobase axis=uu,amp device=2/xs

# run fx calibration to smooth out bandpass a bit.
uvcal options=fxcal,unflagged select='pol(xx)' vis=${VIS}.ff out=${VIS2}-xx
uvcal options=fxcal,unflagged select='pol(yy)' vis=${VIS}.ff out=${VIS2}-yy
uvcal options=fxcal,unflagged select='pol(xx)' vis=${CALVIS}.ff out=${CALVIS2}-xx
uvcal options=fxcal,unflagged select='pol(yy)' vis=${CALVIS}.ff out=${CALVIS2}-yy

# check how data changed
uvspec vis=${CALVIS2}-xx select='pol(xx),ant(21)(15,16,17,18,30,31,32)' interval=1000 device=1/xs nxy=3,2
uvspec vis=${CALVIS}.ff select='pol(xx),ant(21)(15,16,17,18,30,31,32)' interval=1000 device=2/xs nxy=3,2
uvspec vis=${VIS2}-xx select='pol(xx),ant(21)(15,16,17,18,30,31,32)' interval=1000 device=1/xs nxy=3,2
uvspec vis=${VIS}.ff select='pol(xx),ant(21)(15,16,17,18,30,31,32)' interval=1000 device=2/xs nxy=3,2

## Flagging
# flag dc and edges for source and cal
echo "chan=100,1;1,513;100,925" > edges.mf
multiflag2 spec=edges.mf vis=${VIS2}-xx,${VIS2}-yy,${CALVIS2}-xx,${CALVIS2}-yy freq=${FREQ}
# old way
#uvflag flagval=f line=chan,100,1 vis=${SRC}-${FREQ}-POL
#uvflag flagval=f line=chan,100,925 vis=${SRC}-${FREQ}-POL

# do walsh flagging on src and cal (all should be identified in one src/pol?)
walsh-flags.py ${VIS2}-xx > walsh.mf
multiflag2 spec=walsh.mf vis=${VIS2}-xx,${VIS2}-yy,${CALVIS2}-xx,${CALVIS2}-yy freq=${FREQ}

# if missed the first time, again flag "bad C data"
#uvflag flagval=f line=chan,128,START select='ant(ANT),pol(POL)' vis=${SRC}-${FREQ}-POL # do for all src, freq, pol

# check for solar interference, if daytime data
#smauvspec device=1/xs axis=ch,bo select='pol(xx),-auto' nxy=NX,NY vis=${SRC}-${FREQ}-POL # optionally [interval=MINUTES]

# interactive rfi flagging.  this doesn't work on lupus yet;  seems to require installation of 'gobject'.
#amprfi
# else, can run garrett's stuff as noted earlier and redo fxcal step

# after flagging calibrator, study closure phase
closanal.py vis=${CALVIS2}-xx interval=10
closanal.py vis=${CALVIS2}-yy interval=10
# use multiflag2 or uvflg to get rid of troublesome baselines or antennas
# echo 'pol=?? bl=??-?? ant=??' > closure.mf
# multiflag2 spec=closure.mf vis=${CALVIS2}-xx freq=1430
# or
# uvflag vis=${CALVIS2}-yy select='ant(?,?)' flagval=f
# note:  closure phase is not meaningful for typical target, since sky is not dominated by single point

## Calibration
# do bandpass and amplitude calibration
smamfcal options=interp,opolyfit select=-auto polyfit=7 refant=${REFANT} line=chan,824,101 vis=${CALVIS2}-xx
smamfcal options=interp,opolyfit select=-auto polyfit=7 refant=${REFANT} line=chan,824,101 vis=${CALVIS2}-yy

# check gain calibration
uvplt vis=${CALVIS2}-xx select=-auto axis=uvdistance,amp options=nobase device=1/xs
uvplt vis=${CALVIS2}-yy select=-auto axis=uvdistance,amp options=nobase device=2/xs

# check bandpass calibration
gpplt device=1/xs options=bandpass vis=${CALVIS2}-xx
gpplt device=1/xs options=bandpass vis=${CALVIS2}-yy

# if your calibrator is not known by miriad, selfcal yourself
#selfcal select=-auto options=amp,noscale flux=FLUX vis=${CALVIS2}-xx
#selfcal select=-auto options=amp,noscale flux=FLUX vis=${CALVIS2}-yy

# set header that specifies how far the calibration pol should go
puthd type=double value=0.02 in=${CALVIS2}-xx/interval
puthd type=double value=0.02 in=${CALVIS2}-yy/interval

# copy antenna gains over to target
gpcopy vis=${CALVIS2}-xx out=${VIS2}-xx
gpcopy vis=${CALVIS2}-yy out=${VIS2}-yy

# quick and dirty image
micr.sh vis=${VIS2}-xx
micr.sh vis=${VIS2}-yy
