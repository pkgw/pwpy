$-w = true if $0 == __FILE__

# $Id$

require 'tempfile'

module Mirdl
  module Task

    def run(prog,opts={})
      if Hash === opts
        # Allow request for sterr redirect to stdout
        if opts.has_key? :stderr
          stderr = opts[:stderr]
          opts.delete(:stderr)
        elsif opts.has_key? 'stderr'
          stderr = opts['stderr']
          opts.delete('stderr')
        else
          stderr = false
        end
        opts = opts.map do |k,v|
          "#{k}='#{v}'" unless v.to_s.empty?
        end
        opts << '2>&1' if stderr
        opts = opts.join(' ')
      elsif Array === opts
        opts = opts.map do |kv|
          k, v = kv.to_s.split('=', 2)
          (v && !v.empty?) ?  "#{k}='#{v}'" : k
        end
        opts = opts.join(' ')
      elsif ! String === opts
        raise "options must be Hash, Array, or String (not #{opts.class})"
      end
      cmd = %Q{#{prog} #{opts}}.strip
      $stderr.puts cmd if $DEBUG
      %x{#{cmd}}
    end
    module_function :run

    def runlog(prog, opts={})
      tf = Tempfile.new('mirdl_tasks')
      if Hash === opts
        # Allow request for sterr redirect to stdout
        if opts.has_key? :stderr
          stderr = opts[:stderr]
          opts.delete(:stderr)
        elsif opts.has_key? 'stderr'
          stderr = opts['stderr']
          opts.delete('stderr')
        else
          stderr = false
        end
        opts.merge!(:log => tf.path)
        opts = opts.map do |k,v|
          "#{k}='#{v}'" unless v.to_s.empty?
        end
        opts << '2>&1' if stderr
        opts = opts.join(' ')
      elsif Array === opts
        opts = opts.map do |kv|
          k, v = kv.to_s.split('=', 2)
          (v && !v.empty?) ?  "#{k}='#{v}'" : k
        end
        opts = opts.join(' ')
      elsif ! String === opts
        raise "options must be Hash, Array, or String (not #{opts.class})"
      end
      cmd = %Q{#{prog} #{opts}}.strip
      $stderr.puts cmd if $DEBUG
      stdout = %x{#{cmd}}
      log = tf.read
      tf.close!
      [stdout, log]
    end
    module_function :runlog

  end # module Task
end # module Mirdl
