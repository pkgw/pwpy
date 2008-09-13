#! /usr/bin/env python
#
# Filter a list file: print only the filenames in the
# list that have the specified value of the specified
# variables
#
# Arguments: $0 [listfile] [var1=val1] [var2=val2...]

from sys import argv

assert len (argv) > 1

listfn = argv[1]

conds = {}

for tok in argv[2:]:
    var, val = tok.split ('=', 1)
    conds[var] = val

for vis in file (listfn, 'r'):
    vis = vis.strip ()

    match = True
    
    for var, wantval in conds.iteritems ():
        varfn = vis + '/ws-' + var
        thisval = file (varfn, 'r').readline ().strip ()

        if thisval != wantval:
            match = False
            break

    if match: print vis

