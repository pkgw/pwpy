class Formatter
  def initialize(stream)
    @stream = stream
  end
  def <<(a)
    @stream << a
  end
  def print(*a)
    @stream << String(a)
  end
  def stream
    @stream
  end
end

class FormatterRD < Formatter
  def printhead
    @stream << "
=begin
= Ruby/PGPLOT method descriptions
This page contains descriptions of Ruby/PGPLOT method
whose arguments are modified from original PGPLOT subroutines.
"
  end

  def printtrail
    print "
<<< trailer
=end
"
  end

  def subject(x)
    @stream <<
      x.sub(/^\s*(PG\w+)/){'=== ((*%s*))' % $1.downcase}
  end

  def methoddoc(x)
    s=''
    x=[x] if String===x
    x.each{|line| s<<line}
    @stream << s
  end
  def docbegin; end
  def docend; end
end


class FormatterHTML < Formatter
  def encode(a)
    a = a.gsub(/&/,'&amp')
    a.gsub!(/</,'&lt')
    a.gsub!(/>/,'&gt')
    a.gsub!(/\b(PG(?!PLOT)[A-Z0-9]+)/) {
      '<a href="#%s">%s</a>' % [$1,$1]
    }
    a
  end

  def <<(a)
    @stream << encode(a)
  end

  def printhead
    @stream <<'
<?xml version="1.0" ?>
<!DOCTYPE html 
  PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>index</title>
<meta http-equiv="Content-Style-Type" content="text/css">
<style type="text/css"><!--
 body { background: white; color: black }
dl {
  margin-left: 1em;
  margin-right: 2em;
  padding: 2pt 1em 2pt 0.5em;
  border-width: thin 0 thin thin;
  border-color: #aaaaff;
  background-color: #eeeeff
}
h1 {
  padding: 0.2em 0.5em 0.2em 0.5em;
  border-style: solid;
  border-width: thin thick thin thick;
  border-color: #bbbbff;
  color: #444444;
  background-color: #eeeeff;
}
h2 {
  padding: 0 0.75em 0 0.5em;
  border-style: solid;
  text-indent: 0em;
  background-color: #eeffee;
  border-color: #88bb88;
  color: #444444;
  border-width: 0 0 thin 7pt;
}
pre { 
  white-space:  pre;
  padding:      0.5em;
  border-style: solid;
  border-color: #CCCCCC;
  border-width: 1px 2px 2px 1px;
}
h3 {
  padding: 0 2em 0pt 0.25em;
  border-style: solid;
  border-color: #bb88ff;
  color: #444444;
  border-width: 0 0 thin thick;
}
--></style>
</head>
<body bgcolor="#ffffff">
<h1>Ruby/PGPLOT method descriptions</h1>
Most part of this document is from the original PGPLOT distribution
and copyrighted by Dr. Tim Pearson.
<b>Do not</b> redistribute this document
separately from Ruby/PGPLOT distribution
without his permission.
<hr>
<h2>Index</h2>
'
  end

  def printtrail
    print <<EOL
</body>
</html>
EOL
  end

  def subject(x)
    @stream << '<h3>' << x.sub(/^\s*(PG\w+)/) {
      '<a name="%s"><em>%s</em>' % [$1,$1.downcase]
    } << "</a></h3>\n"
    $1.downcase
  end

  def printindex(x)
    @stream << x.chomp.sub(/^\s*(PG\w+)/) {
      '<li><a href="#%s"><code>%s</code></a>' % [$1,$1.downcase]
    } << "\n"
  end

  def methoddoc(x)
    s=''
    if String===x
      x = [x] 
    end 

    line = x.shift
    if line =~ /\(/
      while line !~ /\(.*\)/m
	line << x.shift
      end
    end

    if line =~ /^---\s*(pg.*)/m
      @stream << "<dl><dt><code>%s</code></dl>\n" % encode($1)
      while x[0]=~/^\s*$/
	x.shift
      end
      if !x.empty?
	@stream << "<pre>\n--- Ruby notes ---\n"
	x.each{|i| @stream<<i}
	@stream << "</pre>\n"
      end
    end
    @stream << "<pre>\n"
  end

  def docbegin
    #@stream << "<pre>\n"
  end
  def docend
    @stream << "</pre>\n<hr>\n"
  end
end


class PgDoc

  def autofunclist
    pgfunc_auto = %w(
pgend::
pgbbuf::
pgebuf::
pgpage::
pgpap:1,1:
pgupdt::
pgpanl:1,1:
pgclos::

pgbox:2,1,0,2,1,0:
pgtbox:2,1,0,2,1,0:
pgvsiz:1,1,1,1:
pgvstd::
pgwnad:1,1,1,1:
pgsubp:0,0:

pgwedg:2,1,1,1,1,2:

# Draw Funcs
pgdraw:1,1:
pgmove:1,1:
pgrect:1,1,1,1:
pgarro:1,1,1,1:
pgcirc:1,1,1:
pgpt1:1,1,0:
pgerr1:0,1,1,1,1:
pglab:2,2,2:
pgptxt:1,1,1,1,2:
pgtext:1,1,2:
pgmtxt:2,1,1,1,2:
pgetxt::

pgiden::
pgldev::
pgsave::
pgunsa::
pgeras::

# Set Funcs
pgsch:1:
pgscf:0:
pgsci:0:
pgsfs:0:
pgsls:0:
pgslw:0:
pgsclp:0:
pgsitf:0:
pgslct:0:
pgstbg:0:
pgscr:0,1,1,1:
pgshls:0,1,1,1:
pgsah:0,1,1:
pgscrl:1,1:
pgscir:0,0:
pgscrn:0,2:0
pgshs:1,1,1:
pgsvp:1,1,1,1:
pgswin:1,1,1,1:

# Query Funcs
pgqch::1
pgqcf::0
pgqci::0
pgqfs::0
pgqls::0
pgqlw::0
pgqclp::0
pgqid::0
pgqitf::0
pgqndt::0
pgqtbg::0
pgqcr:0:1,1,1
pgqvp:0:1,1,1,1
pgqwin::1,1,1,1
pgqcol::0,0
pgqcir::0,0
pgqpos::1,1
pgqvsz:0:1,1,1,1

).grep(/:.*:/).collect{|i| i.split(":",3)}

    @autofunc={}
    pgfunc_auto.each do |x|
      @autofunc[x[0]] = x[1..2].collect{|i| i.split(",").size}
    end
  end

  def manualfunclist
    @manualfunc={}
    curfunc=nil
    File.open("../rb_pgplot.c.in").each do |line|
      case line
      when %r'^/\* (PG\w+)'
	curfunc = $1.downcase
	@manualfunc[curfunc] = []
	line.sub!(%r'^/\*\s*','')
      when %r'^\*/'
	curfunc = nil
      else
	if h = @manualfunc[curfunc]
	  h << line
	end
      end
    end
  end

  def mergefunclist
    @mergefunc = @manualfunc.keys
    @autofunc.each_key do |x|
      @mergefunc << x
    end
    @mergefunc.sort!
  end

  def initialize(formatter)
    autofunclist
    manualfunclist
    mergefunclist
    @indx = formatter.new('')
    @head = formatter.new('')
    @body = formatter.new('')
    @tail = formatter.new('')
  end


  def defmode()
    funcdef=''
    while @doc[0] !~ /^C/
      line = @doc.shift
      line.chomp!
      if line.sub!(/^\s+SUBROUTINE /,'--- ') ||
	 line.sub!(/^\s+[A-Z0-9\s]+ FUNCTION /,'--- ') ||
	 line.sub!(/^     [^ ]\s*/,'            ')
	funcdef << line.downcase
      end
    end
    #p [funcdef,@doc[0]]

    if @manualfunc[@name]
      # Definded in rb_pgplot.c.in
      @body.methoddoc(@manualfunc[@name])
    else
      # Automatically generated
      #p [@name,@autofunc[@name]]
      nin  = @autofunc[@name][0]
      nout = @autofunc[@name][1]
      funcdef =~ /\(\s*(\w+\s*(?:,\s*\w+\s*)*)\s*\)/
      if s = $1
	a = s.split(/\s*,\s*/)
	funcdef = "---  #{@name}"
	b = a[0,nin].join(', ')
	funcdef << "( " << b << " )" if b.size>0
	b = a[nin,nout]
	funcdef << " #=> " << b.join(', ') if b.size>0
      end
      @body.methoddoc(funcdef)
    end
  end

  def docmode()
    while line = @doc.shift
      case line
      when /^C%/
	# C definition
      when /^C\+/
	defmode()
	while @doc[0] =~ /^C\s*$/
	  @doc.shift
	end
      when /^C/
	line.sub!(/^(     :)/, ' \1')
	line.sub!(/^C.?/,'')
	@body << line << "\n"
      end
    end
  end

  def docextr(fin)
    @doc = []
    fin.each do |line|
      return @doc if line =~ /^C--/
      @doc << line.chomp
    end
    @doc
  end

  def doit
    dir='/home/masa/src/plot/pgplot/src/'
    @head.printhead
    @mergefunc.each do |f| 
      if name = f[/(pg\w+)/]
	begin
	  fin = open(dir+name+'.f')
	rescue
	  fin = nil
	end
	if fin
	  fin.each do |line|
	    if line.sub!(/^C\*/,'')
	      @indx.printindex(line)
	      @name = @body.subject(line)
	      @body.docbegin
	      @doc = docextr(fin)
	      docmode()
	      @body.docend
	    end
	  end
	end
	@body << "\n\n"
      end
    end
    @tail.printtrail
    b = @head.stream
    b << "<ul>\n" << @indx.stream <<
      "</ul><hr>\n<h2>Descriptions</h2>\n" <<
      @body.stream << @tail.stream
    b
  end

end

#PgDoc.new(FormatterRD.new(File.open(ARGV[0],"w"))).doit
#PgDoc.new(FormatterHTML.new(File.open(ARGV[0],"w"))).doit

File.open(ARGV[0],"w") << PgDoc.new(FormatterHTML).doit
