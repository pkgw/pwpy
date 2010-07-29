require 'rubygems'
require 'rake/gempackagetask'

spec = Gem::Specification.new do |s|
  # Basics
  s.name = 'pgplot'
  s.version = '0.1.3.1'
  s.summary = 'Ruby interface to PGPLOT'
  s.description = 'Provides PGPLOT functions in a Ruby module.'
  #s.platform = Gem::Platform::Ruby
  s.required_ruby_version = '>= 1.8.1'
  s.requirements << 'PGPLOT ver 5.2.x (http://astro.caltech.edu/~tjp/pgplot/)'
  s.requirements << 'X11 library'
  s.requirements << 'PNG library'
  s.requirements << 'GrWin Graphics Library [for MS-Windows] (http://spdg1.sci.shizuoka.ac.jp/grwinlib/english/)'
  s.add_dependency('narray', '>= 0.5.9')

  # About
  s.authors = 'Masahiro Tanaka'
  s.email = 'masa16.tanaka@gmail.com'
  s.homepage = 'http://pgplot.rubyforge.org/'
  s.rubyforge_project = 'pgplot' 

  # Files, Libraries, and Extensions
  s.files = %w[
    cogen.rb
    depend
    extconf.rb
    kwarg.c
    rb_pgplot.c.in
  ]
  s.require_paths = ['.']
  #s.autorequire = nil
  #s.bindir = 'bin'
  #s.executables = []
  #s.default_executable = nil

  # C compilation
  s.extensions = %w[ extconf.rb ]

  # Documentation TODO
  #s.rdoc_options = []
  #s.has_rdoc = false
  #s.extra_rdoc_files = []

  # Testing TODO
  #s.test_files = []
end

Rake::GemPackageTask.new(spec) do |pkg|
  pkg.need_zip = true
  pkg.need_tar = true
end
