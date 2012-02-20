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
	last_ut = start_hr
	firsttime = 1
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
		cmdx = "uvcat vis=" + vis_x + " select=\"time(" + t1 + "," + t2 + ")\" out=" + outfile_x + " 2> /dev/null" 
		cmdy = "uvcat vis=" + vis_y + " select=\"time(" + t1 + "," + t2 + ")\" out=" + outfile_y + " 2> /dev/null"
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
				outmp+ " beam=" + outbm + " cell=1 imsize=1024 sup=0 2> /dev/null"
	                `#{invert}`
			clean = "clean map=" + outmp + " beam=" + outbm + " out=" + outcl + " niters=100 2> /dev/null" 
			`#{clean}`
	                restor = "restor map=" + outmp + " beam=" + outbm + " model=" + outcl + " out=" + outcm + " 2> /dev/null"
			`#{restor}`
	
	                # write a png version of the image
	                cgdisp = "cgdisp in=" + outcm + " labtyp=arcsec olay=olay"
			cgdisp_png = cgdisp + "device=" + raw_vis + "_" + time + ".png/png 2> /dev/null"
			`#{cgdisp_png}`

			# write image to screen	
			cgdisp_x = cgdisp + "device=/xs 2> /dev/null"
			`#{cgdisp_x}`

	                # get time for this snapshot
			select = "time(" + t1 + "," + t2 + ")"
			ut = MirVars.getUTFromFile(outfile_x, select).chomp.to_f
	
			# check ut for rollover at end of UT day
			if ut < last_ut then
				ut += 24.0
			end
			last_ut = ut
			utsec = ut * 3600.0

	                # fit a point source to the cleaned image
			imfit_cmd = "imfit in=" + outcm + " object=point region=quart spar=1,0,0 fix=xy 2> /dev/null"
	                imfit = imfit_cmd + " | grep Offset"
	                offset = `#{imfit}`.chomp
	                imfit = imfit_cmd + " | grep Peak"
	                peak = `#{imfit}`.chomp
	
			# parse the offset position (in arcsec)
			stringarray = offset.chomp.split(/\s+/) # Offset Position (arcsec):   -1.357    51.000
			xpos = stringarray[4].to_f
			ypos = stringarray[5].to_f

			#parse the peak value 
			stringarray = peak.chomp.split(/\s+/) # Peak value: 0.3075     +/-  0.1712
			peak_val = stringarray[3].to_f
			peak_err = stringarray[5].to_f

	                # append all results to a single line
			ret_val =  "%.3f" % utsec + " "
			ret_val += "%.3f" % peak_val + " "
			ret_val += "%.3f" % peak_err + " "
			ret_val += select + " " 
			puts ret_val

			# write header line
			if firsttime == 1 then
				header = "UT(sec) Peak Peak-Err dXDec(\") dDec(\")"
				# opens file, writes data and closes in one line
				File.open(datafile, 'a+') {|f| f.write(header + "\n") }
				firsttime = 0
			end

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


		# here is where we apply parallactic angle correction and convert old azel's to new
		# Excel equations for parallactic rotation
		# dXEL = -xpos*COS(chi) + ypos*SIN(chi) 
		# dEl = xpos*SIN(chi) + ypos*COS(chi)
		#
		stringarray = 

#
# main program runs slice on the command line parameters
#
	# read args from command line
	if ARGV.length != 6
	        puts "Usage: programname raw_vis  vis_x  vis_y  start_hr  end_hr  step_secs" 
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

