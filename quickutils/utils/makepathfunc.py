## Copyright 2012 Peter Williams
## This work is dedicated to the public domain.
##
def makepathfunc (*baseparts):
##<
## Return a function that joins paths onto some base directory.
##>
    from os.path import join
    base = join (*baseparts)
    def pathfunc (*args):
        return join (base, *args)
    return pathfunc
