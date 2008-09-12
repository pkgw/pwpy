#! /bin/sh -e

src="$1"
freq="$2"
radec="$3"
ndumps="$4"
outbase="$5"
antpols="$6"
lo="$7"
nsephem="$8"
duration="$9"

echo frfx64.csh `pwd` $freq $src $radec $ndumps
frfx64.csh `pwd` $freq $src $radec $ndumps &

echo atafx $outbase-$src-$freq $antpols $lo $nsephem -duration $duration -noabort -fringeon
atafx $outbase-$src-$freq $antpols $lo $nsephem -duration $duration -noabort -fringeon

wait
exit $?
