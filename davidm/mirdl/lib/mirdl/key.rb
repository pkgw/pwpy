require 'shellwords'

module Mirdl

  # void keyini_c(int, char *[])
  SYM[:keyini] = LIBMIR_UVIO['keyini_c', '0IA']
  def keyini(argv=ARGV, progname=File.basename($0))
    # If argv is a String
    if String === argv
      # Split argv like a shell command line
      argv = Shellwords.shellwords(argv) if String === argv
      # Unshift progname, if given
      argv.unshift(progname.to_s) if progname
    elsif progname
      argv = argv.dup
      argv.unshift(progname.to_s)
    end
    SYM[:keyini][argv.length, argv]
  end
  module_function :keyini

  # int keyprsnt_c(const char *)
  SYM[:keyprsnt] = LIBMIR_UVIO['keyprsnt_c', 'IS']
  def keyprsnt(keyword)
    r, rs = SYM[:keyprsnt][keyword.to_s]
    r != 0
  end
  module_function :keyprsnt

  # void keya_c(const char *, char *, const char *)
  SYM[:keya] = LIBMIR_UVIO['keya_c', '0SsS']
  def keya(keyword, keydef)
    value = DL.malloc(MAXSTRING)
    r, rs = SYM[:keya][keyword.to_s, value, keydef]
    rs[1].to_s
  end
  module_function :keya

  # void keyf_c(const char *, char *, const char *)
  SYM[:keyf] = LIBMIR_UVIO['keyf_c', '0SsS']
  def keyf(keyword, keydef)
    value = DL.malloc(MAXSTRING)
    r, rs = SYM[:keyf][keyword.to_s, value, keydef]
    rs[1].to_s
  end
  module_function :keyf

  # void keyd_c(const char *, double *, const double)
  SYM[:keyd] = LIBMIR_UVIO['keyd_c', '0SdD']
  def keyd(keyword, keydef)
    r, rs = SYM[:keyd][keyword.to_s, 0.0, keydef]
    rs[1]
  end
  module_function :keyd

  # void keyr_c(const char *, float *, const float)
  SYM[:keyr] = LIBMIR_UVIO['keyr_c', '0SfF']
  def keyr(keyword, keydef)
    r, rs = SYM[:keyr][keyword.to_s, 0.0, keydef]
    rs[1]
  end
  module_function :keyd

  # void keyi_c(const char *, int *, const int)
  SYM[:keyi] = LIBMIR_UVIO['keyi_c', '0SiI']
  def keyi(keyword, keydef)
    r, rs = SYM[:keyd][keyword.to_s, 0, keydef]
    rs[1]
  end
  module_function :keyd

  # void keyl_c(const char *, int *, const int)
  SYM[:keyl] = LIBMIR_UVIO['keyl_c', '0SiI']
  def keyl(keyword, keydef)
    r, rs = SYM[:keyd][keyword.to_s, 0, keydef]
    rs[1] != 0
  end
  module_function :keyd

  # void mkeyd_c(const char *, double [], const int, int *)
  SYM[:mkeyd] = LIBMIR_UVIO['mkeyd_c', '0SpIi']
  def mkeyd(keyword, nmax)
    size = nmax*DL.sizeof('D')
    value = DL.malloc(size)
    r, rs = SYM[:mkeyd][keyword.to_s, value, nmax, 0]
    rs[1].to_s(size).unpack("D#{rs[3]}")
  end
  module_function :mkeyd

  # void mkeyr_c(const char *, float [], const int, int *)
  SYM[:mkeyr] = LIBMIR_UVIO['mkeyr_c', '0SpIi']
  def mkeyr(keyword, nmax)
    size = nmax*DL.sizeof('F')
    value = DL.malloc(size)
    r, rs = SYM[:mkeyr][keyword.to_s, value, nmax, 0]
    rs[1].to_s(size).unpack("F#{rs[3]}")
  end
  module_function :mkeyr

  # void mkeyi_c(const char *, int [], const int, int *)
  SYM[:mkeyi] = LIBMIR_UVIO['mkeyi_c', '0SpIi']
  def mkeyi(keyword, nmax)
    size = nmax*DL.sizeof('I')
    value = DL.malloc(size)
    r, rs = SYM[:mkeyi][keyword.to_s, value, nmax, 0]
    rs[1].to_s(size).unpack("i#{rs[3]}")
  end
  module_function :mkeyi

  # void keyfin_c()
  SYM[:keyfin] = LIBMIR_UVIO['keyfin_c', '0']
  def keyfin
    SYM[:keyfin][]
  end
  module_function :keyfin
end
