require 'narray'
require 'pgplot'
include Pgplot

pgbeg
pgenv 0,10, 0,10

pgtick( 0, 7, 10, 7, 0.25, "quarter" )
pgtick( 0, 7, 10, 7, 0.5,  "half", "tickr"=>1, "disp"=>2, "orient"=>90 )
pgtick( 0, 7, 10, 7, 0.75, "3quarter", "tickl"=>1, "disp"=>-2, "orient"=>180 )

pgaxis( 1, 1, 9, 5, 0, 3, "tickl"=>1, "opt"=>"NL2" )
