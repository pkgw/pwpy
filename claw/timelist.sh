#! /bin/bash
#
# Makes files with select statements for imaging a pulsar

period=0.71452
bin=0.1
t0h=02
t0m=05
t0s=02.4

numpulses=`echo 'scale=0;3000*0.1/'${period}'+1' | bc`  # a guess at the number of pulses to interate over

for ((j=0; j<=7; j++))   # iterate over pulse phase (slightly oversampled)
do

file='time-bin'${j}
touch $file

for ((i=0; i<=${numpulses}; i++))   # iterate over pulse number
do
  # get seconds offset
  t1s=`echo 'scale=5; ('${t0s}' + '${j}' * '${period}' / 8 + '${period}' * '${i}') ' | bc`  # slightly oversamples pulse phase from 0.1/0.71452 to 1/8
  t2s=`echo 'scale=5; ('${t0s}' + ('${j}' + 1) * '${period}' / 8 + '${period}' * '${i} ') ' | bc`  # slightly oversamples pulse phase from 0.1/0.71452 to 1/8

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

  echo 'time('${t1h}':'${t1m}':'${t1s}','${t1h}':'${t2m}':'${t2s}')'  >> $file
done

split ${file} --lines=255 'time-bin'${j}
rm -f ${file}

done
