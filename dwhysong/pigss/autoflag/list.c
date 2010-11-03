/*
 *  list.c routines for linked lists and stacks
 *
 *  Copyright (C) 1999  David Whysong
 *
 *	This library is free software; you can redistribute it and/or
 *	modify it under the terms of the GNU Library General Public
 *	License as published by the Free Software Foundation, version 2.
 *
 * Original version intended for use by my stellar dynamics package
 */

#include <stdlib.h>
#include <stdio.h>
#include "list.h"

/*
 * Dump the contents of a list or stack to the screen. Useful for debugging.
 */
void dump_list(plist list)
{
	printf("Dumping the stack:\n");
	while (list != NULL) {
		printf("\tEntry %p\tnext %p\tprev %p\tdata %p\n",list,list->next,list->prev,list->data);
		list = list->next;
	}
	printf("\n");
}


/*
 * This removes *ALL* occurances of both *a and *b from the stack.
 */
plist strip_from_stack(plist st, void *a, void *b)
{
	plist c, d;

	c = st;
	while (c != NULL) {
		if ((c->data == a) || (c->data == b)) {
			d = c;
			c = c->next;
			st = list_remove(st,d);
		}
		else c = c->next;
	}
	return(st);
}


plist list_removeall(plist st, void *a)
{
	plist tmp, n=st;

	while (n != NULL) {
		if (n->data == a) {
			tmp = n;
			n = n->next;
			st = list_remove(st,tmp);
		}
		else n = n->next;
	}
	return (n);
}


/*
 * Free all entries in a list.
 */
void list_erase(plist list)
{
	plist tmp = list;
	while (list) {
		tmp = list->next;
		free(list);
		list = tmp;
	}
}


/*
 * Return a copy of the list.
 */
plist list_copy(plist list)
{
	plist head, new, prev;

	if (list == NULL) return(NULL);

	head = (plist) malloc(sizeof(struct list));
	head->prev = NULL;
	head->data = list->data;
	prev = head;
	list = list->next;
	while (list) {
		new = (plist) malloc(sizeof(struct list));
		new->prev = prev;
		prev->next = new;
		new->data = list->data;
		prev = new;
		list = list->next;
	}
	prev->next = NULL;
	return(head);
}


/*
 * Add an item to the beginning of a linked list. Returns
 * a pointer to the linked list.
 */
plist list_add(plist list, void *data)
{
	plist tmp;

	tmp = (plist) malloc(sizeof(struct list));
	tmp->prev = NULL;
	tmp->data = data;
	if (list == NULL) {		/* List was empty */
		tmp->next = NULL;
		return (tmp);
	}
	else if (list->prev != NULL) goto bad;
	list->prev = tmp;
	tmp->next = list;
	return(tmp);

bad:	fprintf(stderr,"Error: attempt to insert in middle of linked list.\n");
	return(list);
}

/*
 * Remove an item from a linked list. This does not
 * free whatever item->data points to!
 */
plist list_remove(plist list, plist item)
{
	plist tmp;

	if (list->prev != NULL) abort();

	if (item == NULL) goto bad;
	else if (item->prev == NULL) {		/* Remove first node in list */
		tmp = item->next;
		if (tmp != NULL) tmp->prev = NULL;
		free(item);
		return(tmp);
	}
	else if (item->next == NULL) {		/* Remove last node in list */
		tmp = item->prev;
		tmp->next = NULL;
		free(item);
		return(list);
	}
	else {					/* Remove from middle of list */
		tmp = item->next;
		tmp->prev = item->prev;
		tmp->prev->next = tmp;
		free(item);
		return(list);
	}

bad:	fprintf(stderr,"Error: attempt to free NULL or empty linked list.\n");
	return(NULL);
}

/*
 * Remove the first item from the list, returning it's data.
 * This, and the push macro, treats the list like a stack.
 */
void *pop(plist *stack)
{
	plist tmp;
	void *data;

	if (*stack == NULL) return (NULL);

	tmp = *stack;
	data = (*stack)->data;
	*stack = (*stack)->next;
	if (*stack == NULL) stack = NULL;
	else (*stack)->prev = NULL;
	free(tmp);

	return(data);
}


/*
 * Without debugging, push is just a macro for list_add.
 * But we want to be careful that we never push an item on to the stack
 * if it is already on the stack, hence this function.
 *
 * If something does end up on the list more than once, it is sufficient
 * to fix pop() to remove all instances of that item from the list/stack.
 */
/*
plist push(struct list *st, void *data)
{
	plist tmp;

	tmp = st;
	while (tmp != NULL) {
		if (tmp->data == data) {
			fprintf(stderr,"Danger! Pushing the same object into" \
				" the stack twice!\nStack dump follows:\n\n");
			tmp = st;
			while (tmp != NULL) {
				fprintf(stderr,"%p\n",tmp->data);
				tmp = tmp->next;
			}
			exit(1);
		}
		tmp = tmp->next;
	}

	tmp = (plist) malloc(sizeof(struct list));

fprintf(stderr,"Pushing %p\n",data);

	tmp->prev = NULL;
	tmp->data = data;
	if (st == NULL) {
		tmp->next = NULL;
		return (tmp);
	}
	else if (st->prev != NULL) goto bad;
	st->prev = tmp;
	tmp->next = st;
	return(tmp);

bad:	fprintf(stderr,"Error: attempt to insert in middle of linked list.\n");
	return(st);
}
*/
