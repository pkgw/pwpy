//
// $Id$
//

// Functions from key.c

#include "mirdl.h"

static ID id_ARGV;
static ID id_basename;
static ID id_bug;
static ID id_buglabel;
static ID id_shellwords;
static VALUE cFile;
static VALUE mShellwords;

static int key_argc = 0;
static char ** key_argv = NULL;

// void keyini_c(int, char *[])
VALUE mirdl_keyini(int argc, VALUE *argv, VALUE self)
{
  int i = 0;
  VALUE vargv, vprogname, arg, arg0;

  if(key_argv) {
    rb_funcall(self, id_bug, 2,
        INT2NUM('f'), rb_str_new2("keyini already called"));
    return Qnil;
  }

  rb_scan_args(argc, argv, "02", &vargv, &vprogname);

  switch(argc) {
    case 0: vargv = rb_const_get(rb_cObject, id_ARGV);
    case 1: arg0 = rb_gv_get("$0");
            vprogname = rb_funcall(rb_cFile, id_basename, 1, arg0);
  }

  // If vargv is a String, convert to Array using Shellwords.shellwords
  if(TYPE(vargv) == T_STRING) {
    vargv = rb_funcall(mShellwords, id_shellwords, 1, vargv);
  }

  // If vargv is not an Array, raise TypeError
  Check_Type(vargv, T_ARRAY);

  key_argc = RARRAY_LEN(vargv) + 1;
  key_argv = ALLOC_N(char *, key_argc);
  key_argv[0] = strdup(StringValueCStr(vprogname));
  for(i=0; i<key_argc-1; i++) {
    arg = rb_ary_entry(vargv, i);
    key_argv[i+1] = strdup(StringValueCStr(arg));
  }

  // Shadow miriad's concept of buglabel.
  rb_funcall(self, id_buglabel, 1, vprogname);

  keyini_c(key_argc, key_argv);

  return Qnil;
}

// int keyprsnt_c(const char *)
VALUE mirdl_keyprsnt(VALUE self, VALUE keyword)
{
  int present = keyprsnt_c(SYMSTR_PTR(keyword));

  return present ? Qtrue : Qfalse;
}

// void keya_c(const char *, char *, const char *)
VALUE mirdl_keya(int argc, VALUE *argv, VALUE self)
{
  VALUE keyword, keydef;
  char value[MAXSTRING+1];
  char * keydefptr;

  rb_scan_args(argc, argv, "11", &keyword, &keydef);

  if(argc==1) {
    keydefptr = "\n"; // Key can't start with newline
  } else {
    keydefptr = (char *)SYMSTR_PTR(keydef);
  }

  keya_c(SYMSTR_PTR(keyword), value, keydefptr);

  return value[0] == '\n' ? Qnil : rb_str_new2(value);
}

// void keyf_c(const char *, char *, const char *)
VALUE mirdl_keyf(int argc, VALUE *argv, VALUE self)
{
  VALUE keyword, keydef;
  char value[MAXSTRING+1];
  char * keydefptr;

  rb_scan_args(argc, argv, "11", &keyword, &keydef);

  if(argc==1) {
    keydefptr = "\n"; // Key can't start with newline
  } else {
    keydefptr = StringValueCStr(keydef);
  }

  keyf_c(SYMSTR_PTR(keyword), value, keydefptr);

  return value[0] == '\n' ? Qnil : rb_str_new2(value);
}

// void keyd_c(const char *, double *, const double)
VALUE mirdl_keyd(int argc, VALUE *argv, VALUE self)
{
  VALUE keyword, keydef;
  double value;
  double def;

  rb_scan_args(argc, argv, "11", &keyword, &keydef);

  if(argc==1) {
    def = 0.0;
  } else {
    def = NUM2DBL(keydef);
  }

  keyd_c(SYMSTR_PTR(keyword), &value, def);

  return rb_float_new(value);
}

// void keyr_c(const char *, float *, const float)
VALUE mirdl_keyr(int argc, VALUE *argv, VALUE self)
{
  VALUE keyword, keydef;
  float value;
  float def;

  rb_scan_args(argc, argv, "11", &keyword, &keydef);

  if(argc==1) {
    def = 0.0;
  } else {
    def = (float)NUM2DBL(keydef);
  }

  keyr_c(SYMSTR_PTR(keyword), &value, def);

  return rb_float_new((double)value);
}

// void keyi_c(const char *, int *, const int)
VALUE mirdl_keyi(int argc, VALUE *argv, VALUE self)
{
  VALUE keyword, keydef;
  int value;
  int def;

  rb_scan_args(argc, argv, "11", &keyword, &keydef);

  if(argc==1) {
    def = 0;
  } else {
    def = NUM2INT(keydef);
  }

  keyi_c(SYMSTR_PTR(keyword), &value, def);

  return INT2NUM(value);
}

// void keyl_c(const char *, int *, const int)
VALUE mirdl_keyl(int argc, VALUE *argv, VALUE self)
{
  VALUE keyword, keydef;
  int value;
  int def;

  rb_scan_args(argc, argv, "11", &keyword, &keydef);

  if(argc==1) {
    def = -1;
  } else {
    def = RTEST(keydef) ? 1 : 0;
  }

  keyl_c(SYMSTR_PTR(keyword), &value, def);

  if(value == -1) {
    return Qnil;
  }

  return value != 0 ? Qtrue : Qfalse;
}

// void mkeyd_c(const char *, double [], const int, int *)
VALUE mirdl_mkeyd(int argc, VALUE *argv, VALUE self)
{
  VALUE keyword, nmax;
  int i, n;
  double * value;
  VALUE retval;

  rb_scan_args(argc, argv, "11", &keyword, &nmax);

  if(argc==1) {
    i = 16;
  } else {
    i = NUM2INT(nmax);
  }

  value = ALLOCA_N(double, i);

  mkeyd_c(SYMSTR_PTR(keyword), value, i, &n);

  retval = rb_ary_new2(n);
  for(i=0; i<n; i++) {
    rb_ary_store(retval, i, rb_float_new(value[i]));
  }

  return retval;
}

// void mkeyr_c(const char *, float [], const int, int *)
VALUE mirdl_mkeyr(int argc, VALUE *argv, VALUE self)
{
  VALUE keyword, nmax;
  int i, n;
  float * value;
  VALUE retval;

  rb_scan_args(argc, argv, "11", &keyword, &nmax);

  if(argc==1) {
    i = 16;
  } else {
    i = NUM2INT(nmax);
  }

  value = ALLOCA_N(float, i);

  mkeyr_c(SYMSTR_PTR(keyword), value, i, &n);

  retval = rb_ary_new2(n);
  for(i=0; i<n; i++) {
    rb_ary_store(retval, i, rb_float_new((double)value[i]));
  }

  return retval;
}

// void mkeyi_c(const char *, int [], const int, int *)
VALUE mirdl_mkeyi(int argc, VALUE *argv, VALUE self)
{
  VALUE keyword, nmax;
  int i, n;
  int * value;
  VALUE retval;

  rb_scan_args(argc, argv, "11", &keyword, &nmax);

  if(argc==1) {
    i = 16;
  } else {
    i = NUM2INT(nmax);
  }

  value = ALLOCA_N(int, i);

  mkeyi_c(SYMSTR_PTR(keyword), value, i, &n);

  retval = rb_ary_new2(n);
  for(i=0; i<n; i++) {
    rb_ary_store(retval, i, INT2NUM(value[i]));
  }

  return retval;
}

// void keyfin_c()
VALUE mirdl_keyfin(VALUE self)
{
  int i;

  // Free copies of argv strings
  for(i=0; i<key_argc; i++) {
    free(key_argv[i]);
  }
  free(key_argv);
  key_argv = NULL;

  keyfin_c();

  return Qnil;
}

void init_mirdl_key(VALUE mMirdl)
{
  rb_require("shellwords");

  id_ARGV = rb_intern("ARGV");
  id_basename = rb_intern("basename");
  id_bug = rb_intern("bug");
  id_buglabel = rb_intern("buglabel");
  id_shellwords = rb_intern("shellwords");
  mShellwords = rb_define_module("Shellwords");

  rb_define_module_function(mMirdl, "keyini", mirdl_keyini, -1);
  rb_define_module_function(mMirdl, "keyprsnt", mirdl_keyprsnt, 1);
  rb_define_alias(mMirdl, "keyprsnt?", "keyprsnt");
  rb_define_module_function(mMirdl, "keya", mirdl_keya, -1);
  rb_define_module_function(mMirdl, "keyf", mirdl_keyf, -1);
  rb_define_module_function(mMirdl, "keyd", mirdl_keyd, -1);
  rb_define_module_function(mMirdl, "keyr", mirdl_keyr, -1);
  rb_define_module_function(mMirdl, "keyi", mirdl_keyi, -1);
  rb_define_module_function(mMirdl, "keyl", mirdl_keyl, -1);
  rb_define_module_function(mMirdl, "mkeyd", mirdl_mkeyd, -1);
  rb_define_module_function(mMirdl, "mkeyr", mirdl_mkeyr, -1);
  rb_define_module_function(mMirdl, "mkeyi", mirdl_mkeyi, -1);
  rb_define_module_function(mMirdl, "keyfin", mirdl_keyfin, 0);
}
