#! /usr/bin/env python
"""= multiflag2 - Apply many kinds of flags to UV data.
& pkgw
: calibration
+
 This task applies precomputed flagging commands to UV data files. The
 flagging commands are stored in "specification" files which are read
 in and converted into flagging commands. The current implementation
 applies the flags by invoking the UVFLAG task repeatedly; in the
 future, the flags will be applied internally in one pass, resulting
 in extremely fast flagging operation. (The task name MULTIFLAG is
 reserved for the fast implementation.)

 The data being flagged MUST share certain properties: sky frequency
 and ATA correlator half. This is a technical limitation as well as an
 optimization. Further optimizations can be made if the input data are
 all of the same polarization. The specification files can specify
 that certain flagging operations only apply to data with with certain
 sky frequencies, ATA correlator halves, and/or polarizations, and the
 flagging commands that would not apply to the data currently being
 processed are skipped. For instance, a specification file might
 contain the lines

   pol=xx ant=3
   pol=yy ant=17
   freq=1430 chan=7,600
   freq=1430 pol=yy ant=4
   freq=2240 chan=10,200

 Running the task as

   multiflag2 freq=1430 pol=xx ...

 would cause the first and third lines to have their flagging commands
 applied, but not the other lines.

 The specification file format is that of a sequence of lines. Empty
 lines or those beginning with a hash sign (#) are ignored. Each line
 defines a selection criterion: if a visibility record, or a portion
 of a record, matches the criterion, it is flagged. (MULTIFLAG2 does
 not have facilities for unflagging data.) Put another way, a
 visibility record, or a portion of a record, remains unflagged if and
 only if it matches no lines.

 A line is composed of a sequence of space-separated clauses. A
 visibility record matches a line if and only if it matches all of the
 clauses in the line. The individual clauses match records, or
 portions thereof, based on various criteria. The clauses are
 described below. They are similar to the commands used with the
 "select" keyword, but the syntax is intentionally different because
 the semantics are also different.

   ant=ANT1[,ANT2[,ANT3...]]

     The 'ant' clause matches those visibility records where one of
     the antennas in the baseline is one of the listed antennas.

   bl=ANT1-ANT2[,ANT3-ANT4[,ANT5-ANT6...]]

     The 'bl' clause matches those visibility records having a
     baseline matching one of the baselines listed: ANT1-ANT2,
     ANT3-ANT4, etc.

   pol=POL1[,POL2[,POL3...]]

     The 'pol' clause matches any visibility record having a
     one of the polarization codes listed in the clause.

   chan=LEN1,START1[;LEN2,START2[;LEN3,START3...]]

     The 'chan' clause matches the specified channels in every
     visibility record. Each LEN,START pair in the channel
     specification selects LEN channels starting at START. (This is
     the same syntax as the "chan" form of the "line=" keyword.)

   atahalf=H

     The 'atahalf' clause matches all records in those datasets which
     are associated with the specified ATA correlator half. The
     correlator half of the input datasets is known to MULTIFLAG2 by
     the "half=" keyword.

   freq=FFFF

     The 'freq' clause matches all records in those datasets which have
     the specified sky frequency in MHz. The sky frequency of the
     input datasets is specified with the "freq=" keyword to
     MULTIFLAG2 and is NOT verified in the actual data.

   time=TIME1,TIME2

     The 'time' clause matches those records which have timestamps
     falling between TIME1 and TIME2. An empty string for TIME1 or
     TIME2 is taken to indicate an indefinite lower or upper bound.

   uvrange=UVMIN,UVMAX

     The 'uvrange' clauses matches those records which have a U,V
     position between UVMIN and UVMAX, as measured in kilolambda. An
     empty string for UVMIN or UVMAX is taken to indicate an
     indefinite lower or upper bound.

   shadow=SIZE

     The 'shadow' clause matches those records which would be affected
     by shadowing of an antenna of size SIZE, as measured in meters.

   auto
   
     The 'auto' clause matches all autocorrelation records.

   cross

     The 'cross' clause matches all cross-correlation records.

< vis
 This task accepts multiple input files and flags all of them.

@ spec
 A comma-separated list of flag specification files. The flags
 described in all of the files are applied to all of the UV input files.
 
@ freq
 The sky frequency of the input data in MHz. This keyword MUST be
 specified. However, if there are no "freq=NNNN" conditions in the
 specification files, the value given is irrelevant. Any "freq=NNNN"
 conditions in the specification files will be ignored if NNNN is not
 the same as the value specified for this keyword.

@ half
 The ATA correlator half of the input data: either 0, 1, or 2. Zero
 indicates a glued-together dataset or one not from the ATA. If there
 are "atahalf=N" conditions in the specification files, those
 conditions will be ignored if N is not the same as the value
 specified for this keyword. Default is 0.

@ pol
 The polarization of the input data. If specified, it is assumed
 that the data all have one polarization, and any conditions in the
 specifications that rely on different polarizations will be
 ignored. If unspecified, it is assumed that the data contain multiple
 polarizations, and all polarization-specific conditions will be applied,
 with "select=pol()" clauses to make them apply only to the relevant
 data.
 
--
"""

import sys
from mirexec import TaskUVFlag

# Conditions are:
#
# ant bl pol auto cross chan atahalf freq time

class MultiFlag2 (object):
    def __init__ (self, freq, half, pol):
        self.freq = freq
        self.half = half
        self.pol = pol
        self.lines = []
        
    # Read in the conditions
    #
    # The basic format is line-oriented
    # If an entry matches a line, it is flagged.
    # An entry matches a line if it matches *all* of the conditions in the line
    # A condition in a line just looks like "attr=match"
    # Conditions are separated by spaces
    # If there are multiple match values, a condition is matched if *any* of those
    # values are matched
    # So the overall logical flow is
    #  flag if [match any line]
    #  match line if [match every condition]
    #  match condition if [match any value]
    #
    # E.g. ...
    #
    # ant=24 pol=xx
    # bl=1-4 cross
    # pol=xx chan=128,1

    def loadSpec (self, fname):
        for l in file (fname, 'r'):
            bits = l.strip ().split ()

            if len (bits) < 1: continue
            if bits[0][0] == '#': continue

            shared = []
            multi = None
            lmulti = None
            ignore = False
            
            for b in bits:
                split = b.split ('=', 2)
                if len (split) == 1: cond, arg = split[0], None
                else: cond, arg = split

                if cond == 'auto': shared.append ('auto')
                elif cond == 'cross': shared.append ('-auto')
                elif cond == 'ant': shared.append ('ant(%s)' % arg)
                elif cond == 'bl':
                    assert multi is None
                    multi = [('ant(%s)(%s)' % tuple (x.split ('-'))) for x in arg.split (',')]
                elif cond == 'pol':
                    if self.pol is None: shared.append ('pol(%s)' % arg)
                    else:
                        ignore = ignore or self.pol.lower () not in \
                                 (x.lower () for x in arg.split (','))
                elif cond == 'chan':
                    assert lmulti is None
                    lmulti = ['chan,%s' % x for x in arg.split (';')]
                elif cond == 'atahalf':
                    ignore = ignore or self.half != int (arg)
                elif cond == 'freq':
                    ignore = ignore or self.freq != int (arg)
                elif cond == 'time':
                    shared.append ('time(%s)' % arg)
                elif cond == 'uvrange':
                    shared.append ('uvrange(%s)' % arg)
                elif cond == 'shadow':
                    shared.append ('shadow(%s)' % arg)
                else: assert False, 'Unknown condition'

            if ignore: continue

            if len (shared) == 0:
                if multi is not None: selects = multi
                else: selects = [None]
            else:
                selects = [','.join (shared)]

                if multi is not None:
                    selects = [selects[0] + ',' + x for x in multi]

            if lmulti is not None:
                for x in selects:
                    for y in lmulti:
                        self.lines.append ((x, y))
            else:
                for x in selects:
                    self.lines.append ((x, None))

    def applyDataSet (self, dset, banner):
        t = TaskUVFlag (vis=dset, flagval='f')
        
        for select, line in self.lines:
            t.select = select
            t.line = line
            t.run ()

def task ():
    from mirtask import keys
    from miriad import VisData, basicTrace

    basicTrace ()
    
    banner = 'MULTIFLAG2 (Python): Apply groups of flags by calling UVFLAG'
    print banner

    keys.keyword ('spec', 'f', None, 128)
    keys.keyword ('vis', 'f', None, 128)
    keys.keyword ('freq', 'd', -1)
    keys.keyword ('half', 'i', 0)
    keys.keyword ('pol', 'a', ' ')
    opts = keys.process ()

    if opts.pol == ' ': opts.pol = None
    
    if len (opts.spec) < 1:
        print >>sys.stderr, 'Error: must give at least one "spec" filename'
        sys.exit (1)

    if opts.freq < 0:
        print >>sys.stderr, 'Error: must specify "freq" keyword.'
        sys.exit (1)
    
    mf = MultiFlag2 (opts.freq, opts.half, opts.pol)
    
    for fname in opts.spec: mf.loadSpec (fname)

    print 'Parsed conditions from %d file(s).' % (len (opts.spec))

    for vf in opts.vis:
        mf.applyDataSet (VisData (vf), 'unused')

if __name__ == '__main__':
    task ()
    sys.exit (0)
