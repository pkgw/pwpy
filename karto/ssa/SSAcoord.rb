#! /usr/bin/env ruby

require 'matrix'
require 'mathn'
include Math

def xRotation(long,lat,theta)
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

def yRotation(long,lat,theta)
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

def zRotation(long,lat,theta)
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

raCenter = ARGV[0].split(pattern=":")
raCenter = raCenter[0].to_f+raCenter[1].to_f/60+raCenter[2].to_f/3600
raCenter *= 15
decCenter = ARGV[1].split(pattern=":")
if decCenter[0].to_f > 0
  decCenter = decCenter[0].to_f+decCenter[1].to_f/60+decCenter[2].to_f/3600
else
  decCenter = decCenter[0].to_f-decCenter[1].to_f/60-decCenter[2].to_f/3600
end

raOff = ARGV[2].split(pattern=":")
raOff = raOff[0].to_f+raOff[1].to_f/60+raOff[2].to_f/3600
raOff *= 15
decOff = ARGV[3].split(pattern=":")
if decOff[0].to_f > 0
  decOff = decOff[0].to_f+decOff[1].to_f/60+decOff[2].to_f/3600
else
  decOff = decOff[0].to_f-decOff[1].to_f/60-decOff[2].to_f/3600
end

chi = (ARGV[4].to_f)*(ARGV[7] == "rad" ? 180/PI : 1.0)
az = ARGV[5].to_f
el = ARGV[6].to_f

x = zRotation(raOff,decOff,raCenter)
x = yRotation(x[0],x[1],-decCenter)
x[0] *= -1
x = xRotation(x[0],x[1],chi)
#puts "#{x[0]} #{x[1]}"
x = yRotation(x[0],x[1],el)
x = zRotation(x[0],x[1],-az)
puts "#{(x[0]+360)%360} #{x[1]}"
