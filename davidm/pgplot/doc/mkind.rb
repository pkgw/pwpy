funcs = %w[
  pgopen
  pgbeg
  pgask
  pgenv
  pgline
  pgpt
  pgpnts
  pgbin
  pghist
  pgerrb
  pgerrx
  pgerry
  pgcont
  pgcons
  pgconb
  pgconf
  pgconl
  pgimag
  pggray
  pgctab
  pgpixl
  pgvect
  pgband
  pgolin
  pgncur
  pglcur
  pgtick
  pgaxis
]
rbpg={}
funcs.each{|f| rbpg[f.upcase]=true }

fin=open(ARGV[0])
fout=open(ARGV[1],"w")
fout.print "
=begin
= Ruby/PGPLOT categorized method index
"

fin.each do |line|
  line.chomp!
  name = line[/(^PG[A-Z0-9]+)/]
  #line.sub!(/^# /, "===")
  line.sub!(/^(PG[A-Z0-9]+)/, '* (({\1}))')
  #if rbpg[name]
  #  line.gsub!(/\b(PG(?!PLOT)[A-Z0-9]+)/) do |x|
  #    '((<%s|URL:rbpg-doc.html#%s>))' % [x.downcase,x]
  #  end
  #  line << ' ( ((<FORTRAN|URL:pgplot.html#%s>)) )' % name
  #else
    line.gsub!(/\b(PG(?!PLOT)[A-Z0-9]+)/) do |x|
      '((<%s|URL:rbpgplot.html#%s>))' % [x.downcase,x]
    end
  #end
  fout.puts(line)
end

fout.print "
<<< trailer
=end
"
