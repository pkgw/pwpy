#!/usr/bin/env csh
set name = $argv[1]
set crab770 = 1127.   # baars 1977 model
echo 'Flagging, calibrating, headering ' $name

# flagging, selfcal, and fixing header
#uvflag vis=$name select='ant(4,7,8)' flagval=f
#puthd in=$name/dec value=.3843258913
#puthd in=$name/ra value=1.4624069428

# for selfcal (e.g., Crab), just flag and mfcal
mfcal vis=$name refant=1 interval=90 flux=$crab770

# for xfer cal (e.g., M31), need two files, etc.
