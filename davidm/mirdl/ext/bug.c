// Functions from bug.c

#include "mirdl.h"

#define MIRDL_BUG_FMT "### %s [%s]:  %s"

static ID id_call;
static VALUE eMiriadError;
static VALUE eMiriadNonFatalError;
static VALUE bug_proc = Qnil;
static char * bug_label;

// Until early 2009, external (aka "alien") MIRIAD bug handlers could only be
// installed via bugrecover_c.  Bug handlers installed via bugrecover_c cannot
// fully override MIRIAD's default bug handling.  Specifically, on fatal
// errors, MIRIAD's default bug handling code calls habort_c *before* calling
// the handler installed via bugrecover_c.  This closes all open datasets, but
// does not clean up enough so subsequent accesses to the now closed datasets
// can result in a segfault/bus error.  Because of this, the handler installed
// via bugrecover_c is more of a cleanup function than a truly independent bug
// handler.
//
// In early 2009, an alternative to bugrecover_c was created: bughandler_c.
// The bug handler installed via bughandler_c completely overrides MIRIAD's
// default bug handling.  This is a much cleaner interface in that it gives the
// installed handler complete freedom in deciding how or whether to handle even
// fatal "bugs".
//
// If the new style is available, the preprocessor macro HAVE_BUGHANDLER_C will
// be defined and a new-style handler will be installed via bughandler_c.
//
// If the new style handler is NOT available, the preprocessor macro
// HAVE_BUGHANDLER_C will be UNdefined and an old-style handler will be
// installed via bugrecover_c.
//
// In either case, both Mirdl.bugrecover and Mirdl.bughandler are equivalent.
//
// Note that under this old-style interface, it is critical that:
//
// 1. NO dataset access occurs in the user-defined bug handler.
//
// 2. Fatal errors really do cause the process to terminate.
//
// The first point cannot be controlled since the user-defined bug handler is
// user-defined.  The second point, however, can be (and is!) controlled by
// ensuring that the process termintates on fatal errors if the user-defined
// error handler does not.
//
// These restrictions are not applicable to the new-style bug handler
// interface.

#ifdef HAVE_BUGHANDLER_C
#define INSTALL_BUG_CALLBACK(f) bughandler_c(f)
#else
#define INSTALL_BUG_CALLBACK(f) bugrecover_c(f)
#endif

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

// void bughandler_c(void (*handler)(char s, Const char *m))
// void bugrecover_c(void (*cl)())
static VALUE mirdl_bugrecover(VALUE self, VALUE lambda)
{
  if(!NIL_P(lambda) && !rb_respond_to(lambda, id_call)) {
    rb_raise(rb_eTypeError, "non-callable object passed");
  }
  bug_proc = lambda;
  return Qnil;
}

#ifndef HAVE_BUGHANDLER_C
// If the miriad library lacks the new-style bug handler interface, this is the
// function that calls the user-defined bughandler.  It is not called directly.
// Instead it is called as the "body" parameter to rb_ensure(), which is called
// from the bug_callback function below.
static VALUE call_bug_proc(VALUE args)
{
  VALUE vsev = rb_ary_entry(args, 0);
  VALUE vmsg = rb_ary_entry(args, 1);

  rb_funcall(bug_proc, id_call, 2, vsev, vmsg);
  return Qnil;
}

// If the miriad library lacks the new-style bug handler interface, this is the
// "ensure block" that will be called if a user-defined bug handler does not
// terminate the process.  It is not called directly.  Instead it is called as
// the "ensure" parameter to rb_ensure, which is called from the bug_callback
// function below.  See comments at top of file for more details.
static VALUE bug_proc_ensure(VALUE args)
{
  VALUE vsev = rb_ary_entry(args, 0);
  VALUE vmsg = rb_ary_entry(args, 1);

  char * sev = RSTRING_PTR(vsev);
  char * msg = RSTRING_PTR(vmsg);
  char * errmsg;

  if(sev[0] == 'F') {
    errmsg = ALLOCA_N(char,
        strlen(MIRDL_BUG_FMT) + strlen(sev) +
        strlen(bug_label) + strlen(msg));
    sprintf(errmsg, MIRDL_BUG_FMT "\n", sev, bug_label, msg);
    rb_write_error(errmsg);
    rb_exit(1);
  }
  return Qnil;
}
#endif

// Define bug-handling callback
#ifdef HAVE_BUGHANDLER_C
static void bug_callback(char sev_c, char * msg)
#else
static void bug_callback()
#endif
{
#ifndef HAVE_BUGHANDLER_C
  char sev_c = bugseverity_c();
  char * msg = bugmessage_c();
#endif
  char * sev_s = NULL;
  char * errmsg;
  VALUE vsev, vmsg, args;

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
        errmsg = ALLOCA_N(char,
            strlen(MIRDL_BUG_FMT) + strlen(sev_s) +
            strlen(bug_label) + strlen(msg));
        sprintf(errmsg, MIRDL_BUG_FMT "\n", sev_s, bug_label, msg);
        rb_write_error(errmsg);
        break;
      case 'e': case 'E':
        // Raise MiriadNonFatalError
        rb_raise(eMiriadNonFatalError, MIRDL_BUG_FMT, sev_s, bug_label, msg);
      default:
#ifdef HAVE_BUGHANDLER_C
        // Raise MiriadError
        rb_raise(eMiriadError, MIRDL_BUG_FMT, sev_s, bug_label, msg);
#else
        // Raise SystemExit
        errmsg = ALLOCA_N(char,
            strlen(MIRDL_BUG_FMT) + strlen(sev_s) +
            strlen(bug_label) + strlen(msg));
        sprintf(errmsg, MIRDL_BUG_FMT "\n", sev_s, bug_label, msg);
        rb_write_error(errmsg);
        rb_exit(1);
#endif
    }
  } else {
    vsev = rb_str_new2(sev_s);
    vmsg = rb_str_new2(msg);
#ifdef HAVE_BUGHANDLER_C
    // Call user installed proc directly
    rb_funcall(bug_proc, id_call, 2, vsev, vmsg);
#else
    // Call user installed proc with ensure block
    args = rb_ary_new3( 2, vsev, vmsg);
    rb_ensure(call_bug_proc, args, bug_proc_ensure, args);
#endif
  }
}

void init_mirdl_bug(VALUE mMirdl)
{
  // Initialize IDs etc.
  id_call = rb_intern("call");
  // Define MiriadNonFatalError as subclass of MiriadError so that "rescue
  // MiriadNonFatalError" will not rescue MiriadError, but "rescue MiriadError"
  // will rescue MiriadNonFatalError.

  // MiriadError is raised for fatal bugs.
  eMiriadError = rb_define_class("MiriadError", rb_eStandardError);
  // MiriadNonFatalError is raised for error (i.e. non-fatal) bugs.
  eMiriadNonFatalError = rb_define_class("MiriadNonFatalError", eMiriadError);
  rb_global_variable(&bug_proc);
  bug_label = strdup("(NOT SET)");

  rb_define_module_function(mMirdl, "bug", mirdl_bug, 2);
  rb_define_module_function(mMirdl, "buglabel", mirdl_buglabel, -1);
  rb_define_module_function(mMirdl, "bugrecover", mirdl_bugrecover, 1);
  rb_define_alias(mMirdl, "bughandler", "bugrecover");

  // Install bug-handling callback
  INSTALL_BUG_CALLBACK(bug_callback);

#ifndef HAVE_BUGHANDLER_C
  // Print warning
  rb_warning("using MIRIAD old-style bug handler");
#endif
}
