#!/usr/bin/env python
"""
claw, 14may2011
Script to process PoCo candidate pkl files.
Compiles filenames, consolidates, optionally plots data from them.
"""

import sys, os, string
import pocovis, pickle

#process_pickle(file, pathin=pathin, mode=mode)


def mininmal_list(directory):
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

def consolidate(list_unique):
    """Takes unique set of file name stubs and consolidates pickles to one per nint,nskip.
    Should have no effect on "ph" pickle files, but groups "im" and "uv" to look like "ph".
    """

    list = os.listdir(directory)

    # test input list for contents
    file = list_unique[0] + '.pkl'
    pkl = pickle.load(open(file))
    if len(pkl[3]) > 1:
        print 'pickle is bad! must consolidate!'

        # find multiples of single file and group into one pickle
        for name in list:
            if ((string.find(name, 'poco') > -1) & (string.find(name, '.pkl') > -1)):  # is it actually a good pickle file?
                pass
