#! /usr/bin/tcsh -f


set vis = $1

foreach pol (xx yy xxp yyp xxpp yypp)
    if ((-e $vis/gains.$pol && ! -e $vis/gains.$pol/) || -e $vis/bandpass.$pol) then
	if (-e $vis/header) cp $vis/header $vis/tempheader
	if (-e $vis/gains) cp $vis/gains $vis/tempgains
	if (-e $vis/bandpass) cp $vis/bandpass $vis/tempbandpass
	if (-e $vis/header.$pol) mv -f $vis/header.$pol $vis/header
	if (-e $vis/gains.$pol) mv -f $vis/gains.$pol $vis/gains
	if (-e $vis/bandpass.$pol) mv -f $vis/bandpass.$pol $vis/bandpass
	gpcopy vis=$vis out=$vis/gains.$pol mode=create > /dev/null
	rm -rf $vis/header $vis/gains $vis/bandpass
	if (-e $vis/tempheader) mv -f  $vis/tempheader $vis/header
	if (-e $vis/tempgains) mv -f $vis/tempgains $vis/gains
	if (-e $vis/tempbandpass) mv -f $vis/tempbandpass $vis/bandpass
    endif
end

exit 0
