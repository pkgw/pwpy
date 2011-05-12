#!/usr/bin/env csh
# quick data reduction script for miriad-format poco data from july 2010
## BE SURE TO SET DESTINATION IN GOTO AFTER FLAGGING ##

set name = $argv[1]
set doflag = 1

# calibrators prepared with delay correction
set cal3c147 = data/poco_3c147b0329_171818_del.mir   # one solution
set calcasa = data/poco_casam31_cal.mir    # two solutions bound m31 data

if ( ${doflag} == 1) then
    # standard flagging for poco july 2010 run
    uvflag vis=${name} flagval=f select='ant(4,7,8)'
    uvflag vis=${name} flagval=f select='ant(3)(5)'
    uvflag vis=${name} flagval=f select='auto'
    uvflag vis=${name} flagval=f line=ch,3,1
    uvflag vis=${name} flagval=f line=ch,1,11
    uvflag vis=${name} flagval=f line=ch,14,24
    uvflag vis=${name} flagval=f line=ch,1,40
    uvflag vis=${name} flagval=f line=ch,3,42
    uvflag vis=${name} flagval=f line=ch,15,50
endif

## SET DESTINATION ##
goto end
## SET DESTINATION ##

# for crab
crab:
puthd in=${name}/ra value=1.4624069428
puthd in=${name}/dec value=.3843258913
puthd in=${name}/object value=crab
puthd in=${name}/source value=crab
mfcal vis=${name} interval=90 refant=1 flux=1127,0.77,-0.3 select='-auto'
goto end

#for b0329
b0329:
puthd in=${name}/ra value=0.929314
puthd in=${name}/dec value=0.95255
puthd in=${name}/object value=B0329+54
puthd in=${name}/source value=B0329+54
gpcopy vis=${cal3c147} out=${name}
gpedit vis=${name} options=multiply gain=8,0  # need to multiply flux scale by sqrt(1024/16), since integration time affects gain scaling
goto end

#for 3c147
3c147:
puthd in=${name}/ra value=1.494841
puthd in=${name}/dec value=0.8700
puthd in=${name}/object value=3c147
puthd in=${name}/source value=3c147
mfcal vis=${name} interval=90 refant=1 select='-auto'
goto end

#for 3c84
3c84:
puthd in=${name}/ra value=0.871778
puthd in=${name}/dec value=0.72449
puthd in=${name}/object value=3c84
puthd in=${name}/source value=3c84
mfcal vis=${name} interval=90 refant=1 select='-auto'
goto end

#for casa
casa:
puthd in=${name}/ra value=6.123452
puthd in=${name}/dec value=1.026223
puthd in=${name}/object value=casa
puthd in=${name}/source value=casa
mfcal vis=${name} interval=15 refant=1 select='-auto' flux=2417,0.77,-0.77
goto end

# for casa pointing with m31 phase/delay
casam31:
puthd in=${name}/ra value=6.123452
puthd in=${name}/dec value=1.026223
puthd in=${name}/object value=casa
puthd in=${name}/source value=casa
uvedit vis=${name} out=${name:r}_del.mir delay=0,3.5,33.0,6.7,-2.9,147.6,150.1,119.8
mfcal vis=${name:r}_del.mir interval=15 refant=1 select='-auto' flux=2417,0.77,-0.77
goto end

#for 3c147 pointing with b0329 phase/delays
3c147b0329:
puthd in=${name}/ra value=1.494841
puthd in=${name}/dec value=0.8700
puthd in=${name}/object value=3c147
puthd in=${name}/source value=3c147
uvedit vis=${name} out=${name:r}_del.mir delay=0,-67.9,88.7,110.1,102.7,-36.4,-9.4,83.5
mfcal vis=${name:r}_del.mir interval=90 refant=1 select='-auto'
goto end

#for m31
m31:
puthd in=${name}/ra value=0.186476
puthd in=${name}/dec value=0.720262
puthd in=${name}/object value=m31
puthd in=${name}/source value=m31
gpcopy vis=${calcasa} out=${name}
gpedit vis=${name} options=multiply gain=8,0  # need to multiply flux scale by sqrt(1024/16), since integration time affects gain scaling
goto end

end:
echo 'ending...'
