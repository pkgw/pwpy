import time,datetime
import sys

fn = sys.argv[1]
print "Parsing:", fn
parts = fn.split('_')
year = int(parts[1])
doy = int(parts[2])
hms = parts[3]
h = int(hms[:2])
m = int(hms[2:4])
s = int(hms[4:6])

st = time.strptime("%d_%d_%d_%d_%d" % ( year, doy, h, m, s), "%Y_%j_%H_%M_%S")
print st
print time.strftime("%y%b%d:%H:%M:%S",st)
