#include "ruby.h" // For ALLOCA_N macro only!
#include "mirdl_for.h"

// subroutine Options(key,opts,present,nopt)
// 
// implicit none
// character key*(*)
// integer nopt
// character opts(nopt)*(*)
// logical present(nopt)

int options_c(char *key, char **opts, int *present, int nopt)
{
  int i;
  int maxoptlen = 0;
  int packed_opts_len = 0;
  char * packed_opts;

  for(i=0; i<nopt; i++) {
    if(strlen(opts[i]) > maxoptlen) {
      maxoptlen = strlen(opts[i]);
    }
  }

  packed_opts_len = nopt*maxoptlen;
  packed_opts = ALLOCA_N(char, packed_opts_len);
  if(!packed_opts) {
    return packed_opts_len;
  }
  packed_opts_len *= sizeof(char);
  memset(packed_opts, ' ', packed_opts_len);

  for(i=0; i<nopt; i++) {
    strncpy(packed_opts+i*maxoptlen, opts[i], strlen(opts[i]));
  }

  options_(key, packed_opts, present, &nopt, strlen(key), maxoptlen);
  return 0;
}
