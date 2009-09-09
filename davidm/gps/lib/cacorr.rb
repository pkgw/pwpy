require 'gsl'
require 'rational'
require 'gpsca'

prn = 1
ca = GPSCA[prn]

# Loads ddc data from an ASCII data file of four columns...
#
# re0 im0 re1 im1
#
# Returns two GSL::Vectors: z0, z1
def load_ddc(filename)
  lines = File.readlines(filename).grep(/^(?!#)/)
  nums = lines.map {|l| l.gsub('i','').split.map {|w| Integer(w)}}
  nums = nums.transpose
  z0 = GSL::Vector::Complex.new(nums[0,2].transpose)
  z1 = GSL::Vector::Complex.new(nums[2,2].transpose)
  [z0, z1]
end

# Returns +len+ CA chips starting at chip +off+ for PRN +prn+
def chips(prn, off, len)
  sca = GSL::Vector[205*len]
  len.times do |i|
    sca.subvector(i*205,205).set_all(GPSCA[prn][(off+i)%1023]*2-1)
  end
  # Skip one sample for odd offsets
  off &= 1
  sca.subvector(off,205*len-off).decimate(2)
end

class GSL::Vector; alias :length :size unless defined? :length; end

def object_count(*args)
  args = [Object] if args.empty?
  args.map do |clazz|
    ObjectSpace.each_object(clazz) {}
  end
end

# Correlates complex vector +z+ with +len+ CA chips starting at chip +off+ for
# PRN +prn
def cacorr(z, prn, off, len)
  c = chips(prn, off, len)
end

WAVETABLE = {}
WORKSPACE = {}
def get_wt(len); WAVETABLE[len] ||= GSL::FFT::ComplexWavetable.alloc(len); end
def get_ws(len); WORKSPACE[len] ||= GSL::FFT::ComplexWorkspace.alloc(len); end

def correlate(x,y,fx=nil,fy=nil)
  # Calc length for tranforms
  len = x.size + y.size - 1
  len2 = 2**(Math.log(len)/GSL::M_LN2).ceil
  wt = get_wt(len2)
  ws = get_ws(len2)

  # Create padded arrays
  if fx
    fx.set_all(0)
  else
    fx = GSL::Vector::Complex[len2]
  end
  # Copy x data into padded array
  # Offset the copy of x by (y.size-1)
  fx0 = (y.size-1)
  if x.respond_to? :re
    #x.re.copy(fx.subvector(fx0  ,2,x.size))
    #x.im.copy(fx.subvector(fx0+1,2,x.size))
    x.copy(fx.subvector(fx0,x.size))
  else
    #x.copy(fx.subvector(fx0,2,x.size))
    x.copy(fx.re.subvector(fx0,x.size))
  end
  # Forward transform x
  #fx.radix2_forward!
  #fx.forward!
  fx.forward!(wt,ws)

  if fy.nil?
    fy = GSL::Vector::Complex[len2]
    # Copy y data into y padded array
    if y.respond_to? :re
      #y.re.copy(fy.subvector(0,2,y.size))
      #y.im.copy(fy.subvector(1,2,y.size))
      y.copy(fy.subvector(0,y.size))
    else
      #y.copy(fy.subvector(0,2,y.size))
      y.copy(fy.re.subvector(0,y.size))
    end
    # Forward transform and conjugate y
    #fy = fy.radix2_forward.conj!
    fy.forward!(wt,ws).conj!
  end

  ### This is how I'd like to do it, but it seems to hog memory
  # # HOGS MEMORY!?
  # z = fx; z *= fy
  # # HOGS MEMORY TOO!?
  # z = fx * fy
  # # OK-BUT-SLOW
  #z = GSL::Vector::Complex[len2]
  #len2.times {|i| z[i] = fx[i]*fy[i]}
  #fx = z
  # # Seems good!
  #z = fx; z.mul!(fy)
  fx.mul!(fy)

  # Then inverse transform z
  #z.inverse!(wt,ws)
  fx.inverse!(wt,ws)

  # Return results as GSL::Vector or GSL::Vector::Complex
  xy = if x.respond_to?(:re) || y.respond_to?(:re)
         #z.subvector(0,2*len).to_complex2
         #z.subvector(0,len).dup
         fx.subvector(0,len).dup
         #z.to_complex2
       else
         #z.subvector(0,2,len).dup
         #z.re.subvector(0,len).dup
         fx.re.subvector(0,len).dup
         #z.re.dup
       end
  [xy, fx, fy]
end

# Upsamples and correlates
def up_correlate(x,y,fx=nil,fy=nil,up=1)
  # len is length of upsampled lag space
  len = up*(x.size + y.size) - 1
  # len2 is nextpow2(len)
  len2 = 2**(Math.log(len)/GSL::M_LN2).ceil
  wt = get_wt(len2)
  ws = get_ws(len2)

  # Create padded arrays
  if fx
    fx.set_all(0)
  else
    fx = GSL::Vector::Complex[len2]
  end
  # Copy x data into padded array
  # Offset the copy of x by (y.size-1)
  fx0 = up*y.size-1
  if x.respond_to? :re
    x.copy(fx.subvector(fx0,up,x.size))
  else
    # TODO 2*up?
    x.copy(fx.re.subvector(fx0,up,x.size))
  end
  # Forward transform x
  #fx.radix2_forward!
  #fx.forward!
  fx.forward!(wt,ws)
  # Freq domain filter out the copies of x's sprectrum
  fx.subvector(x.size/2,len2-x.size).set_all(0)

  if fy.nil?
    fy = GSL::Vector::Complex[len2]
    # Copy y data into y padded array
    up.times do |i|
      if y.respond_to? :re
        y.copy(fy.subvector(i*y.size,y.size))
      else
      # TODO 2*i*y.size?
        y.copy(fy.re.subvector(i*y.size,y.size))
      end
    end
    # Forward transform and conjugate y
    #fy = fy.radix2_forward.conj!
    fy.forward!(wt,ws).conj!
  end

  ### This is how I'd like to do it, but it seems to hog memory
  # # HOGS MEMORY!?
  # z = fx; z *= fy
  # # HOGS MEMORY TOO!?
  # z = fx * fy
  # # OK-BUT-SLOW
  #z = GSL::Vector::Complex[len2]
  #len2.times {|i| z[i] = fx[i]*fy[i]}
  #fx = z
  # # Seems good!
  #z = fx; z.mul!(fy)
  #fx.mul!(fy)
  z=fx.dup
  z.mul!(fy)

  # Then inverse transform z
  #z.inverse!(wt,ws)
  z.inverse!(wt,ws)

  # Return results as GSL::Vector or GSL::Vector::Complex
  xy = if x.respond_to?(:re) || y.respond_to?(:re)
         #z.subvector(0,2*len).to_complex2
         #z.subvector(0,len).dup
         z.subvector(0,len).dup
         #z.to_complex2
       else
         #z.subvector(0,2,len).dup
         #z.re.subvector(0,len).dup
         z.re.subvector(0,len).dup
         #z.re.dup
       end
  [xy, fx, fy]
end

## Correlates complex vector +z+ with +len+ CA chips starting at chip +off+ for
## PRN +prn
#def cacorr(z, prn, off, len)
#  c = chips(prn, off, len)
#  correlate(z, c)
#end

if $0 == __FILE__
  sca = chips(1,0,1023)
  [0, 102, 103, 204, 205, 206].each {|i| p sca[i]}
end
