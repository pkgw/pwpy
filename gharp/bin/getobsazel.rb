#!/usr/bin/env ruby


def getUTAzElChiFromFile (miriad_path, select_statement)

	# obsaz and obsel are not copied in a uvcat command, have to go
	# directly to the original file
	cmd = "uvcheck vis=" + miriad_path + " select=\"" + select_statement + "\" "

	# get obsaz	
	azcmd = cmd + "var=obsaz | grep Average"
	azline = `#{azcmd}`
	stringarray = azline.chomp.split(/\s+/)
	obsaz = stringarray[2]

	# get obsel	
	elcmd = cmd + "var=obsel | grep Average"
	elline = `#{elcmd}`
	stringarray = elline.chomp.split(/\s+/)
	obsel = stringarray[2]

	# for the rest of the variables, we can extract them from a slice

	# delete old slice file in case it is hanging around
	outfile = "vis.slice"
	stdout = `#{"rm -rf " + outfile}`

	# slice out the relevant part of visibility file
	cmd = "uvcat vis=" + miriad_path + " select=\"" + select_statement + "\" out=" + outfile
	stdout = `#{cmd}`
	if !File::exists?( outfile + "/visdata" ) then
		puts "No vis data with specified selection"
		return nil
	end

	# first part of uvcheck line operating on slice
	cmd = "uvcheck vis=" + outfile + " "

	# get obsut	
	utcmd = cmd + "var=ut | grep Average"
	utline = `#{utcmd}`
	stringarray = utline.chomp.split(/\s+/)
	obsutrad = stringarray[2]
	obsut = (obsutrad.to_f * 12 / Math::PI).to_s

	# get chi	
	chicmd = cmd + "var=chi | grep Average"
	chiline = `#{chicmd}`
	stringarray = chiline.chomp.split(/\s+/)
	obschi = stringarray[2]

	# delete old slice file in case it is hanging around
	stdout = `#{"rm -rf " + outfile}`

	return obsut + " " + obsaz + " " + obsel + " " + obschi + " "

end

#
# main program returns the obsaz,obsel values for specified select statement
#
	# read args from command line
	if ARGV.length != 2
	        puts "Usage: programname raw_miriad_dataset, miriad_select_statement (w/o the select= part) " 
	        exit
	end
	miriad_path = ARGV[0]
	select_statement = ARGV[1]
	puts getUTAzElChiFromFile(miriad_path, select_statement)

# end main program

# Old version of program code is here for reference
=begin
	cmd = "uvcheck vis=" + miriad_path + " select=\"" + select_statement + "\" "
	azcmd = cmd + "var=obsaz | grep Average"
	uvc = IO.popen(azcmd, "r")
	azline = uvc.gets.chomp
	stringarray = azline.split(/\s+/)
	obsaz = stringarray[2]

	elcmd = cmd + "var=obsel | grep Average"
	uvc = IO.popen(elcmd, "r")
	elline = uvc.gets.chomp
	stringarray = elline.split(/\s+/)
	obsel = stringarray[2]

	chicmd = cmd + "var=chi | grep Average"
	uvc = IO.popen(chicmd, "r")
	chiline = uvc.gets.chomp
	stringarray = chiline.split(/\s+/)
	obschi = stringarray[2]

	utcmd = cmd + "var-ut | grep Average"
	uvc = IO.popen(utcmd, "r")
	utline = uvc.gets.chomp
	stringarray = utline.split(/\s+/)
	obsutrad = stringarray[2]
	obsut = (obsutrad.to_f * 12 / Math::PI)
=end

