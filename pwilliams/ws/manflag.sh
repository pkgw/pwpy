#! /bin/bash
#
# Manually run a uvflag command on several of our datasets

. common.sh

# We accept args that apply to both filter-list and uvflag.
# pol=*, freq=*, and src=* are all for filter-list ; the
# rest are passed onto uvflag.

uvf_args=""
filt_args=""

while [ $# -gt 0 ] ; do
    case $1 in
	pol=*|freq=*|src=*) filt_args="$filt_args $1" ;;
	*) uvf_args="$uvf_args $1" ;;
    esac
    shift
done

# OK do it

for v in `./filter-list.py fx.list $filt_args` ; do
    echo $v ...
    shhcmd uvflag vis=$v flagval=f $uvf_args
done
