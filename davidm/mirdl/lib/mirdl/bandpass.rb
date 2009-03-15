#
# $Id$
#

# bandpass.rb - Method(s) to get antenna bandpass curves (transcribed from gpplot.for:BLoad)

require 'narray'

module Mirdl

  # Returns [bandpass, freqs]
  # +bandpass+ is NArray that is nants*nfeeds*nchan long
  # +freqs+ is an array of frequencies corresponding to each channel
  def get_bandpass(tno, sels=nil)
    return nil unless hdprsnt(tno, :bandpass)

    # Determine the various parameters, and check their validity. We have pretty
    # well checked that all is OK before, so nothing should go wrong.
    #TODO doselect = sels && selProbe(sels,'time?')
    nfeeds = rdhdi(tno,'nfeeds',1)
    ngains = rdhdi(tno,'ngains',1)
    ntau   = rdhdi(tno,'ntau',0)
    nchan  = rdhdi(tno,'nchan0',1)
    nspect = rdhdi(tno,'nspect0',1)

    #puts "# nfeeds = #{nfeeds}"
    #puts "# ngains = #{ngains}"
    #puts "# ntau   = #{ntau  }"
    #puts "# nchan  = #{nchan }"
    #puts "# nspect = #{nspect}"

    if(nfeeds <= 0 || ngains <= 0)
      bug('e','Bad gain table size information')
    end

    nants = ngains / (nfeeds + ntau)
    #puts "# nants  = #{nants }"

    if(nants*(nfeeds+ntau) != ngains)
      bug('e','Number of gains does equal nants*(nfeeds+ntau)')
    end

    if(nchan <= 0)
      bug('e','Bad number of frequencies')
    end

    if(nspect <= 0 || nspect > nchan)
      bug('f', 'Bad number of frequency spectral windows')
    end

    doselect = selProbe(sels,'frequency?')

    #  Read the frequency table.
    item = haccess(tno,'freqs','read')
    ibuf = NArray.int(1)
    sfreq_sdf = NArray.float(2)
    freqs = NArray.float(nspect*nschan)
    select = []
    n = -1
    off = 8
    for i in 1..nspect
      nschan = hreadi(item,ibuf,off,8)[0]
      off += 8
      hreadd(item,sfreq_sdf,off,2*8)
      off += 2*8
      for j in 0...nschan
        n += 1
        freqs[n] = sfreq_sdf[0] + j*sfreq_sdf[1]
        select[n] = !doselect || selProbe(sels,'frequency',freqs[n])
      end
    end
    hdaccess(item)

    # Read the bandpass table now
    item = haccess(tno,'bandpass','read')
    bandpass = NArray.scomplex(nants*nfeeds*nchan)
    off = 8
    hreadc(item,bandpass,off,8*nants*nfeeds*nchan,iostat)
    hdaccess(item)

    # Take reciprocal of gains
    for i in 0...(nants*nfeeds*nchan)
      bandpass[i] = 1.0 / bandpass[i] if bandpass[i].abs > 0
    end

    # TODO Perform frequency selection, if needed.
    # TODO Blank out the unwanted antennas.

    [bandpass, freqs]
  end
  module_function :get_bandpass
end
