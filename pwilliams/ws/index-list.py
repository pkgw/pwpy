#! /usr/bin/env python
#
# Index a list file: print out all of the values
# that the specified variable takes on in the files
# given in the list. The list of files to consider
# can be filtered with var=val clauses after the
# first two argments.

from sys import argv

# $0 listname keyname [var1=val1] [var2=val2...]
assert len (argv) > 2

listfn = argv[1]
idxvar = argv[2]

filters = {}
for tok in argv[3:]:
    var, val = tok.split ('=', 1)
    filters[var] = val

vals = set ()

# Get variable values from vises in list

for vis in file (listfn, 'r'):
    vis = vis.strip ()

    # Possibly filter out this item.
    
    match = True
    
    for var, wantval in filters.iteritems ():
        varfn = vis + '/ws-' + var
        thisval = file (varfn, 'r').readline ().strip ()
        if thisval != wantval:
            match = False
            break

    if not match: continue

    # This one matches our filters, hooray.
    
    varfn = vis + '/ws-' + idxvar
    vals.add (file (varfn, 'r').readline ().strip ())

# Print out all variable values

for v in sorted (vals): print v
