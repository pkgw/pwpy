#! /bin/bash
#
# Makes files with select statements for imaging a pulsar

0.71452/0.100

for ((j=1; j<=7; j++))
do

export file='vis-bin'${j}
touch $file

for ((i=${j}-1; i<=3000; i=i+7))
do
  v1=$((10*${i}+1))
  v2=$((10*${i}+10))
  echo 'vis('${v1}','${v2}')' >> $file
done

split ${file} --lines=255 'vis-bin'${j}
rm -f ${file}

done

