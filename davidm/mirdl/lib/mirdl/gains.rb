# gains.rb - Method(s) to get antenna gains

require 'narray'

module Mirdl

  # Returns Hash with jd as key and NArray.scomplex(ngains) of gains.
  # NArray has gains for a1f1, ..., a1fF, a2f1, ..., a2fF, ..., aNf1, ..., aNfF
  # where F is nfeeds and N is nanta.
  def get_gains(tno, sels=nil)
    return nil unless hdprsnt(tno, :gains)

    # Determine the various parameters, and check their validity. We have pretty
    # well checked that all is OK before, so nothing should go wrong.
    doselect = sels && selProbe(sels,'time?')
    nfeeds = rdhdi(tno,'nfeeds',1)
    ntau   = rdhdi(tno,'ntau',0)
    ngains = rdhdi(tno,'ngains',1)
    nsols  = rdhdi(tno,'nsols',1)

    #puts "# nfeeds = #{nfeeds}"
    #puts "# ntau   = #{ntau  }"
    #puts "# ngains = #{ngains}"
    #puts "# nsols  = #{nsols }"

    if(nfeeds <= 0 || ntau < 0 || ngains <= 0 || nsols <= 0)
      bug('e','Bad gain table size information')
    end

    nants = ngains / (nfeeds + ntau)
    #puts "# nants  = #{nants }"

    if(nants*(nfeeds+ntau) != ngains)
      bug('e','Number of gains does equal nants*(nfeeds+ntau)')
    end

    item = haccess(tno,'gains','read')

    # Determine what we think the number of solutions should be from the
    # size of the file.

    if(hsize(item) != 8+(ngains+1)*8*nsols)
      bug('e','Gain table does not look the right size')
    end

    # All is OK. Lets go for it.
    tbuf = NArray.float(1)
    gains = {}
    k = 0
    offset = 8

    for i in 1..nsols
      t = hreadd(item,tbuf,offset,8)[0]
      offset = offset + 8
      if(doselect)then
        select = SelProbe(sels,'time',t)
      else
        select = true
      end
      if(select)then
        #t0 ||= (t - 1).to_i + 0.5
        gains[t] = NArray.scomplex(ngains)
        hreadc(item,gains[t],offset,8*ngains)
        k = k + 1
      end
      offset = offset + 8*ngains
    end
    hdaccess(item)

    # Return empty gains Hash if no gains were selected
    return gains if k == 0

    nsols = k

    # Blank out the antenna gains that were not selected.

    if(sels && selProbe(sels,'antennae?',0.0))
      ant = []
      for i in 0...nants
        #ant[i] = selProbe(sels, 'antennae', 257.0*i)
        # Add antnum to list of non-selected ants unless it was selected
        ant << i unless selProbe(sels, 'antennae', 257.0*i)
      end

      gains.each_value do |na|
        na[ant] = 0
      end

      #for k in 0...nsols
      #  for j in 0...nants
      #    for i in 0...nfeeds
      #      if !ant[j]
      #        gains[k][j*nfeeds+i] = 0
      #      end
      #    end
      #  end
      #end
    end

    gains
  end
  module_function :get_gains
end
