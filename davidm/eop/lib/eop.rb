# $Id$

# TODO Give precendence to .daily files over .out files

require 'date'
require 'time'
require 'scanf'
require 'ftools'
require 'ostruct'
require 'net/http'

class Eop < OpenStruct

  EOP = {}

  # Dummy EOP for unknown days
  EOP0 = Eop.new(
    'p00000 ' \
    '0.00000 .00000 ' \
    '0.00000 .00000 ' \
    '0.000000 .000000  ' \
    '.00000 0.00000  ' \
    '.00000 0.00000'
  )

  # Used to fetch Eop instances by +amjd+, which can be an (astronomical)
  # Modified Julian Date (or other object which has an #amjd method) or a
  # Numeric.  In either case, it will be "floored" to the largest integer not
  # greater than +amjd+.
  def self.[](amjd)
    amjd = amjd.amjd if amjd.respond_to?(:amjd)
    amjd = amjd.floor
    # Lazy init
    unless EOP.has_key?(amjd)
      today = DateTime.now.amjd.floor
      case amjd
      when today-90..today+15
        # Get last 90 through next 15 days from gpsdaily file
        load_gpsrapid(:file => 'gpsrapid.daily')
      when GPSRAPID_OUT_FIRST...today-90
        # Get other dates from gpsrapid.out
        load_gpsrapid(:file => 'gpsrapid.out')
      end
    end
    eop = EOP[amjd]
    EOP[amjd] = Eop.new(eop) if String === eop
    EOP[amjd]
  end

  def initialize(line)
    fields = line.scanf(GPSRAPID_FMT)
    amjd = fields[1]
    super({
      :prediction  => (fields[ 0] == 'p'),
      :amjd        =>  fields[ 1],
      :pmx         =>  fields[ 2],
      :pmx_err     =>  fields[ 3],
      :pmy         =>  fields[ 4],
      :pmy_err     =>  fields[ 5],
      :ut1_utc     =>  fields[ 6],
      :ut1_utc_err =>  fields[ 7],
      :dpsi        =>  fields[ 8],
      :dpsi_err    =>  fields[ 9],
      :deps        =>  fields[10],
      :deps_err    =>  fields[11],
    })
    # Remove foo= singleton methods
    singleton_methods.grep(/=$/).each do |m|
      instance_eval "undef #{m}"
    end
    # Rename "prediction" method to "prediction?"
    instance_eval 'alias :prediction? :prediction; undef :prediction'
    # Prevent creation of additional fields
    freeze
  end

  # Format string to parse gpsrapid data.
  #
  # The format of the gpsrapid.out and gpsrapid.daily files is:
  #
  # Col.#    Format  Quantity
  # -------  ------  -------------------------------------------------------------
  # 1        X       [blank or "p" if values are predictions]
  # 2-6      I5      Modified Julian Date (MJD)
  # 7        X       [blank]
  # 8-14     F7.5    Bull. A PM-x (sec. of arc)
  # 15-21    F7.5    error in PM-x (sec. of arc)
  # 22       X       [blank]
  # 23-29    F7.5    Bull. A PM-y (sec. of arc)
  # 30-36    F7.5    error in PM-y (sec. of arc)
  # 37       X       [blank]
  # 38-45    F8.6    Bull. A UT1-UTC (sec. of time)
  # 46-53    F8.6    error in UT1-UTC (sec. of time)
  # 54       X       [blank]
  # 55-61    F7.5    Bull. A dPSI (sec. of arc)
  # 62       X       [blank]
  # 63-69    F7.5    error in dPSI (sec. of arc)
  # 70       X       [blank]
  # 71-77    F7.5    Bull. A dEPSILON (sec. of arc)
  # 78       X       [blank]
  # 79-85    F7.5    error in dEPSILON (sec. of arc)
  GPSRAPID_FMT = '%c%5d%*c%7f%7f%*c%7f%7f%*c%8f%8f%*c%7f%*c%7f%*c%7f%*c%7f'

  # Astronomical Modified Julian Date of first entry of gpsrapid.out
  GPSRAPID_OUT_FIRST = DateTime.civil(1992, 5, 1).amjd

  # TODO provide accessor methods
  @@eop_url = 'http://maia.usno.navy.mil/ser7/'
  @@eop_dir = File.join(ENV['HOME'], '.eop')

  def self.http_update(file, url, safe_age)
    dir = File.dirname(file)
    uri = URI.parse(url)
    File.makedirs(dir) unless File.exist?(dir)
    local_lastmod = File.exist?(file) ? File.mtime(file) : Time.at(0)
    # Avoid unecessary checks
    if Time.now - local_lastmod > safe_age * 24*60*60
      remote_lastmod = Net::HTTP.start(uri.host) do |http|
        Time.parse(http.head(uri.path)['Last-Modified']||'19700101')
      end
      if remote_lastmod > local_lastmod
        warn "#{File.basename(__FILE__)}: fetching #{uri}"
        Net::HTTP.get_response(uri) do |res|
          if Net::HTTPSuccess === res
            File.open(file, 'w') do |f|
              res.read_body do |chunk|
                f.write(chunk)
              end
            end
            mtime = Time.parse(res['Last-Modified'])
            File.utime(Time.now, mtime, file)
          end
        end
      end
    end
  end

  def self.fetch_gpsrapid(file, dir=@@eop_dir, url=@@eop_url)
    url += "/" + file
    http_update(url, File.join(dir,file))
  end

  def self.update
    [['out', 7], ['daily', 1]].each do |ext, age|
      name = 'gpsrapid.' + ext
      http_update(File.join(@@eop_dir, name), @@eop_url + name, age)
    end
    nil
  end

  def self.load_gpsrapid(opts={})
    opts = {
      :file => 'gpsrapid.daily',
      :path => ['.', File.join(ENV['HOME'], '.eop'), '/etc/eop']
    }.merge!(opts)

    dir = opts[:path].find {|d| File.readable?(File.join(d, opts[:file]))}
    if dir.nil?
      dir = File.join(ENV['HOME'], '.eop')
      fetch_gpsrapid(opts[:file], dir, opts[:url]||@@eop_url)
      unless File.readable?(File.join(dir, opts[:file]))
        raise "#{opts[:file]} not found in #{opts[:path].join(File::PATH_SEPARATOR)}"
      end
    else
      # TODO Check timestamp of file
    end

    filename = File.join(dir, opts[:file])

    File.foreach(filename) do |l|
      amjd = l[1,5].to_i(10)
      EOP[amjd] = l unless Eop === EOP[amjd] 
    end
  end
end
