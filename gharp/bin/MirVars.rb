#!/usr/bin/env ruby

#
# Tools for getting variables out of miriad files.
# uses uvcheck under the covers.
#
# Author: G.R. Harp
# 5/30/9
# Change log:
#

module MirVars

	def self.getUTAzElChiFromFile (miriad_path, select_statement)
	
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
	
		# get obsir	
		ircmd = cmd + "var=obsir | grep Average"
		irline = `#{ircmd}`
		stringarray = irline.chomp.split(/\s+/)
		obsirkm = stringarray[2].to_f
		obsrange = (1000.0/obsirkm).to_s
	
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
	
		return obsut + " " + obsaz + " " + obsel + " " + obsrange + " " + obschi + " "
	
	end
end

