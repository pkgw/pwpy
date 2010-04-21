#!/usr/bin/bash
# set-defaults.csh
bw.csh fx64a:fxa 100
bw.csh fx64c:fxa 100
fxconf.rb satake fxa `slist.csh none`
scanfx2b.csh 3040 3140 100 100 fx64a:fxa fx64c:fxa 3c286 60
# use mosfx2b with negative stop time to do single scan. This is better than scanfx2b. If you do NOT use the -r option it will re-initialize most things.
fxconf.rb satake none `slist.csh fxa`
