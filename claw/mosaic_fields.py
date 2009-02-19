# script to find optimal pointing centers for a mosaic with the ata
# 
# input:  define region to be mosaicked (gal coords for now), frequency (GHz), and grid type ('rect', 'hex')
# output:  plot of field centers, text to be added to catalog.list
#
# nyquist sampling assuming fwhm of 3.7/freq
# note that center positions are simply converted from galactic.  projection effects not taken into account.

import pylab, ephem, numpy

def calc_centers_gal(lmin,bmin,lmax,bmax,freq,type):
    sp = 3.7/freq/2.  # spacing by half power width
    centerl = []; centerb = []

    if type=='rect':
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

    # define circle for plotting
    phi = numpy.arange(360.)
    circlel = sp*numpy.cos(phi)
    circleb = sp*numpy.sin(phi)

    pylab.plot([lmin,lmin,lmax,lmax,lmin],[bmin,bmax,bmax,bmin,bmin],'r')
    pylab.plot(centerl,centerb,'b*')
    for i in range(len(centerl)):
        pylab.plot(circlel + centerl[i], circleb + centerb[i],'b,')
    pylab.show()

    return centerl,centerb

def print_centers(centerl,centerb):
    for i in range(len(centerl)):
        gal = ephem.Galactic(str(centerl[i]),str(centerb[i]),epoch='2000')
        cel = ephem.Equatorial(gal)
        print 'ata  mosaic     gc-seti%d-20     %.10f           %.10f           cjl' % (i+1,cel.ra*12/ephem.pi, cel.dec*180/ephem.pi)
