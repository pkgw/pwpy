# A little script using miriad python to fit and visualize a gaussian in a set of images
# claw 10mar09

import miriad, mirexec
import glob, string

def main():
    # get files in order
    files = glob.glob('im-0.2s/*rm')
    filesort = natsorted(files)

    peak = []
    bmaj = []
    bmin = []

    # loop over all images
    for file in filesort:
        # import image data
        im = miriad.ImData(file)
        stdout, stderr = mirexec.TaskImFit(in_=im, object='gaussian').snarf()

#        print stdout
        
        # parse output
        for line in stdout:
            if string.find(line, 'Peak') >= 0:
                if len(line.split('   ')) > 8:
                    sp = (float(line.split('   ')[6]), float(line.split('   ')[8]))   # tuple of peak and error
                    peak.append(sp)
                else:
                    sp = (float(line.split('   ')[6]),-1)   # tuple of peak and error
                    peak.append(sp)
            elif string.find(line, 'Major axis') >= 0:
                if len(line.split(' ')) > 16:
                       major = (float(line.split(' ')[13]), float(line.split(' ')[16]))   # tuple of bmaj and error
                       bmaj.append(major)
                else:
                       major = (float(line.split(' ')[13]),-1)   # tuple of bmaj and error
                       bmaj.append(major)
            elif string.find(line, 'Minor axis') >= 0:
                if len(line.split(' ')) > 16:
                       minor = (float(line.split(' ')[13]), float(line.split(' ')[16]))   # tuple of bmin and error
                       bmin.append(minor)
                else:
                       minor = (float(line.split(' ')[13]),-1)   # tuple of bmin and error
                       bmin.append(minor)
                

        print 'Fit %s' % (file)
        print sp, major, minor
    return peak, bmaj, bmin


# "natural" sorting of string list
def try_int(s):
    "Convert to integer if possible."
    try: return int(s)
    except: return s

def natsort_key(s):
    "Used internally to get a tuple by which s is sorted."
    import re
    return map(try_int, re.findall(r'(\d+|\D+)', s))

def natcmp(a, b):
    "Natural string comparison, case sensitive."
    return cmp(natsort_key(a), natsort_key(b))

def natcasecmp(a, b):
    "Natural string comparison, ignores case."
    return natcmp(a.lower(), b.lower())

def natsort(seq, cmp=natcmp):
    "In-place natural string sort."
    seq.sort(cmp)
    
def natsorted(seq, cmp=natcmp):
    "Returns a copy of seq, sorted by natural string sort."
    import copy
    temp = copy.copy(seq)
    natsort(temp, cmp)
    return temp

if __name__ == '__main__':
    main()

