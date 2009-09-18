# cogen.rb : Code generation script for Ruby/PGPLOT
#
#   Copyright (c) 2000,2001 Masahiro TANAKA <masa@ir.isas.ac.jp>
#
#   This program is free software.
#   You can distribute/modify this program
#   under the same terms as Ruby itself.
#   NO WARRANTY.

$pgfuncs = %w(

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
pgqcs:0:1,1
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


def pgfuncgen(name, inp, out)
  inp = inp.split(",").collect{|i| i.to_i}
  out = out.split(",").collect{|i| i.to_i}
  ninp = inp.size
  nout = out.size
  # int->0, float->1
  val2 = ["NUM2INT","NUM2DBL","STR2CSTR"]
  type = ["int","float",nil]
  conv = ["INT2NUM","rb_float_new",nil]
  # Initialize Array
  prot = ["VALUE obj"]
  pass = []
  vars = []
  retn = []
  inp.each_with_index { |i,x|
    prot << "VALUE arg#{x}"
    pass << "#{val2[i]}(arg#{x})"
  }
  out.each_with_index { |i,x|
    vars << "#{type[i]} var#{x};"
    pass << "&var#{x}"
    retn << "#{conv[i]}(var#{x})"
  }
  if nout==0 then
    retn = "Qtrue";
  elsif nout>1 then
    retn = "rb_ary_new3(#{nout},"+retn.join(",")+")"
  end

  prot = prot.join(",")
  pass = pass.join(",")

  return "
static VALUE
  rb_pgplot_#{name}(#{prot})
{
  #{vars}
  c#{name}(#{pass});
  return #{retn};
}
"
end


def cogen_pgplot
  fin  = open("rb_pgplot.c.in","r")
  fout = open("rb_pgplot.c","w")
  while l = fin.gets
    if    /--- auto-generated funcs will be placed here ---/ =~ l
      $pgfuncs.each{|x| fout.print pgfuncgen(*x)}
    elsif /--- auto-generated defs will be placed here ---/  =~ l
      $pgfuncs.each{|x|
	n = x[1].split(",").size
	fout.print "  rb_define_module_function(mPgplot,\"#{x[0]}\",rb_pgplot_#{x[0]},#{n});\n"}
    else
      fout.print
    end
  end
end

cogen_pgplot
