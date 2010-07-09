//
// $Id$
//

// Functions from hio.c

#include <errno.h>
#include "mirdl.h"
#include "narray.h"

static ID id_rstrip_bang;

// Map H_type constants to NArray typecodes
static enum NArray_Types hio2na[] = {
  /* dummy   -> */ NA_NONE,
  /* H_BYTE  -> */ NA_BYTE,
  /* H_INT   -> */ NA_LINT,
  /* H_INT2  -> */ NA_SINT,
  /* H_REAL  -> */ NA_SFLOAT,
  /* H_DBLE  -> */ NA_DFLOAT,
  /* H_TXT   -> */ NA_NONE,
  /* H_CMPLX -> */ NA_SCOMPLEX
};

// Map H_type constants to sizes
static int hio_sizeof[] = {
  /* dummy   -> */ 0,
  /* H_BYTE  -> */ 1,
  /* H_INT   -> */ 4,
  /* H_INT2  -> */ 2,
  /* H_REAL  -> */ 4,
  /* H_DBLE  -> */ 8,
  /* H_TXT   -> */ 0,
  /* H_CMPLX -> */ 8
};

// void hopen_c(int *tno, Const char *name, Const char *status, int *iostat);
static VALUE mirdl_hopen(VALUE self, VALUE vname, VALUE vstatus)
{
  int tno;
  int iostat = 0;
  char * name = StringValueCStr(vname);
  char * status = (char *)SYMSTR_PTR(vstatus);

  switch(status[0]) {
    case 'a': status = "append"; break;
    case 'r': status = "old"; break;
    case 'w': status = (status[1] == '+' ? "append" : "new"); break;
  }

  hopen_c(&tno, name, status, &iostat);
  if(iostat) {
    errno = (iostat == -1 ? EINVAL : iostat);
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
  char * kwptr = (char *)SYMSTR_PTR(keyword);

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
  char * status = (char *)SYMSTR_PTR(vstatus);

  switch(status[0]) {
    case 'a': status = "append"; break;
    case 'r': status = "read"; break;
    case 's': status = "scratch"; break;
    case 'w': status = (status[1] == '+' ? "append" : "write"); break;
  }

  haccess_c(NUM2INT(tno), &ihandle, kwptr, status, &iostat);
  if(iostat) {
    errno = (iostat == -1 ? EINVAL : iostat);
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
  char * kwptr = (char *)SYMSTR_PTR(keyword);

  exists = hexists_c(NUM2INT(tno), kwptr);

  return exists ? Qtrue : Qfalse;
}

// void hdaccess_c(int ihandle, int *iostat);
static VALUE mirdl_hdaccess(VALUE self, VALUE ihandle)
{
  int iostat = 0;

  hdaccess_c(NUM2INT(ihandle), &iostat);
  if(iostat) {
    errno = (iostat == -1 ? EINVAL : iostat);
    rb_sys_fail("hdaccess error");
  }

  return Qnil;
}

// off_t hsize_c(int ihandle);
static VALUE mirdl_hsize(VALUE self, VALUE ihandle)
{
  off_t size = hsize_c(NUM2INT(ihandle));

  return OFFT2NUM(size);
}

// void hio_c(int ihandle, int dowrite, int type, char *buf, off_t offset, size_t length, int *iostat);
static VALUE mirdl_hio(int argc, VALUE *argv, VALUE self)
{
  VALUE vhandle, vdowrite, vtype, vbuf, voff, vlen;
  int ihandle;
  int dowrite;
  int mtype;
  off_t offset;
  size_t length;
  int iostat;
  void * buf;
  struct NARRAY * na;
  int natype;

  rb_scan_args(argc, argv, "51",
      &vhandle, &vdowrite, &vtype, &vbuf, &voff, &vlen);

  if(argc == 5) {
    vlen = Qnil;
  } else {
    length = NUM2ULONG(vlen);
  }

  ihandle = NUM2INT(vhandle);
  dowrite = RTEST(vdowrite) ? 1 : 0;
  mtype = NUM2INT(vtype);
  offset = NUM2OFFT(voff);

  switch(mtype) {
    case H_BYTE:
    case H_INT:
    case H_INT2:
    case H_REAL:
    case H_DBLE:
    case H_CMPLX:
      if(!IsNArray(vbuf)) {
        rb_raise(rb_eArgError, "must use NArray for buffer, not %s", rb_obj_classname(vbuf));
      }
      GetNArray(vbuf, na);
      natype = hio2na[mtype];
      if(na->type != natype) {
        rb_raise(rb_eTypeError, "expected NArray typecode %d, got %d", natype, na->type);
      }
      buf = na->ptr;
      if(NIL_P(vlen) || length > na->total*hio_sizeof[mtype]) {
        length = na->total*hio_sizeof[mtype];
      }
      break;
    //case H_INT8:
    case H_TXT:
      rb_notimplement(); // TODO
      break;
    default:
      bugv_c('f', "hio: Unrecognized write type %d", mtype);
  }

  hio_c(ihandle, dowrite, mtype, buf, offset, length, &iostat);
  if(!dowrite && iostat == -1) {
    return Qnil; // EOF
  }
  if(iostat) {
    errno = (iostat == -1 ? EINVAL : iostat);
    rb_sys_fail(dowrite ? "hio write error" : "hio read error");
  }

  return vbuf;
}

// #define hreadb_c(item,buf,offset,length,iostat)
static VALUE mirdl_hreadb(int argc, VALUE *argv, VALUE self)
{
  int hioargc = argc+2;
  VALUE * hioargv = ALLOCA_N(VALUE, hioargc);
  hioargv[0] = argv[0];          // ihandle
  hioargv[1] = Qfalse;           // dowrite
  hioargv[2] = INT2FIX(H_BYTE);  // type
  memcpy(hioargv+3, argv+1, (argc-1)*sizeof(VALUE));
  return mirdl_hio(hioargc, hioargv, self);
}

// #define hwriteb_c(item,buf,offset,length,iostat)
static VALUE mirdl_hwriteb(int argc, VALUE *argv, VALUE self)
{
  int hioargc = argc+2;
  VALUE * hioargv = ALLOCA_N(VALUE, hioargc);
  hioargv[0] = argv[0];          // ihandle
  hioargv[1] = Qtrue;            // dowrite
  hioargv[2] = INT2FIX(H_BYTE);  // type
  memcpy(hioargv+3, argv+1, (argc-1)*sizeof(VALUE));
  return mirdl_hio(hioargc, hioargv, self);
}

// #define hreadi_c(item,buf,offset,length,iostat)
static VALUE mirdl_hreadi(int argc, VALUE *argv, VALUE self)
{
  int hioargc = argc+2;
  VALUE * hioargv = ALLOCA_N(VALUE, hioargc);
  hioargv[0] = argv[0];          // ihandle
  hioargv[1] = Qfalse;           // dowrite
  hioargv[2] = INT2FIX(H_INT);   // type
  memcpy(hioargv+3, argv+1, (argc-1)*sizeof(VALUE));
  return mirdl_hio(hioargc, hioargv, self);
}

// #define hwritei_c(item,buf,offset,length,iostat)
static VALUE mirdl_hwritei(int argc, VALUE *argv, VALUE self)
{
  int hioargc = argc+2;
  VALUE * hioargv = ALLOCA_N(VALUE, hioargc);
  hioargv[0] = argv[0];          // ihandle
  hioargv[1] = Qtrue;            // dowrite
  hioargv[2] = INT2FIX(H_INT);   // type
  memcpy(hioargv+3, argv+1, (argc-1)*sizeof(VALUE));
  return mirdl_hio(hioargc, hioargv, self);
}

// #define hreadj_c(item,buf,offset,length,iostat)
static VALUE mirdl_hreadj(int argc, VALUE *argv, VALUE self)
{
  int hioargc = argc+2;
  VALUE * hioargv = ALLOCA_N(VALUE, hioargc);
  hioargv[0] = argv[0];          // ihandle
  hioargv[1] = Qfalse;           // dowrite
  hioargv[2] = INT2FIX(H_INT2);  // type
  memcpy(hioargv+3, argv+1, (argc-1)*sizeof(VALUE));
  return mirdl_hio(hioargc, hioargv, self);
}

// #define hwritej_c(item,buf,offset,length,iostat)
static VALUE mirdl_hwritej(int argc, VALUE *argv, VALUE self)
{
  int hioargc = argc+2;
  VALUE * hioargv = ALLOCA_N(VALUE, hioargc);
  hioargv[0] = argv[0];          // ihandle
  hioargv[1] = Qtrue;            // dowrite
  hioargv[2] = INT2FIX(H_INT2);  // type
  memcpy(hioargv+3, argv+1, (argc-1)*sizeof(VALUE));
  return mirdl_hio(hioargc, hioargv, self);
}

// #define hreadr_c(item,buf,offset,length,iostat)
static VALUE mirdl_hreadr(int argc, VALUE *argv, VALUE self)
{
  int hioargc = argc+2;
  VALUE * hioargv = ALLOCA_N(VALUE, hioargc);
  hioargv[0] = argv[0];          // ihandle
  hioargv[1] = Qfalse;           // dowrite
  hioargv[2] = INT2FIX(H_REAL);  // type
  memcpy(hioargv+3, argv+1, (argc-1)*sizeof(VALUE));
  return mirdl_hio(hioargc, hioargv, self);
}

// #define hwriter_c(item,buf,offset,length,iostat)
static VALUE mirdl_hwriter(int argc, VALUE *argv, VALUE self)
{
  int hioargc = argc+2;
  VALUE * hioargv = ALLOCA_N(VALUE, hioargc);
  hioargv[0] = argv[0];          // ihandle
  hioargv[1] = Qtrue;            // dowrite
  hioargv[2] = INT2FIX(H_REAL);  // type
  memcpy(hioargv+3, argv+1, (argc-1)*sizeof(VALUE));
  return mirdl_hio(hioargc, hioargv, self);
}

// #define hreadd_c(item,buf,offset,length,iostat)
static VALUE mirdl_hreadd(int argc, VALUE *argv, VALUE self)
{
  int hioargc = argc+2;
  VALUE * hioargv = ALLOCA_N(VALUE, hioargc);
  hioargv[0] = argv[0];          // ihandle
  hioargv[1] = Qfalse;           // dowrite
  hioargv[2] = INT2FIX(H_DBLE);  // type
  memcpy(hioargv+3, argv+1, (argc-1)*sizeof(VALUE));
  return mirdl_hio(hioargc, hioargv, self);
}

// #define hwrited_c(item,buf,offset,length,iostat)
static VALUE mirdl_hwrited(int argc, VALUE *argv, VALUE self)
{
  int hioargc = argc+2;
  VALUE * hioargv = ALLOCA_N(VALUE, hioargc);
  hioargv[0] = argv[0];          // ihandle
  hioargv[1] = Qtrue;            // dowrite
  hioargv[2] = INT2FIX(H_DBLE);  // type
  memcpy(hioargv+3, argv+1, (argc-1)*sizeof(VALUE));
  return mirdl_hio(hioargc, hioargv, self);
}

// #define hreadc_c(item,buf,offset,length,iostat)
static VALUE mirdl_hreadc(int argc, VALUE *argv, VALUE self)
{
  int hioargc = argc+2;
  VALUE * hioargv = ALLOCA_N(VALUE, hioargc);
  hioargv[0] = argv[0];          // ihandle
  hioargv[1] = Qfalse;           // dowrite
  hioargv[2] = INT2FIX(H_CMPLX); // type
  memcpy(hioargv+3, argv+1, (argc-1)*sizeof(VALUE));
  return mirdl_hio(hioargc, hioargv, self);
}

// #define hwritec_c(item,buf,offset,length,iostat)
static VALUE mirdl_hwritec(int argc, VALUE *argv, VALUE self)
{
  int hioargc = argc+2;
  VALUE * hioargv = ALLOCA_N(VALUE, hioargc);
  hioargv[0] = argv[0];          // ihandle
  hioargv[1] = Qtrue;            // dowrite
  hioargv[2] = INT2FIX(H_CMPLX); // type
  memcpy(hioargv+3, argv+1, (argc-1)*sizeof(VALUE));
  return mirdl_hio(hioargc, hioargv, self);
}

// #define hread_c(item,type,buf,offset,length,iostat)
static VALUE mirdl_hread(int argc, VALUE *argv, VALUE self)
{
  int hioargc = argc+1;
  VALUE * hioargv = ALLOCA_N(VALUE, hioargc);
  hioargv[0] = argv[0];          // ihandle
  hioargv[1] = Qfalse;           // dowrite
  memcpy(hioargv+2, argv+1, (argc-1)*sizeof(VALUE));
  return mirdl_hio(hioargc, hioargv, self);
}

// #define hwrite_c(item,type,buf,offset,length,iostat)
static VALUE mirdl_hwrite(int argc, VALUE *argv, VALUE self)
{
  int hioargc = argc+1;
  VALUE * hioargv = ALLOCA_N(VALUE, hioargc);
  hioargv[0] = argv[0];          // ihandle
  hioargv[1] = Qtrue;            // dowrite
  memcpy(hioargv+2, argv+1, (argc-1)*sizeof(VALUE));
  return mirdl_hio(hioargc, hioargv, self);
}

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

// void hreada_c(int ihandle, char *line, size_t length, int *iostat);
static VALUE mirdl_hreada(int argc, VALUE * argv, VALUE self)
{
  VALUE vhandle, vlen;
  int ihandle, length, iostat;
  char *line;
  VALUE str;

  rb_scan_args(argc, argv, "11", &vhandle, &vlen);

  ihandle = NUM2INT(vhandle);

  if(argc == 1) {
    length = MAXSTRING;
  } else {
    length = NUM2INT(vlen);
  }

  line = ALLOCA_N(char, length+1);
  line[length] = '\0'; // Backstop

  hreada_c(ihandle, line, length, &iostat);
  if(iostat == -1) {
    return Qnil; // EOF
  } else if(iostat) {
    errno = iostat;
    rb_sys_fail("hreada error");
  }

  return rb_str_new2(line);
}

// void hwritea_c(int ihandle, Const char *line, size_t length, int *iostat);
static VALUE mirdl_hwritea(VALUE self, VALUE vhandle, VALUE vline)
{
  int iostat;
  int ihandle = NUM2INT(vhandle);

  StringValue(vhandle);
  hwritea_c(ihandle, RSTRING_PTR(vhandle), RSTRING_LEN(vhandle), &iostat);
  if(iostat) {
    errno = (iostat == -1 ? EINVAL : iostat);
    rb_sys_fail("hwritea error");
  }

  return Qnil;
}

void init_mirdl_hio(VALUE mMirdl)
{
  id_rstrip_bang = rb_intern("rstrip!");

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

  rb_define_module_function(mMirdl, "hio",  mirdl_hio, -1);
  rb_define_module_function(mMirdl, "hreadb", mirdl_hreadb, -1);
  rb_define_module_function(mMirdl, "hwriteb", mirdl_hwriteb, -1);
  rb_define_module_function(mMirdl, "hreadi", mirdl_hreadi, -1);
  rb_define_module_function(mMirdl, "hwritei", mirdl_hwritei, -1);
  rb_define_module_function(mMirdl, "hreadj", mirdl_hreadj, -1);
  rb_define_module_function(mMirdl, "hwritej", mirdl_hwritej, -1);
  rb_define_module_function(mMirdl, "hreadr", mirdl_hreadr, -1);
  rb_define_module_function(mMirdl, "hwriter", mirdl_hwriter, -1);
  rb_define_module_function(mMirdl, "hreadd", mirdl_hreadd, -1);
  rb_define_module_function(mMirdl, "hwrited", mirdl_hwrited, -1);
  rb_define_module_function(mMirdl, "hreadc", mirdl_hreadc, -1);
  rb_define_module_function(mMirdl, "hwritec", mirdl_hwritec, -1);
  rb_define_module_function(mMirdl, "hread", mirdl_hread, -1);
  rb_define_module_function(mMirdl, "hwrite", mirdl_hwrite, -1);

  rb_define_module_function(mMirdl, "hseek",  mirdl_hseek, 1);
  rb_define_module_function(mMirdl, "htell",  mirdl_htell, 1);

  rb_define_module_function(mMirdl, "hreada",  mirdl_hreada, -1);
  rb_define_module_function(mMirdl, "hwritea",  mirdl_hwritea, 2);
}
