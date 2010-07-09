//
// $Id$
//

// Functions from headio.c

#include "mirdl.h"

static ID id_new;
static ID id_real;
static ID id_imag;
static VALUE cComplex;

// void hisopen_c  (int tno, Const char *status);
static VALUE mirdl_hisopen(VALUE self, VALUE vtno, VALUE vstatus)
{
  int tno = NUM2INT(vtno);
  char * status = (char *)SYMSTR_PTR(vstatus);

  switch(status[0]) {
    case 'a': status = "append"; break;
    case 'n': status = "write"; break; // Support "new"
    case 'o': status = "read"; break; // Support "old"
    case 'r': status = "read"; break;
    case 'w': status = (status[1] == '+' ? "append" : "write"); break;
  }

  hisopen_c(tno, status);

  return Qnil;
}

// void hiswrite_c (int tno, Const char *text);
static VALUE mirdl_hiswrite(VALUE self, VALUE vtno, VALUE vtext)
{
  int tno = NUM2INT(vtno);

  hiswrite_c(tno, StringValueCStr(vtext));

  return Qnil;
}

// void hisread_c  (int tno, char *text, size_t length, int *eof);
static VALUE mirdl_hisread(VALUE self, VALUE vtno)
{
  int tno = NUM2INT(vtno);
  char text[MAXSTRING+1];
  int eof = 0;

  hisread_c(tno, text, MAXSTRING, &eof);

  return (eof ? Qnil : rb_str_new2(text));
}

// void hisclose_c (int tno);
static VALUE mirdl_hisclose(VALUE self, VALUE vtno)
{
  int tno = NUM2INT(vtno);

  hisclose_c(tno);

  return Qnil;
}

// void wrhdr_c (int tno, Const char *keyword, double value);
VALUE mirdl_wrhdr(VALUE self, VALUE vtno, VALUE vkeyword, VALUE vvalue)
{
  int tno = NUM2INT(vtno);
  char * keyword = (char *)SYMSTR_PTR(vkeyword);
  double value = NUM2DBL(vvalue);

  wrhdr_c(tno, keyword, value);

  return Qnil;
}

// void wrhdd_c (int tno, Const char *keyword, double value);
VALUE mirdl_wrhdd(VALUE self, VALUE vtno, VALUE vkeyword, VALUE vvalue)
{
  int tno = NUM2INT(vtno);
  char * keyword = (char *)SYMSTR_PTR(vkeyword);
  double value = NUM2DBL(vvalue);

  wrhdd_c(tno, keyword, value);

  return Qnil;
}

// void wrhdi_c (int tno, Const char *keyword, int value);
VALUE mirdl_wrhdi(VALUE self, VALUE vtno, VALUE vkeyword, VALUE vvalue)
{
  int tno = NUM2INT(vtno);
  char * keyword = (char *)SYMSTR_PTR(vkeyword);
  int value = NUM2INT(vvalue);

  wrhdi_c(tno, keyword, value);

  return Qnil;
}

// void wrhdl_c (int tno, Const char *keyword, int8 value); // TODO?

// void wrhdc_c (int tno, Const char *keyword, Const float *value);
VALUE mirdl_wrhdc(VALUE self, VALUE vtno, VALUE vkeyword, VALUE vvalue)
{
  int tno = NUM2INT(vtno);
  char * keyword = (char *)SYMSTR_PTR(vkeyword);
  float value[2];
  VALUE vreal;
  VALUE vimag;

  if(!(rb_respond_to(vvalue, id_real) && rb_respond_to(vvalue, id_imag))) {
    rb_raise(rb_eTypeError, "value does not respond to #real and #imag");
  }

  vreal = rb_funcall(vvalue, id_real, 0);
  vimag = rb_funcall(vvalue, id_real, 0);

  value[0] = (float)NUM2DBL(vreal);
  value[1] = (float)NUM2DBL(vimag);

  wrhdc_c(tno, keyword, value);

  return Qnil;
}

// void wrhda_c (int tno, Const char *keyword, Const char *value);
VALUE mirdl_wrhda(VALUE self, VALUE vtno, VALUE vkeyword, VALUE vvalue)
{
  int tno = NUM2INT(vtno);
  char * keyword = (char *)SYMSTR_PTR(vkeyword);
  char * value = StringValueCStr(vvalue);

  wrhda_c(tno, keyword, value);

  return Qnil;
}

// void rdhdr_c (int tno, Const char *keyword, float *value, double defval);
VALUE mirdl_rdhdr(int argc, VALUE *argv, VALUE self)
{
  VALUE vtno, vkeyword, vdef;
  float value;
  double def;

  rb_scan_args(argc, argv, "21", &vtno, &vkeyword, &vdef);

  if(argc==2) {
    def = 0.0;
  } else {
    def = NUM2DBL(vdef);
  }

  rdhdr_c(NUM2INT(vtno), SYMSTR_PTR(vkeyword), &value, def);

  return rb_float_new((double)value);
}

// void rdhdi_c (int tno, Const char *keyword, int *value, int defval);
VALUE mirdl_rdhdi(int argc, VALUE *argv, VALUE self)
{
  VALUE vtno, vkeyword, vdef;
  int value;
  int def;

  rb_scan_args(argc, argv, "21", &vtno, &vkeyword, &vdef);

  if(argc==2) {
    def = 0;
  } else {
    def = NUM2INT(vdef);
  }

  rdhdi_c(NUM2INT(vtno), SYMSTR_PTR(vkeyword), &value, def);

  return INT2NUM(value);
}

// void rdhdl_c (int tno, Const char *keyword, int8 *value, int8 defval); // TODO?

// void rdhdd_c (int tno, Const char *keyword, double *value, double defval);
VALUE mirdl_rdhdd(int argc, VALUE *argv, VALUE self)
{
  VALUE vtno, vkeyword, vdef;
  double value;
  double def;

  rb_scan_args(argc, argv, "21", &vtno, &vkeyword, &vdef);

  if(argc==2) {
    def = 0.0;
  } else {
    def = NUM2DBL(vdef);
  }

  rdhdd_c(NUM2INT(vtno), SYMSTR_PTR(vkeyword), &value, def);

  return rb_float_new(value);
}

// void rdhdc_c (int tno, Const char *keyword, float *value, Const float *defval);
VALUE mirdl_rdhdc(int argc, VALUE *argv, VALUE self)
{
  VALUE vtno, vkeyword, vdef;
  VALUE vreal, vimag;
  float value[2];
  float def[2];

  rb_scan_args(argc, argv, "21", &vtno, &vkeyword, &vdef);

  if(argc==2) {
    def[0] = 0.0;
    def[1] = 0.0;
  } else {
    if(!(rb_respond_to(vdef, id_real) && rb_respond_to(vdef, id_imag))) {
      rb_raise(rb_eTypeError, "default value does not respond to #real and #imag");
    }

    vreal = rb_funcall(vdef, id_real, 0);
    vimag = rb_funcall(vdef, id_real, 0);

    def[0] = (float)NUM2DBL(vreal);
    def[1] = (float)NUM2DBL(vimag);
  }

  rdhdc_c(NUM2INT(vtno), SYMSTR_PTR(vkeyword), value, def);

  return rb_funcall(cComplex, id_new, 2, rb_float_new(value[0]), rb_float_new(value[1]));
}

// void rdhda_c (int tno, Const char *keyword, char *value, Const char *defval, int len);
VALUE mirdl_rdhda(int argc, VALUE *argv, VALUE self)
{
  VALUE vtno, vkeyword, vdef;
  char value[MAXSTRING];
  char * def;

  rb_scan_args(argc, argv, "21", &vtno, &vkeyword, &vdef);

  if(argc==2) {
    def = "\0";
  } else {
    def = StringValueCStr(vdef);
  }

  rdhda_c(NUM2INT(vtno), SYMSTR_PTR(vkeyword), value, def, MAXSTRING);

  return value[0] ? rb_str_new2(value) : Qnil;
}

// void hdcopy_c (int tin, int tout, Const char *keyword);
VALUE mirdl_hdcopy(VALUE self, VALUE vtin, VALUE vtout, VALUE vkeyword)
{
  int tin = NUM2INT(vtin);
  int tout = NUM2INT(vtout);
  char * keyword = (char *)SYMSTR_PTR(vkeyword);

  hdcopy_c(tin, tout, keyword);

  return Qnil;
}

// int  hdprsnt_c (int tno, Const char *keyword);
VALUE mirdl_hdprsnt(VALUE self, VALUE vtno, VALUE vkeyword)
{
  int tno = NUM2INT(vtno);
  char * keyword = (char *)SYMSTR_PTR(vkeyword);
  int present;

  present = hdprsnt_c(tno, keyword);

  return (present ? Qtrue : Qfalse);
}

// void hdprobe_c (int tno, Const char *keyword, char *descr, size_t length, char *type, int *n);
VALUE mirdl_hdprobe(VALUE self, VALUE vtno, VALUE vkeyword)
{
  int tno = NUM2INT(vtno);
  char * keyword = (char *)SYMSTR_PTR(vkeyword);
  char descr[MAXSTRING+1] = {'\0'};
  char type[81] = {'\0'};
  int n;

  hdprobe_c(tno, keyword, descr, MAXSTRING, type, &n);

  return rb_ary_new3(3, rb_str_new2(descr), rb_str_new2(type), INT2NUM(n));
}

void init_mirdl_headio(VALUE mMirdl)
{
  id_new = rb_intern("new");
  id_real = rb_intern("real");
  id_imag = rb_intern("imag");
  rb_require("complex");
  cComplex = rb_const_get(rb_cObject, rb_intern("Complex"));

  rb_define_module_function(mMirdl, "hisopen", mirdl_hisopen , 2);
  rb_define_module_function(mMirdl, "hiswrite", mirdl_hiswrite, 2);
  rb_define_module_function(mMirdl, "hisread", mirdl_hisread , 1);
  rb_define_module_function(mMirdl, "hisclose", mirdl_hisclose, 1);

  rb_define_module_function(mMirdl, "wrhdr", mirdl_wrhdr, 3);
  rb_define_module_function(mMirdl, "wrhdd", mirdl_wrhdd, 3);
  rb_define_module_function(mMirdl, "wrhdi", mirdl_wrhdi, 3);
  rb_define_module_function(mMirdl, "wrhdc", mirdl_wrhdc, 3);
  rb_define_module_function(mMirdl, "wrhda", mirdl_wrhda, 3);

  rb_define_module_function(mMirdl, "rdhdr", mirdl_rdhdr, -1);
  rb_define_module_function(mMirdl, "rdhdi", mirdl_rdhdi, -1);
  rb_define_module_function(mMirdl, "rdhdd", mirdl_rdhdd, -1);
  rb_define_module_function(mMirdl, "rdhdc", mirdl_rdhdc, -1);
  rb_define_module_function(mMirdl, "rdhda", mirdl_rdhda, -1);

  rb_define_module_function(mMirdl, "hdcopy", mirdl_hdcopy, 3);
  rb_define_module_function(mMirdl, "hdprsnt", mirdl_hdprsnt, 2);
  rb_define_alias(mMirdl, "hdprsnt?", "hdprsnt");
  rb_define_module_function(mMirdl, "hdprobe", mirdl_hdprobe, 2);
}
