# CFLAGS options: -DDEBUG -DFAST_DEBUG -DEXACT -DNEW -DTHREAD
# See http://gcc.gnu.org/onlinedocs/gcc-3.3.1/gcc/i386-and-x86-64-Options.html#i386%20and%20x86-64%20Options
#CFLAGS=-g -O6 -march=opteron -mfpmath=sse,387 -msse2 -m3dnow -Wall $(INCLUDE) -DNEW -DDEBUG -Wno-implicit
CFLAGS=-g -O6 -std=c99 -Wall $(INCLUDE) -DNEW -DDEBUG -Wno-implicit
INCLUDE=-I$(MIRSUBS)
LIBDIR=-L. -L$(MIRLIB) -L/usr/X11R6/lib64 -L/usr/local/lib64/pgplot
CC=gcc
############ Do not edit below this line ############
CFILES= options.c autoflag.c

all: autoflag

autoflag: autoflag.o options.o
	g77 autoflag.o options.o -o autoflag $(LIBDIR) -lmir_uvio -lmir_linpack -lmir -lpgplot -lX11 -lm

dep:
	rm -f .depend
	$(CC) -M $(CFILES) >> .depend

clean:
	rm -f *.o a.out core .depend
	touch .depend

distclean: clean
	rm -f *.a autoflag

tar:
	rm -f autoflag.tar.bz2
	tar cjf autoflag.tar.bz2 autoflag.c  autoflag.h  hio.h  Makefile  mirclib.h  mirflib.h  options.c  sysdep.h list.h

install: autoflag
	strip autoflag
	install autoflag $(MIRBIN)
	install autoflag.doc $(MIRDOC)/prog

# DO NOT DELETE
include .depend
