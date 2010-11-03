#define TRUE 1
#define FALSE 0
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "mirclib.h"

void options_c(char *key, char *opts[], char *present, int nopt) {
	const char blank=0;
	char string[16], *errmsg, found=FALSE;
	int len, i, optlen[nopt];

	for (i=0; i<nopt; i++) {
		present[i]=FALSE;
		optlen[i]=strlen(opts[i]);
	}
	keya_c(key,string,&blank);
	while (string[0]) {
		len=strlen(string);

		for (i=0; i<nopt; i++) {
			if (len <= optlen[i]) {
				if (!strncasecmp(string,opts[i],len)) {
					if (found) {
						errmsg=malloc(30+strlen(string));
						snprintf(errmsg,30+strlen(string),"Ambiguous option %s",string);
						bug_c('f',errmsg);
					}
					if (present[i]) {
						errmsg=malloc(30+strlen(string));
						snprintf(errmsg,30+strlen(string),"Repeated option %s",string);
						bug_c('w',errmsg);
						free(errmsg);

					}
					found=TRUE;
					present[i]=TRUE;
				}
			}
		}
		if (!found) {
			errmsg=malloc(30+strlen(string));
			snprintf(errmsg,30+strlen(string),"Unrecognized option %s",string);
			bug_c('f',errmsg);
		}
		keya_c(key,string,&blank);
		found=FALSE;
	}

}
