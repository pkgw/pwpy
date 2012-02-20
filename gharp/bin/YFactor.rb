#!/usr/bin/env ruby
	
require 'fx/conf'

=begin (this is how you begin / end a comment block)
	Compute the median value of every autocorrelation in a set of "on" files and 
	"off" files, and compute the y-factor for the file pair.
=end

class YFactor

	# Here is an example of a class variable: N.B.
	# class constants (Ruby has retarded class variables that we
	# are all cautioned not to use!)
	def self.JYPK
		return 163.0 
	end

	def self.Header 
		return "Ant1\tAnt2\tPol\tFreq_GHz\tElOff\tElOn\tOff\tOn-Off"
	end

	#
	# Takes two input files, averages, computes median values for autocorrs,
	# and computes Y-factor & more?
	#
	def self.computeYFactor(off, on, ofile)
	
		# get rid of appending slash
		if (off[off.length-1] == "/"[0]) then 
			off = off[0, off.length - 1]
		end
		if (on[on.length-1] == "/"[0]) then 
			on = on[0, on.length - 1]
		end

		# delete temporary files from previous runs
		offaver = "offaver"
		onaver  = "onaver"
		quietDelete(offaver)
		quietDelete(onaver)

		# uvaver the data to a single set of correlations
		cmdoff = "uvaver vis=" + off + " out=" + offaver + " interval=999 >> off.log"
		cmdon  = "uvaver vis=" + on  + " out=" + onaver  + " interval=999 >> on.log"

		puts cmdoff
		puts cmdon
		p1 = fork do 
			system(cmdoff)
		end
		system(cmdon)
		Process.waitpid(p1)

		# compute the files of median values
		offmed = "offmedian"
		onmed  = "onmedian"
		quietDelete(offmed)
		quietDelete(onmed)

		cmdoff = "java jmir.miriad.ACMedian vis=" + 
			offaver + " out=" + offmed + " >> off.log"
		cmdon  = "java jmir.miriad.ACMedian vis=" + 
			onaver  + " out=" + onmed  + " >> on.log"

#		puts cmdoff
#		puts cmdon
		p1 = fork do 
			system(cmdoff)
		end
		system(cmdon)
		Process.waitpid(p1)

		# sort the results of median calc
		offfile = File.open(offmed, "r")
		onfile = File.open(onmed, "r")
		offs = []
		ons = []
		count = 0
		while(offline = offfile.gets)
			online = onfile.gets
			offs[count] = offline.strip
			ons[count]  = online.strip
			count += 1
		end
		# must use modify version of sort (hence bang)
		offs.sort!
		ons.sort!

		# parse the median files, create a file containing the combination of two
		for i in 0..count-1
			offline = offs[i]
			online  = ons [i]
			offvals = parseMedianLine(offline)
			onvals =  parseMedianLine(online)
			if (offvals[0] == onvals[0] &&
			    offvals[1] == onvals[1] &&
			    offvals[2] == onvals[2] &&
			    offvals[3] == onvals[3] )
				outstr = offvals[0].to_s + "\t" + offvals[1].to_s + "\t" + 
				         offvals[2].to_s + "\t" + offvals[3].to_s + "\t" +	
				         offvals[4].to_s + "\t" + onvals[4].to_s  + "\t" +
				         offvals[5].to_s + "\t" + (onvals[5] - offvals[5]).to_s
				ofile.puts outstr
			else
				puts "ERROR: median files do not line up!"
				puts offvals
				puts onvals
			end
		end

		return

	end # YFactor

	# 
	# Parse one line from a median file
	# Prototype: 17      17      XX      0.500   23.093  11707314
	#
	def self.parseMedianLine(line)
		stringarray = line.chomp.split(/\s+/) # ant1 ant2 pol freq el val
		ant1 = stringarray[0].to_i
		ant2 = stringarray[1].to_i
		pol =  stringarray[2]
		freq = stringarray[3].to_f
		el = stringarray[4].to_f
		val = stringarray[5].to_f
		return [ant1, ant2, pol, freq, el, val]
	end # parseMedianLine
	
	
end # end of class	

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
# main program
# Takes input arguemnts and corrects a single-polarization miriad file for system temperatures.
#
	# read args from command line
	if ARGV.length < 1
		puts "Usage: programname file_containing_pair_list" 
		exit
	end

	files = File.open(ARGV[0], "r")
	ofile = File.open("OnOff.dat", "w")
	ofile.puts YFactor.Header
	ofile.close

	# will bomb if any of the filenames are wrong
	while (off = files.gets) do
		ofile = File.open("OnOff.dat", "a")
		on = files.gets
		off = off.strip
		on = on.strip

		YFactor.computeYFactor(off, on, ofile)
		ofile.close
	end

	exit # end of main program

