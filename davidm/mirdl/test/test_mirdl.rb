#!/usr/bin/env ruby
$-w = true if $0 == __FILE__

require 'mirdl'
include Mirdl

require 'shellwords'
ARGV[0..-1] = Shellwords.shellwords(
  "vis=test/test.mir options=foo select='window(1)'"
)

keyini
p options([:foo, :bar])
uvDatInp('dsl')
keyfin
tno = uvDatOpn
puts "tno=#{tno}"

p uvrdvr(tno, H_INT, :nchan, 123)

p uvDatGta('ltype')
p uvDatGti('npol')
p uvDatGti('pols')
p uvDatGti('nchan')
v = Vis.new(1024)
v = uvread(tno,v)
p v
p uvprobvr(tno, :delay0)
p uvprobvr(tno, :delay1)
p uvrdvr(tno, H_INT, :nchan, 123)
p uvrdvri(tno, :nchan, 123)
uvDatRd(v)
p v
uvDatCls

keyini('foo=bar')
p keya('foo', '')
keyfin

sels = Sels.new(100)
keyini
vis = keyf(:vis,'')
selInput(sels)
keyfin
p selProbe(sels,:antennae?)
p selProbe(sels,:window?)
p selProbe(sels,:window,2)
tno = uvopen(vis,:old)
selApply(tno, sels)
uvclose(tno)
