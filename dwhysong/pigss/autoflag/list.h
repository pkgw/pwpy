/*
 *  list.h definitions for doubly linked lists
 *
 *  Copyright (C) 1999  David Whysong
 *
 *	This library is free software; you can redistribute it and/or
 *	modify it under the terms of the GNU Library General Public
 *	License as published by the Free Software Foundation, version 2.
 */

typedef struct list *plist;
typedef struct list {
	plist next, prev;
	void *data;
} list;

void list_erase(plist);
plist list_copy(plist);
void dump_list(plist);
plist list_add(plist, void *);
plist list_removeall(plist, void *);
plist strip_from_stack(plist, void *, void *);
plist list_remove(struct list *, struct list *);
void *pop(plist *);
#define push(stack, data) stack=list_add(stack, data)
