# CFLAGS options: -DDEBUG -DFAST_DEBUG -DEXACT -DNEW -DTHREAD
# See http://gcc.gnu.org/onlinedocs/gcc-3.3.1/gcc/i386-and-x86-64-Options.html#i386%20and%20x86-64%20Options
#CFLAGS=-g -O6 -march=opteron -mfpmath=sse,387 -msse2 -m3dnow -Wall $(INCLUDE) -DNEW -DDEBUG -Wno-implicit
INCLUDE=-I$(MIRSUBS)
LFLAGS=-L. -L$(MIRLIB) -L/usr/X11R6/lib64 -L/usr/local/lib64/pgplot
CFLAGS=-g -O6 -std=c99 -Wall $(INCLUDE) -DNEW -DDEBUG -Wno-implicit
CC=gcc
############ Do not edit below this line ############
SRCS=autoflag.c list.c options.c
OBJS=$(SRCS:.c=.o)
LIBS=-lmir -lm

all: autoflag

autoflag: autoflag.o options.o
	g77 autoflag.o options.o -o autoflag $(CFLAGS) $(LFLAGS) $(LIBS)

# Dep is not necessary
dep:
	makedepend $(SRCS)

clean:
	rm -f $(OBJS) a.out core .depend

distclean: clean
	rm -f *.a autoflag

tar:
	rm -f autoflag.tar.bz2
	tar cjf autoflag.tar.bz2 autoflag.c  autoflag.h  Makefile  mirclib.h  mirflib.h  options.c  list.h

install: autoflag
	strip autoflag
	install autoflag $(MIRBIN)
	install autoflag.doc $(MIRDOC)/prog

