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

# When only using atafx, 'radec' and 'ndumps' are not needed.
# They are used by fxmir.

echo atafx $outbase-$src-$freq $antpols $lo $nsephem -duration $duration -noabort -fringeon
exec atafx $outbase-$src-$freq $antpols $lo $nsephem -duration $duration -noabort -fringeon
