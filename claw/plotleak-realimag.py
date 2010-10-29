#!/usr/bin/env python

# claw, 7may09
#
# Script to plot complex leakages for two different datasets.
# Assumes there are 8 frequency chunks.  File naming convention hardwired;  should change accordingly.
# Run as "python plotleak-realimag.py"

import asciidata, pylab, numpy

def run():
    # params for possible customization
    type = 'overlap'
    plottwo = 1

    a = []; a2 = []
    p = []; p2 = []
    print 'now building leak plot 1'
    for i in range(1,17):
        # specify ascii files output by 'split-cal-leak.csh'
        try:
            a.append(asciidata.AsciiData ('/indirect/big_scr2/claw/data/ata/polcal/oct2010/mosfxc-3c286.uvaver.uvredo-leakamp%d.txt' % i))
            p.append(asciidata.AsciiData ('/indirect/big_scr2/claw/data/ata/polcal/oct2010/mosfxc-3c286.uvaver.uvredo-leakphase%d.txt' % i))
        except:
            print 'skipping %d' % (i)
    print 'now building leak plot 2'
    if plottwo:
        for i in range(1,17):
            try:
                a2.append(asciidata.AsciiData ('/indirect/big_scr2/claw/data/ata/hex14-polcal-sep7/oct2010/hexa-3c286-hp0-1430-leakamp%d.txt' % i))
                p2.append(asciidata.AsciiData ('/indirect/big_scr2/claw/data/ata/hex14-polcal-sep7/oct2010/hexa-3c286-hp0-1430-leakphase%d.txt' % i))
#                a2.append(asciidata.AsciiData ('/indirect/big_scr2/claw/data/ata/polcal2/oct2010/mosfxc-3c286.uvaver.uvcal.uvredo-leakamp%d.txt' % i))
#                p2.append(asciidata.AsciiData ('/indirect/big_scr2/claw/data/ata/polcal2/oct2010/mosfxc-3c286.uvaver.uvcal.uvredo-leakphase%d.txt' % i))
            except:
                print 'skipping %d' % (i)

    nants = len(a[0][0])
    print '%d antennas...' % (nants)
    antnum = [1,4,7,10,13,16,19,22,25,28,31,34,37,40,43,2,5,8,11,14,17,20,23,26,29,32,35,38,41,3,6,9,12,15,18,21,24,27,30,33,36,39,42]  # hack for how rows messed up by 'cut' in 'split-cal-leak.csh'

    print numpy.shape(a)
    if plottwo:
        print numpy.shape(a2)

    # group for data set 1
    # original phase and amplitude
    # assuming 7 frequency chunks
#    px = numpy.array([p[0].columns[0],p[1].columns[0],p[2].columns[0],p[3].columns[0],p[4].columns[0],p[5].columns[0],p[6].columns[0],p[7].columns[0]])
#    ax = numpy.array([a[0].columns[0],a[1].columns[0],a[2].columns[0],a[3].columns[0],a[4].columns[0],a[5].columns[0],a[6].columns[0],a[7].columns[0]])
#    py = numpy.array([p[0].columns[1],p[1].columns[1],p[2].columns[1],p[3].columns[1],p[4].columns[1],p[5].columns[1],p[6].columns[1],p[7].columns[1]])
#    ay = numpy.array([a[0].columns[1],a[1].columns[1],a[2].columns[1],a[3].columns[1],a[4].columns[1],a[5].columns[1],a[6].columns[1],a[7].columns[1]])
# assuming 14 frequency chunks
#    px = numpy.array([p[0].columns[0],p[1].columns[0],p[2].columns[0],p[3].columns[0],p[4].columns[0],p[5].columns[0],p[6].columns[0],p[7].columns[0],p[8].columns[0],p[9].columns[0],p[10].columns[0],p[11].columns[0],p[12].columns[0],p[13].columns[0]])
#    ax = numpy.array([a[0].columns[0],a[1].columns[0],a[2].columns[0],a[3].columns[0],a[4].columns[0],a[5].columns[0],a[6].columns[0],a[7].columns[0],a[8].columns[0],a[9].columns[0],a[10].columns[0],a[11].columns[0],a[12].columns[0],a[13].columns[0]])
#    py = numpy.array([p[0].columns[1],p[1].columns[1],p[2].columns[1],p[3].columns[1],p[4].columns[1],p[5].columns[1],p[6].columns[1],p[7].columns[1],p[8].columns[1],p[9].columns[1],p[10].columns[1],p[11].columns[1],p[12].columns[1],p[13].columns[1]])
#    ay = numpy.array([a[0].columns[1],a[1].columns[1],a[2].columns[1],a[3].columns[1],a[4].columns[1],a[5].columns[1],a[6].columns[1],a[7].columns[1],a[8].columns[1],a[9].columns[1],a[10].columns[1],a[11].columns[1],a[12].columns[1],a[13].columns[1]])
# assuming 16 frequency chunks
    px = numpy.array([p[0].columns[0],p[1].columns[0],p[2].columns[0],p[3].columns[0],p[4].columns[0],p[5].columns[0],p[6].columns[0],p[7].columns[0],p[8].columns[0],p[9].columns[0],p[10].columns[0],p[11].columns[0],p[12].columns[0],p[13].columns[0],p[14].columns[0],p[15].columns[0]])
    ax = numpy.array([a[0].columns[0],a[1].columns[0],a[2].columns[0],a[3].columns[0],a[4].columns[0],a[5].columns[0],a[6].columns[0],a[7].columns[0],a[8].columns[0],a[9].columns[0],a[10].columns[0],a[11].columns[0],a[12].columns[0],a[13].columns[0],a[14].columns[0],a[15].columns[0]])
    py = numpy.array([p[0].columns[1],p[1].columns[1],p[2].columns[1],p[3].columns[1],p[4].columns[1],p[5].columns[1],p[6].columns[1],p[7].columns[1],p[8].columns[1],p[9].columns[1],p[10].columns[1],p[11].columns[1],p[12].columns[1],p[13].columns[1],p[14].columns[1],p[15].columns[1]])
    ay = numpy.array([a[0].columns[1],a[1].columns[1],a[2].columns[1],a[3].columns[1],a[4].columns[1],a[5].columns[1],a[6].columns[1],a[7].columns[1],a[8].columns[1],a[9].columns[1],a[10].columns[1],a[11].columns[1],a[12].columns[1],a[13].columns[1],a[14].columns[1],a[15].columns[1]])
# assuming 32 frequency chunks
#    px = numpy.array([p[0].columns[0],p[1].columns[0],p[2].columns[0],p[3].columns[0],p[4].columns[0],p[5].columns[0],p[6].columns[0],p[7].columns[0],p[8].columns[0],p[9].columns[0],p[10].columns[0],p[11].columns[0],p[12].columns[0],p[13].columns[0],p[14].columns[0],p[15].columns[0],p[16].columns[0],p[17].columns[0],p[18].columns[0],p[19].columns[0],p[20].columns[0],p[21].columns[0],p[22].columns[0],p[23].columns[0],p[24].columns[0],p[25].columns[0],p[26].columns[0],p[27].columns[0],p[28].columns[0],p[29].columns[0],p[30].columns[0],p[31].columns[0]])
#    ax = numpy.array([a[0].columns[0],a[1].columns[0],a[2].columns[0],a[3].columns[0],a[4].columns[0],a[5].columns[0],a[6].columns[0],a[7].columns[0],a[8].columns[0],a[9].columns[0],a[10].columns[0],a[11].columns[0],a[12].columns[0],a[13].columns[0],a[14].columns[0],a[15].columns[0],a[16].columns[0],a[17].columns[0],a[18].columns[0],a[19].columns[0],a[20].columns[0],a[21].columns[0],a[22].columns[0],a[23].columns[0],a[24].columns[0],a[25].columns[0],a[26].columns[0],a[27].columns[0],a[28].columns[0],a[29].columns[0],a[30].columns[0],a[31].columns[0]])
#    py = numpy.array([p[0].columns[1],p[1].columns[1],p[2].columns[1],p[3].columns[1],p[4].columns[1],p[5].columns[1],p[6].columns[1],p[7].columns[1],p[8].columns[1],p[9].columns[1],p[10].columns[1],p[11].columns[1],p[12].columns[1],p[13].columns[1],p[14].columns[1],p[15].columns[1],p[16].columns[1],p[17].columns[1],p[18].columns[1],p[19].columns[1],p[20].columns[1],p[21].columns[1],p[22].columns[1],p[23].columns[1],p[24].columns[1],p[25].columns[1],p[26].columns[1],p[27].columns[1],p[28].columns[1],p[29].columns[1],p[30].columns[1],p[31].columns[1]])
#    ay = numpy.array([a[0].columns[1],a[1].columns[1],a[2].columns[1],a[3].columns[1],a[4].columns[1],a[5].columns[1],a[6].columns[1],a[7].columns[1],a[8].columns[1],a[9].columns[1],a[10].columns[1],a[11].columns[1],a[12].columns[1],a[13].columns[1],a[14].columns[1],a[15].columns[1],a[16].columns[1],a[17].columns[1],a[18].columns[1],a[19].columns[1],a[20].columns[1],a[21].columns[1],a[22].columns[1],a[23].columns[1],a[24].columns[1],a[25].columns[1],a[26].columns[1],a[27].columns[1],a[28].columns[1],a[29].columns[1],a[30].columns[1],a[31].columns[1]])
# assuming 160 chunks
#    px = numpy.array([p[0].columns[0],p[1].columns[0],p[2].columns[0],p[3].columns[0],p[4].columns[0],p[5].columns[0],p[6].columns[0],p[7].columns[0],p[8].columns[0],p[9].columns[0],p[10].columns[0],p[11].columns[0],p[12].columns[0],p[13].columns[0],p[14].columns[0],p[15].columns[0],p[16].columns[0],p[17].columns[0],p[18].columns[0],p[19].columns[0],p[20].columns[0],p[21].columns[0],p[22].columns[0],p[23].columns[0],p[24].columns[0],p[25].columns[0],p[26].columns[0],p[27].columns[0],p[28].columns[0],p[29].columns[0],p[30].columns[0],p[31].columns[0],p[32].columns[0],p[33].columns[0],p[34].columns[0],p[35].columns[0],p[36].columns[0],p[37].columns[0],p[38].columns[0],p[39].columns[0],p[40].columns[0],p[41].columns[0],p[42].columns[0],p[43].columns[0],p[44].columns[0],p[45].columns[0],p[46].columns[0],p[47].columns[0],p[48].columns[0],p[49].columns[0],p[50].columns[0],p[51].columns[0],p[52].columns[0],p[53].columns[0],p[54].columns[0],p[55].columns[0],p[56].columns[0],p[57].columns[0],p[58].columns[0],p[59].columns[0],p[60].columns[0],p[61].columns[0],p[62].columns[0],p[63].columns[0],p[64].columns[0],p[65].columns[0],p[66].columns[0],p[67].columns[0],p[68].columns[0],p[69].columns[0],p[70].columns[0],p[71].columns[0],p[72].columns[0],p[72].columns[0],p[73].columns[0],p[74].columns[0],p[75].columns[0],p[76].columns[0],p[77].columns[0],p[78].columns[0],p[79].columns[0],p[80].columns[0],p[81].columns[0],p[82].columns[0],p[83].columns[0],p[84].columns[0],p[85].columns[0],p[86].columns[0],p[87].columns[0],p[88].columns[0],p[89].columns[0],p[90].columns[0],p[91].columns[0],p[92].columns[0],p[93].columns[0],p[94].columns[0],p[95].columns[0],p[96].columns[0],p[97].columns[0],p[98].columns[0],p[99].columns[0],p[100].columns[0],p[101].columns[0],p[102].columns[0],p[103].columns[0],p[104].columns[0],p[105].columns[0],p[106].columns[0],p[107].columns[0],p[108].columns[0],p[109].columns[0],p[110].columns[0],p[111].columns[0],p[112].columns[0],p[113].columns[0],p[114].columns[0],p[115].columns[0],p[116].columns[0],p[117].columns[0],p[118].columns[0],p[119].columns[0],p[120].columns[0],p[121].columns[0],p[122].columns[0],p[123].columns[0],p[124].columns[0],p[125].columns[0],p[126].columns[0]])
#    ax = numpy.array([a[0].columns[0],a[1].columns[0],a[2].columns[0],a[3].columns[0],a[4].columns[0],a[5].columns[0],a[6].columns[0],a[7].columns[0],a[8].columns[0],a[9].columns[0],a[10].columns[0],a[11].columns[0],a[12].columns[0],a[13].columns[0],a[14].columns[0],a[15].columns[0],a[16].columns[0],a[17].columns[0],a[18].columns[0],a[19].columns[0],a[20].columns[0],a[21].columns[0],a[22].columns[0],a[23].columns[0],a[24].columns[0],a[25].columns[0],a[26].columns[0],a[27].columns[0],a[28].columns[0],a[29].columns[0],a[30].columns[0],a[31].columns[0],a[32].columns[0],a[33].columns[0],a[34].columns[0],a[35].columns[0],a[36].columns[0],a[37].columns[0],a[38].columns[0],a[39].columns[0],a[40].columns[0],a[41].columns[0],a[42].columns[0],a[43].columns[0],a[44].columns[0],a[45].columns[0],a[46].columns[0],a[47].columns[0],a[48].columns[0],a[49].columns[0],a[50].columns[0],a[51].columns[0],a[52].columns[0],a[53].columns[0],a[54].columns[0],a[55].columns[0],a[56].columns[0],a[57].columns[0],a[58].columns[0],a[59].columns[0],a[60].columns[0],a[61].columns[0],a[62].columns[0],a[63].columns[0],a[64].columns[0],a[65].columns[0],a[66].columns[0],a[67].columns[0],a[68].columns[0],a[69].columns[0],a[70].columns[0],a[71].columns[0],a[72].columns[0],a[72].columns[0],a[73].columns[0],a[74].columns[0],a[75].columns[0],a[76].columns[0],a[77].columns[0],a[78].columns[0],a[79].columns[0],a[80].columns[0],a[81].columns[0],a[82].columns[0],a[83].columns[0],a[84].columns[0],a[85].columns[0],a[86].columns[0],a[87].columns[0],a[88].columns[0],a[89].columns[0],a[90].columns[0],a[91].columns[0],a[92].columns[0],a[93].columns[0],a[94].columns[0],a[95].columns[0],a[96].columns[0],a[97].columns[0],a[98].columns[0],a[99].columns[0],a[100].columns[0],a[101].columns[0],a[102].columns[0],a[103].columns[0],a[104].columns[0],a[105].columns[0],a[106].columns[0],a[107].columns[0],a[108].columns[0],a[109].columns[0],a[110].columns[0],a[111].columns[0],a[112].columns[0],a[113].columns[0],a[114].columns[0],a[115].columns[0],a[116].columns[0],a[117].columns[0],a[118].columns[0],a[119].columns[0],a[120].columns[0],a[121].columns[0],a[122].columns[0],a[123].columns[0],a[124].columns[0],a[125].columns[0],a[126].columns[0]])
#    py = numpy.array([p[0].columns[1],p[1].columns[1],p[2].columns[1],p[3].columns[1],p[4].columns[1],p[5].columns[1],p[6].columns[1],p[7].columns[1],p[8].columns[1],p[9].columns[1],p[10].columns[1],p[11].columns[1],p[12].columns[1],p[13].columns[1],p[14].columns[1],p[15].columns[1],p[16].columns[1],p[17].columns[1],p[18].columns[1],p[19].columns[1],p[20].columns[1],p[21].columns[1],p[22].columns[1],p[23].columns[1],p[24].columns[1],p[25].columns[1],p[26].columns[1],p[27].columns[1],p[28].columns[1],p[29].columns[1],p[30].columns[1],p[31].columns[1],p[32].columns[1],p[33].columns[1],p[34].columns[1],p[35].columns[1],p[36].columns[1],p[37].columns[1],p[38].columns[1],p[39].columns[1],p[40].columns[1],p[41].columns[1],p[42].columns[1],p[43].columns[1],p[44].columns[1],p[45].columns[1],p[46].columns[1],p[47].columns[1],p[48].columns[1],p[49].columns[1],p[50].columns[1],p[51].columns[1],p[52].columns[1],p[53].columns[1],p[54].columns[1],p[55].columns[1],p[56].columns[1],p[57].columns[1],p[58].columns[1],p[59].columns[1],p[60].columns[1],p[61].columns[1],p[62].columns[1],p[63].columns[1],p[64].columns[1],p[65].columns[1],p[66].columns[1],p[67].columns[1],p[68].columns[1],p[69].columns[1],p[70].columns[1],p[71].columns[1],p[72].columns[1],p[72].columns[1],p[73].columns[1],p[74].columns[1],p[75].columns[1],p[76].columns[1],p[77].columns[1],p[78].columns[1],p[79].columns[1],p[80].columns[1],p[81].columns[1],p[82].columns[1],p[83].columns[1],p[84].columns[1],p[85].columns[1],p[86].columns[1],p[87].columns[1],p[88].columns[1],p[89].columns[1],p[90].columns[1],p[91].columns[1],p[92].columns[1],p[93].columns[1],p[94].columns[1],p[95].columns[1],p[96].columns[1],p[97].columns[1],p[98].columns[1],p[99].columns[1],p[100].columns[1],p[101].columns[1],p[102].columns[1],p[103].columns[1],p[104].columns[1],p[105].columns[1],p[106].columns[1],p[107].columns[1],p[108].columns[1],p[109].columns[1],p[110].columns[1],p[111].columns[1],p[112].columns[1],p[113].columns[1],p[114].columns[1],p[115].columns[1],p[116].columns[1],p[117].columns[1],p[118].columns[1],p[119].columns[1],p[120].columns[1],p[121].columns[1],p[122].columns[1],p[123].columns[1],p[124].columns[1],p[125].columns[1],p[126].columns[1]])
#    ay = numpy.array([a[0].columns[1],a[1].columns[1],a[2].columns[1],a[3].columns[1],a[4].columns[1],a[5].columns[1],a[6].columns[1],a[7].columns[1],a[8].columns[1],a[9].columns[1],a[10].columns[1],a[11].columns[1],a[12].columns[1],a[13].columns[1],a[14].columns[1],a[15].columns[1],a[16].columns[1],a[17].columns[1],a[18].columns[1],a[19].columns[1],a[20].columns[1],a[21].columns[1],a[22].columns[1],a[23].columns[1],a[24].columns[1],a[25].columns[1],a[26].columns[1],a[27].columns[1],a[28].columns[1],a[29].columns[1],a[30].columns[1],a[31].columns[1],a[32].columns[1],a[33].columns[1],a[34].columns[1],a[35].columns[1],a[36].columns[1],a[37].columns[1],a[38].columns[1],a[39].columns[1],a[40].columns[1],a[41].columns[1],a[42].columns[1],a[43].columns[1],a[44].columns[1],a[45].columns[1],a[46].columns[1],a[47].columns[1],a[48].columns[1],a[49].columns[1],a[50].columns[1],a[51].columns[1],a[52].columns[1],a[53].columns[1],a[54].columns[1],a[55].columns[1],a[56].columns[1],a[57].columns[1],a[58].columns[1],a[59].columns[1],a[60].columns[1],a[61].columns[1],a[62].columns[1],a[63].columns[1],a[64].columns[1],a[65].columns[1],a[66].columns[1],a[67].columns[1],a[68].columns[1],a[69].columns[1],a[70].columns[1],a[71].columns[1],a[72].columns[1],a[72].columns[1],a[73].columns[1],a[74].columns[1],a[75].columns[1],a[76].columns[1],a[77].columns[1],a[78].columns[1],a[79].columns[1],a[80].columns[1],a[81].columns[1],a[82].columns[1],a[83].columns[1],a[84].columns[1],a[85].columns[1],a[86].columns[1],a[87].columns[1],a[88].columns[1],a[89].columns[1],a[90].columns[1],a[91].columns[1],a[92].columns[1],a[93].columns[1],a[94].columns[1],a[95].columns[1],a[96].columns[1],a[97].columns[1],a[98].columns[1],a[99].columns[1],a[100].columns[1],a[101].columns[1],a[102].columns[1],a[103].columns[1],a[104].columns[1],a[105].columns[1],a[106].columns[1],a[107].columns[1],a[108].columns[1],a[109].columns[1],a[110].columns[1],a[111].columns[1],a[112].columns[1],a[113].columns[1],a[114].columns[1],a[115].columns[1],a[116].columns[1],a[117].columns[1],a[118].columns[1],a[119].columns[1],a[120].columns[1],a[121].columns[1],a[122].columns[1],a[123].columns[1],a[124].columns[1],a[125].columns[1],a[126].columns[1]])

    npts = len(ax)
    print '%d frequency points...' % (npts)

    # calculate real and imag for plotting
    rx = ax * numpy.cos(numpy.radians(px))
    ix = ax * numpy.sin(numpy.radians(px))
    ry = ay * numpy.cos(numpy.radians(py))
    iy = ay * numpy.sin(numpy.radians(py))

    if plottwo:
    # group for data set 2
    # original phase and amplitude
    # assuming 7 frequency chunks
#        px2 = numpy.array([p2[0].columns[0],p2[1].columns[0],p2[2].columns[0],p2[3].columns[0],p2[4].columns[0],p2[5].columns[0],p2[6].columns[0],p2[7].columns[0]])
#        ax2 = numpy.array([a2[0].columns[0],a2[1].columns[0],a2[2].columns[0],a2[3].columns[0],a2[4].columns[0],a2[5].columns[0],a2[6].columns[0],a2[7].columns[0]])
#        py2 = numpy.array([p2[0].columns[1],p2[1].columns[1],p2[2].columns[1],p2[3].columns[1],p2[4].columns[1],p2[5].columns[1],p2[6].columns[1],p2[7].columns[1]])
#        ay2 = numpy.array([a2[0].columns[1],a2[1].columns[1],a2[2].columns[1],a2[3].columns[1],a2[4].columns[1],a2[5].columns[1],a2[6].columns[1],a2[7].columns[1]])
# assuming 16 frequency chunks
        px2 = numpy.array([p2[0].columns[0],p2[1].columns[0],p2[2].columns[0],p2[3].columns[0],p2[4].columns[0],p2[5].columns[0],p2[6].columns[0],p2[7].columns[0],p2[8].columns[0],p2[9].columns[0],p2[10].columns[0],p2[11].columns[0],p2[12].columns[0],p2[13].columns[0],p2[14].columns[0],p2[15].columns[0]])
        ax2 = numpy.array([a2[0].columns[0],a2[1].columns[0],a2[2].columns[0],a2[3].columns[0],a2[4].columns[0],a2[5].columns[0],a2[6].columns[0],a2[7].columns[0],a2[8].columns[0],a2[9].columns[0],a2[10].columns[0],a2[11].columns[0],a2[12].columns[0],a2[13].columns[0],a2[14].columns[0],a2[15].columns[0]])
        py2 = numpy.array([p2[0].columns[1],p2[1].columns[1],p2[2].columns[1],p2[3].columns[1],p2[4].columns[1],p2[5].columns[1],p2[6].columns[1],p2[7].columns[1],p2[8].columns[1],p2[9].columns[1],p2[10].columns[1],p2[11].columns[1],p2[12].columns[1],p2[13].columns[1],p2[14].columns[1],p2[15].columns[1]])
        ay2 = numpy.array([a2[0].columns[1],a2[1].columns[1],a2[2].columns[1],a2[3].columns[1],a2[4].columns[1],a2[5].columns[1],a2[6].columns[1],a2[7].columns[1],a2[8].columns[1],a2[9].columns[1],a2[10].columns[1],a2[11].columns[1],a2[12].columns[1],a2[13].columns[1],a2[14].columns[1],a2[15].columns[1]])
# assuming 32 frequency chunks
#    px2 = numpy.array([p2[0].columns[0],p2[1].columns[0],p2[2].columns[0],p2[3].columns[0],p2[4].columns[0],p2[5].columns[0],p2[6].columns[0],p2[7].columns[0],p2[8].columns[0],p2[9].columns[0],p2[10].columns[0],p2[11].columns[0],p2[12].columns[0],p2[13].columns[0],p2[14].columns[0],p2[15].columns[0],p2[16].columns[0],p2[17].columns[0],p2[18].columns[0],p2[19].columns[0],p2[20].columns[0],p2[21].columns[0],p2[22].columns[0],p2[23].columns[0],p2[24].columns[0],p2[25].columns[0],p2[26].columns[0],p2[27].columns[0],p2[28].columns[0],p2[29].columns[0],p2[30].columns[0],p2[31].columns[0]])
#    ax2 = numpy.array([a2[0].columns[0],a2[1].columns[0],a2[2].columns[0],a2[3].columns[0],a2[4].columns[0],a2[5].columns[0],a2[6].columns[0],a2[7].columns[0],a2[8].columns[0],a2[9].columns[0],a2[10].columns[0],a2[11].columns[0],a2[12].columns[0],a2[13].columns[0],a2[14].columns[0],a2[15].columns[0],a2[16].columns[0],a2[17].columns[0],a2[18].columns[0],a2[19].columns[0],a2[20].columns[0],a2[21].columns[0],a2[22].columns[0],a2[23].columns[0],a2[24].columns[0],a2[25].columns[0],a2[26].columns[0],a2[27].columns[0],a2[28].columns[0],a2[29].columns[0],a2[30].columns[0],a2[31].columns[0]])
#    py2 = numpy.array([p2[0].columns[1],p2[1].columns[1],p2[2].columns[1],p2[3].columns[1],p2[4].columns[1],p2[5].columns[1],p2[6].columns[1],p2[7].columns[1],p2[8].columns[1],p2[9].columns[1],p2[10].columns[1],p2[11].columns[1],p2[12].columns[1],p2[13].columns[1],p2[14].columns[1],p2[15].columns[1],p2[16].columns[1],p2[17].columns[1],p2[18].columns[1],p2[19].columns[1],p2[20].columns[1],p2[21].columns[1],p2[22].columns[1],p2[23].columns[1],p2[24].columns[1],p2[25].columns[1],p2[26].columns[1],p2[27].columns[1],p2[28].columns[1],p2[29].columns[1],p2[30].columns[1],p2[31].columns[1]])
#    ay2 = numpy.array([a2[0].columns[1],a2[1].columns[1],a2[2].columns[1],a2[3].columns[1],a2[4].columns[1],a2[5].columns[1],a2[6].columns[1],a2[7].columns[1],a2[8].columns[1],a2[9].columns[1],a2[10].columns[1],a2[11].columns[1],a2[12].columns[1],a2[13].columns[1],a2[14].columns[1],a2[15].columns[1],a2[16].columns[1],a2[17].columns[1],a2[18].columns[1],a2[19].columns[1],a2[20].columns[1],a2[21].columns[1],a2[22].columns[1],a2[23].columns[1],a2[24].columns[1],a2[25].columns[1],a2[26].columns[1],a2[27].columns[1],a2[28].columns[1],a2[29].columns[1],a2[30].columns[1],a2[31].columns[1]])
# assuming 160 chunks
#        px2 = numpy.array([p2[0].columns[0],p2[1].columns[0],p2[2].columns[0],p2[3].columns[0],p2[4].columns[0],p2[5].columns[0],p2[6].columns[0],p2[7].columns[0],p2[8].columns[0],p2[9].columns[0],p2[10].columns[0],p2[11].columns[0],p2[12].columns[0],p2[13].columns[0],p2[14].columns[0],p2[15].columns[0],p2[16].columns[0],p2[17].columns[0],p2[18].columns[0],p2[19].columns[0],p2[20].columns[0],p2[21].columns[0],p2[22].columns[0],p2[23].columns[0],p2[24].columns[0],p2[25].columns[0],p2[26].columns[0],p2[27].columns[0],p2[28].columns[0],p2[29].columns[0],p2[30].columns[0],p2[31].columns[0],p2[32].columns[0],p2[33].columns[0],p2[34].columns[0],p2[35].columns[0],p2[36].columns[0],p2[37].columns[0],p2[38].columns[0],p2[39].columns[0],p2[40].columns[0],p2[41].columns[0],p2[42].columns[0],p2[43].columns[0],p2[44].columns[0],p2[45].columns[0],p2[46].columns[0],p2[47].columns[0],p2[48].columns[0],p2[49].columns[0],p2[50].columns[0],p2[51].columns[0],p2[52].columns[0],p2[53].columns[0],p2[54].columns[0],p2[55].columns[0],p2[56].columns[0],p2[57].columns[0],p2[58].columns[0],p2[59].columns[0],p2[60].columns[0],p2[61].columns[0],p2[62].columns[0],p2[63].columns[0],p2[64].columns[0],p2[65].columns[0],p2[66].columns[0],p2[67].columns[0],p2[68].columns[0],p2[69].columns[0],p2[70].columns[0],p2[71].columns[0],p2[72].columns[0],p2[72].columns[0],p2[73].columns[0],p2[74].columns[0],p2[75].columns[0],p2[76].columns[0],p2[77].columns[0],p2[78].columns[0],p2[79].columns[0],p2[80].columns[0],p2[81].columns[0],p2[82].columns[0],p2[83].columns[0],p2[84].columns[0],p2[85].columns[0],p2[86].columns[0],p2[87].columns[0],p2[88].columns[0],p2[89].columns[0],p2[90].columns[0],p2[91].columns[0],p2[92].columns[0],p2[93].columns[0],p2[94].columns[0],p2[95].columns[0],p2[96].columns[0],p2[97].columns[0],p2[98].columns[0],p2[99].columns[0],p2[100].columns[0],p2[101].columns[0],p2[102].columns[0],p2[103].columns[0],p2[104].columns[0],p2[105].columns[0],p2[106].columns[0],p2[107].columns[0],p2[108].columns[0],p2[109].columns[0],p2[110].columns[0],p2[111].columns[0],p2[112].columns[0],p2[113].columns[0],p2[114].columns[0],p2[115].columns[0],p2[116].columns[0],p2[117].columns[0],p2[118].columns[0],p2[119].columns[0],p2[120].columns[0],p2[121].columns[0],p2[122].columns[0],p2[123].columns[0],p2[124].columns[0],p2[125].columns[0],p2[126].columns[0]])
#        ax2 = numpy.array([a2[0].columns[0],a2[1].columns[0],a2[2].columns[0],a2[3].columns[0],a2[4].columns[0],a2[5].columns[0],a2[6].columns[0],a2[7].columns[0],a2[8].columns[0],a2[9].columns[0],a2[10].columns[0],a2[11].columns[0],a2[12].columns[0],a2[13].columns[0],a2[14].columns[0],a2[15].columns[0],a2[16].columns[0],a2[17].columns[0],a2[18].columns[0],a2[19].columns[0],a2[20].columns[0],a2[21].columns[0],a2[22].columns[0],a2[23].columns[0],a2[24].columns[0],a2[25].columns[0],a2[26].columns[0],a2[27].columns[0],a2[28].columns[0],a2[29].columns[0],a2[30].columns[0],a2[31].columns[0],a2[32].columns[0],a2[33].columns[0],a2[34].columns[0],a2[35].columns[0],a2[36].columns[0],a2[37].columns[0],a2[38].columns[0],a2[39].columns[0],a2[40].columns[0],a2[41].columns[0],a2[42].columns[0],a2[43].columns[0],a2[44].columns[0],a2[45].columns[0],a2[46].columns[0],a2[47].columns[0],a2[48].columns[0],a2[49].columns[0],a2[50].columns[0],a2[51].columns[0],a2[52].columns[0],a2[53].columns[0],a2[54].columns[0],a2[55].columns[0],a2[56].columns[0],a2[57].columns[0],a2[58].columns[0],a2[59].columns[0],a2[60].columns[0],a2[61].columns[0],a2[62].columns[0],a2[63].columns[0],a2[64].columns[0],a2[65].columns[0],a2[66].columns[0],a2[67].columns[0],a2[68].columns[0],a2[69].columns[0],a2[70].columns[0],a2[71].columns[0],a2[72].columns[0],a2[72].columns[0],a2[73].columns[0],a2[74].columns[0],a2[75].columns[0],a2[76].columns[0],a2[77].columns[0],a2[78].columns[0],a2[79].columns[0],a2[80].columns[0],a2[81].columns[0],a2[82].columns[0],a2[83].columns[0],a2[84].columns[0],a2[85].columns[0],a2[86].columns[0],a2[87].columns[0],a2[88].columns[0],a2[89].columns[0],a2[90].columns[0],a2[91].columns[0],a2[92].columns[0],a2[93].columns[0],a2[94].columns[0],a2[95].columns[0],a2[96].columns[0],a2[97].columns[0],a2[98].columns[0],a2[99].columns[0],a2[100].columns[0],a2[101].columns[0],a2[102].columns[0],a2[103].columns[0],a2[104].columns[0],a2[105].columns[0],a2[106].columns[0],a2[107].columns[0],a2[108].columns[0],a2[109].columns[0],a2[110].columns[0],a2[111].columns[0],a2[112].columns[0],a2[113].columns[0],a2[114].columns[0],a2[115].columns[0],a2[116].columns[0],a2[117].columns[0],a2[118].columns[0],a2[119].columns[0],a2[120].columns[0],a2[121].columns[0],a2[122].columns[0],a2[123].columns[0],a2[124].columns[0],a2[125].columns[0],a2[126].columns[0]])
#        py2 = numpy.array([p2[0].columns[1],p2[1].columns[1],p2[2].columns[1],p2[3].columns[1],p2[4].columns[1],p2[5].columns[1],p2[6].columns[1],p2[7].columns[1],p2[8].columns[1],p2[9].columns[1],p2[10].columns[1],p2[11].columns[1],p2[12].columns[1],p2[13].columns[1],p2[14].columns[1],p2[15].columns[1],p2[16].columns[1],p2[17].columns[1],p2[18].columns[1],p2[19].columns[1],p2[20].columns[1],p2[21].columns[1],p2[22].columns[1],p2[23].columns[1],p2[24].columns[1],p2[25].columns[1],p2[26].columns[1],p2[27].columns[1],p2[28].columns[1],p2[29].columns[1],p2[30].columns[1],p2[31].columns[1],p2[32].columns[1],p2[33].columns[1],p2[34].columns[1],p2[35].columns[1],p2[36].columns[1],p2[37].columns[1],p2[38].columns[1],p2[39].columns[1],p2[40].columns[1],p2[41].columns[1],p2[42].columns[1],p2[43].columns[1],p2[44].columns[1],p2[45].columns[1],p2[46].columns[1],p2[47].columns[1],p2[48].columns[1],p2[49].columns[1],p2[50].columns[1],p2[51].columns[1],p2[52].columns[1],p2[53].columns[1],p2[54].columns[1],p2[55].columns[1],p2[56].columns[1],p2[57].columns[1],p2[58].columns[1],p2[59].columns[1],p2[60].columns[1],p2[61].columns[1],p2[62].columns[1],p2[63].columns[1],p2[64].columns[1],p2[65].columns[1],p2[66].columns[1],p2[67].columns[1],p2[68].columns[1],p2[69].columns[1],p2[70].columns[1],p2[71].columns[1],p2[72].columns[1],p2[72].columns[1],p2[73].columns[1],p2[74].columns[1],p2[75].columns[1],p2[76].columns[1],p2[77].columns[1],p2[78].columns[1],p2[79].columns[1],p2[80].columns[1],p2[81].columns[1],p2[82].columns[1],p2[83].columns[1],p2[84].columns[1],p2[85].columns[1],p2[86].columns[1],p2[87].columns[1],p2[88].columns[1],p2[89].columns[1],p2[90].columns[1],p2[91].columns[1],p2[92].columns[1],p2[93].columns[1],p2[94].columns[1],p2[95].columns[1],p2[96].columns[1],p2[97].columns[1],p2[98].columns[1],p2[99].columns[1],p2[100].columns[1],p2[101].columns[1],p2[102].columns[1],p2[103].columns[1],p2[104].columns[1],p2[105].columns[1],p2[106].columns[1],p2[107].columns[1],p2[108].columns[1],p2[109].columns[1],p2[110].columns[1],p2[111].columns[1],p2[112].columns[1],p2[113].columns[1],p2[114].columns[1],p2[115].columns[1],p2[116].columns[1],p2[117].columns[1],p2[118].columns[1],p2[119].columns[1],p2[120].columns[1],p2[121].columns[1],p2[122].columns[1],p2[123].columns[1],p2[124].columns[1],p2[125].columns[1],p2[126].columns[1]])
#        ay2 = numpy.array([a2[0].columns[1],a2[1].columns[1],a2[2].columns[1],a2[3].columns[1],a2[4].columns[1],a2[5].columns[1],a2[6].columns[1],a2[7].columns[1],a2[8].columns[1],a2[9].columns[1],a2[10].columns[1],a2[11].columns[1],a2[12].columns[1],a2[13].columns[1],a2[14].columns[1],a2[15].columns[1],a2[16].columns[1],a2[17].columns[1],a2[18].columns[1],a2[19].columns[1],a2[20].columns[1],a2[21].columns[1],a2[22].columns[1],a2[23].columns[1],a2[24].columns[1],a2[25].columns[1],a2[26].columns[1],a2[27].columns[1],a2[28].columns[1],a2[29].columns[1],a2[30].columns[1],a2[31].columns[1],a2[32].columns[1],a2[33].columns[1],a2[34].columns[1],a2[35].columns[1],a2[36].columns[1],a2[37].columns[1],a2[38].columns[1],a2[39].columns[1],a2[40].columns[1],a2[41].columns[1],a2[42].columns[1],a2[43].columns[1],a2[44].columns[1],a2[45].columns[1],a2[46].columns[1],a2[47].columns[1],a2[48].columns[1],a2[49].columns[1],a2[50].columns[1],a2[51].columns[1],a2[52].columns[1],a2[53].columns[1],a2[54].columns[1],a2[55].columns[1],a2[56].columns[1],a2[57].columns[1],a2[58].columns[1],a2[59].columns[1],a2[60].columns[1],a2[61].columns[1],a2[62].columns[1],a2[63].columns[1],a2[64].columns[1],a2[65].columns[1],a2[66].columns[1],a2[67].columns[1],a2[68].columns[1],a2[69].columns[1],a2[70].columns[1],a2[71].columns[1],a2[72].columns[1],a2[72].columns[1],a2[73].columns[1],a2[74].columns[1],a2[75].columns[1],a2[76].columns[1],a2[77].columns[1],a2[78].columns[1],a2[79].columns[1],a2[80].columns[1],a2[81].columns[1],a2[82].columns[1],a2[83].columns[1],a2[84].columns[1],a2[85].columns[1],a2[86].columns[1],a2[87].columns[1],a2[88].columns[1],a2[89].columns[1],a2[90].columns[1],a2[91].columns[1],a2[92].columns[1],a2[93].columns[1],a2[94].columns[1],a2[95].columns[1],a2[96].columns[1],a2[97].columns[1],a2[98].columns[1],a2[99].columns[1],a2[100].columns[1],a2[101].columns[1],a2[102].columns[1],a2[103].columns[1],a2[104].columns[1],a2[105].columns[1],a2[106].columns[1],a2[107].columns[1],a2[108].columns[1],a2[109].columns[1],a2[110].columns[1],a2[111].columns[1],a2[112].columns[1],a2[113].columns[1],a2[114].columns[1],a2[115].columns[1],a2[116].columns[1],a2[117].columns[1],a2[118].columns[1],a2[119].columns[1],a2[120].columns[1],a2[121].columns[1],a2[122].columns[1],a2[123].columns[1],a2[124].columns[1],a2[125].columns[1],a2[126].columns[1]])

    # calculate real and imag for plotting
        rx2 = ax2 * numpy.cos(numpy.radians(px2))
        ix2 = ax2 * numpy.sin(numpy.radians(px2))
        ry2 = ay2 * numpy.cos(numpy.radians(py2))
        iy2 = ay2 * numpy.sin(numpy.radians(py2))

    if type == 'ratio':
        for i in range(nants):
            if ax2[0,i] == 0:  
                continue
            ratampx = ax2[12:,i]/ax[0:8,i]
            ratphx = px2[12:,i]-px[0:8,i]
            ratampy = ay2[12:,i]/ay[0:8,i]
            ratphy = py2[12:,i]-py[0:8,i]
            pylab.figure(1)
            pylab.subplot(211)
            pylab.plot(range(8), ratphx)
            pylab.text(7,ratphx[0],str(antnum[i]))
            pylab.subplot(212)
            pylab.plot(range(8), ratampx)
            pylab.text(7, ratampx[0],str(antnum[i]))
            pylab.figure(2)
            pylab.subplot(211)
            pylab.plot(range(8), ratphy)
            pylab.text(7,ratphy[0],str(antnum[i]))
            pylab.subplot(212)
            pylab.plot(range(8), ratampy)
            pylab.text(7, ratampy[0],str(antnum[i]))

    if type == 'xy':
        # real-imag (x-y) plot
        # two pols per source
        for i in range(nants):
            if rx[0,i] == 0:
                continue
# mean
#            for j in range(2,len(rx)-3):
#                rx[j,i] = rx[j-2:j+3,i].mean()
#                ix[j,i] = ix[j-2:j+3,i].mean()
            pylab.figure(1)
            pylab.plot(rx[:,i],ix[:,i],'.-')
            pylab.text(rx[0,i],ix[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
        for i in range(nants):
            if ry[0,i] == 0:
                continue
# mean
#            for j in range(2,len(ry)-3):
#                ry[j,i] = ry[j-2:j+3,i].mean()
#                iy[j,i] = iy[j-2:j+3,i].mean()
            pylab.figure(2)
            pylab.plot(ry[:,i],iy[:,i],'.-')
            pylab.text(ry[0,i],iy[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
        if plottwo:
            for i in range(nants):
                if rx2[0,i] == 0:
                    continue
                pylab.figure(3)
# mean
#            for j in range(3,len(rx2)-4):
#                rx2[j,i] = rx2[j-3:j+4,i].mean()
#                ix2[j,i] = ix2[j-3:j+4,i].mean()
                pylab.plot(rx2[:,i],ix2[:,i],'.-')
                pylab.text(rx2[0,i],ix2[0,i],str(antnum[i]))
                pylab.xlabel('Real')
                pylab.ylabel('Imaginary')
                pylab.title('Leakages')
            for i in range(nants):
                if ry2[0,i] == 0:
                    continue
                pylab.figure(4)
# mean
#            for j in range(3,len(ry2)-4):
#                ry2[j,i] = ry2[j-3:j+4,i].mean()
#                iy2[j,i] = iy2[j-3:j+4,i].mean()
                pylab.plot(ry2[:,i],iy2[:,i],'.-')
                pylab.text(ry2[0,i],iy2[0,i],str(antnum[i]))
                pylab.xlabel('Real')
                pylab.ylabel('Imaginary')
                pylab.title('Leakages')

    if type == 'corr':
        sqfile = asciidata.AsciiData('/o/claw/big_scr3/data/ata/nvss-rm2/squint.tab')
        sqamp = numpy.array(sqfile.columns[7])

        # plot amp of leak vs. amp of squint
        for i in range(nants):
            if sqamp[antnum[i]-1] == '    --':  continue
            avax = numpy.average(ax[:,i])
            avay = numpy.average(ay[:,i])
            pylab.figure(1)
            pylab.plot([float(sqamp[antnum[i]-1])], [numpy.sqrt(avax**2+avay**2)], '.')
            pylab.text(float(sqamp[antnum[i]-1]), numpy.sqrt(avax**2+avay**2), str(antnum[i]))
# average x and y leakage
#            pylab.plot([float(sqamp[antnum[i]-1])], [numpy.sqrt(avax**2 + avay**2)], '.')
#            pylab.text(float(sqamp[antnum[i]-1]), numpy.sqrt(avax**2 + avay**2), str(antnum[i]))

            pylab.xlabel('Antenna squint (arcmin)')
            pylab.ylabel('Leak amplitude, freq avg')
            print '%d %.1f %.3f' % (antnum[i], float(sqamp[antnum[i]-1]), numpy.sqrt(avax**2 + avay**2))


    if type == 'joint':
        # real-imag (x-y) plot
        # two pols per source
        for i in range(nants):
            if rx[0,i] == 0:
                continue
            rxj = numpy.concatenate((rx[:,i],rx2[:,i]))
            ixj = numpy.concatenate((ix[:,i],ix2[:,i]))
            ryj = numpy.concatenate((ry[:,i],ry2[:,i]))
            iyj = numpy.concatenate((iy[:,i],iy2[:,i]))
            pylab.figure(1)
            pylab.plot(rxj,ixj,'.-')
            pylab.text(rx[0,i],ix[0,i],str(antnum[i]))
            pylab.text(rx2[0,i],ix2[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
            pylab.figure(2)
            pylab.plot(ryj,iyj,'.-')
            pylab.text(ry[0,i],iy[0,i],str(antnum[i]))
            pylab.text(ry2[0,i],iy2[0,i],str(antnum[i]))
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')

    if type == 'overlap':
        # real-imag (x-y) plot
        # two pols per source
        colors = ['b','g','r','c','m','y','k','b','g','r','c','m','y','k','b','g','r','c','m','y','k','b','g','r','c','m','y','k','b','g','r','c','m','y','k','b','g','r','c','m','y','k','b','g','r','c','m','y','k']
        nantlist = range(nants)
        for i in nantlist:
            if rx[0,i] == 0:
                continue
            pylab.figure(1)
            print i, nantlist.index(i), colors[nantlist.index(i)]
            pylab.plot(rx[:,i],ix[:,i],colors[nantlist.index(i)]+'.-')
            pylab.plot(rx2[:,i],ix2[:,i],colors[nantlist.index(i)]+'--')
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
            pylab.text(rx[0,i],ix[0,i],str(antnum[i]))
            pylab.text(rx2[0,i],ix2[0,i],str(antnum[i]))
            pylab.figure(2)
            pylab.plot(ry[:,i],iy[:,i],colors[nantlist.index(i)]+'.-')
            pylab.plot(ry2[:,i],iy2[:,i],colors[nantlist.index(i)]+'--')
            pylab.xlabel('Real')
            pylab.ylabel('Imaginary')
            pylab.title('Leakages')
            pylab.text(ry[0,i],iy[0,i],str(antnum[i]))
            pylab.text(ry2[0,i],iy2[0,i],str(antnum[i]))
#            pylab.figure(3)
#            pylab.plot(ry-ry2,iy-iy2,'.-')
#            pylab.plot(rx-rx2,ix-ix2,'--')
#            pylab.text(ry[0,i]-ry2[0,i],iy[0,i]-iy2[0,i],str(antnum[i]))
#            pylab.text(rx[0,i]-rx2[0,i],ix[0,i]-ix2[0,i],str(antnum[i]))
#            pylab.xlabel('Real')
#            pylab.ylabel('Imaginary')
        pylab.title('Leakages')

    pylab.show()

if __name__ == '__main__':
    run()
