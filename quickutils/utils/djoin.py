## Copyright 2012 Peter Williams
## This work is dedicated to the public domain.
##
def djoin (*args):
##<
## 'dotless' join, for nicer paths
##>
    from os.path import join
    i, alen = 0, len (args)
    while i < alen and (args[i] == '' or args[i] == '.'):
        i += 1
    if i == alen:
        return '.'
    return join (*args[i:])
