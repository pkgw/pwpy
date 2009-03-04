//
// $Id$
//

#ifndef _MIRDL_H_
#define _MIRDL_H_

#include "ruby.h"
#include "miriad.h"

// Value from key.c and keyf.for.  Why not in miriad.h?
#define MAXSTRING 4096

#define SYMSTR_PTR(v) (rb_id2name(rb_to_id(v)))
#define SYMSTR_SYM(v) (ID2SYM(rb_to_id(v)))

#endif // _MIRDL_H_
