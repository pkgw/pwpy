#!/usr/bin/env ruby

# read args from command line
if ARGV.length != 3
	puts "Usage: single_pol_tsys_flag.rb <full sefd path/file> miriad_file max_tsys_retained" 
	exit
end
sefd_path = ARGV[0]
miriad_path = ARGV[1]
max_tsys = ARGV[2].to_f
jypk = 160

# Read data from sefd file
if File.exist?(sefd_path) then
	sefd_file = File.open(sefd_path, "r")
else
	puts "No file \"" + sefd_path + "\" found."
	exit
end

# Are we doing XX or YY pol?
len = sefd_path.length
is_xx = sefd_path[len-2,len] == "xx"
if ! is_xx then 
	is_yy = sefd_path[len-2,len] == "yy"
	if ! is_yy then
		puts "SEFD filename does not end with xx or yy, cannot proceed."
		exit
	end
end

# parse ants and tsys from from sefd file
good_ant_tsys = Hash.new
good_ants = []
tsys = []
line = sefd_file.gets
line = sefd_file.gets # discard first two lines
while (line = sefd_file.gets)
	stringarry = line.split(/\s+/)
	ant = stringarry[1].to_i
	ts = stringarry[7].to_f / 163.0
	if ts < max_tsys then
		good_ants << ant
		good_ant_tsys[ant] = ts
	end
end


ant_len = good_ants.length
for i in (0..ant_len-1)
	puts good_ants[i].to_s + "\t" + good_ant_tsys[good_ants[i]].to_s
end

# Extract number of antennas from miriad file (all are represented in some sense)
nant_file = "nants"	
system("uvcheck vis=" + miriad_path.to_s + " var=nants | grep Average | awk '{print $2}' > " + nant_file)	
nant_file = File.open(nant_file)
nant_str = nant_file.gets
nants = nant_str.to_i
puts "Number of antennas = " + nants.to_s
nant_file.close

# Overwrite tsys table in new miriad file
newfile = miriad_path + "_tsys"
cmd = "uvputhd vis=" + miriad_path + " out=" + newfile + " hdvar=systemp varval="
for i in (1..nants)
	if good_ants.include?(i) then
		cmd += good_ant_tsys[i].to_s
	else
		cmd += "1000000"
	end
	if (i != nants) then
		cmd += ","
	end
end
puts cmd
system(cmd)

# Generate comma delimited lists of bad antennas and tsys values
bad_commas = ""
tsys_commas = ""
for i in (1..nants)
	if good_ants.include?(i) then
		tsys_commas << good_ant_tsys[i].to_s
	else
		tsys_commas += "1000000"
		bad_commas += i.to_s
		if (i != nants) then 
			bad_commas += ","
		end
	end
	if (i != nants) then 
		tsys_commas += ","
	end
end

# flag band antennas
cmd = "uvflag vis=" + newfile + " flagval=flag select=\"ant(" + bad_commas + ")\""
puts cmd
system (cmd)

exit

