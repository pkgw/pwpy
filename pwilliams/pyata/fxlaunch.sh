#! /bin/sh -e

src="$1"
freq="$2"
outbase="$3"
antpols="$4"
lo="$5"
nsephem="$6"
duration="$7"

echo atafx $outbase-$src-$freq $antpols fx64c:fxa $nsephem -duration $duration -noabort -fringeon
exec atafx $outbase-$src-$freq $antpols fx64c:fxa $nsephem -duration $duration -noabort -fringeon
