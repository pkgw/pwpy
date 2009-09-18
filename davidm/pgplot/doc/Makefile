.SUFFIXES: .ja.rd .html.ja .rd .html .rb $(SUFFIXES)

.ja.rd.html.ja:
	rd2 -r rd2html-img-lib.rb --html-lang=ja --out-code=jis --with-css=css.css $< > $@
.rd.html:
	rd2 -r rd2html-img-lib.rb --with-css=css.css -o $* $<
.rb.html:
	rd2 -r rd2html-img-lib.rb --with-css=css.css -o $* $<

targets_en=index.html \
  pgline.html pgcont.html pgimag.html pghist.html \
  rbpg-ind.html
# rbpgplot.html
targets_ja=install.html.ja tutorial-01.html.ja method.html.ja

all: $(targets_en) $(targets_ja)

# Examples
pgline.html: pgline.rd trailer.html
pgcont.html: pgcont.rd trailer.html
pgimag.html: pgimag.rd trailer.html
pghist.html: pgimag.rd trailer.html

install.html.ja: trailer.html 
tutorial-01.html.ja: tutorial-01.ja.rd trailer.html

# Method description
rbpgplot.html: mkdoc.rb
	ruby mkdoc.rb rbpgplot.html

# Method index categolized
rbpg-ind.rd: rbpg-ind.txt mkind.rb trailer.html
	ruby mkind.rb rbpg-ind.txt rbpg-ind.rd

rbpg-ind.html: rbpg-ind.rd

# Method description (obsolete)
# rbpg-doc.html: rbpg-doc.in.html
# 	  rm -f $@
# 	  ruby -p rbpg-relabel.rb rbpg-doc.in.html > $@
# rbpg-doc.in.html: rbpg-doc.rd
# 	  rd2 -r rd2html-img-lib.rb --with-css=css.css -o $* $?
# rbpg-doc.rd: rbpg-mkdoc.rb
# 	  rm -f $@
# 	  ruby rbpg-mkdoc.rb  $< > $@

webdir=masa@rubyforge:/var/www/gforge-projects/pgplot/

webup:
	scp -p css.css rbpgplot.html $(targets_en) $(targets_ja) *.png README.?? $(webdir)

clean:
	rm -f $(targets_en) $(targets_ja)
