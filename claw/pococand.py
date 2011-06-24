#!/usr/bin/env python
"""
claw, 14may2011
Script to process PoCo candidate pkl files.
Compiles filenames, consolidates, optionally plots data from them.
"""

import sys, os, string, pickle
from pocovis import *

#process_pickle(file, pathin=pathin, mode=mode)


def minimal_list(directory):
    """Function takes directory with pickles and puts cands with separate dmt0 into same pickle.
    Returns reduced set of pickle file names.
    """

    list = os.listdir(directory)
    
    list_split = []
    for name in list:
        if ((string.find(name, 'poco') > -1) & (string.find(name, '.pkl') > -1)):
            if len(name.split('-')) > 1:
                list_split.append(name.split('-')[0])
            else:
                list_split.append(name[:-4])

    list_unique = []
    for name in list_split:
        if name in list_unique:
            continue
        else:
            list_unique.append(name)

    return list_unique

def display(directory, start=0, stop=0):
    """Takes directory of pickle files and displays dm tracks
    start,end give index of range of file list to display. start=end=0 means use all.
    """

    interactive = 0
    mode = 'spec'
    datadir = 'data/'
    bgwindow = 10
    list0 = os.listdir(directory)
    list = []

    for filename in list0:   # build good list of pickle files
        if ((string.find(filename, 'poco') > -1) & (string.find(filename, '.pkl') > -1)):  # is it actually a good pickle file?
            list.append(filename)

    if string.find(list[0], '-') > -1:   # determine if all candidates are broken up by integration
        broken = 1
    else:
        broken = 0

    if (start == 0) & (stop == 0):
        start = 0
        stop = len(list0)
    else:
        start = int(start)
        stop = int(stop)

    # find multiples of single file and group into one pickle
    firstpass = 1
    for j in range(start, stop):
        filename = list[j]
        print
        print 'Starting number ', j, filename
        file = open(directory + filename, 'rb')
        dump = pickle.load(file)
        name0 = dump[0]
        nints0 = dump[2]
        nintskip0 = dump[1]
        dmbinarr0 = dump[3]
        dmarr0 = dump[4]
        tbinarr0 = dump[5]
        snrarr0 = dump[6]

        name = name0
        nints = nints0
        nintskip = nintskip0
        dmarr = dmarr0
        if firstpass:  # don't overwrite if iterating over broken files
            dmbinarr = dmbinarr0
            tbinarr = tbinarr0
            snrarr = snrarr0

        if broken and len(list) > j+1:   # test append, if list long enough
            if (string.split(filename, '-')[0] == string.split(list[j+1], '-')[0]):
                print 'next file has same data, nskip. merging...'
                file2 = open(directory + list[j+1], 'rb')
                dump = pickle.load(file2)
                dmbinarr = n.concatenate( (dmbinarr, dump[3]) )
                tbinarr = n.concatenate( (tbinarr, dump[5]) )
                snrarr = n.concatenate( (snrarr, dump[6]) )
                firstpass = 0
                continue
            else:
                firstpass = 1

        if snrarr[0] <= 1:  # reim mode has p-values for normality, which should be small when there is a pulse
            peaktrial = n.where(snrarr == min(snrarr))[0][0]
        else:
            peaktrial = n.where(snrarr == max(snrarr))[0][0]

        print 'Loaded pickle file for %s plot of %s' % (mode, name)
        print 'Has peaks for DM = ', dmarr, ' with tbin = ', tbinarr, 'sig = ', snrarr
        print 'Grabbing %d ints at %d' % (nints, nintskip)

        pv = poco(datadir + name, nints=nints, nskip=nintskip)
        pv.prep()

        p.figure(1)
        p.clf()
        track = []
        for i in range(len(dmbinarr)):
            track.append(pv.dmtrack(dm=pv.dmarr[dmbinarr[i]], t0=pv.reltime[tbinarr[i]], show=0))
            p.plot(pv.reltime[track[i][0]], track[i][1], 'w*')

        pv.spec(save=int(not(interactive)))
        if interactive:
            print 'Showing tracks from file.'
            try:
                text = raw_input ( 'Which trials to fit? (0-based, comma-delimited; default is peaksnr)' )
                cands = n.cast['int16'](n.array(text.split(',')))
            except:
                cands = n.array([peaktrial])
        else:
            cands = []
            snrref = snrarr[0]
            for tint in range(1, len(tbinarr)):
                if tbinarr[tint] == tbinarr[tint - 1] + 1:
                    if snrarr[tint] > snrref:
                        snrref = snrarr[tint]
                else:
                    cands.append(n.where(snrref == snrarr)[0][0])
                    snrref = snrarr[tint]
            cands.append(n.where(snrref == snrarr)[0][0])

        print 'Fitting tracks for ', cands
        for i in cands:
            status = pv.writetrack2(dmbinarr[i], tbinarr[i], tshift=0, bgwindow=bgwindow)
            if status:
                newfile = string.join(pv.file.split('.')[:-1]) + '.' + str(pv.nskip/pv.nbl) + '-' + 'dm' + str(dmbinarr[i]) + 't' + str(tbinarr[i]) + '.mir'
                print 'Loading file', newfile
                pv2 = poco(newfile, nints=1)
                pv2.prep()
                p.figure(2)
                p.clf()
                pv2.fitspec(obsrms=0, save=int(not(interactive)))
                if interactive:
                    text = raw_input( 'Hit a key to proceed.')
                shutil.rmtree(newfile, ignore_errors=True)


if __name__ == '__main__':
#    display('crab_fixdm_ph/', start=30, stop=40)
    display('b0329_fixdm_im2/', start=0, stop=0)

