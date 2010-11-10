#! /usr/bin/tcsh -f
# $Id$
onintr fail

#################################################################
# This is a utility for finding the minimum number of selection
# commands needed for a listing of channels. Given that MIRAID
# does not allow for multiple line selections, this can be an
# important step in reducing processing time.
#################################################################

if ($#argv == 0) then
      #################################################################
echo "================================================================="
echo "OPTFLAGCHAN - Channel flagging optimization utility"
echo "'For the lazy spectral flagging enthusiast'"
echo ""
echo "CALLS - None"
echo "PURPOSE - Create a the minimum number of line selection commands"
echo "   for a given listing of channels."
echo "RESPONSIBLE - Karto (karto@hcro.org)"
echo "================================================================="
echo ""
echo "OPTFLAGCHAN is a very simple utility, designed to minimize the"
echo "number of line commands in order to select a given number of"
echo "channels. OPTFLAGCHAN works best with smaller listings of"
echo "channels, but should work relatively well on larger channel"
echo "selections."
echo ""
echo "OPTFLAGCHAN operates by measuring the distance between each pair"
echo "of channels, and finding other channels integer multpiples away"
echo "from the orginal pair (e.g. if channels 1 and 5 are bad, the"
echo "program will first look to see if channel 9 is also bad, then"
echo "13 and so forth until it finds a the (n*4)+5 channel that is not"
echo "IDed as bad). When the program finds the longest string of"
echo "channels, it prints out the corresponding line command for that"
echo "string and repeats the process until no more channels are left."
echo ""
echo "OPTFLAGCHAN - like most basic utilities - does not manipulate any"
echo "data, and is therefore safe to use multiple times without"
echo "conseqeunce."
echo ""
echo "TECHNICAL NOTE: OPTFLAGCHAN creates a temporary directory to"
echo "work from, named flagXXXXX (where X is a random character)."
echo "These directories are supposed to be automatically deleted after"
echo "RFILOCK completes, but might remain in the event of a program"
echo "error. Remnant directories can be safely deleted."
echo ""
echo "CALLING SEQUENCE: newoptfchan.csh chanlist=chanlist"
echo "    (optlim=optlim options=debug)"
echo ""
echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo ""
echo "REQUIRED INPUTS:"
echo " chanlist - A listing of channels (comma seperated) to be"
echo "    optimized. Channels do not need to be in numerical order,"
echo "    but channel ranges are not supported (e.g. to optimize"
echo "    channels 5,6 and 7, the proper input would be chanlist=5,6,"
echo "    7). No default."
echo ""
echo "OPTIONAL INPUTS:"
echo " optlim - Limit (in number of channels) for the optimization"
echo "    algorithm. If the number of channels for a line selection"
echo "    drops below this limit, OPTFLAGCHAN will not optimize"
echo "    further, instead prining out individual line selection"
echo "    commands for any remaining channels. Default is 0."
echo ""
echo " options=debug"
echo "    debug - Don't remove working directory after completion."
exit 0
endif

set chanlist
set optlim = 1
set debug

varassign:

if ("$argv[1]" =~ 'chanlist='*) then
    set chanlist = (`echo "$argv[1]" | sed 's/chanlist=//g' | tr ',' ' '`)
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'optlim='*) then
    set optlim = `echo "$argv[1]" | sed 's/optlim=//g'`
    shift argv; if ("$argv" == "") set argv = "finish"
else if ("$argv[1]" =~ 'options='*) then
    set options = `echo "$argv[1]" | sed 's/options=//g' | tr ',' ' ' | tr '[A-Z]' '[a-z]'`
    set badopt
    foreach option (`echo $options`)
	if ($option == "debug") then
	    set corr = "debug"
	else	
	    set badopt = ($badopt $option)
	endif
    end
    if ("$badopt" != "") echo 'options='`echo $badopt | tr ' ' ','`' not recognized!'
    shift argv; if ("$argv" == "") set argv = "finish"
else
    echo "FATAL ERROR: $argv[1] not recognized..."
    exit 1
endif

if ("$argv[1]" != "finish") goto varassign

set wd = `mktemp -d flagXXXXX`

if ($wd == "") then # Can a temp work directory be created?
    echo "FATAL ERROR: Problems creating temp directory. Make sure you have permissions for the current directory..."
    exit 1
endif


#################################################################
# The first thing the program needs to do is take the list of
# channels and sort them in numeric order. After sorting, the
# program will look at each channel pairing, measure the
# distance between those channels, and look for other channels
# that have the same distance from the second channel, third
# channel, so on and so forth (e.g. if channels 1 and 3 are bad,
# then the program will look to see if channel 5 is bad. If 5 is
# bad, then it will go on to channel 7). The pairing with the
# must number of channels is provided back to the user, and
# the process repeats until no more channels are left.
#################################################################

foreach chan ($chanlist)
    echo $chan >> $wd/prelist
end

sort -unk1 $wd/prelist > $wd/optlist
set optcount = `wc -l $wd/optlist | awk '{print $1}'`
set optdelta = $optcount
set chans = `tail -n 1 $wd/optlist`

while (`wc -l $wd/optlist | awk '{print $1}'` > 1 && $optlim <= $optdelta)
    set lim = `wc -l $wd/optlist | awk '{print $1}'`
    set cmax = 2
    set iidx = 1
    set jidx = 2
    set opts
    set chan1 = `sed -n {$iidx}p $wd/optlist`
    set chan2 = `sed -n {$jidx}p $wd/optlist`
    set opts = ($chan1 `echo $chan1 $chan2 | awk '{print $2-$1}'` 2)
    while (`echo $lim $iidx | awk '{print ($1-$2)+1}'` > $cmax)
	set chan1 = `sed -n {$iidx}p $wd/optlist`
	set chan2 = `sed -n {$jidx}p $wd/optlist`
	while (`echo $lim $jidx | awk '{print ($1-$2)+2}'` > $cmax && `echo $chan1 $chan2 $chans | awk '{print 1+int(($3-$1)/($2-$1))}'` > $cmax)
	    set chanlim = `echo $cmax $chan1 $chan2 | awk '{print (($1-1)*($3-$2))+$2}'` 
	    set counter = 2
	    set delta = `echo $chan2 $chan1 | awk '{print $1-$2}'`
	    if (`awk '{if ($1 == chanlim) print "go"}' chanlim=$chanlim $wd/optlist | head -n 1` == "go") then
#" $rfioptlist " =~ *" $chanlim "*) then
#
		while (`awk '{if ($1 == ((delta*counter)+chan1)) print "go"}' chan1=$chan1 delta=$delta counter=$counter $wd/optlist | head -n 1` == "go")
#" $rfioptlist " =~ *`echo $delta $counter $chan1 | awk '{print " "($1*$2)+$3" "}'`*) 
#
		    @ counter++
		end
	    endif
	    if ($counter > $cmax) set opts = ($chan1 $delta $counter)
	    if ($counter > $cmax) set cmax = $counter
	    @ jidx++
	    set chan2 = `sed -n {$jidx}p $wd/optlist`
	    if ($chan2 == "") set chan2 = $chans
	end
	@ iidx++
	set jidx = `echo $iidx | awk '{print $1+1}'`
    end
    echo "line=chan,$opts[3],$opts[1],1,$opts[2]"
    awk '{if ($1 < chan1) print $0; else if (($1-chan1)%delta != 0) print $0; else if (($1-chan1)/delta > counter) print $0}' chan1=$opts[1] delta=$opts[2] counter=$opts[3] $wd/optlist > $wd/opttemp
    mv $wd/opttemp $wd/optlist
    set optdelta = `wc -l $wd/optlist | awk '{print precou-$1}' precou=$optcount`
    set optcount = `wc -l $wd/optlist | awk '{print $1}'`
end

if (`wc -l $wd/optlist | awk '{print $1}'` > 0) then
    set lastchan = `wc -l $wd/optlist | awk '{print $1}'`
    if ($lastchan != 1) then
	awk '{if (NR == 1) {bchan=$1; idx=1} else if ((bchan+idx) == $1) {idx++} else {print "line=chan,"idx","bchan; bchan=$1; idx=1}; if (NR == lastchan) print "line=chan,"idx","bchan}' lastchan=$lastchan $wd/optlist
    else if ($lastchan == 1) then
	echo "line=chan,1,"`head -n 1 $wd/optlist | awk '{print $1}'`
    endif
endif

finish:

rm -rf $wd

fail:

rm -rf $wd
