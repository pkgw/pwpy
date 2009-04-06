#! /bin/bash
#
# Makes files with select statements for imaging a pulsar
#
######################
# customize here
#period=0.71452    # period from literature
#period=0.7136692   # period that fixes phase shift?
#bin=0.1
#phasebins=16
#outphases=1  # not yet implemented
#ints=3000
#t0h=02
#t0m=05
#t0s=02.4
#suffix='tst'
######################
period="$1"
bin="$2"
phasebins="$3"
outphases="$4"
ints="$5"
t0h="$6"
t0m="$7"
t0s="$8"
suffix="$9"
frac="${10}"

#set -e -x  # for debugging

# a guess at the number of pulses to interate over
numpulses=`echo 'scale=0;'${ints}'*'${bin}'/'${period}'+ 1' | bc`  # original
numpulses_half=`echo 'scale=0;'${ints}'*'${bin}'/(2*'${period}')' | bc`
numpulses_third=`echo 'scale=0;'${ints}'*'${bin}'/(3*'${period}')' | bc`
numpulses_2third=`echo 'scale=0;'2*${ints}'*'${bin}'/(3*'${period}')' | bc`

if [ "$frac" = 'all' ]; then
    istart=0
    istop=${numpulses}
elif [ "$frac" = '1/2' ]; then
    istart=0
    istop=${numpulses_half}
elif [ "$frac" = '2/2' ]; then
    istart=${numpulses_half}
    istop=${numpulses}
elif [ "$frac" = '1/3' ]; then
    istart=0
    istop=${numpulses_third}
elif [ "$frac" = '2/3' ]; then
    istart=${numpulses_third}
    istop=${numpulses_2third}
elif [ "$frac" = '3/3' ]; then
    istart=${numpulses_2third}
    istop=${numpulses}
fi

echo
echo '***Getting '${numpulses}' pulses assuming period '${period}'s***'
echo '***Averaging into '${phasebins}' bins across 1 phase. Data bin size is '${bin}'s.***'  # to do:  multiple phases
echo

for ((j=0; j<=${phasebins}-1; j++))   # iterate over pulse phase, zero based
do

outn='time-'${suffix}
file=${outn}'-bin'${j}
touch $file

for ((i=${istart}; i<=${istop}; i++))   # iterate over pulse number, 0-based
  do
  # get seconds offset
  t1s=`echo 'scale=5; ('${t0s}' + '${j}' * '${period}' / ' ${phasebins} ' + '${period}' * '${i}') ' | bc`
  t2s=`echo 'scale=5; ('${t0s}' + ('${j}' + 1) * '${period}' / ' ${phasebins} ' + '${period}' * '${i} ') ' | bc`

  # adjust minutes offset
  t1m=`echo 'scale=0; '${t1s}'/60' | bc`
  t2m=`echo 'scale=0; '${t2s}'/60' | bc`
  t1s=`echo 'scale=5; '${t1s}' - 60 * '${t1m} | bc`
  t2s=`echo 'scale=5; '${t2s}' - 60 * '${t2m} | bc`

  # adjust hour offset
  t1h=`echo 'scale=0; '${t1m}'/60' | bc`
  t2h=`echo 'scale=0; '${t2m}'/60' | bc`
  t1m=`echo 'scale=5; '${t1m}' - 60 * '${t1h} | bc`
  t2m=`echo 'scale=5; '${t2m}' - 60 * '${t2h} | bc`

  # adjust minutes and second by origin
  t1m=`echo 'scale=0; '${t0m}' + '${t1m} | bc`
  t2m=`echo 'scale=0; '${t0m}' + '${t2m} | bc`
  t1h=`echo 'scale=0; '${t0h}' + '${t1h} | bc`
  t2h=`echo 'scale=0; '${t0h}' + '${t2h} | bc`

## bug in here somewhere.  turning of hour doesn't work ##

  # print time filter to file
  echo 'time('${t1h}':'${t1m}':'${t1s}','${t1h}':'${t2m}':'${t2s}')'  >> $file
done

# check if file is over miriad select limit of 256 lines.  if so, split
numlines=`wc ${file} | gawk '{printf "%d \n", $0}' | head -n 1`
if [ $numlines -ge 256 ]
    then
    echo 'File too long.  Splitting.'
    split ${file} --lines=255 ${outn}'-bin'${j}
    rm -f ${file}
else
    mv ${file} ${file}aa
    rm -f ${file}
fi

done
