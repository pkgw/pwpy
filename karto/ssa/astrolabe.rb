#! /usr/bin/env ruby

###############################################################
#
#  astrolabe.rb
#  
#  Takes an SSA target visibilities file (with calibrations
#  already applied) and an ephemeris and generates a new ephemeris
#  of observed satellite positions. This program will only operate
#  on one channel range of one MIRIAD file at a time, although one
#  can launch multiple instances of this program on different vis
#  files. Current processing does not support multiple launches
#  on the same file (i.e. same MIRIAD file, different channel ranges)
#  although this may change in the near future.
#
#  Similar to most RAPID software, this program does generate it's
#  own "working directory" that is deleted upon successful completion
#  of the process. Working directories for this task will begin
#  with the tag "SSA2".
#
#  Author: Garrett "Karto" Keating
#  Original Date: Sept 1 2009
#  Last Revised Date: Sept 1 2009
#
################################################################

if ARGV[0] == nil
  # If no arguments have been passed, return the usage
  puts ""
  puts "SYNOPSIS"
  puts "\tastrolabe.rb visfile line ephemfile outfile"
  puts "DESCRIPTION"
  puts "\tTakes a MIRIAD visibilities file and an ephemeris and generates"
  puts "\tan ephemeris of observed source positions."
  puts "\tArguments are:"
  puts "\tVISFILE: MIRIAD visibilities file containing SSA data."
  puts "\tLINE: Line selection command for imaging (see MIRIAD 'line' task)"
  puts "\tEPHEMFILE: Ephemeris used during the creation of the visibilies file"
  puts "\tOUTFILE: Name of output file to write the results to (in ascii)"
  puts "" 
  puts "EXAMPLES"
  puts "\tastrolabe.rb TDRS-5-2140 line=chan,1,195 TDRS-5.ephem results.txt"
  puts "\tImages channel 195 of \"TDRS-5-2140\" file, and uses the"
  puts "\t\"TDRS-5.ephem\" ephemeris that was used during the observation to"
  puts "\tcalculate the actual position of the satellite, writing the results"
  puts "\tto \"results.txt\"."
  puts ""
  exit
end


require 'date'
require 'time'
require 'matrix'
require 'mathn'
include Math
require 'gsl'
include GSL

def executeAndLog(command, executeCommand)

  f = File.open(Dir.pwd + "/log.txt",  "a")
  time = Time.new
  dateAndCommand = "[" + time.day.to_s + "/" + time.month.to_s + "/" + time.year.to_s + " " + time.hour.to_s + ":" + time.min.to_s + ":" + time.sec.to_s + "] " + command
  f.puts(dateAndCommand)
  f.flush
  f.fsync
  f.close

  if(executeCommand == true)
    system(command)
  end

end

# Spline fit for Az and El of ephem REQUIRES GSL
# NOTE: This could be converted into a vector operation if neccessary. The bulk of the time is spent reading in the file.
def ephemSpline(ephemFile,ephemTime) # Input: standardard ATA ephem file, time in UTC seconds
  ephemTime = ephemTime.to_f # Force ephemTime to be a float
  az = [] # init the az array
  el = [] # init the elevation array
  times = [] # init the times array
  File.open(ephemFile).each do |row|
    # General ephem format goes [time] [az] [el] [distance]
    rowValues = row.split
    times << rowValues[0].to_f
    az << rowValues[1].to_f
    el << rowValues[2].to_f
  end
  azVector = GSL::Vector.alloc(az) # Convert from array to vector
  elVector = GSL::Vector.alloc(el) # Convert from array to vector 
  timesVector = GSL::Vector.alloc(times) # Convert from array to vector 
  azSpline = GSL::Spline.alloc(timesVector,azVector) # Generate the az spline
  elSpline = GSL::Spline.alloc(timesVector,elVector) # Generate the el spline
  ephemTime *= 10**((log(times[-1])/log(10)).floor-9) # Figure out what format the time stamps in the ephem file is
  azelSpline =  [azSpline.eval(ephemTime),elSpline.eval(ephemTime)] # Calculate the az and el from the generated splines
  return azelSpline # returns azPrime, elPrime
end

# Rotation around x-axis - REQUIRES Matrix
def xRotation(long,lat,theta) # Input : longitude, latitude, theta (rotation amount) - all three are assumed to be in degrees
  thetaRad = theta*PI/180
  rotMatrix = Matrix[[1.0,0.0,0.0],[0.0,cos(thetaRad),-sin(thetaRad)],[0.0,sin(thetaRad),cos(thetaRad)]]
  longRad = long*PI/180
  latRad = lat*PI/180
  xpos = Matrix[[cos(latRad)*cos(longRad),cos(latRad)*sin(longRad),sin(latRad)]]
  xPrime = xpos*rotMatrix
  longPrimeRad = atan2(xPrime[0,1],xPrime[0,0])
  latPrimeRad = asin(xPrime[0,2])
  latPrime = latPrimeRad*180/PI
  longPrime = longPrimeRad*180/PI
  return [longPrime,latPrime]
end

# Rotation around y-axis - REQUIRES Matrix
def yRotation(long,lat,theta) # Input : longitude, latitude, theta (rotation amount) - all three are assumed to be in degrees
  thetaRad = theta*PI/180
  rotMatrix = Matrix[[cos(thetaRad),0.0,sin(thetaRad)],[0.0,1.0,0.0],[-sin(thetaRad),0.0,cos(thetaRad)]]
  longRad = long*PI/180
  latRad = lat*PI/180
  xpos = Matrix[[cos(latRad)*cos(longRad),cos(latRad)*sin(longRad),sin(latRad)]]
  xPrime = xpos*rotMatrix
  longPrimeRad = atan2(xPrime[0,1],xPrime[0,0])
  latPrimeRad = asin(xPrime[0,2])
  latPrime = latPrimeRad*180/PI
  longPrime = longPrimeRad*180/PI
  return [longPrime,latPrime]
end

# Rotation around z-axis - REQUIRES Matrix
def zRotation(long,lat,theta) # Input : longitude, latitude, theta (rotation amount) - all three are assumed to be in degrees
  thetaRad = theta*PI/180
  rotMatrix = Matrix[[cos(thetaRad),-sin(thetaRad),0.0],[sin(thetaRad),cos(thetaRad),0.0],[0.0,0.0,1.0]]
  longRad = long*PI/180
  latRad = lat*PI/180
  xpos = Matrix[[cos(latRad)*cos(longRad),cos(latRad)*sin(longRad),sin(latRad)]]
  xPrime = xpos*rotMatrix
  longPrimeRad = atan2(xPrime[0,1],xPrime[0,0])
  latPrimeRad = asin(xPrime[0,2])
  latPrime = latPrimeRad*180/PI
  longPrime = longPrimeRad*180/PI
  return [longPrime,latPrime]
end

# Grabs timestamps from a vis file using the UVLIST command
def grabDumpTimes(file) # Input: filename
  miriadGrabCommand = "uvlist vis=" + file + " recnum=0 | sed 1,8d | awk '{if ($1$2$3 == keyword) date = $4; if ($1*1 >= 1) print date,$2}' keyword=Datavaluesfor | tr ' ' ':' | sort -u"
  dumpTimes = `#{miriadGrabCommand}`.split
  return dumpTimes
end

#Given an array of times an and integration time, provides an array of start,end (in MIRAID time format) and mid (in UTC seconds) times for a series of time frames
def deriveFrameTimes(miriadTimeArray,intTime,startTime,endTime) # Input time array (from grabDumpTimes), integration time
  startTime = startTime.to_f
  endTime = endTime.to_f
  idx = 1
  utcMidFrameTimes = [] # init the mid-time array
  utcFullFrameTimes = [] # init the full-time array
  currentStart = [] # array to store the current time-frame start
  while idx < miriadTimeArray.nitems do
    dumpTime = DateTime.strptime(miriadTimeArray[idx].split('.')[0],'%y%b%d:%H:%M:%S') # Convert the time stamp from MIRIAD format to DateTime object
    dumpTimeUTC = Time.at(dumpTime.strftime('%s').to_f,miriadTimeArray[idx].split('.')[1].to_f*100000) # Convert DateTime to UTC seconds
    if (dumpTimeUTC.to_f < startTime || dumpTimeUTC.to_f > endTime)
    elsif (currentStart.size == 0) # If this is the first cycle, set the first time as the current start time for the time frame
      currentStart = [dumpTimeUTC]
    elsif (currentStart[-1] + intTime/2.0 < dumpTimeUTC) # If the difference between two dump times exceeds the dump threshold, then dump the average UTC seconds time and mark the current frame as the new start time
      utcMidFrameTimes << currentStart.inject{ |sum, el| sum + el }.to_f / currentStart.size # Averages and adds result to the mid-time array
      currentStart = [dumpTimeUTC] # starts a new time frame
    else
      currentStart << dumpTimeUTC # else, add the current dump time to those contained in the current time frame
    end
    idx += 1
  end
  if currentStart.size > 0
    utcMidFrameTimes << currentStart.inject{ |sum, el| sum + el }.to_f / currentStart.size # dump the remaining elements in the current time frame
  end
  utcMidFrameTimes.each do |midTime| # For each time frame, generate a "start" and "end" time, and convert those times into the MIRAID timestamp format
    midMirTimeArray =  Time.at(midTime).utc.to_s.split(' ')
    midMirTime = midMirTimeArray[5][2,3] + midMirTimeArray[1].upcase + midMirTimeArray[2] + ':' + midMirTimeArray[3] + '.' + ((midTime)%1*10).round.to_s
    startTimeArray = Time.at(midTime-intTime/2.0).utc.to_s.split(' ')
    startTime = startTimeArray[5][2,3] + startTimeArray[1].upcase + startTimeArray[2] + ':' + startTimeArray[3] + '.' + ((midTime-intTime/2.0)%1*10).round.to_s
    endTimeArray = Time.at(midTime+intTime/2.0).utc.to_s.split(' ')
    endTime = endTimeArray[5][2,3] + endTimeArray[1].upcase + endTimeArray[2] + ':' + endTimeArray[3] + '.' + ((midTime+intTime/2.0)%1*10).round.to_s
    utcFullFrameTimes << [startTime,endTime,midTime.to_s,midMirTime]
  end
  return utcFullFrameTimes #return Array[start time (MIRIAD format), end time (MIRAD format), mid time (UTC seconds)
end

# Images a particular time frame
def imageFrame (visFile,frameTimes,wd)
  # For this particular invocation of newautomap, the following options are invoked
  # Nopha - no phase calibration, since it will destroy the "reference frame" of the satellite, and can produce positioning errors
  # Noflag - don't flag data, since we assume that is good in the cal is good on the satellite
  # Autoamp - do an amp-only self-cal, which should reduce the residual fitting errors of the source
  # SEFD - use the system temps to weight the data, should downweight antennas with possible calibration errors
  # savedata - for use when grabbing the chi values
  imageLog = `newautomap.csh vis=#{visFile} select="time("#{frameTimes[0]},#{frameTimes[1]}")" options=nopha,noflag,autoamp,sefd,savedata outdir=#{wd}/maps`
  return imageLog # returns the image log for possible debugging
end

# Fits the brightest point source in the field of view
def fitImage (imageFile)
  fitRA = "0"
  fitDec = "0"
  fitErr = ["0","0"]
  # Find the source peak first, which gives you a smaller region over which to fit your point source (leading to smaller residual errors)
  sourcePeak = `maxfit in="#{imageFile}" | grep "Fitted pixel" | head -n 1 | tr '(),' '   ' | awk '{print $4,$5}'`
  sourceBox = [sourcePeak.split[0].to_f-50,sourcePeak.split[1].to_f-50,sourcePeak.split[0].to_f+50,sourcePeak.split[1].to_f+50]
  fitResults = `imfit in=#{imageFile} object=point region=box"(#{sourceBox[0]},#{sourceBox[1]},#{sourceBox[2]},#{sourceBox[3]})"` # Fit your point source
  fitResults.split("\n").each do |line|
    if line["Right Ascension"]
      fitRA = line.split(" ")[2]
    elsif line["Declination"]
      fitDec = line.split(" ")[1]
    elsif line["Positional errors"]
      fitErr = line.split(" ")[3,2]
    end
  end
  return [fitRA,fitDec,fitErr].flatten # return RA of target, Dec of target, and fitting error RA and Dec of target
end

# Gets the J2000 RA/Dec out of a MIRIAD vis or image file
def getRADec(miriadFile)
  fileRA = "0"
  fileDec = "0"
  if File.exist?(miriadFile + "/image")
    prthdOutput = `prthd in=#{miriadFile}`
    prthdOutput.split("\n").each do |line|
      if line["RA-"]
        fileRA = line.split(" ")[2]
      elsif line["DEC-"]
        fileDec = line.split(" ")[2]
      end
    end
  elsif File.exist?(miriadFile + "/visdata")
    prthdOutput = `prthd in=#{miriadFile}`
    prthdOutput.split("\n").each do |line|
      if line["J2000    Source"]
        fileRA = line.split(" ")[3]
        fileDec = line.split(" ")[5]
      end
    end
  end
  return [fileRA,fileDec]
end

# Gets chi out of a MIRIAD vis file
def getChi(miriadFile)
  chi = "0"
  if File.exist?(miriadFile + "/visdata")
    chi = `uvcheck vis=#{miriadFile} var=chi | grep Average | tr '=' ' '`.split(" ")[1]
    return chi
  end
end

def getEVector(miriadFile)
  eVector = "0"
  if File.exist?(miriadFile + "/visdata")
    if `uvlist vis=#{miriadFile} options=var,full`["evector"]
      eVector = `uvcheck vis=#{miriadFile} var=evector | grep Average | tr '=' ' ' | awk '{print $2*1}'`.chomp
    end
    return eVector
  end
end

# Rotates the RADec offset found by imfit and rotates it to the ephem position
def rotateRADectoAzEl(raCenter,decCenter,raOff,decOff,antChi,antAz,antEl)
  raCenter = raCenter.split(pattern=":") # if in HH:MM:SS format, convert
  raCenter = raCenter[0].to_f+raCenter[1].to_f/60+raCenter[2].to_f/3600
  raCenter *= 15
  decCenter = decCenter.split(pattern=":") # if in HH:MM:SS format, convert
  if decCenter[0].to_f > 0 # Correct for HMS -> Decimal conversion if dec < 0
    decCenter = decCenter[0].to_f+decCenter[1].to_f/60+decCenter[2].to_f/3600
  else
    decCenter = decCenter[0].to_f-decCenter[1].to_f/60-decCenter[2].to_f/3600
  end  
  raOff = raOff.split(pattern=":") # if in HH:MM:SS format, convert
  raOff = raOff[0].to_f+raOff[1].to_f/60+raOff[2].to_f/3600
  raOff *= 15
  decOff = decOff.split(pattern=":") # if in HH:MM:SS format, convert
  if decOff[0].to_f > 0 # Correct for HMS -> Decimal conversion if dec < 0
    decOff = decOff[0].to_f+decOff[1].to_f/60+decOff[2].to_f/3600
  else
    decOff = decOff[0].to_f-decOff[1].to_f/60-decOff[2].to_f/3600
  end
  
  antChi = (antChi.to_f)*180/PI # Assume chi is in radians (MIRIAD default)
  antAz = antAz.to_f
  antEl = antEl.to_f

  x = zRotation(raOff,decOff,raCenter) # Rotate to image field center
  x = yRotation(x[0],x[1],-decCenter) # Rotate to image field center
  x[0] *= -1 # Correct for RA being CCW, versus Az being CW
  x = xRotation(x[0],x[1],antChi) # Rotate offset for chi
  offsetsPrime = x
  x = yRotation(x[0],x[1],antEl) # Rotate to antenna elevation
  x = zRotation(x[0],x[1],-antAz) # Rotate to antenna azimuth
  azelPrime = x
  x[0] = (x[0]+360.0)%360 # Force az > 0
  return [offsetsPrime,azelPrime].flatten # Return offAz, offEl, newAz, newEl
end

# Here is where the main script starts
executeAndLog(">>Start astrolabe.rb", false);
visFile = ARGV[0]
lineSelection = ARGV[1]
ephemFile = ARGV[2]
resultsFile = ARGV[3]
wd = `mktemp -d SSA2XXXXX`.chomp

ephemStart = IO.readlines(ephemFile)[0].split[0].to_f
ephemEnd = IO.readlines(ephemFile)[-1].split[0].to_f

ephemStart /= 10**((log(ephemStart)/log(10)).floor-9)
ephemEnd /= 10**((log(ephemEnd)/log(10)).floor-9)

puts "Calculating frame times..."
executeAndLog("Calculating frame times...", false);
dumpTimes = grabDumpTimes(visFile) # Grab the dump times
puts "Calculating frame widths..."
frameTimes = deriveFrameTimes(dumpTimes,10,ephemStart,ephemEnd) # Calculate what the time ranges should be for each image frame
executeAndLog("Calculating frame widths...", false);

if frameTimes.nitems == 0
  puts "FATAL ERROR: #{ephemFile} times do match up with those in #{visFile}"
  `rm -rf #{wd}`
  exit
end

puts "Extracting relevant data..." # Excise the relevant data (i.e. only those channels that we are interested in)
executeAndLog("Extracting relevant data...", false);
extractCheck = `newautomap.csh vis="#{visFile}" mode=skip outdir=#{wd}/data options=savedata,sefd interval=0 cleanlim=50 #{lineSelection}`

if File.exist?(wd + "/data") == false
  puts "FATAL ERROR: #{visFile} has no usable data for the channel range specified"
  `rm -rf #{wd}`
  exit
end

sourceName = extractCheck.split(' ')[1].chop.chop.chop # Second "word" that newautomap spits out is the source name
extractFiles = `du #{wd}/data/#{sourceName}.1.* | awk '{printf "%s,",$2}'` # Look for files matching what newautomap would produce

idx = 1
File.open(wd + "/results", 'a') {|f| f.write("Time(UTCSec) ActualAz ActualEl EphemAz EphemEl OffsetXEl OffsetEl Chi FitErrRA FitErrDec MirTime\n")}
frameTimes.each do |currentFrame| # For each time frame, use newautomap to image
  startTimeStamp = Time.now.to_i
  print "Imaging frame #{idx} of #{frameTimes.nitems}..."
  executeAndLog("Imaging frame #{idx} of #{frameTimes.nitems}...", false);

  STDOUT.flush
  imageCheck = imageFrame(extractFiles,currentFrame,wd)
  if File.exist?(wd + "/maps/" + sourceName + ".cm") # Check to see that imaging was successfully completed
    posFit = fitImage("#{wd}/maps/#{sourceName}.cm") # Fit a point source on the image
    if (posFit[0] == "0" || posFit[1] == "0" || posFit[2] == "0" || posFit[3] == "0")    
      puts "FAILED! (Bad fit)"
    else
      fieldRADec = getRADec(wd + "/maps/" + sourceName + ".cm") # get the RADec of the image
      fieldChi = getChi(`du #{wd}/maps/#{sourceName}.*.* | head -n 1 | awk '{printf "%s",$2}'`) # Get Chi from the visibilities
      fieldEVector = getEVector(`du #{wd}/maps/#{sourceName}.*.* | head -n 1 | awk '{printf "%s",$2}'`)
      antAzEl = ephemSpline(ephemFile,currentFrame[2]) # Calculate the azel at that time
      fieldChi = fieldChi.to_f - fieldEVector.to_f
      # raCenter,decCenter,raOff,decOff,antChi,antAz,antEl
      sourceAzEl = rotateRADectoAzEl(fieldRADec[0],fieldRADec[1],posFit[0],posFit[1],fieldChi,antAzEl[0],antAzEl[1]) # Caluclate the total offsets
      puts "success! Done in #{Time.now.to_i - startTimeStamp} sec, offset is #{(sourceAzEl[0]*3600.0).round}\" x #{(sourceAzEl[1]*3600).round}\""
      File.open(wd + "/results", 'a') {|f| f.write("#{currentFrame[2]} #{sourceAzEl[2]} #{sourceAzEl[3]} #{antAzEl[0]} #{antAzEl[1]} #{sourceAzEl[0]} #{sourceAzEl[1]} #{fieldChi} #{posFit[2]} #{posFit[3]} #{currentFrame[3]}\n")} # write results to file
    end
  else
    puts "FAILED! (No image)" # If no image, go on to the next time frame
  end
  idx += 1
end

FileUtils::mv(wd + "/results", resultsFile)

puts "Done!"
puts ""
puts "Imaging of #{sourceName} successfully completed, results have been written to #{resultsFile}."

executeAndLog(">>Finish astrolabe.rb", false);

`rm -rf #{wd}`
  
