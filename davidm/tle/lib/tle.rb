require 'tle_ext'

module Tle

  # Array mapping gps prn to satellite number
  GPSPRN_SATNUM = [
      nil, 22231, 28474, 23833, 22877, 22779, 23027, 32711, 25030, 22700, #  1 -  9
    23953, 25933, 29601, 24876, 26605, 32260, 27663, 28874, 26690, 28190, # 10 - 19
    26360, 27704, 28129, 28361, 21552, 21890, 22014, 22108, 26407, 32384, # 20 - 29
    24320, 29486, 20959                                                   # 30 - 32
  ]

  # Hash mapping satellite aliases to satellite number
  TLE_ALIASES = {
    :iss => 25544,
    :xm4 => 29520,
  }

  # Hash mapping satellite number to Tle::Elements object.
  # Also supports alias lookups
  TLE = Hash.new {|h, k| TLE[TLE_ALIASES[k]] if TLE_ALIASES.has_key?(k)}

  # Special GPS alias that returns Object allowing for lookup by PRN
  TLE[:gps] = Hash.new {|h, k| TLE[GPSPRN_SATNUM[k]]}

  # Reads a TLE file and returns hash mapping satellite number to Tle::Elements
  # object for all TLEs contained in the file.
  def read_tle(f, consts=Tle::WGS72)
    tle = {}
    line1 = nil
    File.foreach(f) do |l|
      l.chomp!
      case l
      when /^1 /
        line1 = l
      when /^2 /
        satnum = l[2..6].to_i
        tle[satnum] = Tle::Elements.new(line1, l, consts) if line1
        line1 = nil
      end
    end
    tle
  end
  module_function :read_tle

  # Reads a TLE file named +f+ and merges the contents with the TLE Hash.  Note
  # that the file contents always take precedence over any existing TLE
  # contents regardless of epochs.  +f+ may also be an Array of filenames.
  def load_tle(f, consts=Tle::WGS72)
    f = [f] unless Array === f
    f.each {|ff| TLE.merge!(read_tle(ff, consts))}
    nil
  end
  module_function :load_tle

end
