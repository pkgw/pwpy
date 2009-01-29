$-w = true if $0 == __FILE__

# $Id$

require 'tempfile'

module MiriadRunner

  begin
    require 'fx/conf'
    def get_antmap
      namenum = FXConf.antpos_file.grep(/^[^#]/).map do |l|
        name, num = l.split[3..4]
        [name, num.to_i]
      end
      antmap = Hash[*(namenum.flatten)]
      antmap.merge!(antmap.invert)
    end
  rescue LoadError
    def get_antmap
      {}
    end
  end
  module_function :get_antmap

  ANTMAP = get_antmap

  def run_miriad(prog,opts)
    optstr = opts.map {|k,v| "#{k}='#{v}'" unless v.to_s.empty?}.join(' ')
    cmd = %Q{#{prog} #{optstr}}
    STDERR.puts cmd if $verbose
    %x{#{cmd}}
  end
  module_function :run_miriad

  # Get nants
  def get_nants(vis)
    lines = run_miriad(:prthd, :in => vis)
    nants = lines.grep(/^Number of antennae:/) do |line|
      line.split[3].to_i
    end
    nants[0]
  end
  module_function :get_nants

  # Get pols present
  def get_pols_present(vis)
    lines = run_miriad(:prthd, :in => vis)
    pols = lines.grep(/^Polarisations Present:/) do |line|
      line.split[2].downcase!.split(',')
    end
    pols.flatten
  end
  module_function :get_pols_present

  # pol is two character pol code (e.g. xx, yy, etc.)
  def get_ants_present_by_pol(vis,pol)
    nants = get_nants(vis)
    lines = run_miriad(
      :uvlist,
      :vis => vis,
      :line => 'ch,1,1,1',
      :select => "auto,pol(#{pol})",
      :recnum => "#{nants}"
    ).split("\n")
    lines.slice!(0,12)
    ants = {}
    lines.each do |line|
      ant = line.split[3].to_i
      break if ants.has_key?(ant)
      ants[ant] = true
    end
    ants.keys.sort
  end
  module_function :get_ants_present_by_pol
   
  # Get ants present.  Returns a two element array [[xants],[yants]]
  def get_ants_present(vis)
    ['xx','yy'].map {|pol| get_ants_present_by_pol(vis,pol)}
  end
  module_function :get_ants_present

  # Get default refants
  def default_refants(vis)
    xants, yants = get_ants_present(vis)
    # Use common ant if dual pol dataset
    refantx = refanty = (xants&yants)[0]
    refantx ||= xants[0] || 0
    refanty ||= yants[0] || 0
    [refantx, refanty]
  end
  module_function :default_refants

  # Get delay0 values from dataset
  def get_fixed_delays(vis)
    nants = get_nants(vis)
    tf = Tempfile.new('varplt');
    run_miriad(
      :varplt,
      :vis => vis,
      :xaxis => 'time',
      :yaxis => 'delay0',
      :options => 'dtime',
      :log => tf.path
    )
    # Skip first three lines
    3.times {tf.readline}
    # Get number of delay0 values (nants*nfeed)
    ndelays = tf.readline.split[2].to_i
    nfeed = ndelays / nants
    # Get all remaining lines, join, then split into "words"
    words = tf.readlines.join.split
    # Close and delete tempfile
    tf.close!

    # Parse words
    delay0 = words[1..ndelays].map {|w| w.to_f}
    if nfeed == 2
      # Partition into [[1x, 2x, ...], [1y, 2y, ...]]
      delay0 = [delay0[0...ndelays/2], delay0[ndelays/2..-1]]
    else
      # "Partition" into [[1, 2, ...]]
      delay0 = [delay0]
    end
    # Unshift 0.0 onto each pol's delays so that ant number can be used as index
    delay0.map! {|dp| dp.unshift 0.0}
  end
  module_function :get_fixed_delays

  # Get delay values from gains file
  # Returns array of arrays (i.e. one array for each time interval)
  # The 0th entry of each array of delays if the dtime, this means that
  # antenna numbers can be used as indexes into these delay arrays.
  def get_gains_delays(vis)
    tf = Tempfile.new('gpplt');
    run_miriad(
      :gpplt,
      :vis => vis,
      :options => 'delays,dtime',
      :log => tf.path
    )
    # Skip first three lines
    3.times {tf.readline}
    # Get number of "words" per solution (i.e. one plus number of delay values
    # (nants only, not nants*nfeed))
    num_words_per_sol = 1 + tf.readline.split[4].to_i
    # Add one for the dtime value
    # Get all remaining lines, join, then split into "words"
    words = tf.readlines.join.split
    # Close and delete tempfile
    tf.close!

    # Parse words in batches of num_words_per_sol (i.e. one batch per solution)
    nsols = words.length / (num_words_per_sol)
    (0...nsols).map do |i|
      offset = i * num_words_per_sol
      words[offset,num_words_per_sol].map {|w| w.to_f}
    end
  end
  module_function :get_gains_delays

  def mfcal(vis,opts={})
    opts.merge!(:vis => vis)
    output = run_miriad(:mfcal, opts)
    # TODO use output.grep
    raise "no solutions saved" unless output.split("\n")[-1] == "Saving solution ..."
    output
  end
  module_function :mfcal

  # TODO Dynamically determine suitable number of channels to let mfcal work
  # with given its limited buffer space
  def mfcal_delays(vis,pol,opts={})
    refant = opts[:refant] || default_refants(vis)[(pol[0] == ?y) ? 1 : 0]
    opts = {
      # Overridable opts
      :line => 'ch,45,106,18',
      :refant => refant,
      :interval => 1
    }.merge!(opts).merge!(
      # Non-overridable opts
      :options => 'delay,nopassol',
      :select => "pol(#{pol})"
    )
    mfcal(vis,opts)
  end
  module_function :mfcal_delays

  # Returns [[xants],[xsol0,xsol1,...],[yants],[ysol0,ysol1,...]]
  # where each solution is an array (nants elements long) of floats
  def get_delay_solutions(vis,refantx,refanty,opts={})
    xsols = ysols = []
    xants, yants = get_ants_present(vis)

    xants.clear unless xants.include?(refantx)
    unless xants.empty?
      optsxx = opts.merge(:refant => refantx)
      mfcal_delays(vis,'xx',optsxx)
      xsols = get_gains_delays(vis)
    end

    yants.clear unless yants.include?(refanty)
    unless yants.empty?
      optsyy = opts.merge(:refant => refanty)
      mfcal_delays(vis,'yy',optsyy)
      ysols = get_gains_delays(vis)
    end

    [xants, xsols, yants, ysols]
  end
  module_function :get_delay_solutions

end # module MiriadRunner
