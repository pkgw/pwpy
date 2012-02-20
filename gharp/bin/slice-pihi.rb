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

	# define name of file that will contain output peak value data
	peakfile = "peak-" + raw_vis + ".dat"
	quietDelete(peakfile)

	# compute the number of iterations we'll need
	maxiters = ((end_hr - start_hr)/time_step_hr).to_i

	hour = start_hr
	last_ut = start_hr
	firsttime = 1
	pprev = ""
	prev = ""
	outline = ""
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
		secondderiv = outfile + ".sd"
		quietDelete(outfile)
		quietDelete(outbm)
		quietDelete(outmp)
		quietDelete(outcl)
#		quietDelete(outcm) # comment this out because cm files always have index appended
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
			outcm_index = outcm + i.to_s
			quietDelete(outcm_index) # could be left over from previous run

	                # create the cleaned image
	                lspec = "line=chan,1"
	                invert = "invert vis=" + outfile_x + "," + outfile_y + " " + lspec + " map=" + 
				outmp+ " beam=" + outbm + " cell=5 imsize=1000 sup=0"
	                `#{invert}`
			clean = "clean map=" + outmp + " beam=" + outbm + " out=" + outcl + " niters=5" 
			`#{clean}`
	                restor = "restor map=" + outmp + " beam=" + outbm + " model=" + outcl + " out=" + outcm_index 
			`#{restor}`
	
	                # write a png version of the image
	                cgdisp = "cgdisp in=" + outcm_index + "," + outcm_index + " region=relcenter,arcsec labtyp=arcmin options=beambl,wedge,mirr csize=1,1 type=contour,pix range=0,0,lin,3"
#			cgdisp in=VIZ.cm13,VIZ.cm13 region=relcenter,arcsec labtyp=arcmin options=beambl,wedge,mirr csize=1,1 type=contour,pix range=0,0,lin,3 device=/xs
			cgdisp_png = cgdisp + " device=" + raw_vis + "_" + time + ".png/png"

			`#{cgdisp_png}`

			# write image to screen	
			cgdisp_x = cgdisp + " device=/xs"
#			`#{cgdisp_x}`

	                # calculate the numerical second derivative
			peak = ""
	               	if (pprev != "") then
				secondderiv_index = "secondderiv" + (i-1).to_s
				quietDelete(secondderiv_index)

	                	maths = "2*<" + prev + ">-<" + outcm_index + ">-<" + pprev + ">"
				maths = "maths exp=\"" + maths + "\" out=" + secondderiv_index 
				`#{maths}`

				getpeak= "imfit in=" + secondderiv_index + " object=point | grep Peak"
				peak = `#{getpeak}`.chomp
				print "#############" + peak + "\n"
			end

			#increment counters
			pprev = prev
			prev = outcm_index
	
	                # get time, az, el, and chi for this snapshot
			select = "time(" + t1 + "," + t2 + ")"
			utazel = MirVars.getUTAzElChiFromFile(raw_vis, select)
	
			# parse the ephemeris position
			stringarray = utazel.chomp.split(/\s+/) # ut az el ir chi
			ut = stringarray[0].to_f
			az = stringarray[1].to_f
			el = stringarray[2].to_f
			range = stringarray[3].to_f
			chirad = stringarray[4].to_f

			# check ut for rollover at end of UT day
			if ut < last_ut then
				ut += 24.0
			end
			last_ut = ut
			utsec = ut * 3600.0

	                # fit a point source to the cleaned image
	                imfit = "imfit in=" + outcm + i.to_s + " object=point | grep Offset"
	                offset = `#{imfit}`.chomp
	
			# parse the offset position (in arcsec)
			stringarray = offset.chomp.split(/\s+/) # Offset Position (arcsec):   -1.357    51.000
			xpos = stringarray[4].to_f
			ypos = stringarray[5].to_f

			# here is where we apply parallactic angle correction and convert offsets to azel's
			# Equations for parallactic rotation
			# dXEL = -xpos*COS(chi) + ypos*SIN(chi) 
			# dEl = xpos*SIN(chi) + ypos*COS(chi)
			#
			# rotate the positions by the parallactic angle
			xpos_prime = -xpos * Math.cos(chirad) + ypos * Math.sin(chirad)
			ypos_prime =  xpos * Math.sin(chirad) + ypos * Math.cos(chirad)

			# update the ephemeris position with az el offsets
			xpdeg = xpos_prime / 3600.0
			ypdeg = ypos_prime / 3600.0
			az_prime = az + xpdeg
			el_prime = el + ypdeg

			# write header line
			if firsttime == 1 then
				header = "Peak +/- RMS UT(sec) dXEl(\") dEl(\") azdeg\' eldeg\' range(m) chirad rawxpos(\") rawypos(\") ephemazdeg ephemeldeg"
				# opens file, writes data and closes in one line
				File.open(datafile, 'a+') {|f| f.write(header + "\n") }
				firsttime = 0
			end

			# opens file, writes data and closes in one line
			puts peak + " " + outline
			File.open(datafile, 'a+') {|f| f.write(peak + " " + outline + "\n") }

			# prepare outline for next time
			outline =  "%.3f" % utsec + " "
			outline += "%.3f" % xpos_prime + " "
			outline += "%.3f" % ypos_prime + " "
			outline += "%.6f" % az_prime + " "
			outline += "%.6f" % el_prime + " "
			outline += "%.3f" % range + " "
			outline += "%.3f" % chirad + " "
			outline += "%.3f" % xpos + " "
			outline += "%.3f" % ypos + " "
			outline += "%.6f" % az + " "
			outline += "%.6f" % el + " "

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

