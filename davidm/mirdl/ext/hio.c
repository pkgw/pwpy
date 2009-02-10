// Functions from hio.c

#include <errno.h>
#include "mirdl.h"

// void hopen_c(int *tno, Const char *name, Const char *status, int *iostat);
static VALUE mirdl_hopen(VALUE self, VALUE vname, VALUE vstatus)
{
  int tno;
  int iostat = 0;
  char * name = StringValueCStr(vname);
  char * status = SYMSTR_PTR(vstatus);

  switch(status[0]) {
    case 'a': status = "append"; break;
    case 'r': status = "old"; break;
    case 'w': status = (status[1] == '+' ? "append" : "new"); break;
  }

  hopen_c(&tno, name, status, &iostat);
  if(iostat == -1) {
    errno = EINVAL;
    rb_sys_fail(status);
  } else {
    errno = iostat;
    rb_sys_fail(name);
  }

  return INT2NUM(tno);
}

// void hflush_c(int tno, int *iostat);
static VALUE mirdl_hflush(VALUE self, VALUE tno)
{
  int iostat = 0;

  hflush_c(NUM2INT(tno), &iostat);
  if(iostat) {
    errno = (iostat == -1 ? EINVAL : iostat);
    rb_sys_fail("hflush error");
  }

  return Qnil;
}

// void habort_c(void);
static VALUE mirdl_habort(VALUE self)
{
  habort_c();
  return Qnil;
}

// void hrm_c(int tno);
static VALUE mirdl_hrm(VALUE self, VALUE tno)
{
  hrm_c(NUM2INT(tno));
  return Qnil;
}

// void hclose_c(int tno); 
static VALUE mirdl_hclose(VALUE self, VALUE tno)
{
  hclose_c(NUM2INT(tno));
  return Qnil;
}

// void hdelete_c(int tno, Const char *keyword, int *iostat);
static VALUE mirdl_hdelete(VALUE self, VALUE tno, VALUE keyword)
{
  int iostat = 0;
  char * kwptr = SYMSTR_PTR(keyword);

  hdelete_c(NUM2INT(tno), kwptr, &iostat);
  if(iostat) {
    errno = (iostat == -1 ? EINVAL : iostat);
    rb_sys_fail(kwptr);
  }

  return Qnil;
}

// void haccess_c(int tno, int *ihandle, Const char *keyword, Const char *status, int *iostat);
static VALUE mirdl_haccess(VALUE self, VALUE tno, VALUE keyword, VALUE vstatus)
{
  int ihandle;
  int iostat = 0;
  char * kwptr = StringValueCStr(keyword);
  char * status = SYMSTR_PTR(vstatus);

  switch(status[0]) {
    case 'a': status = "append"; break;
    case 'r': status = "read"; break;
    case 's': status = "scratch"; break;
    case 'w': status = (status[1] == '+' ? "append" : "write"); break;
  }

  haccess_c(tno, &ihandle, kwptr, status, &iostat);
  if(iostat == -1) {
    errno = EINVAL;
    rb_sys_fail(status);
  } else {
    errno = iostat;
    rb_sys_fail(kwptr);
  }

  return INT2NUM(ihandle);
}

// void hmode_c(int tno, char *mode);
static VALUE mirdl_hmode(VALUE self, VALUE tno)
{
  char mode[3] = {'\0'};

  hmode_c(NUM2INT(tno), mode);

  return rb_str_new2(mode);
}

// int  hexists_c(int tno, Const char *keyword);
static VALUE mirdl_hexists(VALUE self, VALUE tno, VALUE keyword)
{
  int exists;
  char * kwptr = SYMSTR_PTR(keyword);

  exists = hexists_c(NUM2INT(tno), kwptr);

  return exists ? Qtrue : Qfalse;
}

// void hdaccess_c(int ihandle, int *iostat);
static VALUE mirdl_hdaccess(VALUE self, VALUE ihandle)
{
  int iostat = 0;

  hdaccess_c(ihandle, &iostat);
  if(iostat) {
    errno = (iostat == -1 ? EINVAL : iostat);
    rb_sys_fail("hdelete error");
  }

  return Qnil;
}

// off_t hsize_c(int ihandle);
static VALUE mirdl_hsize(VALUE self, VALUE ihandle)
{
  off_t size = hsize_c(NUM2INT(ihandle));

  return OFFT2NUM(size);
}

// TODO
#if 0
// void hio_c(int ihandle, int dowrite, int type, char *buf, off_t offset, size_t length, int *iostat);
static VALUE mirdl_hio(VALUE self, VALUE )
{
    SYM[:%][]
  end
  module_function :%
}
#endif

// void hseek_c(int ihandle, off_t offset);
static VALUE mirdl_hseek(VALUE self, VALUE ihandle, VALUE voffset)
{
  off_t offset = NUM2OFFT(voffset);

  hseek_c(NUM2INT(ihandle), offset);

  return Qnil;
}

// off_t htell_c(int ihandle);
static VALUE mirdl_htell(VALUE self, VALUE ihandle)
{
  off_t offset = hsize_c(NUM2INT(ihandle));

  return OFFT2NUM(offset);
}

// TODO
#if 0
// void hreada_c(int ihandle, char *line, size_t length, int *iostat);
static VALUE mirdl_hreada(VALUE self, VALUE )
{
    SYM[:%][]
  end
  module_function :%
}

// void hwritea_c(int ihandle, Const char *line, size_t length, int *iostat);
static VALUE mirdl_hwritea(VALUE self, VALUE )
{
    SYM[:%][]
  end
  module_function :%
}
#endif

void init_mirdl_hio(VALUE mMirdl)
{
  rb_define_module_function(mMirdl, "hopen", mirdl_hopen, 2);
  rb_define_module_function(mMirdl, "hflush",  mirdl_hflush, 1);
  rb_define_module_function(mMirdl, "habort",  mirdl_habort, 0);
  rb_define_module_function(mMirdl, "hrm",  mirdl_hrm, 1);
  rb_define_module_function(mMirdl, "hclose",  mirdl_hclose, 1);
  rb_define_module_function(mMirdl, "hdelete",  mirdl_hdelete, 2);
  rb_define_module_function(mMirdl, "haccess",  mirdl_haccess, 3);
  rb_define_module_function(mMirdl, "hmode",  mirdl_hmode, 1);
  rb_define_module_function(mMirdl, "hexists",  mirdl_hexists, 2);
  rb_define_module_function(mMirdl, "hdaccess",  mirdl_hdaccess, 1);
  rb_define_module_function(mMirdl, "hsize",  mirdl_hsize, 1);
  //TODO rb_define_module_function(mMirdl, "hio",  mirdl_hio, _);
  rb_define_module_function(mMirdl, "hseek",  mirdl_hseek, 1);
  rb_define_module_function(mMirdl, "htell",  mirdl_htell, 1);
  //TODO rb_define_module_function(mMirdl, "hreada",  mirdl_hreada, _);
  //TODO rb_define_module_function(mMirdl, "hwritea",  mirdl_hwritea, _);
}
