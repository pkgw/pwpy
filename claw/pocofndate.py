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

subintsperchunk = int(parts[6])
segment = parts[7][0:4]
offset = int(segment) * 128*128/208e6 * subintsperchunk * 131072
print 'Offset from first int of %.3f s' % (offset)
dt = datetime.timedelta(seconds=offset)

st = time.strptime("%d_%d_%d_%d_%d" % ( year, doy, h, m, s), "%Y_%j_%H_%M_%S")
stoff = datetime.datetime(*st[:6]) + dt


print 'First segment start time:  %s' % (time.strftime("%y%b%d:%H:%M:%S",st))
print 'Segment %d start time:  %s.%.4s' % (int(segment), stoff.strftime("%y%b%d:%H:%M:%S"), stoff.microsecond)
