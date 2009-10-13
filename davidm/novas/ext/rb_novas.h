/*
  rb_novas.h
  NOVAS wrapper for Ruby
  (C) Copyright 2007 by David MacMahon

  This program is free software.
  You can distribute/modify this program
  under the same terms as Ruby itself.
  NO WARRANTY.
*/

#if !defined(RUBY)
#error ruby.h must be included before rb_novas.h
#endif

#define DEFINE_GET_ATTR_INT(ctype,attr) \
static VALUE \
rb_novas_ ## ctype ## _get_ ## attr(VALUE self, VALUE value) \
{ \
  ctype * p; \
  Data_Get_Struct(self,ctype,p); \
  return INT2NUM(p->attr); \
}

#define DEFINE_SET_ATTR_INT(ctype,attr,itype) \
static VALUE \
rb_novas_ ## ctype ## _set_ ## attr(VALUE self, VALUE value) \
{ \
  ctype * p; \
  Data_Get_Struct(self,ctype,p); \
  p->attr = (itype)NUM2INT(value); \
  return value; \
}

#define DEFINE_GET_ATTR_DBL(ctype,attr) \
static VALUE \
rb_novas_ ## ctype ## _get_ ## attr(VALUE self, VALUE value) \
{ \
  ctype * p; \
  Data_Get_Struct(self,ctype,p); \
  return rb_float_new(p->attr); \
}

#define DEFINE_SET_ATTR_DBL(ctype,attr) \
static VALUE \
rb_novas_ ## ctype ## _set_ ## attr(VALUE self, VALUE value) \
{ \
  ctype * p; \
  Data_Get_Struct(self,ctype,p); \
  p->attr = NUM2DBL(value); \
  return value; \
}

#define DEFINE_GET_ATTR_STR(ctype,attr) \
static VALUE \
rb_novas_ ## ctype ## _get_ ## attr(VALUE self, VALUE value) \
{ \
  ctype * p; \
  Data_Get_Struct(self,ctype,p); \
  return rb_str_new2(p->attr); \
}

#define DEFINE_SET_ATTR_STR(ctype,attr,max) \
static VALUE \
rb_novas_ ## ctype ## _set_ ## attr(VALUE self, VALUE value) \
{ \
  ctype * p; \
  int len=RSTRING(value)->len; \
  Data_Get_Struct(self,ctype,p); \
  value = StringValue(value); \
  if(len > max) { \
    len = max; \
  } \
  if(RSTRING(value)->ptr) { \
    strncpy(p->attr,RSTRING(value)->ptr,len); \
    p->attr[len] = '\0';\
  } else { \
    p->attr[0] = '\0';\
  } \
  return value; \
}

#define BIND_GET_ATTR(clazz,mname,ctype,attr) \
rb_define_method(rb_c##clazz,#mname,rb_novas_ ## ctype ## _get_ ## attr, 0)

#define BIND_SET_ATTR(clazz,mname,ctype,attr) \
rb_define_method(rb_c##clazz,#mname "=",rb_novas_ ## ctype ## _set_ ## attr, 1)

void init_body();
void init_site_info();
void init_cat_entry();

/* Utility functions from rb_novas.c */
int rb_novas_ary2dbl(VALUE ary, double * p, int len);
VALUE rb_novas_dbl2ary(double * p, int len);
