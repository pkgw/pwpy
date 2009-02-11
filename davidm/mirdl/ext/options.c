// Subroutines and functions from options.for

#include "mirdl.h"
#include "mirdl_for.h"

// void Options(const char *key, const char *opts[nopt], int present[nopts], int *nopt)
VALUE mirdl_options(int argc, VALUE *argv, VALUE self)
{
  int i;
  int nopt;
  int *present;
  char *key;
  char **opts;
  VALUE opts_ary, vkey, flag_ary;

  rb_scan_args(argc, argv, "11", &opts_ary, &vkey);

  Check_Type(opts_ary, T_ARRAY);
  nopt = RARRAY_LEN(opts_ary);
  key = (argc < 2 ? "options" : SYMSTR_PTR(vkey));
  present = ALLOCA_N(int, nopt);
  opts = ALLOCA_N(char *, nopt);

  if(!present || !opts) {
    rb_raise(rb_eNoMemError, "not enough memory for %d options", nopt);
  }

  for(i=0; i<nopt; i++) {
    present[i] = 0;
    opts[i] = SYMSTR_PTR(rb_ary_entry(opts_ary, i));
  }

  if(options_c(key, opts, present, nopt)) {
    rb_raise(rb_eNoMemError, "not enough memory to pack keywords");
  }

  // Build flag array
  flag_ary = rb_ary_new2(nopt);
  for(i=0; i<nopt; i++) {
    rb_ary_store(flag_ary, i, present[i] ? Qtrue : Qfalse);
  }

  return flag_ary;
}

void init_mirdl_options(VALUE mMirdl)
{
  rb_define_module_function(mMirdl, "options", mirdl_options, -1);
}
