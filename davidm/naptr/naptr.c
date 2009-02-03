/*
   naptr.c : Ruby/NArray extension library

   Copyright (c) 2009 David MacMahon <davidm@astro.berkeley.edu>

   This program is free software.
   You can distribute/modify this program
   under the same terms as Ruby itself.
   NO WARRANTY.
*/
#include <ruby.h>
#include "narray.h"

static VALUE naptr_ptr(int argc, VALUE *argv, VALUE self)
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
  return UINT2NUM((unsigned int)p);
}

void Init_naptr()
{
  rb_require("narray");
  //cNArray = rb_define_class("NArray", rb_cObject);
  rb_define_method(cNArray, "ptr", naptr_ptr, -1);
}
