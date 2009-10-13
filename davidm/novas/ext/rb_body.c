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

#define MAKE_BODY_CONST(type, number, name) do { \
  rb_define_const(rb_cBody,#name, \
    rb_novas_body_initialize_c( \
      rb_novas_body_alloc(rb_cBody), type, number, #name)); \
} while(0)

// Body class

/*
 * Document-class: Novas::Body
 *
 * A +Body+ object designates a celestial object.
 */

static VALUE
rb_novas_body_alloc(VALUE klass)
{
  body * p;
  return Data_Make_Struct(klass, body, 0, free, p);
}

DEFINE_GET_ATTR_INT(body,type)
DEFINE_GET_ATTR_INT(body,number)
DEFINE_GET_ATTR_STR(body,name)

static VALUE
rb_novas_body_initialize_c(VALUE self, short int type, short int number, char *name)
{
  body tmp;
  body * p;
  short int error;

  Data_Get_Struct(self,body,p);

  error = set_body(type, number, name, &tmp);

  switch(error) {
    case 0: break;
    case 1: rb_raise(rb_eArgError, "invalid type (%d)", type);
    case 2: rb_raise(rb_eRangeError, "number out of range (%d)", number);
    default:
            rb_raise(rb_eRuntimeError,
                "unexpected error code from set_body (%d)", error);
  }
  memcpy(p,&tmp,sizeof(body));
  return self;
}

/*
 * call-seq: Body.new(type, number, name) -> body
 *
 * Creates a new Body object using the specified parameters.  Body objects for
 * the major planets, Sun, and Moon exist as constants in the Novas module.
 *
 *   type              = type of body
 *                     = 0 ... major planet, Sun, or Moon
 *                     = 1 ... minor planet
 *   number            = body number
 *                       For 'type' = 0: Mercury = 1, ..., Pluto = 9,
 *                                       Sun = 10, Moon = 11
 *                       For 'type' = 1: minor planet number
 *   name              = name of the body (limited to 99 characters)
 */

static VALUE
rb_novas_body_initialize(VALUE self, VALUE v_type, VALUE v_number, VALUE v_name)
{
  short int type;
  short int number;
  char * name;
  char nul = '\0';

  type = (short int)NUM2INT(v_type);
  number = (short int)NUM2INT(v_number);
  v_name = StringValue(v_name);
  name = RSTRING(v_name)->ptr;
  if(name == NULL) {
    name = &nul;
  }

  rb_novas_body_initialize_c(self, type, number, name);
  return self;
}

void
init_body()
{
  // Novas::Body class
  VALUE rb_mNovas = rb_define_module("Novas");
  VALUE rb_cBody = rb_define_class_under(rb_mNovas,"Body",rb_cObject);

  // Body Class
  rb_define_alloc_func(rb_cBody, rb_novas_body_alloc);
  rb_define_method(rb_cBody, "initialize", rb_novas_body_initialize, 3);

  BIND_GET_ATTR(Body,type,body,type);
  BIND_GET_ATTR(Body,number,body,number);
  BIND_GET_ATTR(Body,name,body,name);

  // Novas Module Constants
  MAKE_BODY_CONST(0,1,MERCURY);
  MAKE_BODY_CONST(0,2,VENUS);
  MAKE_BODY_CONST(0,3,EARTH);
  MAKE_BODY_CONST(0,4,MARS);
  MAKE_BODY_CONST(0,5,JUPITER);
  MAKE_BODY_CONST(0,6,SATURN);
  MAKE_BODY_CONST(0,7,URANUS);
  MAKE_BODY_CONST(0,8,NEPTUNE);
  MAKE_BODY_CONST(0,9,PLUTO);
  MAKE_BODY_CONST(0,10,SUN);
  MAKE_BODY_CONST(0,11,MOON);
}
