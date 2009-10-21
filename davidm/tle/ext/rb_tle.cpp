/*
 * Document-class: Tle
 *
 * Wraps functions provided by the sgp4 library.
 */

//
//
// rb_tle.c
//

#include "ruby.h"
#include "sgp4ext.h"
#include "sgp4io.h"
#include "sgp4unit.h"

// From the cpp files
#define pi 3.14159265358979323846

static VALUE cDateTime = Qnil;
static ID id_ajd = Qnil;

/* Document-method: rv2coe
 *
 * call-seq: Tle.rv2coe(r,v,mu) -> [p, a, ecc, incl, omega, argp, nu, m, arglat, truelon, lonper]
 *
 * Convert geocentric equatorial position and velocity vectors (i.e. Arrays +r+
 * and +v+) to common orbital elements.
 *
 *   inputs          description                    range / units
 *     r           - ijk position vector            km
 *     v           - ijk velocity vector            km / s
 *     mu          - gravitational parameter        km3 / s2
 *
 *  outputs       :
 *     p           - semilatus rectum               km
 *     a           - semimajor axis                 km
 *     ecc         - eccentricity
 *     incl        - inclination                    0.0  to pi rad
 *     omega       - longitude of ascending node    0.0  to 2pi rad
 *     argp        - argument of perigee            0.0  to 2pi rad
 *     nu          - true anomaly                   0.0  to 2pi rad
 *     m           - mean anomaly                   0.0  to 2pi rad
 *     arglat      - argument of latitude      (ci) 0.0  to 2pi rad
 *     truelon     - true longitude            (ce) 0.0  to 2pi rad
 *     lonper      - longitude of periapsis    (ee) 0.0  to 2pi rad
 */
static VALUE rb_tle_rv2coe(VALUE self, VALUE vr, VALUE vv, VALUE vmu)
{
  double r[3], v[3], mu;
  double p, a, ecc, incl, omega, argp, nu, m, arglat, truelon, lonper;

  Check_Type(vr, rb_cArray);
  Check_Type(vv, rb_cArray);

  if(RARRAY_LEN(vr) == 3) {
    for(int i=0; i <3; ++i) {
      r[i] = NUM2DBL(rb_ary_entry(vr, i));
    }
  } else {
    rb_raise(rb_eArgError, "r must have exactly 3 elements");
  }

  if(RARRAY_LEN(vv) == 3) {
    for(int i=0; i <3; ++i) {
      v[i] = NUM2DBL(rb_ary_entry(vv, i));
    }
  } else {
    rb_raise(rb_eArgError, "v must have exactly 3 elements");
  }

  mu = NUM2DBL(vmu);

  rv2coe(r, v, nu,
      p, a, ecc, incl, omega, argp, nu, m, arglat, truelon, lonper);

  // TODO Define Coe class
  return rb_ary_new3(11,
      rb_float_new(p),
      rb_float_new(a),
      rb_float_new(ecc),
      rb_float_new(incl),
      rb_float_new(omega),
      rb_float_new(argp),
      rb_float_new(nu),
      rb_float_new(m),
      rb_float_new(arglat),
      rb_float_new(truelon),
      rb_float_new(lonper)
      );
}

/* Document-method: jday
 *
 * call-seq: Tle.jday(year=2000, month=1, day=1, hour=0, min=0, sec=0.0) -> Float
 *
 *  Finds the julian date given the year, month, day, and time.
 *  The julian date is defined by each elapsed day since noon, Jan 1, 4713 BC.
 */
static VALUE rb_tle_jday(int argc, VALUE *argv, VALUE self)
{
  VALUE vyear;   int year = 2000;
  VALUE vmon;    int mon = 1;
  VALUE vday;    int day = 1;
  VALUE vhr;     int hr = 0;
  VALUE vminute; int minute = 0;
  VALUE vsec;    double sec = 0.0;

  double jd;

  rb_scan_args(argc, argv, "06", &vyear, &vmon, &vday, &vhr, &vminute, &vsec);

  switch(argc) {
    case 6: sec = NUM2DBL(vsec);
    case 5: minute = NUM2INT(vminute);
    case 4: hr = NUM2INT(vhr);
    case 3: day = NUM2INT(vday);
    case 2: mon = NUM2INT(vmon);
    case 1: year = NUM2INT(vyear);
    case 0: break;
    default:
      // rb_scan_args should have already taken care of this
      rb_raise(rb_eArgError, "wrong number of arguments (%d for 0-6)", argc);
  }

  jday(year, mon, day, hr, minute, sec, jd);

  return rb_float_new(jd);
}

/* Document-method: invjday
 *
 * call-seq: Tle.invjday(ajd) -> [year, month, day, hour, min, sec]
 *
 * Finds the year, month, day, hour, minute and second given the julian date
 * +ajd+.
 */
static VALUE rb_tle_invjday(VALUE self, VALUE vjd)
{
  int year;
  int mon;
  int day;
  int hr;
  int minute;
  double sec;
  double jd = NUM2DBL(vjd);

  invjday(jd, year, mon, day, hr, minute, sec);

  return rb_ary_new3(6,
      INT2NUM(year),
      INT2FIX(mon),
      INT2FIX(day),
      INT2FIX(hr),
      INT2FIX(minute),
      rb_float_new(sec)
      );
}

/*
 * Document-class: Tle::Elements
 *
 * Class that encapsulates a two line elements set.
 */

/* call-seq: Tle::Elements.new(line1, line2, grav_const) -> Elements object
 *
 * Creates a new Elements object from the two lines of a TLE.  +grav_const+ can
 * be one of <tt>Tle::WGS72OLD</tt>, <tt>Tle::WGS72</tt>, or
 * <tt>Tle::WGS84</tt>.
 */
static VALUE rb_elements_initialize(VALUE self, VALUE vline1, VALUE vline2, VALUE vwhichconst)
{
  elsetrec * e;
  char * line1;
  char * line2;
  gravconsttype whichconst;
  double startmfe, stopmfe, deltamin;

  Data_Get_Struct(self, elsetrec, e);

  Check_Type(vline1, T_STRING);
  line1 = RSTRING_PTR(vline1);
  if(strlen(line1) < 69) {
    rb_raise(rb_eArgError, "line1 must be at least 69 characters");
  }

  Check_Type(vline2, T_STRING);
  line2 = RSTRING_PTR(vline2);
  if(strlen(line2) < 69) {
    rb_raise(rb_eArgError, "line2 must be at least 69 characters");
  }

  whichconst = (gravconsttype)NUM2INT(vwhichconst);

  twoline2rv(line1, line2, 'c', 'm', whichconst, startmfe, stopmfe, deltamin, *e);

  return self;
}

/* :nodoc: */
static VALUE rb_elements_new(int argc, VALUE *argv, VALUE clazz)
{
  elsetrec * e;
  VALUE self;

  if(argc != 3) {
    rb_raise(rb_eArgError, "wrong number of arguments (%d for 3)", argc);
  }

  self = Data_Make_Struct(clazz, elsetrec, NULL, free, e);
  rb_obj_call_init(self, argc, argv);
  return self;
}

/* Document-method: sgp4
 *
 * call-seq: sgp4(tsince, grav_const, ee=0.0) -> [r, v]
 *
 * Calls prediction code to calculate geocentric equatorial position +r+ and
 * velocity +v+ of object whose orbit is represented by +self+ at +tsince+
 * minutes since TLE epoch.  +r+ and +v+ are three element Arrays in units of
 * km and km/s, respectively.
 *
 * +tsince+ can also be given as a DateTime object (or any object responding to
 * +ajd+).  In this case, the minutes since TLE epoch will be calculated as...
 *
 *   (tsince.ajd - jdsatepoch) * (24*60)
 *
 * +grav_const+ can be one of <tt>Tle::WGS72OLD</tt>, <tt>Tle::WGS72</tt>, or
 * <tt>Tle::WGS84</tt>.  Presumably, this should be the same value that was
 * used when creating this object, but the underlying library does not enforce
 * this so this method does not either.
 *
 * The underlying sgp4 library uses a coordinate system that is referenced to
 * the true equator and mean equinox (TEME) of the TLE epoch.  If +ee+, the
 * equation of the equinoxes (in hours) at the TLE epoch, is given and is
 * non-zero then the results returned by the underlying library will be rotated
 * around the Z axis (i.e.  pole) by the amount specified, thereby transforming
 * the values into a coordinate system that is referenced to the true equator
 * and true equinox (TETE) of the TLE epoch.
 */
static VALUE rb_elements_sgp4(int argc, VALUE *argv, VALUE self)
{
  VALUE vtsince;     double tsince;
  VALUE vwhichconst; gravconsttype whichconst;
  VALUE veqeq;       double eqeq_rad = 0.0;
  VALUE vajd;
  elsetrec * e;
  double r[3], v[3], cosee, sinee, x, y;

  rb_scan_args(argc, argv, "21", &vtsince, &vwhichconst, &veqeq);

  Data_Get_Struct(self, elsetrec, e);
  if(rb_respond_to(vtsince, id_ajd)) {
    vajd = rb_funcall(vtsince, id_ajd, 0);
    tsince = (NUM2DBL(vajd) - e->jdsatepoch) * (24*60);
  } else {
    tsince = NUM2DBL(vtsince);
  }
  whichconst = (gravconsttype)NUM2INT(vwhichconst);
  if(argc == 3) {
    eqeq_rad = NUM2DBL(veqeq) * pi / 12.0;
  }

  // TODO Raise exception on error
  sgp4(whichconst, *e, tsince, r, v);

  if(eqeq_rad != 0.0)
  {
    cosee = cos(eqeq_rad);
    sinee = sin(eqeq_rad);
    x = r[0]*cosee - r[1]*sinee;
    y = r[0]*sinee + r[1]*cosee;
    r[0] = x;
    r[1] = y;
    x = v[0]*cosee - v[1]*sinee;
    y = v[0]*sinee + v[1]*cosee;
    v[0] = x;
    v[1] = y;
  }

  return rb_ary_new3(2,
      rb_ary_new3(3,
        rb_float_new(r[0]),
        rb_float_new(r[1]),
        rb_float_new(r[2])
        ),
      rb_ary_new3(3,
        rb_float_new(v[0]),
        rb_float_new(v[1]),
        rb_float_new(v[2])
        )
      );
}

#define CHR2STR(c) rb_str_new(&(c), 1)

#define DEFINE_ELEMENTS_GETTER(field_name, conv_func) \
static VALUE rb_elements_##field_name(VALUE self)     \
{                                                     \
  elsetrec * e;                                       \
  Data_Get_Struct(self, elsetrec, e);                 \
  return conv_func(e->field_name);                    \
}

DEFINE_ELEMENTS_GETTER(satnum, INT2NUM)
DEFINE_ELEMENTS_GETTER(epochyr, INT2NUM)
DEFINE_ELEMENTS_GETTER(epochtynumrev, INT2NUM)

/* Document-method: error
 *
 * call-seq: error -> Integer
 *
 * Returns most recent error code.
 */
DEFINE_ELEMENTS_GETTER(error, INT2NUM)

//DEFINE_ELEMENTS_GETTER(init, CHR2STR)
DEFINE_ELEMENTS_GETTER(method, CHR2STR)
DEFINE_ELEMENTS_GETTER(t, rb_float_new)
DEFINE_ELEMENTS_GETTER(epochdays, rb_float_new)

/* Document-method: jdsatepoch
 *
 * call-seq: jdsatepoch -> Float
 *
 * Returns (astronomical) Julian Date at TLE epoch.
 */
DEFINE_ELEMENTS_GETTER(jdsatepoch, rb_float_new)

#define BIND_ELEMENTS_GETTER(field_name) \
  rb_define_method(cElements, #field_name, RUBY_METHOD_FUNC(rb_elements_##field_name), 0);

extern "C" void Init_tle_ext()
{
  rb_require("date");

  ID idDateTime = rb_intern("DateTime");
  cDateTime = rb_const_get(rb_cObject, idDateTime);
  if(cDateTime == Qnil) {
    rb_raise(rb_eLoadError, "DateTime not found");
  }
  id_ajd = rb_intern("ajd");

  VALUE mTle = rb_define_module("Tle");
  rb_define_singleton_method(mTle, "rv2coe", RUBY_METHOD_FUNC(rb_tle_rv2coe), -1);

  rb_define_const(mTle, "WGS72OLD", INT2FIX(0));
  rb_define_const(mTle, "WGS72", INT2FIX(1));
  rb_define_const(mTle, "WGS84", INT2FIX(2));

  rb_define_module_function(mTle, "jday", RUBY_METHOD_FUNC(rb_tle_jday), -1);
  rb_define_module_function(mTle, "invjday", RUBY_METHOD_FUNC(rb_tle_invjday), 1);

  VALUE cElements = rb_define_class_under(mTle, "Elements", rb_cObject);
  rb_define_singleton_method(cElements, "new", RUBY_METHOD_FUNC(rb_elements_new), -1);
  rb_define_method(cElements, "initialize", RUBY_METHOD_FUNC(rb_elements_initialize), 3);
  rb_define_method(cElements, "sgp4", RUBY_METHOD_FUNC(rb_elements_sgp4), -1);
  BIND_ELEMENTS_GETTER(satnum);
  BIND_ELEMENTS_GETTER(satnum);
  BIND_ELEMENTS_GETTER(epochyr);
  BIND_ELEMENTS_GETTER(epochtynumrev);
  BIND_ELEMENTS_GETTER(error);
  //BIND_ELEMENTS_GETTER(init);
  BIND_ELEMENTS_GETTER(method);
  BIND_ELEMENTS_GETTER(t);
  BIND_ELEMENTS_GETTER(epochdays);
  BIND_ELEMENTS_GETTER(jdsatepoch);
#if 0
  /* These are just for RDOC */
  rb_define_method(cElements, "error", NULL, 0);
  rb_define_method(cElements, "jdsatepoch", NULL, 0);
#endif
}
