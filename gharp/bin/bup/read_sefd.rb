#!/usr/bin/env ruby
	
require 'miriad' # David M's miriad tools
require 'fx/conf'

def ReadSEFD(sefd_path=nil, max_tsys = 100.0)
	# read args from command line
	if sefd_path == nil 
		puts "Usage: read_sefd.rb <full sefd path/file> [max_tsys default=100K]" 
		exit
	end
	sefd_path = sefd_path + "/sefd"

	# check value of tsys
	if  max_tsys <= 0.0 then
		puts "max_tsys value " + max_tsys.to_s + " must be strictly positive."
		exit
	end

	# discover how many antennas are in the array
	nants = 0
	antpos = FXConf.antpos_file.chomp()
	antpos_array = antpos.split(/\n/)
	antpos_array.each do |line|
		if line[0,1] != "#" then
			nants += 1
		end
	end
	
	# make arrays to hold all results
	x_ant_tsys = Array.new(nants)
	y_ant_tsys = Array.new(nants)
	
	# Read data from sefd file
	sefd_file = File.open(sefd_path, "r")
	
	# discard first two lines
	line = sefd_file.gets
	line = sefd_file.gets
	
	obviously_bad_tsys = 10000000.0
	while (line = sefd_file.gets)
		string_array = line.split(/\s+/)
		ant = string_array[1].to_i
		pol = string_array[2]
		ts = string_array[7].to_f / 163.0
		if ts < max_tsys then
#puts "ts is low, max_tsys = " + max_tsys.to_s + " ts = " + ts.to_s
			if pol["x"] then
				x_ant_tsys[ant] = ts.to_f
			elsif pol["y"] 
				y_ant_tsys[ant] = ts.to_f
			end
		else
#puts "ts is high, max_tsys = " + max_tsys.to_s + " ts = " + ts.to_s
			if pol["x"] then
				x_ant_tsys[ant] = obviously_bad_tsys
			elsif pol["y"] then
				y_ant_tsys[ant] = obviously_bad_tsys
			end
		end
	end
	
	for i in 0..(x_ant_tsys.length-1) do
		puts i.to_s + ", " + x_ant_tsys[i].to_s
		i += 1
	end
end	


#main program
	ReadSEFD(ARGV[0], ARGV[1].to_f)
exit

