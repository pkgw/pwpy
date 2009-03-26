# $Id$

require 'narray'
require 'pgplot'

module Pgplot

  module Color
    BLACK, WHITE, RED, GREEN, BLUE, CYAN, MAGENTA, YELLOW, ORANGE,
    GREEN_YELLOW, GREEN_CYAN, BLUE_CYAN, BLUE_MAGENTA, RED_MAGENTA, DARK_GRAY,
    LIGHT_GRAY = (0..15).to_a

    RAINBOW = [RED, ORANGE, YELLOW, GREEN_YELLOW, GREEN, GREEN_CYAN, CYAN, BLUE_CYAN, BLUE, BLUE_MAGENTA, MAGENTA, RED_MAGENTA]
    def rainbow(i)
      if i.respond_to? :map
        i.map {|ii| rainbow(ii)}
      else
        RAINBOW[i%RAINBOW.length]
      end
    end
    module_function :rainbow
  end

  module Marker
    SQUARE     =  0
    DOT        =  1
    PLUS       =  2
    STAR       =  3
    CIRCLE     =  4
    CROSS      =  5
    SQUARE1    =  6
    TRIANGLE   =  7
    CIRCPLUS   =  8
    CIRCDOT    =  9
    SQUAREDOTS = 10
    DIAMOND    = 11
    STAR5      = 12
  end

  module Line
    FULL = SOLID = NORMAL = DEFAULT = 1
    DASHED = 2
    DOT_DASH_DOT_DASH = 3
    DOTTED = 4
    DASH_DOT_DOT_DOT = 5
  end

  module Fill
    SOLID = NORMAL = DEFAULT = 1
    OUTLINE = 2
    HATCHED = 3
    CROSS_HATCHED = 4
  end

  class Plotter
    include Pgplot

    VERSION = '$Id$'

    @@instances = {}
    @@last_selected = nil

    attr_reader :pgid
    attr_reader :device

    def initialize(opts={})
      opts = {
        :device => nil,
        :ask => false,
        :nx => 1,
        :ny => 1
      }.merge!(opts)

      @device = opts[:device] || opts[:dev] || ENV['PGPLOT_DEV'] || '/xs'
      @pgid = pgopen(device)
      raise "error opening device #{device}" if @pgid < 0
      @@instances[@pgid] = self
      @@last_selected = self
      @state = {}
      pgask(opts[:ask])
      if opts[:nx] != 1 || opts[:ny] != 1
        pgsubp(opts[:nx], opts[:ny])
      end
    end

    #def self.reopen(id)
    #  raise "invalid id (#{id})" unless @@instances[id]
    #end

    def self.last_selected
      @@last_selected
    end

    def self.instances
      @@instances
    end

    def select(pgid=@pgid)
      raise 'pgid #{pgid} not opened by Pgplot::Plotter' unless @@instances[pgid]

      pgin, pgout = IO.pipe
      begin
        pgout.sync = true
        dupout = STDOUT.dup
        begin
          STDOUT.reopen(pgout)
          begin
            pgslct(pgid)
          ensure
            STDOUT.reopen(dupout)
          end
        ensure
          dupout.close
        end
      ensure
        pgout.close
        begin
          msg = pgin.read.chomp!
          raise msg if msg =~ /%PGPLOT/
          @@last_selected = @@instances[pgid]
        ensure
          pgin.close
        end
      end
      @@last_selected
    end

    def close
      select
      Pgplot.pgclos
      @@instances.delete(@pgid)
    end
    alias :clos   :close
    alias :pgclos :close

    def method_missing(sym, *args)
      select
      m = sym.to_s
      m = 'pg' + m unless m =~ /^pg/
      Pgplot.send(m, *args)
    end

    def to_plotable(a)
      case a
      when Array, NArray: a
      else
        [:to_na, :to_a2, :to_a].each do |m|
          return a.send(m) if a.respond_to? m
        end
        a
      end
    end
    private :to_plotable

    def plot_args(*args)
      zz=to_plotable(args[0])
      case args.length
      when 1: [(0...zz.length).to_a, zz, {}]
      when 2:
        if args[1].is_a? Hash
          [(0...zz.length).to_a, zz, args[1]]
        else
          [zz, to_plotable(args[1]), {}]
        end
      when 3: [zz, to_plotable(args[1]), args[2]]
      else raise ArgumentError, "wrong number of arguments (#{args.length} for 1, 2, or 3)"
      end
    end
    private :plot_args

    def plot(*args)
      xx, yy, opts = plot_args(*args)
                             
      opts = {
        :just => 0,
        :title => 'Untitled Plot',
        :title2 => nil,
        :xlabel => 'X Axis',
        :ylabel => 'Y Axis',
        :use_color => true,
        :border_color => Color::WHITE,
        :line_color => Color::BLUE,
        :line => :line,
        :marker => nil,
        :overlay => false,
        :yrange => nil
      }.merge!(opts)

      # Convert true to 1
      opts[:just] = 1 if opts[:just] == true

      xxmin = xx.min
      xxmax = xx.max
      if xxmin == xxmax
        xxmin -= 1
        xxmax += 1
      end

      yymin, yymax = opts[:yrange]
      unless yymin && yymax
        yymin = yy.min
        yymax = yy.max
        if yymin == yymax
          yymin -= 1
          yymax += 1
        else
          yyavg = (yymin + yymax)/2.0
          yydev = (yymax - yymin)/2.0
          yymin = yyavg - 1.1*yydev
          yymax = yyavg + 1.1*yydev
        end
      end

      # Make sure this Plotter's device is pgplot's current selection
      select
      pgbbuf

      if !opts[:overlay]
        ls = pgqls
        pgsls(Line::SOLID)
        pgsci(opts[:border_color]) if opts[:use_color]
        pgenv(xxmin, xxmax, yymin, yymax, opts[:just], -1)
        pglab(opts[:xlabel], opts[:ylabel], opts[:title])
        pgmtxt('T',0.5,0.5,0.5,opts[:title2].to_s) if opts[:title2]
        # Draw bottom and top axes
        pgaxis(xxmin,yymin,xxmax,yymin,xxmin,xxmax,:opt=>'N',:step=>0,
               :tickl=>0.5,:tickr=>0,:frac=>0.5,
               :disp=>0.5,:orient=>0)
        pgaxis(xxmin,yymax,xxmax,yymax,xxmin,xxmax,:step=>0,
               :tickl=>0,:tickr=>0.5,:frac=>0.5,
               :disp=>0.5,:orient=>0)
        # Draw y axis on left and right
        pgaxis(xxmin,yymin,xxmin,yymax,yymin,yymax,:opt=>'N',:step=>0,
               :tickl=>0,:tickr=>0.5,:frac=>0.5,
               :disp=>-0.5,:orient=>0)
        pgaxis(xxmax,yymin,xxmax,yymax,yymin,yymax,:step=>0,
               :tickl=>0.5,:tickr=>0,:frac=>0.5,
               :disp=>0.5,:orient=>0)
        pgsls(ls)
      end

      # Optionally change color
      pgsci(opts[:line_color]) if opts[:use_color]
      # Plot line
      case opts[:line]
      when :none, :nil, nil: nil
      when :bin, :stairs, :steps: pgbin(xx, yy, true)
      when :impulse
        base = if (yymin..yymax) === 0
                 old_ci = pgqci
                 old_ls = pgqls
                 pgsci(Color::WHITE)
                 pgsls(Line::DASHED)
                 pgmove(xxmin,0)
                 pgdraw(xxmax,0)
                 pgsls(old_ls)
                 pgsci(old_ci)
                 0
               elsif yymax < 0
                 yymax
               else
                 yymin
               end
        xx.length.times do |i|
          pgmove(xx[i],base)
          pgdraw(xx[i],yy[i])
        end
      else pgline(xx, yy)
      end
      # Plot points
      pgpt(xx, yy, opts[:marker]) if opts[:marker]

      pgebuf

      nil
    end

    def bin(xx,yy)
      raise 'cannot plot fewer than two bins' if xx.length < 2

      # Draw first bin
      if yy[0].to_f.nan?
        gap = true
      else
        pgmove(xx[0],yy[0])
        pgdraw((xx[0]+xx[1])/2.0,yy[0])
        gap = false
      end

      # Draw middle bins
      (1..xx.length-2).each do |i|
        if yy[i].to_f.nan?
          gap = true
          next
        end
        if gap
          pgmove((xx[i-1]+xx[i])/2.0,yy[i])
        else
          pgdraw((xx[i-1]+xx[i])/2.0,yy[i])
        end
        pgdraw((xx[i]+xx[i+1])/2.0,yy[i])
        gap = false
      end

      # Draw last bin
      if !yy[-1].to_f.nan?
        if gap
          pgmove((xx[-2]+xx[-1])/2.0,yy[-1])
        else
          pgdraw((xx[-2]+xx[-1])/2.0,yy[-1])
        end
        pgdraw(xx[-1],yy[-1])
      end
    end

    def magphase(*args)
      xx, zz, opts = plot_args(*args)
                             
      opts = {
        :just => 0,
        :title => 'Magnitude/Phase Plot',
        :title2 => nil,
        :xlabel => 'X Axis',
        :mag_label => 'Magnitude',
        :phase_label => 'Phase (degrees)',
        :use_color => true,
        :border_color => Color::WHITE,
        :mag_color => Color::BLUE,
        :phase_color => Color::YELLOW,
        :device => '/xs',
        :ph_range => [-180, 180],
        :overlay => false,
      }.merge!(opts)

      # Kludge for GSL::FFT::Complex::PackedArray
      #zz = zz.to_a2 if zz.respond_to? :to_a2

      xxmin = xx.min
      xxmax = xx.max
      if xxmin == xxmax
        xxmin -= 1
        xxmax += 1
      end

      zzabs   = if zz.respond_to? :abs; zz.abs
                else zz.map {|z| z.abs}
                end
      zzangle = if zz.respond_to? :phase; zz.phase * 180 / Math::PI
                elsif zz.respond_to? :angle; zz.angle * 180 / Math::PI
                elsif zz[0].respond_to? :phase; zz.map {|z| z.phase * 180 / Math::PI}
                elsif zz[0].respond_to? :angle; zz.map {|z| z.angle * 180 / Math::PI}
                else [0] * zz.length
                end

      zzmin = zzabs.min
      zzmax = zzabs.max
      if zzmin == zzmax
        zzmin -= 1
        zzmax += 1
      else
        zzavg = (zzmin + zzmax)/2.0
        zzdev = (zzmax - zzmin)/2.0
        zzmin = zzavg - 1.1*zzdev
        zzmax = zzavg + 1.1*zzdev
      end


      # Make sure this Plotter's device is pgplot's current selection
      select
      pgbbuf
      #pgvstd # This might be useful?

      if !opts[:overlay]
        pgsci(opts[:border_color]) if opts[:use_color]
        pgenv(xxmin, xxmax, zzmin, zzmax, opts[:just], -1)
        # Save world coordinates for magnitude axes
        @state[:wc_mag] = [xxmin, xxmax, zzmin, zzmax]
        pglab(opts[:xlabel], '', opts[:title])
        pgmtxt('T',0.5,0.5,0.5,opts[:title2].to_s) if opts[:title2]
        # Draw bottom and top axes
        pgaxis(xxmin,zzmin,xxmax,zzmin,xxmin,xxmax,:opt=>'N', :step=>0,
               :tickl=>0.5,:tickr=>0,:frac=>0.5,
               :disp=>0.5,:orient=>0)
        pgaxis(xxmin,zzmax,xxmax,zzmax,xxmin,xxmax, :step=>0,
               :tickl=>0,:tickr=>0.5,:frac=>0.5,
               :disp=>0.5,:orient=>0)

        # Plot magnitude
        # Draw y axis on left for magnitudes
        pgaxis(xxmin,zzmin,xxmin,zzmax,zzmin,zzmax,:opt=>'N',:step=>0,
               :tickl=>0,:tickr=>0.5,:frac=>0.5,
               :disp=>-0.5,:orient=>0)
        # Optionally change color
        pgsci(opts[:mag_color]) if opts[:use_color]
        # Label magnitude axis
        pgmtxt('L',2.2,0.5,0.5,opts[:mag_label])
      else # overlay mode
        # Optionally change color
        pgsci(opts[:mag_color]) if opts[:use_color]
        # TODO Set line style (etc?)
        # Restore world coords for magnitude
        pgswin(*@state[:wc_mag])
      end
      # Plot magnitude data
      #pgbin(xx, zzabs, true)
      bin(xx, zzabs)

      if !opts[:overlay]
        zzmin, zzmax = opts[:ph_range] || [zzangle.min, zzangle.max]
        zzmin = -180 if zzmin < -180
        zzmax =  180 if zzmax >  180
        if zzmin == zzmax
          zzmin -= 1
          zzmax += 1
        else
          zzmin, zzmax = zzmax, zzmin if zzmin > zzmax
          #zzavg = (zzmin + zzmax)/2.0
          #zzdev = (zzmax - zzmin)/2.0
          #zzmin = zzavg - 1.1*zzdev
          #zzmax = zzavg + 1.1*zzdev
        end
        step, nsub = case (zzmax-zzmin)
                     when (135..360): [45, 3]
                     when (45...135): [15, 3]
                     else [0, 0]
                     end

        # Save world coordinates for phase axes
        @state[:wc_phase] = [xxmin, xxmax, zzmin, zzmax]
        pgswin(*@state[:wc_phase])
        pgsci(opts[:border_color]) if opts[:use_color]
        # Draw y axis on right for phase
        pgaxis(xxmax,zzmin,xxmax,zzmax,zzmin,zzmax,:opt=>'N',
               :step=>step,:nsub=>nsub,
               :tickl=>0.5,:tickr=>0,:frac=>0.5,
               :disp=>0.3,:orient=>0)
        # Optionally change color
        pgsci(opts[:phase_color]) if opts[:use_color]
        # Label phase axis
        pgmtxt('R',2.7,0.5,0.5,opts[:phase_label])
      else
        # Optionally change color
        pgsci(opts[:phase_color]) if opts[:use_color]
        # Change window's world coordinates
        pgswin(*@state[:wc_phase])
      end
      # Plot phase points
      marker = xx.length > 100 ? Marker::DOT : Marker::STAR
      xx.length.times do |i|
        pgpt1(xx[i], zzangle[i], marker)
      end

      pgebuf

      nil
    end

    # Used to select between magnitude coordinates or phase coordinates on
    # peviously created magphase plots to enable overlay etc.
    def axis(*args)
      case args[0]
      when :mag
        pgswin(*@state[:wc_mag]) if @state[:wc_mag]
      when :phase
        pgswin(*@state[:wc_phase]) if @state[:wc_phase]
      else
        warn("Unsupported axis type #{type.inspect}")
      end
    end

  end # class Plotter

  # If +pgid+ is less than 0, create and return a new Plotter using +opts+.
  # If +pgid+ is nil, return last selected Plotter, if any, or a new Plotter
  # using +opts+.  If +pgid+ >= 0, select and return the specified Plotter.
  def figure(pgid=-1,opts={})
    if pgid.nil?
      p = Plotter.last_selected || Plotter.new(opts)
    elsif pgid < 0
      p = Plotter.new(opts)
    else
      p = Plotter.instances[pgid]
      return nil unless p
    end
    p.select
  end
  module_function :figure

  # Do an X-Y plot on the most recently selected (or new if none exist) Plotter
  def plot(*args)
    figure(nil).plot(*args)
  end
  module_function :plot

  # Do a magphase plot on the most recently selected (or new if none exist)
  # Plotter
  def magphase(*args)
    figure(nil).magphase(*args)
  end
  module_function :magphase

  # Select axis (e.g. :mag or :phase) on the most recently selected (or new if
  # none exist) Plotter
  def axis(*args)
    figure(nil).axis(*args)
  end
  module_function :axis
end
