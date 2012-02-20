#!/bin/tcsh 
set root = mosfx; set bw=-100
goto map
foreach freq (3140 4960)
 set cor=a; if ($freq == 3140) set cor=c
 foreach sou (0744-064 0834+555 2038+513 3c119 3c123 3c138 3c147 3c295 3c48 3c84 bllac) 
  set vis = ../$root{$cor}-$sou-$freq$bw
  newrfisweep.csh vis=$vis options=autoedge scans=4 subint=999
 end  # loop over sou
end   # loop over freq

map:
foreach freq (4960) #3140
 set cor=a; if ($freq == 3140) set cor=c
# foreach phcal (0744-064 0834+555 2038+513 3c119 3c123 3c138 3c147 3c295 3c48 3c84 bllac)
 foreach phcal (3c119 3c147 3c48)
   set cal = ../$root{$cor}-$phcal-$freq$bw
   set sf = `echo $root{$cor}-$phcal-$freq$bw | tr '-' ' ' | awk '{print $2,$3,$3/1000}'`
   set flux = `calinfo target=$sf[1] freq=$sf[3] | grep Est | awk '{print $3}'`
   newcalcal.csh vis=$cal flux=$flux plim=40 sysflux=4 device=/null options=polsplit,sefd,autocal addflux=2
  foreach sou (3c123 3c147 2038+513 3c119 3c345 3c380 3c395 3c48 3c84 bllac) 
   set vis = ../$root{$cor}-$sou-$freq$bw
   if ($sou == $phcal) goto next
   newcalcal.csh vis=$cal tvis=$vis options=copy
   newautomap.csh vis=$vis options=noflag,sefd,autocal,autolim device=/xs
   mv $sou-maps $sou.$freq-$phcal-maps
   next:
  end  # loop over sou
 end  # loop over phcal
end  # loop over freq

exit 0
