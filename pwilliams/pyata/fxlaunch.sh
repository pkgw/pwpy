#! /bin/sh -e

src="$1"
freq="$2"
instr="$3"
outbase="$4"
antpols="$5"
nsephem="$6"
duration="$7"

echo atafx $outbase-$src-$freq-$instr $antpols $instr $nsephem \
           -duration $duration -noabort -fringeon
exec atafx $outbase-$src-$freq-$instr $antpols $instr $nsephem \
           -duration $duration -noabort -fringeon
