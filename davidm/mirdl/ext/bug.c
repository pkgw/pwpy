// Functions from bug.c

#include "mirdl.h"

#define MIRDL_BUG_FMT "### %s [%s]:  %s"

static ID id_call;
static VALUE bug_proc = Qnil;
static char * bug_label;

// On fatal errors, the MIRIAD bug_c function calls habort_c *before* calling
// the user-defined bug handling/cleanup function.  This closes all open
// datasets, but does not clean up enough so subsequent accesses to the now
// closed datasets can result in a segfault/bus error.
//
// It is therefore critical that:
//
// 1. NO dataset access occurs in the user-defined bug handler.
// 2. Fatal errors really do cause the process to terminate.
//
// The first point cannot be controlled since the user-defined bug handler is
// user-defined.  The second point, however, can be controlled by ensuring that
// the process termintates on fatal errors if the user-defined error handler
// does not.

// void bug_c(char s,Const char *m)
static VALUE mirdl_bug(VALUE self, VALUE vs, VALUE vm)
{
  char sev;
  char * msg;

  if(FIXNUM_P(vs)) {
    sev = (char)FIX2INT(vs);
  } else {
    sev = *SYMSTR_PTR(vs);
  }
  msg = StringValueCStr(vm);

  bug_c(sev, msg);
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

// This is the function that calls the user-defined bughandler.  It is not
// called directly.  Instead it is called as the "body" parameter to
// rb_ensure(), which is called from the bug_callback function below.
static VALUE call_bug_proc(VALUE args)
{
  VALUE vsev = rb_ary_entry(args, 0);
  VALUE vmsg = rb_ary_entry(args, 1);

  rb_funcall(bug_proc, id_call, 2, vsev, vmsg);
  return Qnil;
}

// This is the "ensure block" that will be called if a user-defined bug handler
// does not terminate the process.  It is not called directly.  Instead it is
// called as the "ensure" parameter to rb_ensure, which is called from the
// bug_callback function below.  See comments at top of file for more details.
static VALUE bug_proc_ensure(VALUE args)
{
  VALUE vsev = rb_ary_entry(args, 0);
  VALUE vmsg = rb_ary_entry(args, 1);

  char * sev = RSTRING_PTR(vsev);
  char * msg = RSTRING_PTR(vmsg);

  if(sev[0] == 'F') {
    rb_fatal(MIRDL_BUG_FMT "\nprocess terminating", sev, bug_label, msg);
  }
  return Qnil;
}

// Define bug-handling callback
static void bug_callback()
{
  char sev_c = bugseverity_c();
  char * sev_s = NULL;
  char * msg = bugmessage_c();
  VALUE args;

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
      case 'e': case 'E':
        rb_raise(rb_eRuntimeError, "\n" MIRDL_BUG_FMT "\n", sev_s, bug_label, msg);
      default:
        rb_fatal("\n" MIRDL_BUG_FMT "\nprocess terminating\n", sev_s, bug_label, msg);
    }
  } else {
    // Call user installed proc with ensure block
    args = rb_ary_new3( 2, rb_str_new2(sev_s), rb_str_new2(msg));
    rb_ensure(call_bug_proc, args, bug_proc_ensure, args);
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
