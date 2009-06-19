#!/usr/bin/env ruby
        
# read args from command line
if ARGV.length != 2
        puts "Usage: programname raw_miriad_dataset, miriad_select_statement (w/o the select= part) " 
        exit
end
miriad_path = ARGV[0]
select_statement = ARGV[1]

#
# main program returns the obsaz,obsel values for specified select statement
#
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
	obsut = (obsutrad.to_f * 12 / Math::PI).to_s

	puts obsut + " " + obsaz.to_s + " " + obsel.to_s + " " + obschi.to_s + " "

# end main program

