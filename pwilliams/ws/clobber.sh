#! /bin/bash
#
# Delete all of our generated files

. common.sh

for l in *.list ; do
    cmd rm -rf `cat $l`
done
