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

// "Private" (i.e. file local) values
static VALUE rb_cCatEntry;
static VALUE rb_vEarth;
static VALUE rb_symApparent;
static VALUE rb_symVirtual;
static VALUE rb_symAstro;
static VALUE rb_symTopo;
static VALUE rb_symLocal;

// CatEntry class

static VALUE
rb_novas_cat_entry_alloc(VALUE klass)
{
  cat_entry * p;
  return Data_Make_Struct(klass, cat_entry, 0, free, p);
}

DEFINE_GET_ATTR_STR(cat_entry,catalog)
DEFINE_GET_ATTR_STR(cat_entry,starname)
DEFINE_GET_ATTR_INT(cat_entry,starnumber)
DEFINE_GET_ATTR_DBL(cat_entry,ra)
DEFINE_GET_ATTR_DBL(cat_entry,dec)
DEFINE_GET_ATTR_DBL(cat_entry,promora)
DEFINE_GET_ATTR_DBL(cat_entry,promodec)
DEFINE_GET_ATTR_DBL(cat_entry,parallax)
DEFINE_GET_ATTR_DBL(cat_entry,radialvelocity)

DEFINE_SET_ATTR_STR(cat_entry,catalog,3)
DEFINE_SET_ATTR_STR(cat_entry,starname,50)
DEFINE_SET_ATTR_INT(cat_entry,starnumber,long int)
DEFINE_SET_ATTR_DBL(cat_entry,ra)
DEFINE_SET_ATTR_DBL(cat_entry,dec)
DEFINE_SET_ATTR_DBL(cat_entry,promora)
DEFINE_SET_ATTR_DBL(cat_entry,promodec)
DEFINE_SET_ATTR_DBL(cat_entry,parallax)
DEFINE_SET_ATTR_DBL(cat_entry,radialvelocity)

/* 
 * call-seq: CatEntry.new(ra, dec) -> cat_entry
 *           CatEntry.new(ra, dec, starname) -> cat_entry
 *           CatEntry.new(ra, dec, starname, starnumber, catalog) -> cat_entry
 *           CatEntry.new(ra, dec, starname, starnumber, catalog,
 *                        promora, promodec, parallax, radialvelocity) -> cat_entry
 *
 * Constructs a new CatEntry objects to hold the astrometric catalog data for a
 * star or other extra-solor object.  Equator and equinox and units will depend
 * on the catalog.  While this structure can be used as a generic container for
 * catalog data, all high-level NOVAS-C functions require J2000.0 catalog data
 * with FK5-type units (shown in square brackets below).
 *                   
 *   catalog            = character catalog designator (String, maxlen = 3).
 *   starname           = name of star (String, maxlen = 50).
 *   starnumber         = integer identifier assigned to star (Fixnum).
 *   ra                 = mean right ascension [hours] (Float).
 *   dec                = mean declination [degrees] (Float).
 *   promora            = proper motion in RA [seconds of time per 
 *                        century] (Float).
 *   promodec           = proper motion in declination [arcseconds per 
 *                        century] (Float).
 *   parallax           = parallax [arcseconds] (Float).
 *   radialvelocity     = radial velocity [kilometers per second] (Float).
 */
static VALUE
rb_novas_cat_entry_initialize(VALUE self, VALUE args)
{
  int argc = RARRAY(args)->len;

  // If one arg and it's an array, expand it
  if(argc == 1 && TYPE(rb_ary_entry(args,0)) == T_ARRAY) {
    args = rb_ary_entry(args,0);
    argc = RARRAY(args)->len;
  }

  switch(argc) {
    case 9: rb_novas_cat_entry_set_radialvelocity(self,rb_ary_entry(args,8));
            rb_novas_cat_entry_set_parallax(self,rb_ary_entry(args,7));
            rb_novas_cat_entry_set_promodec(self,rb_ary_entry(args,6));
            rb_novas_cat_entry_set_promora(self,rb_ary_entry(args,5));
    case 5: rb_novas_cat_entry_set_catalog(self,rb_ary_entry(args,4));
            rb_novas_cat_entry_set_starnumber(self,rb_ary_entry(args,3));
    case 3: rb_novas_cat_entry_set_starname(self,rb_ary_entry(args,2));
    case 2: rb_novas_cat_entry_set_dec(self,rb_ary_entry(args,1));
            rb_novas_cat_entry_set_ra(self,rb_ary_entry(args,0));
            break;
    default:
      rb_raise(rb_eArgError, "wrong number of arguments (%d for 2, 3, 5, or 9)", argc);
  }
  return self;
}

static VALUE
rb_novas_cat_entry_geocentric(VALUE self, VALUE v_tjd, VALUE v_sym)
{
  //ID id;
  double tjd;
  body * earth;
  cat_entry * star;
  double ra;
  double dec;
  short int error;

  //id = SYM2ID(v_sym);
  tjd = NUM2DBL(v_tjd);
  Data_Get_Struct(rb_vEarth,body,earth);
  Data_Get_Struct(self,cat_entry,star);

  // TODO Check that v_sym is actually a symbol

  if(v_sym == rb_symApparent) {
    error = app_star(tjd,earth,star,&ra,&dec);
  } else if(v_sym == rb_symVirtual) {
    error = virtual_star(tjd,earth,star,&ra,&dec);
  } else if(v_sym == rb_symAstro) {
    error = astro_star(tjd,earth,star,&ra,&dec);
  } else {
    // TODO Convert v_sym to string better
    rb_raise(rb_eArgError, "invalid geocentric mode (%s)", StringValuePtr(v_sym));
  }

  // These error codes are for solorsystem version 3
  switch(error) {
    case 0: break;
    case 1: rb_raise(rb_eArgError, "Julian date out of range (%f)", tjd);
            break;
    case 2: rb_raise(rb_eRuntimeError, "invalid body parameter for Earth", tjd);
            break;
    default: rb_raise(rb_eRuntimeError,
                 "unexpected error code from app_star (%d)", error);
  }

  return rb_ary_new3(2, rb_float_new(ra), rb_float_new(dec));
}

/*
 * call-seq: app_star(tjd) -> [ra, dec]
 *
 * Computes the apparent place of a star at date +tjd+, given its mean place,
 * proper motion, parallax, and radial velocity for J2000.0.
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
 *         TT (or TDT) Julian date for apparent place.
 *
 *   OUTPUTS:
 *      ra (Float)
 *         Apparent right ascension in hours, referred to true equator
 *         and equinox of date 'tjd'.
 *      dec (Float)
 *         Apparent declination in degrees, referred to true equator
 *         and equinox of date 'tjd'.
 */
static VALUE
rb_novas_cat_entry_app_star(VALUE self, VALUE v_tjd)
{
  return rb_novas_cat_entry_geocentric(self,v_tjd,rb_symApparent);
}

/*
 * call-seq: virtual_star(tjd) -> [ra, dec]
 *
 * Computes the virtual place of a star at date 'tjd', given its mean place,
 * proper motion, parallax, and radial velocity for J2000.0.
 *
 *    REFERENCES: 
 *       Kaplan, G. H. et. al. (1989). Astron. Journ. Vol. 97, 
 *          pp. 1197-1210.
 *       Kaplan, G. H. "NOVAS: Naval Observatory Vector Astrometry
 *          Subroutines"; USNO internal document dated 20 Oct 1988;
 *          revised 15 Mar 1990.
 *
 *    INPUTS:
 *       tjd (Float)
 *          TT (or TDT) Julian date for virtual place.
 *
 *    OUTPUTS:
 *       ra (Float)
 *          Virtual right ascension in hours, referred to mean equator
 *          and equinox of J2000.
 *       dec (Float)
 *          Virtual declination in degrees, referred to mean equator
 *          and equinox of J2000.
 */
static VALUE
rb_novas_cat_entry_virtual_star(VALUE self, VALUE v_tjd)
{
  return rb_novas_cat_entry_geocentric(self,v_tjd,rb_symVirtual);
}

/*
 * call-seq: astro_star(tjd) -> [ra, dec]
 *
 * Computes the astrometric place of a star, given its mean place, proper
 * motion, parallax, and radial velocity for J2000.0.
 *
 *    REFERENCES: 
 *       Kaplan, G. H. et. al. (1989). Astron. Journ. Vol. 97, 
 *          pp. 1197-1210.
 *       Kaplan, G. H. "NOVAS: Naval Observatory Vector Astrometry
 *          Subroutines"; USNO internal document dated 20 Oct 1988;
 *          revised 15 Mar 1990.
 *
 *    INPUTS:
 *       tjd (Float)
 *          TT (or TDT) Julian date for astrometric place.
 *
 *    OUTPUTS:
 *       ra (Float)
 *          Astrometric right ascension in hours, referred to mean equator
 *          and equinox of J2000.
 *       dec (Float)
 *          Astrometric declination in degrees, referred to mean equator
 *          and equinox of J2000.
 */
static VALUE
rb_novas_cat_entry_astro_star(VALUE self, VALUE v_tjd)
{
  return rb_novas_cat_entry_geocentric(self,v_tjd,rb_symAstro);
}

static VALUE
rb_novas_cat_entry_topocentric(VALUE self, VALUE v_tjd, VALUE v_deltat, VALUE v_location, VALUE v_sym)
{
  //ID id;
  double tjd;
  body * earth;
  cat_entry * star;
  site_info * location;
  double deltat;
  double ra;
  double dec;
  short int error;

  //id = SYM2ID(v_sym);
  tjd = NUM2DBL(v_tjd);
  Data_Get_Struct(rb_vEarth,body,earth);
  Data_Get_Struct(self,cat_entry,star);
  deltat = NUM2DBL(v_deltat);
  Data_Get_Struct(v_location,site_info,location);
  //printf("%s:      =%s\n", __FUNCTION__, RSTRING(rb_funcall(v_sym, rb_intern("inspect"), 0))->ptr);

  // TODO Check that v_sym is actually a symbol
  // TODO Convert v_sym to an ID?

  if(v_sym == rb_symTopo) {
    error = topo_star(tjd,earth,deltat,star,location,&ra,&dec);
  } else if(v_sym == rb_symLocal) {
    error = local_star(tjd,earth,deltat,star,location,&ra,&dec);
  } else {
    // TODO Convert v_sym to string better
    rb_raise(rb_eArgError, "invalid topocentric mode (%s)",
        RSTRING(rb_funcall(v_sym, rb_intern("inspect"), 0))->ptr);
  }

  // These error codes are for solorsystem version 3
  switch(error) {
    case 0: break;
    case 1: rb_raise(rb_eArgError, "Julian date out of range (%f)", tjd);
            break;
    case 2: rb_raise(rb_eRuntimeError, "invalid body parameter for Earth", tjd);
            break;
    default: rb_raise(rb_eRuntimeError,
                 "unexpected error code from app_star (%d)", error);
  }

  return rb_ary_new3(2, rb_float_new(ra), rb_float_new(dec));
}

/*
 * call-seq: topo_star(tjd, deltat, location) -> [ra, dec]
 *
 * Computes the topocentric place of a star at date 'tjd', given its mean
 * place, proper motion, parallax, and radial velocity for J2000.0 and the
 * location of the observer.
 *
 *    REFERENCES: 
 *       Kaplan, G. H. et. al. (1989). Astron. Journ. Vol. 97, 
 *          pp. 1197-1210.
 *       Kaplan, G. H. "NOVAS: Naval Observatory Vector Astrometry
 *          Subroutines"; USNO internal document dated 20 Oct 1988;
 *          revised 15 Mar 1990.
 *
 *    INPUTS:
 *       tjd (Float)
 *          TT (or TDT) Julian date for topocentric place.
 *       deltat (Float)
 *          Difference TT-UT1 (or TDT-UT1) at 'tjd', in seconds.
 *       location (Site)
 *          Site object containing observer's location.
 *
 *    OUTPUTS:
 *       ra (Float)
 *          Topocentric right ascension in hours, referred to true equator
 *          and equinox of date 'tjd'.
 *       dec (Float)
 *          Topocentric declination in degrees, referred to true equator
 *          and equinox of date 'tjd'.
 */
static VALUE
rb_novas_cat_entry_topo_star(VALUE self, VALUE v_tjd, VALUE v_deltat, VALUE v_location)
{
  return rb_novas_cat_entry_topocentric(self,v_tjd,v_deltat,v_location,rb_symTopo);
}

/*
 * call-seq: local_star(tjd, deltat, location) -> [ra, dec]
 *
 * Computes the local place of a star, given its mean place, proper motion,
 * parallax, and radial velocity for J2000.0, and the location of the observer.
 *
 *    REFERENCES: 
 *       Kaplan, G. H. et. al. (1989). Astron. Journ. Vol. 97, 
 *          pp. 1197-1210.
 *       Kaplan, G. H. "NOVAS: Naval Observatory Vector Astrometry
 *          Subroutines"; USNO internal document dated 20 Oct 1988;
 *          revised 15 Mar 1990.
 *
 *    INPUTS:
 *       tjd (Float)
 *          TT (or TDT) Julian date for local place.
 *       deltat (Float)
 *          Difference TT-UT1 (or TDT-UT1) at 'tjd', in seconds.
 *       location (Site)
 *          Site object containing observer's location.
 *
 *    OUTPUTS:
 *       ra (Float)
 *          Local right ascension in hours, referred to mean equator and
 *          equinox of J2000.
 *       dec (Float)
 *          Local declination in degrees, referred to mean equator and
 *          equinox of J2000.
 */
static VALUE
rb_novas_cat_entry_local_star(VALUE self, VALUE v_tjd, VALUE v_deltat, VALUE v_location)
{
  return rb_novas_cat_entry_topocentric(self,v_tjd,v_deltat,v_location,rb_symLocal);
}

/*
 * Document-class: CatEntry
 *
 * CatEntry objects store the astrometric catalog data for a star or other
 * distant object.
 */
void
init_cat_entry()
{
  // Novas::CatEntry Class
  VALUE rb_mNovas = rb_define_module("Novas");
  VALUE rb_cCatEntry = rb_define_class_under(rb_mNovas,"CatEntry",rb_cObject);

  rb_symApparent = ID2SYM(rb_intern("apparent"));
  rb_symVirtual = ID2SYM(rb_intern("virtual"));
  rb_symAstro = ID2SYM(rb_intern("astro"));
  rb_symTopo = ID2SYM(rb_intern("topo"));
  rb_symLocal = ID2SYM(rb_intern("local"));

  // Get reference to Body::EARTH
  // (init_body must be called before init_cat_entry).
  VALUE rb_cBody = rb_const_get(rb_mNovas,rb_intern("Body"));
  rb_vEarth = rb_const_get(rb_cBody,rb_intern("EARTH"));

  // CatEntry Class
  rb_define_alloc_func(rb_cCatEntry, rb_novas_cat_entry_alloc);
  rb_define_method(rb_cCatEntry, "initialize", rb_novas_cat_entry_initialize, -2);
  rb_define_method(rb_cCatEntry, "geocentric", rb_novas_cat_entry_geocentric, 2);
  rb_define_method(rb_cCatEntry, "app_star", rb_novas_cat_entry_app_star, 1);
  rb_define_method(rb_cCatEntry, "virtual_star", rb_novas_cat_entry_virtual_star, 1);
  rb_define_method(rb_cCatEntry, "astro_star", rb_novas_cat_entry_astro_star, 1);
  rb_define_method(rb_cCatEntry, "topocentric", rb_novas_cat_entry_topocentric, 4);
  rb_define_method(rb_cCatEntry, "topo_star", rb_novas_cat_entry_topo_star, 3);
  rb_define_method(rb_cCatEntry, "local_star", rb_novas_cat_entry_local_star, 3);

  BIND_GET_ATTR(CatEntry,catalog,cat_entry,catalog);
  BIND_GET_ATTR(CatEntry,starname,cat_entry,starname);
  BIND_GET_ATTR(CatEntry,starnumber,cat_entry,starnumber);
  BIND_GET_ATTR(CatEntry,ra,cat_entry,ra);
  BIND_GET_ATTR(CatEntry,dec,cat_entry,dec);
  BIND_GET_ATTR(CatEntry,promora,cat_entry,promora);
  BIND_GET_ATTR(CatEntry,promodec,cat_entry,promodec);
  BIND_GET_ATTR(CatEntry,parallax,cat_entry,parallax);
  BIND_GET_ATTR(CatEntry,radialvelocity,cat_entry,radialvelocity);

  BIND_SET_ATTR(CatEntry,catalog,cat_entry,catalog);
  BIND_SET_ATTR(CatEntry,starname,cat_entry,starname);
  BIND_SET_ATTR(CatEntry,starnumber,cat_entry,starnumber);
  BIND_SET_ATTR(CatEntry,ra,cat_entry,ra);
  BIND_SET_ATTR(CatEntry,dec,cat_entry,dec);
  BIND_SET_ATTR(CatEntry,promora,cat_entry,promora);
  BIND_SET_ATTR(CatEntry,promodec,cat_entry,promodec);
  BIND_SET_ATTR(CatEntry,parallax,cat_entry,parallax);
  BIND_SET_ATTR(CatEntry,radialvelocity,cat_entry,radialvelocity);
}
