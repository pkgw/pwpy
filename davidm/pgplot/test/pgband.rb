require 'narray'
require 'pgplot'
include Pgplot

pgbeg
pgenv 0, 1, 0, 1
pglab '','','Demo of PGBAND'

c = PgCursor.new(0,0)
for mode in 0..7
  puts 'Mode %d: Enter key or click on the window'%mode
  c = pgband(mode, c.x, c.y)
  p c
end

x = y = 0
for mode in 0..7
  puts 'Mode %d: Enter key or click on the window'%mode
  x,y = pgband(mode, x, y)
  p [x,y]
end
