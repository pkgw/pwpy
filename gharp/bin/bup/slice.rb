#!/usr/bin/env ruby

require 'MirVars'

#
# Takes the output of a "processed" miriad file (x and y pols separated)
# and generates short time slices (~10s) from it and images them.
# You can use the images to make a movie, and a data file is created
# to hold the results
# NOTE: Unlike previous c-shell versions, this program applies the
# parallactic angle correction and generates an output ephemeris suitable
# for sending to the AF
#
# Author: G.R.Harp
# Change log:
#
def slice (raw_vis, vis_x, vis_y, start_hr = 0.0, end_hr = 23.999, time_step_sec = 10.0)

	# check ranges
	if start_hr < 0 || start_hr > 24 then
		puts "start_hr " + start_hr.to_f + " is not in range (0 <= start < 24)"
		exit
	end
	if end_hr < 0 || end_hr > 24 then
		puts "end_hr " + end_hr.to_f + " is not in range (0 <= end < 24)"
		exit
	end
	time_step_hr = time_step_sec.to_f / 3600.0

	# define names of temporary files
	outfile = "VIZ"
	outfile_x = outfile + "-xx"
	outfile_y = outfile + "-yy"

	# define name of file that will contain output position data
	datafile = "pos-" + raw_vis + ".dat"
	quietDelete(datafile)

	# compute the number of iterations we'll need
	maxiters = ((end_hr - start_hr)/time_step_hr).to_i

	hour = start_hr
	for i in 0..maxiters-1 do
		# convert begin time for slice to format for select statement
		begintime = convertHoursToHHMMSS(hour)
		hr=  begintime[0].to_s
		min= begintime[1].to_s
		sec= begintime[2].to_s
		t1 = hr + ":" + min + ":" + sec

		# generate a filename suffix for this slice
		sec = begintime[2].round.to_s # only want integer seconds in filename
		time = hr + "-" + min + "-" + sec # filenames can't contain colons

		# add time step to get end time for this slice
		hour = hour + time_step_hr

		# convert end time to format for select statement
		endtime = convertHoursToHHMMSS(hour)
		hr=  endtime[0].to_s
		min= endtime[1].to_s
		sec= endtime[2].to_s
		t2 = hr + ":" + min + ":" + sec

		# miriad doesn't like overwriting files so we delete old ones
		# if present
		outmp = outfile + ".mp"
		outbm = outfile + ".bm"
		outcl = outfile + ".cl"
		outcm = outfile + ".cm"
		quietDelete(outfile)
		quietDelete(outbm)
		quietDelete(outmp)
		quietDelete(outcl)
		quietDelete(outcm)
		quietDelete(outfile_x)
		quietDelete(outfile_y)

		# select out the bit of data for this time frame, have to process x-pol and y-pol 
		# files separately
		cmdx = "uvcat vis=" + vis_x + " select=\"time(" + t1 + "," + t2 + ")\" out=" + outfile_x  
		cmdy = "uvcat vis=" + vis_y + " select=\"time(" + t1 + "," + t2 + ")\" out=" + outfile_y 
		puts cmdx
		`#{cmdx}`
		`#{cmdy}`
	
	        # do invert, clean, restor and cgplot steps, outputs files
		# but don't bother if there is no data extant for this time frame
		if File.exist?(outfile_x + "/visdata") then
	
			# remove temporary files from previous iteration
			quietDelete(outmp)
			quietDelete(outbm)
			quietDelete(outcl)
			quietDelete(outcm)

	                # create the cleaned image
	                lspec = "line=chan,1"
	                invert = "invert vis=" + outfile_x + "," + outfile_y + " " + lspec + " map=" + 
				outmp+ " beam=" + outbm + " cell=1 imsize=1200 sup=0"
	                `#{invert}`
			clean = "clean map=" + outmp + " beam=" + outbm + " out=" + outcl + " niters=5" 
			`#{clean}`
	                restor = "restor map=" + outmp + " beam=" + outbm + " model=" + outcl + " out=" + outcm + " mode=convolve fwhm=10"
			`#{restor}`
	
	                # write a png version of the image
	                cgdisp = "cgdisp in=" + outcm + " labtyp=arcsec olay=olay "
			cgdisp_png = cgdisp + "device=" + raw_vis + "_" + time + ".png/png"
			`#{cgdisp_png}`

			# write image to screen	
			cgdisp_x = cgdisp + "device=/xs"
#			`#{cgdisp_x}`

	                # get time, az, el, and chi for this snapshot
			select = "time(" + t1 + "," + t2 + ")"
			utazel = MirVars.getUTAzElChiFromFile(raw_vis, select)
	
	                # fit a point source to the cleaned image
	                imfit = "imfit in=" + outcm + " object=point | grep Offset"
	                offset = `#{imfit}`.chomp
	
	                # append all results to a single line
	                ret_val = offset + " UT,Az,El,Range,Chi " + utazel
			puts ret_val

			# opens file, writes data and closes in one line
			File.open(datafile, 'a+') {|f| f.write(ret_val + "\n") }

	        end
	
	end
end


#
# Takes decimal hour as input and converts to an array of three
# elements of the form [HH, MM, SS.SSS]
# First two are integers, last is float.
#
def convertHoursToHHMMSS(decimal_hours)
	
		ms = (decimal_hours * 60.0 * 60.0 * 1000.0).round

		sec = (ms / 1000)
		ms = ms % 1000

		min = sec / 60;
		sec = sec % 60;

		hour = min / 60;
		min = min % 60;

		secfloat = sec.to_f + ms.to_f/1000.0

		return [hour,min,secfloat]
end

#
# Deletes a file (or directory), quietly. It checks if the file is present before
# attempting delete so there are no error messages
#
def quietDelete(filename)

	if File.exist?(filename) then
		if File.directory?(filename) then
			FileUtils.rm_rf(filename)
		else
			File.delete(filename) 
		end
	end
end

#
#
#


=begin

while ($n < $maxiters)
	set t1=`atahourstohhmmss $hour`
	MATH hour = ( $hour + 0.002777777778 )
	set t2=`atahourstohhmmss $hour`
	set hr=`awk 'BEGIN { print substr("'"$t1"'", 1,2) }'`
	set min=`awk 'BEGIN { print substr("'"$t1"'", 4,2) }'`
	set sec=`awk 'BEGIN { print substr("'"$t1"'", 7,2) }'`
	set time=$hr-$min-$sec

	rm -rf $outfile $outfile.bm $outfile.mp $outfile.cl $outfile.cm
	rm -rf $outfilex $outfiley 

	echo uvcat vis=$vis select="time($t1,$t2)" out=$outfile
	uvcat vis=$visx select="time($t1,$t2)" out=$outfilex >& junk
	uvcat vis=$visy select="time($t1,$t2)" out=$outfiley >& junk

	# do invert, clean, restor and cgplot steps, outputs files
	if (-e $outfilex/visdata) then

		# create the cleaned image
		set lspec="line=chan,1"
		rm -rf $outfile.mp $outfile.bm $outfile.cl $outfile.cm
		invert vis=$outfilex,$outfiley $lspec map=$outfile.mp beam=$outfile.bm cell=1 imsize=1200 sup=0 >& junk
		clean map=$outfile.mp beam=$outfile.bm out=$outfile.cl niters=5 >& junk
		restor map=$outfile.mp beam=$outfile.bm model=$outfile.cl out=$outfile.cm mode=convolve fwhm=10 >& junk
		
		# write a png version of the image
		cgdisp in=$outfile.cm labtyp=arcsec device=${outfile}.png/png olay=olay >& junk
		mv $outfile.png ${vis}_$time.png

		# echo image to screen
		#cgdisp in=$outfile.cm labtyp=arcsec device=/xs olay=olay

		# get time, az, el, and chi for this snapshot
		set utazelchi = `getobsazel.rb $vis "time($t1,$t2)"` 

		# fit a point source to the cleaned image
		set offset = `imfit in=$outfile.cm object=point | grep Offset` 
		
		# append all results to a single line in output file
		set ret_val = "$offset UT,Az,El,Range,Chi $utazelchi" 
		echo $ret_val >> $datafile
		echo $ret_val 
	endif

	@ n += 1
end
=end


#
# main program runs slice on the command line parameters
#
	# read args from command line
	if ARGV.length != 6
	        puts "Usage: programname raw_vis  vis_x  vis_y  start_hr  end_hr  step_hr" 
	        exit
	end
	raw_vis = ARGV[0]
	vis_x = ARGV[1]
	vis_y = ARGV[2]
	start_hr = ARGV[3].to_f
	end_hr = ARGV[4].to_f
	step_hr = ARGV[5].to_f

	slice(raw_vis, vis_x, vis_y, start_hr, end_hr, step_hr)

# end main program

