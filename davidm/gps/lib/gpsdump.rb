#!/usr/bin/env ruby

require 'narray'
require 'gsl'
require 'readbytes'

module GPS
  def load(f,rows=nil,row_offset=0)
    cols = 8
    rows ||= (File.size(f)/cols/2 - row_offset)
    m = GSL::Matrix::Complex[rows, cols]
    io = File.open(f)
    begin
      io.seek(row_offset*cols*2)
      s = io.readbytes(rows*cols*2)
      rows.times do |r|
        row = s.unpack("x#{r*cols*2}c#{cols*2}").to_gsl_vector.to_complex2
        row.copy(m.row(r))
      end
    ensure
      io.close rescue nil
    end
    m
  end
  module_function :load

  def oldload(f,rows=nil)
    c = 16
    r = rows || (File.size(f)/c)
    s = File.read(f, c*r)
    a = NArray.to_na(s, NArray::BYTE, c, r).to_type(NArray::INT)
    a = (a+128) % 256 - 128
    z = []
    (0...c/2).map do |i|
      z[i] = GSL::Vector::Complex[a[2*i,nil].to_gv,a[2*i+1,nil].to_gv];
    end
  end
  module_function :oldload

  # filenames is Array of filenames
  # num_chunks is how many chunks to do
  # chunk_rows is number of rows per chunk
  # chunk_step is number of rows to step per chunk
  # offset is initial offset from beginning of file
  # yields complex vector that is chunk_rows rows by 8*filenames.length cols
  def each_chunk(filenames, num_chunks, chunk_rows, chunk_step, offset=0)
    # Convert filenames to Array, if needed
    filenames = [filenames] unless Array === filenames
    # Set number of cols per file
    file_cols = 16
    # Calc amount of overlap for adjacent chunks
    overlap = chunk_rows - chunk_step
    overlap = 0 if overlap < 0
    non_overlap = chunk_rows - overlap
    # Create complex matrix to hold chunks
    m = GSL::Matrix::Complex[chunk_rows, file_cols*ios.length]
    # Create Array to hold IO objects
    ios = []
    # Every IO object opened in this block will get closed in
    # the corresponding ensure block.
    begin
      # Open files
      ios = filenames.map {|fn| io=File.open(fn); io.seek(offset); io}
      # Read in overlap amount if overlap > 0
      if overlap > 0
        ios.each_index do |i|
          s = ios[i].readbytes(overlap*file_cols)
          overlap.times do |r|
            row = s.unpack("x#{r*file_cols}c#{file_cols}").to_gsl_vector.to_complex2
            row.copy(m.view(r,file_cols*i,1,file_cols))
          end
        end
      end

      # For each chunk
      num_chunks.times do |c|
        ios.each_index do |i|
          s = ios[i].readbytes(non_overlap*file_cols)
          non_overlap.times do |r|
            row = s.unpack("x#{r*file_cols}c#{file_cols}").to_gsl_vector.to_complex2
            row.copy(m.view(overlap+r,file_cols*i,1,file_cols))
          end
        end
        # Yield chunk
        yield m
        # Move overlap
        if overlap > 0
          overlap.times do |o|
            m.row(overlap+o).copy(m.row(o))
          end
        end
      end # for each chunk
    ensure
      ios.each {|io| io.close rescue nil if io}
    end
  end
  module_function :each_chunk
end

class NArray
  def self.from_dump(f,typecode=NArray::INT)
    c=16
    r = File.size(f)/c
    s = File.read(f)
    a = NArray.to_na(s, NArray::BYTE, c, r).to_type(NArray::INT)
    a = (a+128) % 256 - 128
    a = a.to_type(typecode) unless typecode == NArray::INT
    a
  end
end

class GSL::Matrix
  def self.from_dump(f)
    a = NArray.from_dump(f,NArray::FLOAT)
    a.to_gm
  end
end

class GSL::Matrix::Int
#  def self.from_dump(f)
#    c=16
#    r = File.size(f)/c
#    s = File.read(f)
#    a = NArray.to_na(s, NArray::BYTE, c, 3).to_type(NArray::INT)
#    a = (a+128) % 256 - 128
#    gm=a.to_gm_int
#  end
  def self.from_dump(f)
    a = NArray.from_dump(f,NArray::INT)
    a.to_gm_int
  end

  def to_dat(s='', fmt='%d')
    self.each_row do |r|
      r.each do |e|
        s << fmt % [e] << ' '
      end
      s << "\n"
    end
    s
  end
end

if $0 == __FILE__
  cols=16
  while fn=ARGV.shift
    raise 'cannot to_dat a dat file' if fn =~ /\.dat$/
    rows = File.size(fn)/cols
    s = File.read('prn06.1220600023.0.00.dmp')
    a = NArray.to_na(s, NArray::BYTE, cols, rows).to_type(NArray::INT)
    a = (a+128) % 256 - 128
    gm=a.to_gm_int_view

    g = gm #.view(0,0,10,16)
    dat = fn.sub(/\.[^.]*$/,'.dat')
    puts "Writing to #{dat}"
    File.open(dat, 'w') {|f| g.to_dat(f, '%4d')}
  end
end
