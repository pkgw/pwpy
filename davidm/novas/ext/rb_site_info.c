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

// Site class

static VALUE
rb_novas_site_info_alloc(VALUE klass)
{
  site_info * p;
  VALUE self = Data_Make_Struct(klass, site_info, 0, free, p);
}

/*
 * Document-method: latitude
 * call-seq: latitude -> degrees
 *
 * Returns the geodetic latitude of +self+ in degrees; north positive.
 */
DEFINE_GET_ATTR_DBL(site_info,latitude)
/*
 * Document-method: longitude
 * call-seq: longitude -> degrees
 *
 * Returns the geodetic longitude of +self+ in degrees; east positive.
 */
DEFINE_GET_ATTR_DBL(site_info,longitude)
/*
 * Document-method: height
 * call-seq: height -> meters
 *
 * Returns the height of +self+ in meters.
 */
DEFINE_GET_ATTR_DBL(site_info,height)
/*
 * Document-method: temperature
 * call-seq: temperature -> degreesC
 *
 * Returns the temperature of +self+ in degrees Celcius.
 */
DEFINE_GET_ATTR_DBL(site_info,temperature)
/*
 * Document-method: pressure
 * call-seq: pressure -> millibars
 *
 * Returns the atmospheric pressure of +self+ in millibars.
 */
DEFINE_GET_ATTR_DBL(site_info,pressure)

/*
 * Document-method: latitude=
 * call-seq: latitude = <em>degrees</em>
 *
 * Sets the geodetic latitude of +self+ in degrees; north positive.
 */
DEFINE_SET_ATTR_DBL(site_info,latitude)
/*
 * Document-method: longitude=
 * call-seq: longitude = -> <em>degrees</em>
 *
 * Returns the geodetic longitude of +self+ in degrees; east positive.
 */
DEFINE_SET_ATTR_DBL(site_info,longitude)
/*
 * Document-method: height=
 * call-seq: height = -> <em>meters</em>
 *
 * Returns the height of +self+ in meters.
 */
DEFINE_SET_ATTR_DBL(site_info,height)
/*
 * Document-method: temperature=
 * call-seq: temperature = -> <em>degreesC</em>
 *
 * Returns the temperature of +self+ in degrees Celcius.
 */
DEFINE_SET_ATTR_DBL(site_info,temperature)
/*
 * Document-method: pressure=
 * call-seq: pressure = <em>millibars</em>
 *
 * Returns the atmospheric pressure of +self+ in millibars.
 */
DEFINE_SET_ATTR_DBL(site_info,pressure)

/*
 * call-seq: Site.new(latitude, longitude) -> site
 *           Site.new(latitude, longitude, height) -> site
 *           Site.new(latitude, longitude, height, temperature, pressure) -> site
 *
 * Constructs a new Site object to hold the data for the observer's
 * location.  The atmospheric parameters are used only by the refraction
 * function called from function equ2hor.  Additional parameters can be added
 * to this structure if a more sophisticated refraction model is employed.
 *
 * All parameters are stored as Floats.
 *                   
 *   latitude           = geodetic latitude in degrees; north positive.
 *   longitude          = geodetic longitude in degrees; east positive.
 *   height             = height of the observer in meters.
 *   temperature        = temperature (degrees Celsius).
 *   pressure           = atmospheric pressure (millibars)
 *
 * +height+:: Defaults to <tt>0.0</tt>
 * +temperature+:: Defaults to <tt>10.0</tt>
 * +pressure+:: Defaults to <tt>1010.0 * Math.exp(-height/9.1e3)</tt> 
 */

static VALUE
rb_novas_site_info_initialize(VALUE self, VALUE args)
{
  site_info * p;
  int argc = RARRAY(args)->len;

  Data_Get_Struct(self, site_info, p);

  // If one arg and it's an array, expand it
  if(argc == 1 && TYPE(rb_ary_entry(args,0)) == T_ARRAY) {
    args = rb_ary_entry(args,0);
    argc = RARRAY(args)->len;
  }

  // Get values from args
  switch(argc) {
    case 5: p->pressure    = NUM2DBL(rb_ary_entry(args,4));
    case 4: p->temperature = NUM2DBL(rb_ary_entry(args,3));
    case 3: p->height      = NUM2DBL(rb_ary_entry(args,2));
    case 2: p->longitude   = NUM2DBL(rb_ary_entry(args,1));
            p->latitude    = NUM2DBL(rb_ary_entry(args,0));
            break;
    default:
      rb_raise(rb_eArgError, "wrong number of arguments (%d for 2 to 5)", argc);
  }
  // Set default values for missing params
  switch(argc) {
    case 2: p->height      = 0.0;
    case 3: p->temperature = 10.0;
    case 4: p->pressure    = 1010.0 * exp(-p->height/9.1e3);
  }
  return self;
}

/*
 * call-seq: equ2hor(tjd, deltat, ra, dec, refopt = NONE) -> [az, el, rar, decr]
 *           equ2hor(tjd, deltat, ra, dec, refopt, x, y) -> [az, el, rar, decr]
 *
 * This function transforms apparent equatorial coordinates (right ascension
 * and declination) to horizon coordinates (azimuth and elevation) for the location
 * specified by +self+.  It uses a method that properly accounts for polar
 * motion, which is significant at the sub-arcsecond level.  This function can
 * also adjust coordinates for atmospheric refraction for optical wavelengths.
 *
 *   REFERENCES:
 *       None.
 *
 *   INPUTS:
 *      tjd (Float)
 *         TT (or TDT) Julian date.
 *      deltat (Float)
 *         Difference TT (or TDT)-UT1 at +tjd+, in seconds.
 *      ra (Float)
 *         Topocentric right ascension of object of interest, in hours, 
 *         referred to true equator and equinox of date.
 *      dec (Float)
 *         Topocentric declination of object of interest, in degrees, 
 *         referred to true equator and equinox of date.
 *      ref_option (Fixnum)
 *         = 0 (or Novas::NONE)    ... no refraction
 *         = 1 (or Novas::DEFAULT) ... include refraction, using 'standard'
 *                                     atmospheric conditions.
 *         = 2 (or Novas::ATMOS)   ... include refraction, using atmospheric
 *                                     parameters input in the 'location'
 *                                     structure.
 *      x (Float)
 *         Conventionally-defined x coordinate of celestial ephemeris 
 *         pole with respect to IERS reference pole, in arcseconds. 
 *      y (Float)
 *         Conventionally-defined y coordinate of celestial ephemeris 
 *         pole with respect to IERS reference pole, in arcseconds.
 *
 *   OUTPUTS:
 *      az (Float)
 *         Topocentric azimuth (measured east from north) in degrees.
 *      el (Float)
 *         Topocentric elevation in degrees, affected by 
 *         refraction if +refopt+ is non-zero.
 *      rar (Float)
 *         Topocentric right ascension of object of interest, in hours, 
 *         referred to true equator and equinox of date, affected by 
 *         refraction if +refopt+ is non-zero.
 *      decr (Float)
 *         Topocentric declination of object of interest, in degrees, 
 *         referred to true equator and equinox of date, affected by 
 *         refraction if +refopt+ is non-zero.
 */
static VALUE
rb_novas_site_info_equ2hor(VALUE self, VALUE args)
{
  site_info * location;
  double tjd = 0.0;
  double deltat = 0.0;
  double ra = 0.0;
  double dec = 0.0;
  short int ref_option = 0;
  double x = 0.0;
  double y = 0.0;
  double az;
  double zd;
  double rar;
  double decr;
  int argc = RARRAY(args)->len;

  Data_Get_Struct(self, site_info, location);

  // Get values from args
  switch(argc) {
    case 7: y = NUM2DBL(rb_ary_entry(args,6));
            x = NUM2DBL(rb_ary_entry(args,5));
    case 5: ref_option = NUM2INT(rb_ary_entry(args,4));
    case 4: dec = NUM2DBL(rb_ary_entry(args,3));
            ra = NUM2DBL(rb_ary_entry(args,2));
            deltat = NUM2DBL(rb_ary_entry(args,1));
            tjd = NUM2DBL(rb_ary_entry(args,0));
            break;
    default:
      rb_raise(rb_eArgError, "wrong number of arguments (%d for 4, 5, or 7)", argc);
  }

  equ2hor(tjd, deltat, x, y, location, ra, dec, ref_option, &zd, &az, &rar, &decr);

  return rb_ary_new3(4,
      rb_float_new(az), rb_float_new(90.0-zd),
      rb_float_new(rar), rb_float_new(decr));
}

/*
 * call-seq: terra(st=0) -> [pos, vel]
 *
 * Computes the position and velocity vectors of a terrestrial observer with
 * respect to the center of the Earth.
 *
 * If reference meridian is Greenwich and +st+ is 0 (the default), +pos+ is
 * effectively referred to equator and Greenwich.
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
 *         Local apparent sidereal time at reference meridian in hours.
 *
 *   OUTPUTS:
 *      pos (Array of 3 Floats)
 *         Position vector of observer with respect to center of Earth,
 *         equatorial rectangular coordinates, referred to true equator
 *         and equinox of date, components in AU.
 *      vel (Array of 3 Floats)
 *         Velocity vector of observer with respect to center of Earth,
 *         equatorial rectangular coordinates, referred to true equator
 *         and equinox of date, components in AU/Day.
 */
static VALUE
rb_novas_site_info_terra(VALUE self, VALUE args)
{
  site_info * location;
  double st = 0.0;
  double pos[3], vel[3];
  int i;
  int argc = RARRAY(args)->len;

  Data_Get_Struct(self, site_info, location);

  // Get values from args
  switch(argc) {
    case 1: st = NUM2DBL(rb_ary_entry(args,0));
    case 0: break;
    default:
      rb_raise(rb_eArgError, "wrong number of arguments (%d for 0 or 1)", argc);
  }

  terra(location, st, pos, vel);

  return rb_ary_new3(2, rb_novas_dbl2ary(pos, 3), rb_novas_dbl2ary(vel, 3));
}

/*
 * Document-class: Site
 *
 * A Site object holds data for the observer's location.
 */
void
init_site_info()
{
  // Novas::Site Class
  VALUE rb_mNovas = rb_define_module("Novas");
  VALUE rb_cSiteInfo = rb_define_class_under(rb_mNovas,"Site",rb_cObject);

  // Site Class
  rb_define_alloc_func(rb_cSiteInfo, rb_novas_site_info_alloc);
  rb_define_method(rb_cSiteInfo, "initialize", rb_novas_site_info_initialize, -2);
  rb_define_method(rb_cSiteInfo, "equ2hor", rb_novas_site_info_equ2hor, -2);
  rb_define_method(rb_cSiteInfo, "terra", rb_novas_site_info_terra, -2);

  rb_define_method(rb_cSiteInfo, "latitude",    rb_novas_site_info_get_latitude,    0);
  rb_define_method(rb_cSiteInfo, "longitude",   rb_novas_site_info_get_longitude,   0);
  rb_define_method(rb_cSiteInfo, "height",      rb_novas_site_info_get_height,      0);
  rb_define_method(rb_cSiteInfo, "temperature", rb_novas_site_info_get_temperature, 0);
  rb_define_method(rb_cSiteInfo, "pressure",    rb_novas_site_info_get_pressure,    0);

  rb_define_method(rb_cSiteInfo, "latitude=",    rb_novas_site_info_set_latitude,    1);
  rb_define_method(rb_cSiteInfo, "longitude=",   rb_novas_site_info_set_longitude,   1);
  rb_define_method(rb_cSiteInfo, "height=",      rb_novas_site_info_set_height,      1);
  rb_define_method(rb_cSiteInfo, "temperature=", rb_novas_site_info_set_temperature, 1);
  rb_define_method(rb_cSiteInfo, "pressure=",    rb_novas_site_info_set_pressure,    1);
}
