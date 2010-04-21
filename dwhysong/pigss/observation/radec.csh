#!/bin/csh -f
# finds radec in catalogs                                 jrf - 7sept07
#  uses Geoff's gawk for absolute match ignoring case

set src = $1
if ( "$2" != "" ) then
  set catalog=$2
else
  set catalog=/home/obs/archive/bin/catalog.list
endif

rm -f radec
gawk -v sname=$src '{if (toupper($3)==toupper(sname)) print $0}' $catalog | head -n 1 > radec
if (`wc radec|cut -c1` == 0) then
  grep -i $src $catalog | head -n 1 > radec
endif
if (`wc radec|cut -c1` == 0) then
  atalistcatalog -l | grep -i $src | head -n 1 > radec
endif

if (`wc radec|cut -c1` == 0) then
  echo " "
  echo ">>>>>>> ERROR -  $src not found in any ATA catalog >>>>>>>>"
  echo " "
else
  cat radec
endif

exit 0
