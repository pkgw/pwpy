/*
  rb_novas.c
  NOVAS wrapper for Ruby
  (C) Copyright 2007 by David MacMahon

  This program is free software.
  You can distribute/modify this program
  under the same terms as Ruby itself.
  NO WARRANTY.
*/
#include <ruby.h>
#include "novas.h"
#include "rb_novas.h"

/*
   "Global" variables to shadow NOVAS's "global" variables.

   'PSI_COR' and 'EPS_COR' are celestial pole offsets for high-
   precision applications.  See function 'cel_pole' for more details.
*/

static double PSI_COR = 0.0;
static double EPS_COR = 0.0;

/*
 * Convert Array of Floats to array of doubles.
 *
 * ary should be an array of Floats
 * p if a pointer to array of doubles
 * len is max number of entries to convert
 *
 * Returns number of values converted.
 */
int
rb_novas_ary2dbl(VALUE ary, double * p, int len)
{
  int i, arylen;

  if(TYPE(ary) != T_ARRAY) {
    rb_raise(rb_eArgError, "Array argument is not an Array");
  }

  arylen = RARRAY(ary)->len;
  if(arylen < len) {
    len = arylen;
  }

  for(i=0; i<len; i++) {
    p[i] = NUM2DBL(rb_ary_entry(ary,i));
  }

  return len;
}

/*
 * Convert array of doubles to Array of Floats
 *
 * p if a pointer to array of doubles
 * len is max number of entries to convert
 *
 * Returns Array of Floats
 */
VALUE
rb_novas_dbl2ary(double * p, int len)
{
  int i;
  VALUE ary = rb_ary_new2(len);

  for(i=0; i<len; i++) {
    rb_ary_store(ary, i, rb_float_new(p[i]));
  }

  return ary;
}

// Module functions

/*
 * Document-class: Novas
 *
 * The Novas module exposes contatnts and functions from the NOVAS-C library.
 */

/*
 * call-seq: Novas.sidereal_time(jd) -> gmst
 * Novas.sidereal_time(jd_high, jd_low) -> gmst
 * Novas.sidereal_time(jd_high, jd_low, ee) -> gast
 * 
 * This function computes Greenwich sidereal time.  To obtain the Greenwich
 * mean sidereal time, set +ee+ = 0.0 (or omit it altogether).  To obtain
 * Greenwich apparent sidereal time, supply the correct value for the equation
 * of the equinoxes (+ee+) which can be computed by calling Novas#earthtilt. 
 *
 * The input Julian date may be split into two parts to ensure maximum precision in the 
 * computation.  For maximum precision, jd_high should be set to be equal to the integral 
 * part of the Julian date, and jd_low should be set to be equal to the fractional part.  For 
 * most applications the position of the split is not critical as long as the sum jd_high + 
 * jd_low is correct:  for example, when used with computers providing 16 decimal digits 
 * of precision in double variables, this function will yield values of gst precise to better 
 * than 1 millisecond even if jd_high contains the entire Julian date and jd_low is set to 
 * 0.0.  For ICRS/IERS compatibility when computing apparent sidereal time at millisecond 
 * precision or better, you should also use Novas#cel_pole and supply the published 
 * celestial pole offsets. 
 *
 * For most uses, the input Julian date should be in the UT1 time scale.  If the input 
 * Julian date is in the TDB time scale, the output must be considered to be dynamical 
 * sidereal time.
 *
 *   INPUTS:
 *        jd (Float)
 *           Julian date
 *        jd_high (Float) 
 *           Julian date, integral part.
 *        jd_low (Float) 
 *           Julian date, fractional part. 
 *        ee (Float) 
 *           Equation of the equinoxes (seconds of time). [Note: this 
 *           quantity is computed by Novas#earthtilt.] 
 *
 *   OUTPUTS:
 *        gmst (Float) [when +ee+ is zero or omitted]
 *           Greenwich mean sidereal time, in hours.
 *        gast (Float) [when +ee+ is non-zero]
 *           Greenwich apparent sidereal time, in hours.
 */
static VALUE
rb_novas_sidereal_time(VALUE v_mod, VALUE args)
{
  double jd_high = 0.0;
  double jd_low = 0.0;
  double ee = 0.0;
  double gst;
  int argc = RARRAY(args)->len;

  // If one arg and it's an array, expand it
  if(argc == 1 && TYPE(rb_ary_entry(args,0)) == T_ARRAY) {
    args = rb_ary_entry(args,0);
    argc = RARRAY(args)->len;
  }
  switch(argc) {
    case 3: ee = NUM2DBL(rb_ary_entry(args,2));
    case 2: jd_low = NUM2DBL(rb_ary_entry(args,1));
    case 1: jd_high = NUM2DBL(rb_ary_entry(args,0));
            break;
    case 0: // TODO Default to now
            break;
    default:
      rb_raise(rb_eArgError, "wrong number of arguments (%d for 0..3)", argc);
  }
  sidereal_time(jd_high,jd_low,ee,&gst);
  return rb_float_new(gst);
}

/*
 * call-seq: julian_date(year, month=1, day=1, hour=12.0) -> jd
 *
 * This function will compute the Julian date for a given [Gregorian?] calendar
 * date (year, month, day, hour).
 *
 *   REFERENCES: 
 *      Fliegel & Van Flandern, Comm. of the ACM, Vol. 11, No. 10, October
 *      1968, p. 657.

 *   INPUTS:
 *      year (Fixnum)
 *         Year.
 *      month (Fixnum)
 *         Month number.
 *      day (Fixnum)
 *         Day-of-month.
 *      hour (Float)
 *         Hour-of-day.

 *   OUTPUTS:
 *      jd (Float)
 *         Julian date.
 */
static VALUE
rb_novas_julian_date(VALUE v_mod, VALUE args)
{
  short int year = 2000;
  short int month = 1;
  short int day = 1;
  double hour = 12.0;
  int argc = RARRAY(args)->len;

  // If one arg and it's an array, expand it
  if(argc == 1 && TYPE(rb_ary_entry(args,0)) == T_ARRAY) {
    args = rb_ary_entry(args,0);
    argc = RARRAY(args)->len;
  }
  switch(argc) {
    case 4: hour = NUM2DBL(rb_ary_entry(args,3));
    case 3: day = NUM2INT(rb_ary_entry(args,2));
    case 2: month = NUM2INT(rb_ary_entry(args,1));
    case 1: year = NUM2INT(rb_ary_entry(args,0));
    case 0: break;
    default:
      rb_raise(rb_eArgError, "wrong number of arguments (%d for 0..4)", argc);
  }
  return rb_float_new(julian_date(year,month,day,hour));
}

/*
 * call-seq: cal_date(tjd) -> [year, month, day, hour]
 *
 * This function will compute a date on the Gregorian calendar given the Julian
 * date.
 *
 *    REFERENCES: 
 *       Fliegel & Van Flandern, Comm. of the ACM, Vol. 11, No. 10,
 *          October 1968, p. 657.
 *
 *    INPUTS:
 *       tjd (Float)
 *          Julian date.
 *
 *    OUTPUS:
 *       year (Fixnum)
 *          Year.
 *       month (Fixnum)
 *          Month number.
 *       day (Fixnum)
 *          Day-of-month.
 *       hour (Float)
 *          Hour-of-day.
 */
static VALUE
rb_novas_cal_date(VALUE v_mod, VALUE v_tjd)
{
  double tjd = NUM2DBL(v_tjd);
  short int year, month, day;
  double hour;
  cal_date(tjd,&year,&month,&day,&hour);
  return rb_ary_new3(4,
      INT2FIX(year),INT2FIX(month),INT2FIX(day),rb_float_new(hour));
}

/*
 * call-seq: earthtilt(tjd) -> [mobl, tobl, eq, dpsi, deps]
 *
 * Computes quantities related to the orientation of the Earth's rotation axis
 * at Julian date +tjd+.

 *   REFERENCES: 
 *      Kaplan, G. H. et. al. (1989). Astron. Journ. Vol. 97, 
 *         pp. 1197-1210.
 *      Kaplan, G. H. "NOVAS: Naval Observatory Vector Astrometry
 *         Subroutines"; USNO internal document dated 20 Oct 1988;
 *         revised 15 Mar 1990.
 *      Transactions of the IAU (1994). Resolution C7; Vol. XXIIB, p. 59.
 *      McCarthy, D. D. (ed.) (1996). IERS Technical Note 21. IERS
 *         Central Bureau, Observatoire de Paris), pp. 21-22.
 *
 *   INPUTS:
 *      tjd (Float)
 *         TDB Julian date of the desired time
 *
 *   OUTPUTS:
 *      mobl (Float)
 *         Mean obliquity of the ecliptic in degrees at +tjd+.
 *      tobl (Float)
 *         True obliquity of the ecliptic in degrees at +tjd+.
 *      eq (Float)
 *         Equation of the equinoxes in seconds of time at +tjd+.
 *      dpsi (Float)
 *         Nutation in longitude in arcseconds at +tjd+.
 *      deps (Float)
 *         Nutation in obliquity in arcseconds at +tjd+.
 */
static VALUE
rb_novas_earthtilt(VALUE v_mod, VALUE v_tjd)
{
  double tjd = NUM2DBL(v_tjd);
  double mobl, tobl, eq, dpsi, deps;
  earthtilt(tjd, &mobl, &tobl, &eq, &dpsi, &deps);
  return rb_ary_new3(5,
      rb_float_new(mobl), rb_float_new(tobl),
      rb_float_new(eq),
      rb_float_new(dpsi), rb_float_new(deps));
}

/*
 * call-seq: cel_pole -> [del_psi, del_eps]
 *           cel_pole(del_psi, del_eps) -> nil
 *
 * This function allows for the specification of celestial pole offsets for
 * high-precision applications.  These are added to the nutation parameters
 * delta psi and delta epsilon.  If no parameters are given, the current values
 * are returned.
 *
 * This function sets the values of Novas global variables 'PSI_COR' and
 * 'EPS_COR' declared at the top of file 'novas.c'.  These global variables are
 * used only in Novas function 'earthtilt'.
 *
 * This function, if used, should be called before any other Novas functions
 * for a given date.  Values of the pole offsets specified via a call to this
 * function will be used until explicitly changed.
 *
 * Daily values of the offsets are published, for example, in IERS Bulletins A
 * and B.
 *
 *   REFERENCES:
 *      None.
 *
 *   INPUTS or OUTPUTS:
 *      del_dpsi (double)
 *         Value of offset in delta psi (dpsi) in arcseconds.
 *      del_deps (double)
 *         Value of offset in delta epsilon (deps) in arcseconds.
 */
static VALUE
rb_novas_cel_pole(VALUE v_mod, VALUE args)
{
  VALUE retval = Qnil;
  int argc = RARRAY(args)->len;

  // If one arg and it's an array, expand it
  if(argc == 1 && TYPE(rb_ary_entry(args,0)) == T_ARRAY) {
    args = rb_ary_entry(args,0);
    argc = RARRAY(args)->len;
  }

  if(argc == 0) {
    retval = rb_ary_new3(2, rb_float_new(PSI_COR), rb_float_new(EPS_COR));
  } else if(argc == 2) {
    PSI_COR = NUM2DBL(rb_ary_entry(args, 0));
    EPS_COR = NUM2DBL(rb_ary_entry(args, 1));
    cel_pole(PSI_COR, EPS_COR);
  } else {
    rb_raise(rb_eArgError, "wrong number of arguments (%d for 0 or 2)", argc);
  }
  return retval;
}

/*
 * call-seq: precesion(tjd1, pos1, tjd2) -> pos2
 *
 * Precesses equatorial rectangular coordinates from one epoch to another.  The
 * coordinates are referred to the mean equator and equinox of the two
 * respective epochs.
 *
 *   REFERENCES:
 *      Explanatory Supplement to AE and AENA (1961); pp. 30-34.
 *      Lieske, J., et al. (1977). Astron. & Astrophys. 58, 1-16. 
 *      Lieske, J. (1979). Astron. & Astrophys. 73, 282-284. 
 *      Kaplan, G. H. et. al. (1989). Astron. Journ. Vol. 97, 
 *         pp. 1197-1210.
 *      Kaplan, G. H. "NOVAS: Naval Observatory Vector Astrometry
 *         Subroutines"; USNO internal document dated 20 Oct 1988;
 *         revised 15 Mar 1990.
 *
 *   INPUTS:
 *      tjd1 (Float)
 *         TDB Julian date of first epoch.
 *      pos1 (Array of three Floats)
 *         Position vector, geocentric equatorial rectangular coordinates,
 *         referred to mean equator and equinox of first epoch.
 *      tjd2 (Float)
 *         TDB Julian date of second epoch.
 *
 *   OUTPUTS:
 *      pos2 (Array of three Floats)
 *         Position vector, geocentric equatorial rectangular coordinates,
 *         referred to mean equator and equinox of second epoch.
 */
static VALUE
rb_novas_precession(VALUE v_mod, VALUE v_tjd1, VALUE v_pos1, VALUE v_tjd2)
{
  double tjd1 = NUM2DBL(v_tjd1);
  double tjd2 = NUM2DBL(v_tjd2);
  double pos1[3];
  double pos2[3];
  int i;

  if(TYPE(v_pos1) != T_ARRAY || RARRAY(v_pos1)->len != 3) {
    rb_raise(rb_eArgError, "pos1 must be an Array of length 3");
  }

  rb_novas_ary2dbl(v_pos1, pos1, 3);

  precession(tjd1, pos1, tjd2, pos2);

  return rb_novas_dbl2ary(pos2, 3);
}

/*
 * call-seq: nutate(tdb, pos1, inverse=false) -> pos2
 *
 * Nutates equatorial rectangular coordinates from mean equator and equinox of
 * epoch to true equator and equinox of epoch.  Inverse transformation may be
 * applied by setting flag +inverse+ to +true+.
 *
 *   REFERENCES: 
 *      Kaplan, G. H. et. al. (1989). Astron. Journ. Vol. 97, 
 *         pp. 1197-1210.
 *      Kaplan, G. H. "NOVAS: Naval Observatory Vector Astrometry
 *         Subroutines"; USNO internal document dated 20 Oct 1988;
 *         revised 15 Mar 1990.
 *
 *   INPUTS:
 *      tdb (Float)
 *         TDB julian date of epoch.
 *      pos1 (Array of three Floats)
 *         Position vector, geocentric equatorial rectangular coordinates,
 *         referred to mean equator and equinox of epoch.
 *      inverse (true or false)
 *         Flag determining 'direction' of transformation;
 *            false = transformation applied, mean to true.
 *            true  = inverse transformation applied, true to mean.
 *
 *   OUTPUTS:
 *      pos2 (Array of three Floats)
 *         Position vector, geocentric equatorial rectangular coordinates,
 *         referred to true equator and equinox of epoch.
 */
static VALUE
rb_novas_nutate(VALUE v_mod, VALUE args)
{
  double tdb, pos1[3], pos2[3];
  int fn = FN0; // Default to foward transform
  int argc = RARRAY(args)->len;

  switch(argc) {
    case 3: fn = RTEST(rb_ary_entry(args, 2)) ? FN1 : FN0;
    case 2: if(rb_novas_ary2dbl(rb_ary_entry(args, 1), pos1, 3) != 3) {
              rb_raise(rb_eArgError, "pos1 must be an Array of length 3");
            }
            tdb = NUM2DBL(rb_ary_entry(args, 0));
            break;
    default:
      rb_raise(rb_eArgError, "wrong number of arguments (%d for 2 or 3)", argc);
  }

  nutate(tdb, fn, pos1, pos2);

  return rb_novas_dbl2ary(pos2, 3);
}

/*
 * call-seq: spin(tdb, pos1) -> pos2
 *
 * Transforms geocentric rectangular coordinates from rotating system based on
 * rotational equator and orthogonal reference meridian to non-rotating system
 * based on true equator and equinox of date.
 *
 *   REFERENCES: 
 *      Kaplan, G. H. et. al. (1989). Astron. Journ. Vol. 97, 
 *         pp. 1197-1210.
 *      Kaplan, G. H. "NOVAS: Naval Observatory Vector Astrometry
 *         Subroutines"; USNO internal document dated 20 Oct 1988;
 *         revised 15 Mar 1990.
 *
 *   INPUTS:
 *      st (Float)
 *         Local apparent sidereal time at reference meridian, in hours.
 *      pos1 (Array of 3 Floats)
 *         Vector in geocentric rectangular rotating system, referred
 *         to rotational equator and orthogonal reference meridian.
 *
 *   OUTPUTS:
 *      pos2 (Array of 3 Floats)
 *         Vector in geocentric rectangular non-rotating system,
 *         referred to true equator and equinox of date.
 */
static VALUE
rb_novas_spin(VALUE v_mod, VALUE v_st, VALUE v_pos1)
{
  double pos1[3], pos2[3];
  double st = NUM2DBL(v_st);

  if(rb_novas_ary2dbl(v_pos1, pos1, 3) != 3) {
    rb_raise(rb_eArgError, "pos1 must be an Array of length 3");
  }

  spin(st, pos1, pos2);

  return rb_novas_dbl2ary(pos2, 3);
}

/*
 * call-seq: wobble(x, y, pos1) -> pos2
 *
 * Corrects Earth-fixed geocentric rectangular coordinates for polar motion.
 * Transforms a vector from Earth-fixed geographic system to rotating system
 * based on rotational equator and orthogonal Greenwich meridian through axis
 * of rotation.
 *
 *   REFERENCES: 
 *      Kaplan, G. H. et. al. (1989). Astron. Journ. Vol. 97, 
 *         pp. 1197-1210.
 *      Kaplan, G. H. "NOVAS: Naval Observatory Vector Astrometry
 *         Subroutines"; USNO internal document dated 20 Oct 1988;
 *         revised 15 Mar 1990.
 *
 *   INPUTS:
 *      x (Float)
 *         Conventionally-defined X coordinate of rotational pole with
 *         respect to CIO, in arcseconds.
 *      y (Float)
 *         Conventionally-defined Y coordinate of rotational pole with
 *         respect to CIO, in arcseconds.
 *      pos1 (Array of 3 Floats)
 *         Vector in geocentric rectangular Earth-fixed system,
 *         referred to geographic equator and Greenwich meridian.
 *
 *   OUTPUTS:
 *      pos2 (Array of 3 Floats)
 *         Vector in geocentric rectangular rotating system, referred
 *         to rotational equator and orthogonal Greenwich meridian
 */
static VALUE
rb_novas_wobble(VALUE v_mod, VALUE v_x, VALUE v_y, VALUE v_pos1)
{
  double pos1[3], pos2[3];
  double x = NUM2DBL(v_x);
  double y = NUM2DBL(v_y);

  if(rb_novas_ary2dbl(v_pos1, pos1, 3) != 3) {
    rb_raise(rb_eArgError, "pos1 must be an Array of length 3");
  }

  wobble(x, y, pos1, pos2);

  return rb_novas_dbl2ary(pos2, 3);
}

/*
 * call-seq: pnsw(tjd, gast, x, y, vece) -> vecs
 *
 * Transforms a vector from an Earth-fixed geographic system to a space-fixed
 * system based on mean equator and equinox of J2000.0; applies rotations for
 * wobble, spin, nutation, and precession.
 *
 *   REFERENCES: 
 *      Kaplan, G. H. et. al. (1989). Astron. Journ. Vol. 97, 
 *         pp. 1197-1210.
 *      Kaplan, G. H. "NOVAS: Naval Observatory Vector Astrometry
 *         Subroutines"; USNO internal document dated 20 Oct 1988;
 *         revised 15 Mar 1990.
 *
 *   INPUTS:
 *      tjd (Float)
 *         TT (or TDT) Julian date
 *         (tjd == 0.0 -> no precession/nutation transformation)
 *      gast (Float)
 *         Greenwich apparent sidereal time, in hours.
 *         (gast == 0.0 -> no spin transformation)
 *      x (Float)
 *         Conventionally-defined X coordinate of rotational pole with
 *         respect to CIO, in arcseconds.
 *         (x == y == 0 -> no wobble transformation)
 *      y (Float)
 *         Conventionally-defined Y coordinate of rotational pole with
 *         respect to CIO, in arcseconds.
 *         (x == y == 0 -> no wobble transformation)
 *      vece (Array of 3 Floats)
 *         Vector in geocentric rectangular Earth-fixed system,
 *         referred to geographic equator and Greenwich meridian.
 *
 *   OUTPUTS:
 *      vecs (Array of 3 Floats)
 *         Vector in geocentric rectangular space-fixed system,
 *         referred to mean equator and equinox of J2000.0.
 */
static VALUE
rb_novas_pnsw(VALUE v_mod, VALUE v_tjd, VALUE v_gast, VALUE v_x, VALUE v_y, VALUE v_vece)
{
  double vece[3], vecs[3];
  double tjd = NUM2DBL(v_tjd);
  double gast = NUM2DBL(v_gast);
  double x = NUM2DBL(v_x);
  double y = NUM2DBL(v_y);

  if(rb_novas_ary2dbl(v_vece, vece, 3) != 3) {
    rb_raise(rb_eArgError, "vece must be an Array of length 3");
  }

  pnsw(tjd, gast, x, y, vece, vecs);

  return rb_novas_dbl2ary(vecs, 3);
}

/*
 * call-seq: Novas.earthrad() -> earthrad_km
 *
 * Returns current Earth equatorial radius in kilometers.
 */
static VALUE
rb_novas_earthrad(VALUE v_mod)
{
  return rb_float_new(EARTHRAD);
}

/*
 * call-seq: Novas.earthrad=(earthrad_km)
 *
 * Sets the Earth equatorial radius in kilometers.
 */
static VALUE
rb_novas_earthrad_assign(VALUE v_mod, VALUE v_earthrad)
{
  EARTHRAD = NUM2DBL(v_earthrad);
  return v_earthrad;
}

/*
 * call-seq: Novas.f() -> earth_ellipsoid_flattening
 *
 * Returns current Earth ellipsoid flattening.
 */
static VALUE
rb_novas_f(VALUE v_mod)
{
  return rb_float_new(F);
}

/*
 * call-seq: Novas.f=(earth_ellipsoid_flattening)
 *
 * Sets the earth ellipsoid flattening.
 */
static VALUE
rb_novas_f_assign(VALUE v_mod, VALUE v_f)
{
  F = NUM2DBL(v_f);
  return v_f;
}

#ifdef TODO
/*
 * call-seq:
 *
 */
static VALUE
rb_novas_template_args(VALUE v_mod, VALUE args)
{
  int argc = RARRAY(args)->len;

  // If one arg and it's an array, expand it
  if(argc == 1 && TYPE(rb_ary_entry(args,0)) == T_ARRAY) {
    args = rb_ary_entry(args,0);
    argc = RARRAY(args)->len;
  }
}

rb_novas_radec2vector
rb_novas_vector2radec
#endif

#define rb_define_const_nodoc rb_define_const

void
Init_novas_ext()
{
  // Novas Module
  VALUE rb_mNovas = rb_define_module("Novas");

  // Document-constant: BARYCENTRIC
  //
  // Foo
  rb_define_const_nodoc(rb_mNovas,"BARYCENTRIC",INT2FIX(BARYC));
  rb_define_const_nodoc(rb_mNovas,"HELIOCENTRIC",INT2FIX(HELIOC));
  rb_define_const_nodoc(rb_mNovas,"T0",rb_float_new(T0));
  rb_define_const_nodoc(rb_mNovas,"KMAU",rb_float_new(KMAU));
  rb_define_const_nodoc(rb_mNovas,"MAU",rb_float_new(MAU));
  rb_define_const_nodoc(rb_mNovas,"C",rb_float_new(C));
  rb_define_const_nodoc(rb_mNovas,"GS",rb_float_new(GS));
  rb_define_const_nodoc(rb_mNovas,"EARTHRAD",rb_float_new(EARTHRAD));
  rb_define_const_nodoc(rb_mNovas,"F",rb_float_new(F));
  rb_define_const_nodoc(rb_mNovas,"OMEGA",rb_float_new(OMEGA));
  rb_define_const_nodoc(rb_mNovas,"TWOPI",rb_float_new(TWOPI));
  rb_define_const_nodoc(rb_mNovas,"PI",rb_float_new(TWOPI/2.0));
  rb_define_const_nodoc(rb_mNovas,"RAD2SEC",rb_float_new(RAD2SEC));
  rb_define_const_nodoc(rb_mNovas,"DEG2RAD",rb_float_new(DEG2RAD));
  rb_define_const_nodoc(rb_mNovas,"RAD2DEG",rb_float_new(RAD2DEG));
  // Refraction options
  rb_define_const_nodoc(rb_mNovas,"NONE",INT2FIX(0));
  rb_define_const_nodoc(rb_mNovas,"DEFAULT",INT2FIX(1));
  rb_define_const_nodoc(rb_mNovas,"ATMOS",INT2FIX(2));

  // Novas Module Functions
  rb_define_module_function(rb_mNovas, "sidereal_time", rb_novas_sidereal_time, -2);
  rb_define_module_function(rb_mNovas, "cal_date", rb_novas_cal_date, 1);
  rb_define_module_function(rb_mNovas, "julian_date", rb_novas_julian_date, -2);
  rb_define_module_function(rb_mNovas, "earthtilt", rb_novas_earthtilt, 1);
  rb_define_module_function(rb_mNovas, "cel_pole", rb_novas_cel_pole, -2);
  rb_define_module_function(rb_mNovas, "precession", rb_novas_precession, 3);
  rb_define_module_function(rb_mNovas, "nutate", rb_novas_nutate, -2);
  rb_define_module_function(rb_mNovas, "spin", rb_novas_spin, 2);
  rb_define_module_function(rb_mNovas, "wobble", rb_novas_wobble, 3);
  rb_define_module_function(rb_mNovas, "pnsw", rb_novas_pnsw, 5);
  rb_define_module_function(rb_mNovas, "earthrad", rb_novas_earthrad, 0);
  rb_define_module_function(rb_mNovas, "earthrad=", rb_novas_earthrad_assign, 1);
  rb_define_module_function(rb_mNovas, "f", rb_novas_f, 0);
  rb_define_module_function(rb_mNovas, "f=", rb_novas_f_assign, 1);

  // Init other classes
  init_body();
  init_site_info();
  init_cat_entry();

  // Init cel_pole
  PSI_COR = 0.0;
  EPS_COR = 0.0;
  cel_pole(0.0, 0.0);
}
