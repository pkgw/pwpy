# claw, 18feb09
# 
# Script to find optimal pointing centers for a mosaic with the ATA.  
#
# Input:  define region to be mosaicked (only gal coords for now), frequency (GHz), and grid type ('rect', 'hex')
# Output:  plot of field centers.  optionally can take coordinate object and feed to second function to get text to be added to catalog.list.
#
# Notes:
#  - The algorithm for stepping through the selected box is not terribly clever.  This script is most useful when interactively checking results and rerunning to get best coverage.
#  - Nyquist sampling assuming fwhm of 3.7/freq
#  - Note that center positions are simply converted from Galactic.  Projection effects not taken into account, which may cause problems away from the Galactic equator.

import pylab, ephem, numpy

def calc_centers_gal(lmin,bmin,lmax,bmax,freq,type):
    sp = 3.7/freq/2.  # spacing by half power width
    centerl = []; centerb = []

    if type=='rect':
        # create a rectangular grid
        # start at the bottom right corner
        l = lmin+sp; b = bmin+sp
        while b <= bmax:
            while l <= lmax:
                centerl.append(l)
                centerb.append(b)
                l += sp
            l = lmin+sp
            b += sp

    elif type=='hex':
        # create a hexagonal grid
        # start at the bottom right corner
        l = lmin+sp*numpy.cos(numpy.radians(30.)); b = bmin+sp*numpy.sin(numpy.radians(30.))
        shift = 0  # hack to make rows alternate a shift in l
        while b <= bmax:
            while l <= lmax:
                centerl.append(l)
                centerb.append(b)
                l += 2*sp*numpy.cos(numpy.radians(30.))
            shift += 1
            l = lmin + sp*numpy.cos(numpy.radians(30.)) + sp*numpy.cos(numpy.radians(30.)) * numpy.mod(shift,2)  # off first time, on next time, etc.
            b += sp*numpy.sin(numpy.radians(30.))

    else:
        print 'Sorry, that is not a type that I know...'
        exit()

    # define circle for plotting fwhm for each field
    phi = numpy.arange(360.)
    circlel = sp*numpy.cos(phi)
    circleb = sp*numpy.sin(phi)

    # plot edge defined by user
    pylab.plot([lmin,lmin,lmax,lmax,lmin],[bmin,bmax,bmax,bmin,bmin],'r')

    # plot centers of fields
    pylab.plot(centerl,centerb,'b*')

    # plot circles for each field
    for i in range(len(centerl)):
        pylab.plot(circlel + centerl[i], circleb + centerb[i],'b,')
    pylab.show()

    # return the center coords for fields
    return centerl,centerb

def print_centers(centerl,centerb):
    # This function can take the returned field center values and print them out with the syntax of 'catalog.list'.
    # Note:  you will need to edit the string below for yourself.

    ra = []
    dec = []
    for i in range(len(centerl)):
        gal = ephem.Galactic(str(centerl[i]),str(centerb[i]),epoch='2000')
        cel = ephem.Equatorial(gal)
        ra.append(cel.ra*12/ephem.pi)
        dec.append(cel.dec*180/ephem.pi)

    radec = numpy.array(zip(ra,dec), dtype=[('ra','float'),('dec','float')])
    radec.sort(order='dec')

    for i in range(len(radec)):
        print 'ata  mosaic     gc-seti3-%d     %.10f           %.10f           cjl' % (i+1,radec[i][0],radec[i][1])
