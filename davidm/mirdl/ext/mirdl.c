#include "ruby.h"

void init_mirdl_bug(VALUE mod);
void init_mirdl_key(VALUE mod);
void init_mirdl_options(VALUE mod);
void init_mirdl_hio(VALUE mod);
void init_mirdl_headio(VALUE mod);

void Init_mirdl()
{
  VALUE mMirdl = rb_define_module("Mirdl");
  init_mirdl_bug(mMirdl);
  init_mirdl_key(mMirdl);
  init_mirdl_options(mMirdl);
  init_mirdl_hio(mMirdl);
  init_mirdl_headio(mMirdl);
}
