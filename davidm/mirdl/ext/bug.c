// Functions from bug.c

#include "mirdl.h"

#define MIRDL_BUG_FMT ("### %s [%s]:  %s")
#define MIRDL_BUGABOO "mirdl_bugaboo"

static ID id_call;
static VALUE bug_proc = Qnil;
static char * bug_label;

// TODO Move constants to mirdl.rb
//module Mirdl
//
//  BUGSEV = {
//    'i' => 'Informational', 'I' => 'Informational',
//    'w' => 'Warning',       'W' => 'Warning',
//    'e' => 'Error',         'E' => 'Error',
//    'f' => 'Fatal',         'F' => 'Fatal'
//  }
//
//  BUGSEV_INFO  = 'i'
//  BUGSEV_WARN  = 'w'
//  BUGSEV_ERROR = 'e'
//  BUGSEV_FATAL = 'f'
//
//  BUGLABEL = '(NOT SET)'

// void bug_c(char s,Const char *m)
static VALUE mirdl_bug_body(VALUE sym, VALUE args)
{
  char sev;
  char * msg;
  VALUE vs = rb_ary_entry(args, 0);
  VALUE vm = rb_ary_entry(args, 1);

  if(FIXNUM_P(vs)) {
    sev = (char)FIX2INT(vs);
  } else {
    sev = *SYMSTR_PTR(vs);
    rb_warn("sev=%c", sev);
  }
  msg = StringValueCStr(vm);

  bug_c(sev, msg);
}

static VALUE mirdl_bug(VALUE self, VALUE vs, VALUE vm)
{
  // Catch mirdl bugaboo to get around "code should not come here" if handler
  // does not raise exceptions for errors or fatal errors.
  return rb_catch(MIRDL_BUGABOO, mirdl_bug_body, rb_ary_new3(2, vs, vm));
}

// void buglabel_c(char s,Const char *m)
static VALUE mirdl_buglabel(int argc, VALUE *argv, VALUE self)
{
  if(argc > 0) {
    // Free old copy
    free(bug_label);
    // Make new copy
    bug_label = strdup(StringValueCStr(argv[0]));
    // Pass to miriad
    buglabel_c(bug_label);
    // Return passed in String
    return argv[0];
  }
  // Return copy of current label
  return rb_str_new2(bug_label);
}

// char *bugmessage_c()
static VALUE mirdl_bugmessage(VALUE self)
{
  return rb_str_new2(bugmessage_c());
}

// char bugseverity_c()
static VALUE mirdl_bugseverity(VALUE self)
{
  char sev = bugseverity_c();
  return rb_str_new(&sev, 1);
}

// void bugrecover_c(void (*cl)())
static VALUE mirdl_bugrecover(VALUE self, VALUE lambda)
{
  if(!NIL_P(lambda) && !rb_respond_to(lambda, id_call)) {
    rb_raise(rb_eTypeError, "non-callable object passed");
  }
  bug_proc = lambda;
  return Qnil;
}

// Define bug-handling callback
static void bug_callback()
{
  char sev_c = bugseverity_c();
  char * sev_s = NULL;
  char * msg = bugmessage_c();

  switch(sev_c) {
    //case 'd': case 'D': sev_s = "Debug"; break;
    case 'i': case 'I': sev_s = "Informational"; break;
    case 'w': case 'W': sev_s = "Warning"; break;
    case 'e': case 'E': sev_s = "Error"; break;
    default: sev_s = "Fatal Error"; break;
  }

  if(NIL_P(bug_proc)) {
    // default bug handling
    switch(sev_c) {
      //case 'd': case 'D':
      case 'i': case 'I':
      case 'w': case 'W':
        fprintf(stderr, MIRDL_BUG_FMT, sev_s, bug_label, msg);
        fprintf(stderr, "\n");
        break;
      default:
        rb_raise(rb_eRuntimeError, MIRDL_BUG_FMT, sev_s, bug_label, msg);
    }
  } else {
    // Call user installed proc
    rb_funcall(bug_proc, id_call, 2, rb_str_new2(sev_s), rb_str_new2(msg));
    // Throw mirdl bugaboo to get around "code should not come here" if handler
    // does not raise exceptions for errors or fatal errors.
    rb_throw(MIRDL_BUGABOO, Qnil);
  }
}

void init_mirdl_bug(VALUE mMirdl)
{
  // Initialize IDs etc.
  id_call = rb_intern("call");
  rb_global_variable(&bug_proc);
  bug_label = strdup("(NOT SET)");

  rb_define_module_function(mMirdl, "bug", mirdl_bug, 2);
  rb_define_module_function(mMirdl, "buglabel", mirdl_buglabel, -1);
  rb_define_module_function(mMirdl, "bugmessage", mirdl_bugmessage, 0);
  rb_define_module_function(mMirdl, "bugseverity", mirdl_bugseverity, 0);
  rb_define_module_function(mMirdl, "bugrecover", mirdl_bugrecover, 1);

  // Install bug-handling callback
  bugrecover_c(bug_callback);
}
