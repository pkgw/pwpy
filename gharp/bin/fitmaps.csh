#!/bin/csh -f

#du -sk *-maps/*.cm | grep -v cal- | awk '{print $2}' > maplist
du -sk *-maps/*.cm | awk '{print $2}' > maplist

set arc = 400
set chmap = allchans
set name = fitmaps
rm -f $name.fit

foreach map (`cat maplist`)

fit:
 if !(-e $name.fit) then
  echo "Map                                 beamsize      fit offset  fit error  RadOff  Peak" > $name.fit
  echo "-------------------------------------------------------------------------------------" >> $name.fit
 endif

 imfit object=point region="relcen,arcsec,box($arc,-$arc,-$arc,$arc)" in=$map > $name.log
 echo 'imfit object=point region="relcen,arcsec,box($arc,-$arc,-$arc,$arc)" in=$map > $name.log'

 set fitoff = `grep  Offset     $name.log | cut -d: -f2 | awk '{print $1,$2}'`
 set radoff = `grep  Offset     $name.log | cut -d: -f2 | awk '{print sqrt($1**2+$2**2)}'`
 set fiterr = `grep  Positional $name.log | cut -d: -f2 | awk '{print $1,$2}'`
 set bsize =  `grep  Major      $name.log | cut -d: -f2 | awk '{print $1,$2}'`
 set peak  =  `grep  Peak       $name.log | cut -d: -f2 | awk '{print $1}'`
 set mname =  `echo $map | cut -d/ -f1`

 echo $mname $bsize $fitoff $fiterr $radoff $peak | \
  awk '{printf "%-35s %5.1f %5.1f %6.1f %4.1f %6.1f %4.1f %6.2f %6.2f\n", $1,$2,$3,$4,$5,$6,$7,$8,$9}' >> $name.fit
end

echo " "
echo $name.fit
cat $name.fit

exit 0
