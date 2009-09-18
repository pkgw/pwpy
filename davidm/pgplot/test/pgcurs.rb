require 'narray'
require 'pgplot'
include Pgplot

pgbeg
pgenv 0, 1, 0, 1
pglab '','','Demo of PGCURS'

c = PgCursor.new(0,0)
for mode in 0..7
  puts 'Enter a key on the window:'
  c = pgcurs(c.x, c.y)
  pgpt1(c.x, c.y, c.char[0])
end
