#!/bin/bash

if [ -z "$1" ]
then
  echo "Usage: $(basename $0) DATASET" >&2
  exit 1
fi

sed -n '3,66p' "${1}/history" \
| grep Walsh \
| tr ':|' ' ' \
| sort -k8 \
| awk '
  i==$3 && a==and(substr($4,3,1),2) && w==$NF {
    printf "%s\n%s\n\n", p, $0
  }
  {
    i=$3; a=and(substr($4,3,1),2); w=$NF; p=$0
  }
'
