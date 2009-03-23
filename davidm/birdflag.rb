#!/usr/bin/env ruby

# $Id$

require 'mirdl'
include Mirdl

keyini
  # d = use select keyword
  # s = use stokes keyword (needed?)
  # l = use line keyword
  # 3 = include w in preamble
  uvDatInp('dsl3')

  # Acceptance threshhold from mean (as multiples of standard deviation)
  # NB: This can be a floating point number!
  nsigma = keyr(:nsigma, 3.0)
  iter_limit = keyi(:maxiter, 50)
  
  # Allow "options=dryrun" to not do any modifications, but to report what
  # would have been done.
  optkeys = [:dryrun]
  optvals = options(optkeys)
  # Convert optkeys and optvals into a Hash
  opts = Hash[*optkeys.zip(optvals).flatten!]
keyfin

# Loop through data files
while tno = uvDatOpn
  # Count newly-flagged channels
  nflagged = 0
  # Track maxiter
  maxiter = 1

  # Get number of channels
  nchan = uvDatGti(:nchan)
  nchan = uvrdvri(tno, :nchan) if nchan == 0
  # Create a new Vis object
  v = Vis.new(nchan)

  # Loop through data
  while uvDatRd(v)
    # Skip to next if completely flagged
    # TODO What if only a few channels are not flagged?
    next if v.flags.sum == 0

    # Get data and initial flags
    d = v.data
    not_bird = v.flags

    iter = 0
    # Start iteration loop
    begin
      # Increment iter counter
      iter += 1
      # Get non-birdie subset of current data subset
      d = d[not_bird.where]
      # Compute mean and stddev of non-birdie data
      mean = d.mean
      sigma = d.stddev
      # Determine new list of non-birdie data points
      not_bird = (d-mean).abs.le(nsigma*sigma).to_type(NArray::INT)
    # End iterations if limit is exceeded or all channels are birdies or no channels are birdies
    end until iter >= iter_limit || not_bird.length == 0 || not_bird.sum == not_bird.length

    # Update maxiter?
    maxiter = iter if maxiter < iter

    # Get channel by channel flags for all channels against original data
    not_bird = (v.data-mean).abs.le(nsigma*sigma)

    # Compute new flags as not previously flagged and not_bird
    # NB: 1 means GOOD data, 0 means BAD data
    new_flags = v.flags * not_bird
    #p [v.preamble[4], mean, sigma, not_bird.where2[1].to_a, new_flags.sum - v.flags.sum]
    nflagged += v.flags.sum - new_flags.sum

    # Write out new flags
    uvflgwr(tno, new_flags) unless opts[:dryrun]
  end

  print("would have ") if opts[:dryrun]
  puts "flagged #{nflagged} baseline-channels in #{uvDatGta(:name)} (nsigma= #{nsigma} )(maxiter= #{maxiter} )"
  uvDatCls
end
