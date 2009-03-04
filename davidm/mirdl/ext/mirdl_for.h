//
// $Id$
//

#ifndef _MIRDL_FOR_H_
#define _MIRDL_FOR_H_

// Functions from options.for
void options_(char * key, char *packed_opts, int *present, int *nopt, int keylen, int maxoptlen);
int options_c(char * key, char **opts, int *present, int nopt);

#endif // _MIRDL_FOR_H_
