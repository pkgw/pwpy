//
// $Id$
//

#include "ruby.h"
#include "narray.h"

void init_mirdl_bug(VALUE mod);
void init_mirdl_key(VALUE mod);
void init_mirdl_options(VALUE mod);
void init_mirdl_hio(VALUE mod);
void init_mirdl_headio(VALUE mod);

static VALUE na_ptr(int argc, VALUE *argv, VALUE self)
{
  VALUE iv = Qnil;
  int i = 0;
  struct NARRAY * na;
  void * p;

  GetNArray(self, na);
  rb_scan_args(argc, argv, "01", &iv);
  if(iv != Qnil) {
    i = NUM2INT(iv);
  }
  p = NA_PTR(na, i);

  return ULONG2NUM((unsigned long)p);
}

static VALUE na_bsize(VALUE self)
{
  struct NARRAY * na;

  GetNArray(self, na);
  return LONG2NUM( ((long)na->total) * ((long)na_sizeof[na->type]) );
}

void Init_mirdl()
{
  VALUE mMirdl = rb_define_module("Mirdl");
  init_mirdl_bug(mMirdl);
  init_mirdl_key(mMirdl);
  init_mirdl_options(mMirdl);
  init_mirdl_hio(mMirdl);
  init_mirdl_headio(mMirdl);

  if(!rb_respond_to(cNArray, rb_intern("ptr"))) {
    rb_define_method(cNArray, "ptr", na_ptr, -1);
  }
  if(!rb_respond_to(cNArray, rb_intern("bsize"))) {
    rb_define_method(cNArray, "bsize", na_bsize, 0);
  }
}
