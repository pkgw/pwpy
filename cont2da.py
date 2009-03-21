"""cont2da - 2-D analytic contour finding.

Uses my own homebrew algorithm. So far, it's only tested on
extremely well-behaved functions, so probably doesn't cope
well with poorly-behaved ones.
"""

import numpy as N

def cont2da (f, df, x0, y0, maxiters=5000, defeta=0.05, netastep=12,
             vtol1=1e-3, vtol2=1e-8, maxnewt=20):
    """Required arguments:
    
f  - a function, mapping (x, y) -> z
df - the derivative: df (x, y) -> [df/dx, df/dy]
     (Should be 1D size-2 ndarray)
x0 - initial x value
y0 - initial y value

Optional arguments:

maxiters - Maximum number of points to create. Default 5000.
defeta - Initially offset by distances of defeta*[df/dx, df/dy]
  Default 0.05.
netastep - Number of steps between defeta and the machine resolution
  in which we test eta values for goodness. (OMG FIXME doc). Default
  12.
vtol1 - Tolerance for constancy in the value of the function in the
  initial offset step. The value is only allowed to vary by
  f(x0,y0) * vtol1. Default 1e-3.
vtol2 - Tolerance for constancy in the value of the function in the
  along the contour. The value is only allowed to vary by
  f(x0,y0) * vtol2. Default 1e-8.
maxnewt - Maximum number of Newton's method steps to take when
  attempting to hone in on the desired function value. Default 20.
"""
    
    # Coerce argument types.

    if not callable (f): raise ValueError ('f')
    if not callable (df): raise ValueError ('df')
    x0 = float (x0)
    y0 = float (y0)
    maxiters = int (maxiters)
    if maxiters < 3: raise ValueError ('maxiters')
    defeta = float (defeta)
    if defeta <= 0: raise ValueError ('defeta')
    netastep = int (netastep)
    if netastep < 2: raise ValueError ('netastep')
    vtol1 = float (vtol1)
    if vtol1 <= 0: raise ValueError ('vtol1')
    vtol2 = float (vtol2)
    if vtol2 >= vtol1: raise ValueError ('vtol2')
    maxnewt = int (maxnewt)
    if maxnewt < 1: raise ValueError ('maxnewt')
    
    # What value are we contouring?
    v = f (x0, y0)

    # Init eta progression
    rez = N.finfo (N.double).resolution
    if rez > defeta: raise ValueError ('defeta below resolution!')
    eta_scale = N.exp ((N.log (rez) - N.log (defeta)) / netastep)

    # Init data storage
    n = 1
    pts = N.empty ((maxiters, 2))
    pts[0] = (x0, y0)
    x = x0
    y = y0

    # Quitflag: 0 if first iteration
    # 1 if inited but not yet ok to quit (definition of this below)
    # 2 if ok to quit
    # intiquad: 0 if x > 0, y > 0
    # 1 if x < 0, y > 0
    # 2 if x < 0, y < 0
    # 3 if x > 0, y < 0
    # we invert these senses in the in-loop test to
    # make comparison easy.
    
    quitflag = 0
    initquad = -1
    
    # Start finding contours.
    
    while n < maxiters:
        dfdx, dfdy = df (x, y)

        # If we're booting up, remember the quadrant that df/dx points
        # in. Once we've rotated around to the other direction, it is
        # safe to quit once we return close to the original point,
        # since we must have completed a circle.

        if quitflag == 0:
            if dfdx > 0:
                if dfdy > 0: initquad = 0
                else: initquad = 3
            else:
                if dfdy > 0: initquad = 1
                else: initquad = 2
            quitflag = 1
        elif quitflag == 1:
            if dfdx > 0:
                if dfdy > 0: curquad = 2
                else: curquad = 1
            else:
                if dfdy > 0: curquad = 3
                else: curquad = 0

            if curquad == initquad:
                quitflag = 2
            
        # We will move perpendicular to [df/dx, df/dy], rotating to
        # the left (arbitrarily) from that direction. We need to
        # figure out how far we can safely move in this direction.

        dx = -dfdy * defeta
        dy = dfdx * defeta
        i = 0

        while i < netastep:
            nx = x + dx
            ny = y + dy
            nv = f (nx, ny)

            # Is the value of the function sufficently close to what
            # we're aiming for?

            if abs (nv / v - 1) < vtol1:
                break

            # No. Try a smaller dx/dy

            dx *= eta_scale
            dy *= eta_scale
            i += 1
        else:
            # Failed to find a sufficiently small eta (did not break
            # out of loop)
            s = 'xy %g,%g; dv %g; df %g,%g; dxy %g,%g; defeta %g; eta_scale %g' \
                % (x, y, nv - v, dfdx, dfdy, dx, dy, defeta, eta_scale)
            raise RuntimeError ('Failed to find sufficiently small'
                                'eta: ' + s)

        # Now compute a new [df/dx, df/dy], and move along it, finding
        # our way back to the desired value, 'v'. Newton's method should
        # suffice. This loop usually exits after one iteration.

        i = 0
        
        while i < maxnewt:
            dfdx, dfdy = df (nx, ny)
            df2 = dfdx**2 + dfdy**2
            dv = nv - v

            nx -= dv * dfdx / df2
            ny -= dv * dfdy / df2
            nv = f (nx, ny)

            if abs (nv/v - 1) < vtol2:
                break

            i += 1
        else:
            # Did not break out of loop.
            raise RuntimeError ('Failed to converge with Newton\'s method!')
        
        # Ok, we found our next value.
        pts[n] = (nx, ny)
        x = nx
        y = ny
        n += 1

        # Time to stop? Make sure we've gone at least a half-turn so
        # that we don't just exit on the first iteration.
        
        if quitflag == 2:
            dist2 = (x0/x - 1)**2 + (y0/y - 1)**2
            if dist2 < vtol1**2:
                break
    else:
        # Did not break out of loop -- too many pts.
        raise RuntimeError ('Needed too many points to close contour.')

    # Woohoo! All done.

    pts = pts[0:n]
    return pts


__all__ = ['cont2da']
