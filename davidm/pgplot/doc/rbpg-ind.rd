
=begin
= Ruby/PGPLOT categorized method index
=== Drawing primitives

* (({((<pgline|URL:rbpgplot.html#PGLINE>))})) -- draw a polyline (curve defined by line-segments)
* (({((<pgpoly|URL:rbpgplot.html#PGPOLY>))})) -- draw a polygon, using fill-area attributes

* (({((<pgpt1|URL:rbpgplot.html#PGPT1>))}))  -- draw one graph marker
* (({((<pgpt|URL:rbpgplot.html#PGPT>))}))   -- draw several graph markers
* (({((<pgpnts|URL:rbpgplot.html#PGPNTS>))})) -- draw several graph markers, not all the same

* (({((<pgarro|URL:rbpgplot.html#PGARRO>))})) -- draw an arrow
* (({((<pgcirc|URL:rbpgplot.html#PGCIRC>))})) -- draw a circle, using fill-area attributes
* (({((<pgrect|URL:rbpgplot.html#PGRECT>))})) -- draw a rectangle, using fill-area attributes

* (({((<pgmove|URL:rbpgplot.html#PGMOVE>))})) -- move pen (change current pen position)
* (({((<pgdraw|URL:rbpgplot.html#PGDRAW>))})) -- draw a line from the current pen position to a point

=== Axis
* (({((<pgaxis|URL:rbpgplot.html#PGAXIS>))})) -- draw an axis
* (({((<pgbox|URL:rbpgplot.html#PGBOX>))}))  -- draw labeled frame around viewport
* (({((<pgtick|URL:rbpgplot.html#PGTICK>))})) -- draw a single tick mark on an axis
* (({((<pgtbox|URL:rbpgplot.html#PGTBOX>))})) -- draw frame and write (DD) HH MM SS.S labelling

=== Text
* (({((<pglab|URL:rbpgplot.html#PGLAB>))}))  -- write labels for x-axis, y-axis, and top of plot

* (({((<pgtext|URL:rbpgplot.html#PGTEXT>))})) -- write text (horizontal, left-justified)
* (({((<pgmtxt|URL:rbpgplot.html#PGMTXT>))})) -- write text at position relative to viewport
* (({((<pgptxt|URL:rbpgplot.html#PGPTXT>))})) -- write text at arbitrary position and angle

* (({((<pgetxt|URL:rbpgplot.html#PGETXT>))})) -- erase text from graphics display
* (({((<pgiden|URL:rbpgplot.html#PGIDEN>))})) -- write username, date, and time at bottom of plot
* (({((<pglen|URL:rbpgplot.html#PGLEN>))}))  -- find length of a string in a variety of units
* (({((<pgqtxt|URL:rbpgplot.html#PGQTXT>))})) -- find bounding box of text string

=== Histgram
* (({((<pgbin|URL:rbpgplot.html#PGBIN>))}))  -- histogram of binned data
* (({((<pghist|URL:rbpgplot.html#PGHIST>))})) -- histogram of unbinned data

=== Error bar
* (({((<pgerr1|URL:rbpgplot.html#PGERR1>))})) -- horizontal or vertical error bar
* (({((<pgerrb|URL:rbpgplot.html#PGERRB>))})) -- horizontal or vertical error bar
* (({((<pgerrx|URL:rbpgplot.html#PGERRX>))})) -- horizontal error bar
* (({((<pgerry|URL:rbpgplot.html#PGERRY>))})) -- vertical error bar

=== 2D drawing
* (({((<pgcont|URL:rbpgplot.html#PGCONT>))})) -- contour map of a 2D data array (contour-following)
* (({((<pgcons|URL:rbpgplot.html#PGCONS>))})) -- contour map of a 2D data array (fast algorithm)
* (({((<pgconb|URL:rbpgplot.html#PGCONB>))})) -- contour map of a 2D data array, with blanking
* (({((<pgconf|URL:rbpgplot.html#PGCONF>))})) -- fill between two contours
* (({((<pgconl|URL:rbpgplot.html#PGCONL>))})) -- label contour map of a 2D data array 
* (({((<pgconx|URL:rbpgplot.html#PGCONX>))})) -- contour map of a 2D data array (non rectangular) (not implemented in Ruby/PGPLOT)

* (({((<pgimag|URL:rbpgplot.html#PGIMAG>))})) -- color image from a 2D data array
* (({((<pgctab|URL:rbpgplot.html#PGCTAB>))})) -- install the color table to be used by ((<pgimag|URL:rbpgplot.html#PGIMAG>))
* (({((<pggray|URL:rbpgplot.html#PGGRAY>))})) -- gray-scale map of a 2D data array
* (({((<pgpixl|URL:rbpgplot.html#PGPIXL>))})) -- draw pixels

* (({((<pgvect|URL:rbpgplot.html#PGVECT>))})) -- vector map of a 2D data array, with blanking

* (({((<pgwedg|URL:rbpgplot.html#PGWEDG>))})) -- annotate an image plot with a wedge
* (({((<pghi2d|URL:rbpgplot.html#PGHI2D>))})) -- cross-sections through a 2D data array

=== Cursor
* (({((<pgband|URL:rbpgplot.html#PGBAND>))})) -- read cursor position, with anchor
* (({((<pgcurs|URL:rbpgplot.html#PGCURS>))})) -- read cursor position
* (({((<pglcur|URL:rbpgplot.html#PGLCUR>))})) -- draw a line using the cursor
* (({((<pgncur|URL:rbpgplot.html#PGNCUR>))})) -- mark a set of points using the cursor
* (({((<pgolin|URL:rbpgplot.html#PGOLIN>))})) -- mark a set of points using the cursor

=== Control
* (({((<pgopen|URL:rbpgplot.html#PGOPEN>))})) -- open a graphics device
* (({((<pgbeg|URL:rbpgplot.html#PGBEG>))}))  -- open a graphics device
* (({((<pgclos|URL:rbpgplot.html#PGCLOS>))})) -- close the selected graphics device
* (({((<pgend|URL:rbpgplot.html#PGEND>))}))  -- close all open graphics devices

* (({((<pgenv|URL:rbpgplot.html#PGENV>))}))  -- set window and viewport and draw labeled frame

* (({((<pgask|URL:rbpgplot.html#PGASK>))}))  -- control new page prompting
* (({((<pgpage|URL:rbpgplot.html#PGPAGE>))})) -- advance to new page
* (({((<pgeras|URL:rbpgplot.html#PGERAS>))})) -- erase all graphics from current page
* (({((<pgbbuf|URL:rbpgplot.html#PGBBUF>))})) -- begin batch of output (buffer)
* (({((<pgebuf|URL:rbpgplot.html#PGEBUF>))})) -- end batch of output (buffer)
* (({((<pgpanl|URL:rbpgplot.html#PGPANL>))})) -- switch to a different panel on the view surface
* (({((<pgpap|URL:rbpgplot.html#PGPAP>))}))  -- change the size of the view surface 
* (({((<pgrnge|URL:rbpgplot.html#PGRNGE>))})) -- choose axis limits
* (({((<pgsave|URL:rbpgplot.html#PGSAVE>))})) -- save PGPLOT attributes
* (({((<pgunsa|URL:rbpgplot.html#PGUNSA>))})) -- restore PGPLOT attributes
* (({((<pgscrl|URL:rbpgplot.html#PGSCRL>))})) -- scroll window
* (({((<pgsubp|URL:rbpgplot.html#PGSUBP>))})) -- subdivide view surface into panels
* (({((<pgupdt|URL:rbpgplot.html#PGUPDT>))})) -- update display

=== Set attributes
* (({((<pgsah|URL:rbpgplot.html#PGSAH>))}))  -- set arrow-head style
* (({((<pgscf|URL:rbpgplot.html#PGSCF>))}))  -- set character font
* (({((<pgsch|URL:rbpgplot.html#PGSCH>))}))  -- set character height
* (({((<pgsci|URL:rbpgplot.html#PGSCI>))}))  -- set color index
* (({((<pgscir|URL:rbpgplot.html#PGSCIR>))})) -- set color index range
* (({((<pgsclp|URL:rbpgplot.html#PGSCLP>))})) -- enable or disable clipping at edge of viewport
* (({((<pgscr|URL:rbpgplot.html#PGSCR>))}))  -- set color representation
* (({((<pgscrn|URL:rbpgplot.html#PGSCRN>))})) -- set color representation by name
* (({((<pgsfs|URL:rbpgplot.html#PGSFS>))}))  -- set fill-area style
* (({((<pgshls|URL:rbpgplot.html#PGSHLS>))})) -- set color representation using HLS system
* (({((<pgshs|URL:rbpgplot.html#PGSHS>))}))  -- set hatching style
* (({((<pgsitf|URL:rbpgplot.html#PGSITF>))})) -- set image transfer function
* (({((<pgslct|URL:rbpgplot.html#PGSLCT>))})) -- select an open graphics device
* (({((<pgsls|URL:rbpgplot.html#PGSLS>))}))  -- set line style
* (({((<pgslw|URL:rbpgplot.html#PGSLW>))}))  -- set line width
* (({((<pgstbg|URL:rbpgplot.html#PGSTBG>))})) -- set text background color index
* (({((<pgsvp|URL:rbpgplot.html#PGSVP>))}))  -- set viewport (normalized device coordinates)
* (({((<pgswin|URL:rbpgplot.html#PGSWIN>))})) -- set window
* (({((<pgvsiz|URL:rbpgplot.html#PGVSIZ>))})) -- set viewport (inches)
* (({((<pgvstd|URL:rbpgplot.html#PGVSTD>))})) -- set standard (default) viewport
* (({((<pgwnad|URL:rbpgplot.html#PGWNAD>))})) -- set window and adjust viewport to same aspect ratio

=== Inquire attributes
* (({((<pgldev|URL:rbpgplot.html#PGLDEV>))})) -- list available device types on standard output
* (({((<pgqah|URL:rbpgplot.html#PGQAH>))}))  -- inquire arrow-head style
* (({((<pgqcf|URL:rbpgplot.html#PGQCF>))}))  -- inquire character font
* (({((<pgqch|URL:rbpgplot.html#PGQCH>))}))  -- inquire character height
* (({((<pgqci|URL:rbpgplot.html#PGQCI>))}))  -- inquire color index
* (({((<pgqcir|URL:rbpgplot.html#PGQCIR>))})) -- inquire color index range
* (({((<pgqclp|URL:rbpgplot.html#PGQCLP>))})) -- inquire clipping status
* (({((<pgqcol|URL:rbpgplot.html#PGQCOL>))})) -- inquire color capability
* (({((<pgqcr|URL:rbpgplot.html#PGQCR>))}))  -- inquire color representation
* (({((<pgqcs|URL:rbpgplot.html#PGQCS>))}))  -- inquire character height in a variety of units
* (({((<pgqdt|URL:rbpgplot.html#PGQDT>))}))  -- inquire name of nth available device type
* (({((<pgqfs|URL:rbpgplot.html#PGQFS>))}))  -- inquire fill-area style
* (({((<pgqhs|URL:rbpgplot.html#PGQHS>))}))  -- inquire hatching style
* (({((<pgqid|URL:rbpgplot.html#PGQID>))}))  -- inquire current device identifier
* (({((<pgqinf|URL:rbpgplot.html#PGQINF>))})) -- inquire PGPLOT general information
* (({((<pgqitf|URL:rbpgplot.html#PGQITF>))})) -- inquire image transfer function
* (({((<pgqls|URL:rbpgplot.html#PGQLS>))}))  -- inquire line style
* (({((<pgqlw|URL:rbpgplot.html#PGQLW>))}))  -- inquire line width
* (({((<pgqndt|URL:rbpgplot.html#PGQNDT>))})) -- inquire number of available device types
* (({((<pgqpos|URL:rbpgplot.html#PGQPOS>))})) -- inquire current pen position
* (({((<pgqtbg|URL:rbpgplot.html#PGQTBG>))})) -- inquire text background color index
* (({((<pgqvp|URL:rbpgplot.html#PGQVP>))}))  -- inquire viewport size and position
* (({((<pgqvsz|URL:rbpgplot.html#PGQVSZ>))})) -- inquire size of view surface
* (({((<pgqwin|URL:rbpgplot.html#PGQWIN>))})) -- inquire window boundary coordinates

==== Hereafter not implemented in Ruby/PGPLOT

=== Utility
* (({((<pgnumb|URL:rbpgplot.html#PGNUMB>))})) -- convert a number into a plottable character string
* (({((<pgrnd|URL:rbpgplot.html#PGRND>))}))  -- find the smallest `round' number greater than x

=== Drawing function
* (({((<pgfunt|URL:rbpgplot.html#PGFUNT>))})) -- function defined by X = F(T), Y = G(T)
* (({((<pgfunx|URL:rbpgplot.html#PGFUNX>))})) -- function defined by Y = F(X)
* (({((<pgfuny|URL:rbpgplot.html#PGFUNY>))})) -- function defined by X = F(Y)

=== Alias
* (({((<pgadvance|URL:rbpgplot.html#PGADVANCE>))})) -- non-standard alias for ((<pgpage|URL:rbpgplot.html#PGPAGE>))
* (({((<pgbegin|URL:rbpgplot.html#PGBEGIN>))}))  -- non-standard alias for ((<pgbeg|URL:rbpgplot.html#PGBEG>))
* (({((<pgcurse|URL:rbpgplot.html#PGCURSE>))}))  -- non-standard alias for ((<pgcurs|URL:rbpgplot.html#PGCURS>))
* (({((<pglabel|URL:rbpgplot.html#PGLABEL>))}))  -- non-standard alias for ((<pglab|URL:rbpgplot.html#PGLAB>))
* (({((<pgmtext|URL:rbpgplot.html#PGMTEXT>))}))  -- non-standard alias for ((<pgmtxt|URL:rbpgplot.html#PGMTXT>))
* (({((<pgncurse|URL:rbpgplot.html#PGNCURSE>))})) -- non-standard alias for ((<pgncur|URL:rbpgplot.html#PGNCUR>))
* (({((<pgpaper|URL:rbpgplot.html#PGPAPER>))}))  -- non-standard alias for ((<pgpap|URL:rbpgplot.html#PGPAP>))
* (({((<pgpoint|URL:rbpgplot.html#PGPOINT>))}))  -- non-standard alias for ((<pgpt|URL:rbpgplot.html#PGPT>))
* (({((<pgptext|URL:rbpgplot.html#PGPTEXT>))}))  -- non-standard alias for ((<pgptxt|URL:rbpgplot.html#PGPTXT>))
* (({((<pgvport|URL:rbpgplot.html#PGVPORT>))}))  -- non-standard alias for ((<pgsvp|URL:rbpgplot.html#PGSVP>))
* (({((<pgvsize|URL:rbpgplot.html#PGVSIZE>))}))  -- non-standard alias for ((<pgvsiz|URL:rbpgplot.html#PGVSIZ>))
* (({((<pgvstand|URL:rbpgplot.html#PGVSTAND>))})) -- non-standard alias for ((<pgvstd|URL:rbpgplot.html#PGVSTD>))
* (({((<pgwindow|URL:rbpgplot.html#PGWINDOW>))})) -- non-standard alias for ((<pgswin|URL:rbpgplot.html#PGSWIN>))

<<< trailer
=end
